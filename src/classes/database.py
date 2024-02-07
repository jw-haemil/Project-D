import asyncio
import aiomysql
import logging

from src.classes.enums import FishRating, fish_kor_name
import random

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
    
    async def _query(self, query: str, args: tuple = None, fetch: bool = False) -> list | None:
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

    def get_fish_info(self) -> "FishInfo":
        """물고기 정보를 생성합니다.

        Returns:
            FishInfo: 물고기 정보
        """
        return FishInfo(self)


class UserInfo():
    def __init__(self, database: DataSQL, user_id: int) -> None:
        self._database = database
        self._user_id = user_id

    @property
    def id(self) -> int:
        """유저 아이디를 반환힙니다.

        Returns:
            int: 유저 아이디
        """
        return self._user_id


    async def is_valid_user(self) -> bool:
        """|coro|
        유저 정보가 유효한지 확인합니다.

        Args:
            user_id (int): 유저 아이디

        Returns:
            bool: 유효 여부
        """
        logger.debug(f"Checking if user {self._user_id} is valid")
        return await self._database.count("user_info", {"id": self._user_id}) > 0

    async def add_user(self) -> None:
        """|coro|
        유저 정보를 추가합니다.

        Args:
            user_id (int): 유저 아이디
        """
        logger.debug(f"Adding user {self._user_id}")
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
        logger.debug(f"Deleting user {self._user_id}")
        await self._database.delete(table="user_info", user_id=self._user_id)

    async def get_money(self) -> int:
        """|coro|
        유저의 돈을 조회합니다.

        Returns:
            int: 돈
        """
        logger.debug(f"Getting money of user {self._user_id}")
        result = await self._database.select(table="user_info", user_id=self._user_id)
        return int(result[0][1])
    
    async def set_money(self, money: int) -> None:
        """|coro|
        유저의 돈을 설정합니다.

        Args:
            money (int): 돈
        """
        logger.debug(f"Setting money of user {self._user_id}")
        await self._database.update(table="user_info", data={"money": money}, user_id=self._user_id)

    async def add_money(self, money: int) -> None:
        """|coro|
        유저의 돈을 추가합니다.

        Args:
            money (int): 돈
        """
        logger.debug(f"Adding money of user {self._user_id}")
        await self._database._query("UPDATE user_info SET money=money+%s WHERE id=%s", (money, self._user_id))

    async def get_check_time(self) -> int | None:
        """|coro|
        유저의 최근 출석체크 시간을 조회합니다.

        Returns:
            int: 최근 출석체크 시간
        """
        logger.debug(f"Getting check time of user {self._user_id}")
        result = await self._database.select(table="user_info", user_id=self._user_id)
        return int(result[0][2])
    
    async def set_check_time(self, check_time: int) -> None:
        """|coro|
        유저의 최근 출석체크 시간을 설정합니다.

        Args:
            check_time (int): 최근 출석체크 시간
        """
        logger.debug(f"Setting check time of user {self._user_id}")
        await self._database.update(table="user_info", data={"check_time": check_time}, user_id=self._user_id)


class Fish():
    def __init__(
        self,
        id: int,
        name: str,
        rating: int,
        min_length: int,
        max_length: int,
        default_price: int,
        const_value: float,
        description: str
) -> None:
        self._id = id
        self._name = name
        self._rating = rating
        self._min_length = min_length
        self._max_length = max_length
        self._default_price = default_price
        self._const_value = const_value
        self._description = description

        self._length = random.randint(self._min_length, self._max_length)
        self._price = int((self._default_price * self._length) * self._const_value)

    @property
    def id(self) -> int:
        """물고기의 ID를 반환합니다.

        Returns:
            int: 물고기 ID
        """
        return self._id

    @property
    def name(self) -> str:
        """물고기의 이름을 반환합니다.

        Returns:
            str: 물고기 이름
        """
        return self._name

    @property
    def rating(self) -> FishRating:
        """물고기의 등급을 반환합니다.

        Returns:
            FishRating: 물고기 등급
        """
        return FishRating(self._rating)

    @property
    def rating_str(self) -> str:
        """물고기의 등급을 문자열로 반환합니다.

        Returns:
            str: 물고기 등급 문자열
        """
        return fish_kor_name[self.rating]

    @property
    def length(self) -> int | None:
        """물고기의 길이를 반환합니다.

        Returns:
            int: 길이
        """
        return self._length

    @property
    def length_str(self) -> str:
        """물고기의 길이를 문자열로 반환합니다.

        Returns:
            str: 길이 문자열
        """
        if self._length >= 1000:
            length = self._length / 1000
            unit = "m"
        else:
            length = self._length / 10
            unit = "cm"

        return f"{round(length, 2)}{unit}"

    @property
    def price(self) -> int:
        """물고기의 가격을 반환합니다.

        Returns:
            int: 가격
        """
        return self._price

    @property
    def description(self) -> str:
        """물고기의 설명을 반환합니다.

        Returns:
            str: 설명
        """
        return self._description


class FishInfo():
    def __init__(self, database: DataSQL) -> None:
        self._database = database
    
    def _return_value(self, result: list[tuple]) -> list[Fish]:
        return [Fish(
            id=int(row[0]),
            name=row[1],
            rating=int(row[2]),
            min_length=int(row[3]),
            max_length=int(row[4]),
            default_price=int(row[5]),
            const_value=float(row[6]),
            description=row[7]
        ) for row in result]

    def _choose_grade(self) -> FishRating:
        grade_prob = { # 물고기 등급 확률
            FishRating.COMMON: 62.825,
            FishRating.UNCOMMON: 30,
            FishRating.RARE: 5,
            FishRating.EPIC: 2,
            FishRating.LEGENDARY: 0.1,
            FishRating.MYTHIC: 0.025,
        }
        rand_num = random.uniform(0, 100) # 0에서 100까지의 난수 생성
        cumulative_prob = 0

        for grade, prob in grade_prob.items():
            cumulative_prob += prob
            if rand_num <= cumulative_prob:
                return grade


    async def get_random_fish(self) -> Fish:
        """|coro|
        물고기를 랜덤으로 조회합니다.

        Args:
            grade (FishRating): 물고기 등급

        Returns:
            Fish: 물고기
        """
        grade = self._choose_grade() # 물고기 등급 선택
        logger.debug(f"Getting random fish of grade {grade}")
        result = await self._database._query("SELECT * FROM fish_info WHERE rating=%s ORDER BY RAND() LIMIT 1", (grade.value,), fetch=True)
        return self._return_value(result)[0]
