import asyncio
import aiomysql
import logging


class DataSQL():
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
    
    async def auth(self, user: str, password: str, database: str, autocommit: bool = True) -> bool:
        """mysql서버에 접속합니다.

        Args:
            user (str): user 이름
            password (str): 접속 비밀번호
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
            logging.getLogger("discord").error(e)
            return False
        else:
            return True
    
    async def close(self) -> bool:
        if hasattr(self, "pool") and self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            return True
        return False
    
    async def _query(self, query: str, args: tuple = None, fetch: bool = False) -> list:
        # TODO: 쿼리 실행 시 로그 처리
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