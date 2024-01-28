import discord
from discord.ext import commands

from classes.bot import Bot


class UserManagement(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
    
    @commands.command(
        name="사용자등록",
        aliases=["등록"],
        description="데이터베이스에 사용자를 등록합니다."
    )
    async def register_user(self, ctx: commands.Context):
        if await self.bot.database.count(table="user_info", condition={"id": ctx.author.id}) > 0:
            return await ctx.send("이미 등록된 사용자입니다.")

        await self.bot.database.insert(
            table="user_info",
            data={
                "id": ctx.author.id,
                "money": 0
            }
        )
        await ctx.send("사용자를 등록했습니다.")


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(UserManagement(bot))