import discord
from discord.ext import commands


class Life(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



def setup(bot: commands.Bot): # setup 함수로 명령어 추가
    bot.add_cog(Life(bot))