import discord
from discord.ext import commands

from src.classes.bot import Bot, Cog


class Fishing(Cog): ...


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Fishing(bot))