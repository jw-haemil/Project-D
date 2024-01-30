import asyncio
import aiomysql
import logging

logger = logging.getLogger("discord.bot.database")


class DataSQL():
    """데이터베이스 클래스"""

    def __init__(self, host: str, port: int, loop: asyncio.AbstractEventLoop = None):
        """데이터베이스

        Args:
            host (str): 호스트
            port (int): 포트
            loop (asyncio.AbstractEventLoop, optional): 비동기 작업을 위한 eventloop Defaults to None.
        """
        self.host = host
        self.port = int(port)
        self.loop = loop

        self.pool = None

    async def auth(self, user: str, password: str, database: str, autocommit: bool = True) -> bool:
        """mysql서버에 접속합니다.

        Args:
            user (str): user 이름
            password (str): 접속 비밀번호
            database (str): 접속할 데이터베이스 이름.
            autocommit (bool, optional): 변경내용 자동반영. Defaults to True.
        
        Return:
            bool: 접속 성공 여부.
        """
        # self.__auth_user = user
        # self.__auth_password = password
        # self.__auth_database = database
        # self.__auth_autocommit = autocommit

        try:
            self.pool: aiomysql.Pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=user,
                password=password,
                db=database,
                loop=self.loop,
                autocommit=autocommit
            )
        except aiomysql.MySQLError as e:
            self.pool = None
            logger.error(f"Database connection failed: {e}")
            return False
        else:
            logger.info("Database connection established")
            return True
    
    async def close(self) -> bool:
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()

            logger.info("Database connection closed")
            return True
        return False
    
    async def _query(self, query: str, args: tuple = None, fetch: bool = False) -> list:
        logger.debug(f"Query: {query}, Args: {args}")

        async with self.pool.acquire() as conn: # poll에 접속
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                if fetch:
                    return await cur.fetchall()
                else:
                    return None

    async def select(self, table: str, columns: list[str] = None, user_id: int = None) -> list:
        """|coro|
        테이블의 데이터를 조회합니다.
        
        Args:
            table (str): 테이블 이름
            columns (list[str], optional): 조회할 컬럼. Defaults to None.
            user_id (int, optional): 유저 아이디. Defaults to None.
        
        Returns:
            list: 조회된 데이터
        """
        if columns is None:
            columns = "*"
        query = f"SELECT {','.join(columns)} FROM {table}"
        if user_id is not None:
            query += f" WHERE id={user_id}"
        return await self._query(query, fetch=True)

    async def update(self, table: str, data: dict, user_id: int = None) -> None:
        """|coro|
        테이블의 데이터를 업데이트합니다.

        Args:
            table (str): 테이블 이름
            data (dict): 업데이트할 데이터
            user_id (int, optional): 유저 아이디. Defaults to None.
        """
        query = f"UPDATE {table} SET {','.join([f'{k}=%s' for k in data.keys()])}"
        if user_id is not None:
            query += f" WHERE id={user_id}"
        args = tuple(data.values())
        return await self._query(query, args)

    async def delete(self, table: str, user_id: int = None) -> None:
        """|coro|
        테이블의 데이터를 삭제합니다.

        Args:
            table (str): 테이블 이름
            user_id (int, optional): 유저 아이디. Defaults to None.
        """
        query = f"DELETE FROM {table}"
        if user_id is not None:
            query += f" WHERE id={user_id}"
        return await self._query(query)

    async def insert(self, table: str, data: dict) -> None:
        """|coro|
        테이블에 데이터를 추가합니다.

        Args:
            table (str): 테이블 이름
            data (dict): 추가할 데이터
        """
        query = f"INSERT INTO {table} ({','.join(data.keys())}) VALUES ({','.join(['%s'] * len(data))})"
        args = tuple(data.values())
        return await self._query(query, args)

    async def count(self, table: str, condition: dict = None) -> int:
        """|coro|
        테이블의 데이터 개수를 조회합니다.

        Args:
            table (str): 테이블 이름
            condition (dict, optional): 조건. Defaults to None.

        Returns:
            int: 데이터 개수
        """
        query = f"SELECT COUNT(*) FROM {table}"
        if condition is not None:
            query += f" WHERE {' AND '.join([f'{k}=%s' for k in condition.keys()])}"
        args = tuple(condition.values()) if condition is not None else None
        return (await self._query(query, args, fetch=True))[0][0]
    
    def get_user_info(self, user_id: int) -> "UserInfo":
        """유저 정보를 생성합니다.

        Args:
            user_id (int): 유저 아이디

        Returns:
            UserInfo: 유저 정보
        """
        return UserInfo(self, user_id)


class UserInfo():
    def __init__(self, database: DataSQL, user_id: int) -> None:
        self._database = database
        self._user_id = user_id
    
    async def is_valid_user(self) -> bool:
        """|coro|
        유저 정보가 유효한지 확인합니다.

        Args:
            user_id (int): 유저 아이디

        Returns:
            bool: 유효 여부
        """
        return await self._database.count("user_info", {"id": self._user_id}) > 0

    async def add_user(self) -> None:
        """|coro|
        유저 정보를 추가합니다.

        Args:
            user_id (int): 유저 아이디
        """
        await self._database.insert(
            table="user_info",
            data={
                "id": self._user_id,
                "money": 0
            }
        )

    async def delete_user(self) -> None:
        """|coro|
        유저 정보를 삭제합니다.

        Args:
            user_id (int): 유저 아이디
        """
        await self._database.delete(table="user_info", user_id=self._user_id)

    def get_id(self) -> int:
        """유저 아이디를 반환힙니다.

        Returns:
            int: 유저 아이디
        """
        return self._user_id

    async def get_money(self) -> int:
        """|coro|
        유저의 돈을 조회합니다.

        Returns:
            int: 돈
        """
        result = await self._database.select(table="user_info", user_id=self._user_id)
        return int(result[0][1])
    
    async def set_money(self, money: int) -> None:
        """|coro|
        유저의 돈을 설정합니다.

        Args:
            money (int): 돈
        """
        await self._database.update(table="user_info", data={"money": money}, user_id=self._user_id)

    async def add_money(self, money: int) -> None:
        """|coro|
        유저의 돈을 추가합니다.

        Args:
            money (int): 돈
        """
        await self.set_money(await self.get_money() + money)

    async def get_check_time(self) -> int | None:
        """|coro|
        유저의 최근 출석체크 시간을 조회합니다.

        Returns:
            int: 최근 출석체크 시간
        """
        result = await self._database.select(table="user_info", user_id=self._user_id)
        return int(result[0][2])
    
    async def set_check_time(self, check_time: int) -> None:
        """|coro|
        유저의 최근 출석체크 시간을 설정합니다.

        Args:
            check_time (int): 최근 출석체크 시간
        """
        await self._database.update(table="user_info", data={"check_time": check_time}, user_id=self._user_id)
