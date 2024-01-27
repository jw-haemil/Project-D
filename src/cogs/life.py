import discord
from discord.ext import commands


class Life(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot



async def setup(bot: commands.Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Life(bot))