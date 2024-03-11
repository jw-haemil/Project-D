import random
import logging
from typing import TYPE_CHECKING

from src.classes.enums import EFishRating, fish_kor_name

if TYPE_CHECKING:
    from .data_sql import DataSQL

logger = logging.getLogger("discord.bot.database.fish_info")


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
        self._price = round((self._default_price * self._length) * self._const_value)

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
    def rating(self) -> EFishRating:
        """물고기의 등급을 반환합니다.

        Returns:
            FishRating: 물고기 등급
        """
        return EFishRating(self._rating)

    @property
    def rating_str(self) -> str:
        """물고기의 등급을 문자열로 반환합니다.

        Returns:
            str: 물고기 등급 문자열
        """
        return fish_kor_name[self.rating]

    @property
    def length(self) -> int:
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
    def __init__(self, database: "DataSQL") -> None:
        self._database = database

    def _return_value(self, result: list[tuple]) -> list[Fish]:
        return [Fish(
            id=int(row[0]),
            name=row[2],
            rating=int(row[3]),
            min_length=int(row[4]),
            max_length=int(row[5]),
            default_price=int(row[6]),
            const_value=float(row[7]),
            description=row[8]
        ) for row in result]

    def _choose_grade(self) -> EFishRating:
        grade_prob = { # 물고기 등급 확률
            EFishRating.COMMON: 62.825,
            EFishRating.UNCOMMON: 30,
            EFishRating.RARE: 5,
            EFishRating.EPIC: 2,
            EFishRating.LEGENDARY: 0.1,
            EFishRating.MYTHIC: 0.025,
        }
        return random.choices(list(grade_prob.keys()), weights=grade_prob.values())[0]


    async def get_random_fish(self) -> Fish:
        """|coro|
        물고기를 랜덤으로 조회합니다.

        Returns:
            Fish: 물고기
        """
        grade = self._choose_grade() # 물고기 등급 선택
        logger.debug(f"Getting random fish of grade {grade}")
        result = await self._database._query(
            "SELECT * FROM item_types INNER JOIN fish_info ON item_types.id = fish_info.foreign_id WHERE item_types.type = 'fish' AND rating = %s ORDER BY RAND() LIMIT 1",
            (grade.value,),
            fetch=True
        )

        return self._return_value(result)[0]
