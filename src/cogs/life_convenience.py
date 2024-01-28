import discord
from discord.ext import commands

from classes.bot import Bot


class LifeConvenience(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot



async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(LifeConvenience(bot))