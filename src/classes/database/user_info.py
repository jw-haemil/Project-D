import discord

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data_sql import DataSQL

logger = logging.getLogger("discord.bot.database.user_info")


class UserInfo():
    def __init__(self, database: "DataSQL", user: int | discord.User | discord.Member) -> None:
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
        # logger.debug(f"Checking if user {self._user_id} is valid")
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

    async def get_check_time(self) -> int:
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
