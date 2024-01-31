import discord
from discord.ext import commands

from classes.bot import Bot, Cog


class LifeConvenience(Cog): ...


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(LifeConvenience(bot))