import discord

import asyncio
import aiomysql
import logging
import random
from typing import TypedDict

from src.classes.enums import FishRating, fish_kor_name

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

    async def select(self, table: str, columns: list[str] = None, condition: dict = None) -> list:
        """|coro|
        테이블의 데이터를 조회합니다.

        Args:
            table (str): 테이블 이름
            columns (list[str], optional): 조회할 컬럼. Defaults to None.
            condition (dict, optional): 조건. Defaults to None.

        Returns:
            list: 조회된 데이터
        """
        if columns is None:
            columns = "*"
        query = f"SELECT {','.join(columns)} FROM {table}"
        if condition is not None:
            query += f" WHERE {' AND '.join([f'{k}=%s' for k in condition.keys()])}"
        return await self._query(query, tuple(condition.values()), fetch=True)

    async def update(self, table: str, data: dict, condition: dict = None) -> None:
        """|coro|
        테이블의 데이터를 업데이트합니다.

        Args:
            table (str): 테이블 이름
            data (dict): 업데이트할 데이터
            condition (dict, optional): 조건. Defaults to None.
        """
        query = f"UPDATE {table} SET {','.join([f'{k}=%s' for k in data.keys()])}"
        if condition is not None:
            query += f" WHERE {' AND '.join([f'{k}=%s' for k in condition.keys()])}"
        args = tuple(data.values()) + tuple(condition.values())
        return await self._query(query, args)

    async def delete(self, table: str, condition: dict = None) -> None:
        """|coro|
        테이블의 데이터를 삭제합니다.

        Args:
            table (str): 테이블 이름
            condition (dict, optional): 조건. Defaults to None.
        """
        query = f"DELETE FROM {table}"
        if condition is not None:
            query += f" WHERE {' AND '.join([f'{k}=%s' for k in condition.keys()])}"
        args = tuple(condition.values()) if condition is not None else None
        return await self._query(query, args)

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

    async def get_bot_setting(self) -> "BotSetting":
        """|coro|
        봇 설정 정보를 생성합니다.

        Returns:
            BotSetting: 봇 설정 정보
        """
        result = BotSetting(self)
        await result.update_setting()
        return result


class UserInfo():
    def __init__(self, database: DataSQL, user: int | discord.User | discord.Member) -> None:
        self._database = database

        if isinstance(user, (discord.User, discord.Member)):
            self._user = user
            self._user_id = user.id
        else:
            self._user = None
            self._user_id = user

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
        await self._database.delete(table="user_info", condition={"id": self._user_id})

    async def get_money(self) -> int:
        """|coro|
        유저의 돈을 조회합니다.

        Returns:
            int: 돈
        """
        logger.debug(f"Getting money of user {self._user_id}")
        result = await self._database.select(table="user_info", columns=["money"], condition={"id": self._user_id})
        return int(result[0][0])

    async def set_money(self, money: int) -> None:
        """|coro|
        유저의 돈을 설정합니다.

        Args:
            money (int): 돈
        """
        logger.debug(f"Setting money of user {self._user_id}")
        await self._database.update(table="user_info", data={"money": money}, condition={"id": self._user_id})

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
        result = await self._database.select(table="user_info", columns=["check_time"], condition={"id": self._user_id})
        return int(result[0][0])

    async def set_check_time(self, check_time: int) -> None:
        """|coro|
        유저의 최근 출석체크 시간을 설정합니다.

        Args:
            check_time (int): 최근 출석체크 시간
        """
        logger.debug(f"Setting check time of user {self._user_id}")
        await self._database.update(table="user_info", data={"check_time": check_time}, condition={"id": self._user_id})


class Fish():
    def __init__(
        self,
        id: int, # 고유ID
        name: str, # 물고기 이름
        rating: int, # 물고기의 등급
        min_length: int, # 최소길이
        max_length: int, # 최대길이
        default_price: int, # 기본가격
        const_value: float, # 기본가격에 곱할 상수
        description: str # 물고기 설명
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


class BotSettingColumns(TypedDict):
    attendance_cooldown: int # 출석체크 쿨타임 (시간)
    attendance_bonus_money: int # 출석체크 보너스 돈
    attendance_bonus_money_prob: float # 출석체크 보너스 확률 (%)
    attendance_multiple: int # 출석체크 랜덤값의 배수
    attendance_random_money_money_min: int # 출석체크 랜덤값의 최소값
    attendance_random_money_money_max: int # 출석체크 랜덤값의 최대값
    fishing_random_min: int # 낚시에서 물고기가 걸리는 최소시간 (초)
    fishing_random_max: int # 낚시에서 물고기가 걸리는 최대시간 (초)
    fishing_timeout: int # 낚시에서 물고기를 잡는 시간 (초)
    coinflip_total_loss_prob: float # 동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률 (%)


class BotSetting():
    def __init__(self, database: DataSQL) -> None:
        self._database = database
        self._settings: BotSettingColumns = {}

    async def update_setting(self):
        """|coro|
        봇 설정을 업데이트합니다.
        """
        logger.debug("Updating bot setting")
        self._settings['attendance_cooldown'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_cooldown"}))[0][0])
        self._settings['attendance_bonus_money'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_bonus_money"}))[0][0])
        self._settings['attendance_bonus_money_prob'] = float((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_bonus_money_prob"}))[0][0])
        self._settings['attendance_multiple'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_multiple"}))[0][0])
        self._settings['attendance_random_money_min'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_random_money_min"}))[0][0])
        self._settings['attendance_random_money_max'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "attendance_random_money_max"}))[0][0])
        self._settings['fishing_random_min'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "fishing_random_min"}))[0][0])
        self._settings['fishing_random_max'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "fishing_random_max"}))[0][0])
        self._settings['fishing_timeout'] = int((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "fishing_timeout"}))[0][0])
        self._settings['coinflip_total_loss_prob'] = float((await self._database.select(table="bot_setting", columns=["value"], condition={"name": "coinflip_total_loss_prob"}))[0][0])


    @property
    def attendance_cooldown(self) -> int:
        """출석체크 쿨타임을 반환합니다.
        단위: 시간

        Returns:
            int: 출석체크 쿨타임
        """
        return self._settings['attendance_cooldown']

    @property
    def attendance_bonus_money(self) -> int:
        """출석체크 보너스 돈을 반환합니다.

        Returns:
            int: 출석체크 보너스 돈
        """
        return self._settings['attendance_bonus_money']

    @property
    def attendance_bonus_money_prob(self) -> float:
        """출석체크 보너스 확률을 반환합니다.

        확률은 0 ~ 1 사이의 값
        
        Returns:
            float: 출석체크 보너스 확률
        """
        return self._settings['attendance_bonus_money_prob'] / 100 # 확률 단위를 % 로 변환합니다.

    @property
    def attendance_multiple(self) -> int:
        """출석체크 랜덤값의 배수를 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 배수
        """
        return self._settings['attendance_multiple']

    @property
    def attendance_random_money_min(self) -> int:
        """출석체크 랜덤값의 최소값을 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 최소값
        """
        return self._settings['attendance_random_money_min']

    @property
    def attendance_random_money_max(self) -> int:
        """출석체크 랜덤값의 최대값을 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 최대값
        """
        return self._settings['attendance_random_money_max']

    @property
    def fishing_random_min(self) -> int:
        """낚시에서 물고기가 걸리는 최소시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기가 걸리는 최소시간
        """
        return self._settings['fishing_random_min']

    @property
    def fishing_random_max(self) -> int:
        """낚시에서 물고기가 걸리는 최대시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기가 걸리는 최대시간
        """
        return self._settings['fishing_random_max']

    @property
    def fishing_timeout(self) -> int:
        """낚시에서 물고기를 잡는 시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기를 잡는 시간
        """
        return self._settings['fishing_timeout']

    @property
    def coinflip_total_loss_prob(self) -> float:
        """동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률을 반환합니다.

        확률은 0 ~ 1 사이의 값

        Returns:
            float: 동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률
        """
        return self._settings['coinflip_total_loss_prob'] / 100 # 확률 단위를 % 로 변환합니다.