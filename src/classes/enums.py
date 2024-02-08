import discord
from enum import Enum


class UserInfoColumns(Enum):
    ID = 0
    MONEY = 1
    CHECK_TIME = 2


class FishInfoColumns(Enum):
    ID = 0
    NAME = 1
    RATING = 2
    MIN_LENGTH = 3
    MAX_LENGTH = 4
    DEFAULT_PRICE = 5
    CONST_VALUE = 6
    DESCRIPTION = 7


class FishRating(Enum):
    COMMON = 0 # 일반
    UNCOMMON = 1 # 고급
    RARE = 2 # 희귀
    EPIC = 3 # 에픽
    LEGENDARY = 4 # 전설
    MYTHIC = 5 # 신화

fish_embed_color = {
    FishRating.COMMON: discord.Color.light_grey(),
    FishRating.UNCOMMON: discord.Color.green(),
    FishRating.RARE: discord.Color.blue(),
    FishRating.EPIC: discord.Color.purple(),
    FishRating.LEGENDARY: discord.Color.gold(),
    FishRating.MYTHIC: discord.Color.red()
}

fish_kor_name = {
    FishRating.COMMON: "일반",
    FishRating.UNCOMMON: "고급",
    FishRating.RARE: "희귀",
    FishRating.EPIC: "에픽",
    FishRating.LEGENDARY: "전설",
    FishRating.MYTHIC: "신화"
}