import discord
from enum import Enum


class EUserInfoColumns(Enum):
    ID = 0
    MONEY = 1
    CHECK_TIME = 2


class EFishInfoColumns(Enum):
    ID = 0
    NAME = 1
    RATING = 2
    MIN_LENGTH = 3
    MAX_LENGTH = 4
    DEFAULT_PRICE = 5
    CONST_VALUE = 6
    DESCRIPTION = 7


class EFishRating(Enum):
    COMMON = 0 # 일반
    UNCOMMON = 1 # 고급
    RARE = 2 # 희귀
    EPIC = 3 # 에픽
    LEGENDARY = 4 # 전설
    MYTHIC = 5 # 신화

fish_embed_color = {
    EFishRating.COMMON: discord.Color.light_grey(),
    EFishRating.UNCOMMON: discord.Color.green(),
    EFishRating.RARE: discord.Color.blue(),
    EFishRating.EPIC: discord.Color.purple(),
    EFishRating.LEGENDARY: discord.Color.gold(),
    EFishRating.MYTHIC: discord.Color.red()
}

fish_kor_name = {
    EFishRating.COMMON: "일반",
    EFishRating.UNCOMMON: "고급",
    EFishRating.RARE: "희귀",
    EFishRating.EPIC: "에픽",
    EFishRating.LEGENDARY: "전설",
    EFishRating.MYTHIC: "신화"
}


class EItemTypes(Enum):
    FISH = "fish"
    ITEM = "item"
    GACHA = "gacha"
