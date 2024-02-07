import discord
from discord.ext import commands

import asyncio
import random

from src.classes.bot import Bot, Cog
from src.classes.bot_checks import Checks
from src.classes.enums import fish_embed_color


class Fishing(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.fishing_users = set() # 낚시 유저 정보 저장

    def add_fishing_user(self, user: discord.Member):
        """낚시 유저 정보 저장"""
        self.fishing_users.add(user)

    def remove_fishing_user(self, user: discord.Member):
        """낚시 유저 정보 삭제"""
        self.fishing_users.remove(user)

    def is_fishing_user(self, user: discord.Member):
        """낚시중인 유저인지 확인"""
        return user in self.fishing_users


    @commands.command(
        name="낚시",
        aliases=["ㄴㅅ"],
        description="낚시를 합니다. 낚시도중 메시지가 바뀌었을 때, 반응을 누르면 물고기가 잡힙니다."
    )
    @Checks.is_registered()
    async def fishing(self, ctx: commands.Context[Bot]):
        if self.is_fishing_user(ctx.author):
            await ctx.reply("이미 낚시중입니다.", delete_after=3)
            return

        self.add_fishing_user(ctx.author) # 낚시 시작 처리
        message = await ctx.reply("낚시하는중...")
        await asyncio.sleep(random.randint(5, 15)) # 낚는 시간

        await message.edit(content="무언가가 걸린것 같다!")
        await message.add_reaction("🎣")


        # 반응을 받아서 물고기를 잡았는지 확인하는 코드
        def check(reaction: discord.Reaction, user: discord.Member):
            return user == ctx.author and str(reaction.emoji) == "🎣"

        try:
            await self.bot.wait_for("reaction_add", timeout=3, check=check)
            user_info = ctx.bot.database.get_user_info(ctx.author.id)
            fish_info = ctx.bot.database.get_fish_info()

            fish = await fish_info.get_random_fish()
            await user_info.add_money(fish.price)

            embed = discord.Embed(
                title=f"{fish.name}",
                description=f"{fish.description}",
                colour=fish_embed_color[fish.rating]
            )
            embed.add_field(name="길이", value=f"{fish.length_str}")
            embed.add_field(name="가격", value=f"{fish.price:,}원")
            embed.add_field(name="등급", value=f"{fish.rating_str}")

            await message.edit(content="물고기를 잡았다!", embed=embed)

        except asyncio.TimeoutError:
            await message.edit(content="물고기를 놓쳐버렸다...")

        self.remove_fishing_user(ctx.author) # 낚시 종료 처리
        await message.clear_reactions()

    @fishing.error
    async def fishing_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if ctx.author in self.fishing_users:
            self.remove_fishing_user(ctx.author)


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Fishing(bot))