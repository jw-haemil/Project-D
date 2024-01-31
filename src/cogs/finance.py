import discord
from discord.ext import commands

import random
import time
from datetime import datetime, timedelta

from src.classes.bot import Bot, Cog


class Finance(Cog):
    @commands.command(
        name="내자산",
        aliases=["돈", "자산", "잔액", "잔고"],
        description="내 자산, 타인의 자산을 확인합니다."
    )
    async def asset_info(self, ctx: commands.Context, other_user: discord.User = None):
        self.logger.info(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")

        if other_user == ctx.author or other_user is None:
            user = ctx.author
            user_info = self.bot.database.get_user_info(user.id)
            if not await user_info.is_valid_user():
                await ctx.reply("사용자 등록을 먼저 해 주세요.")
                return
        else:
            user = other_user
            user_info = self.bot.database.get_user_info(user.id)
            if not await user_info.is_valid_user():
                await ctx.reply(f"{other_user.display_name}님은 등록되어 있지 않은 유저입니다.")
                return

        embed = discord.Embed(
            title=f"{user.display_name}님의 자산정보",
            color=0x00ff00
        )
        embed.add_field(name="자산", value=f"{await user_info.get_money():,}원")
        await ctx.reply(embed=embed)


    @commands.command(
        name="출석체크",
        aliases=["출첵", "ㅊㅊ"],
        description="출석체크를 합니다."
    )
    async def attendance(self, ctx: commands.Context):
        self.logger.info(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")
        user_info = self.bot.database.get_user_info(ctx.author.id)

        if not await user_info.is_valid_user(): # 사용자 등록 여부 확인
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
            return

        check_time = datetime.utcfromtimestamp(await user_info.get_check_time()) # 출석체크 시간 가져오기
        if check_time.date() + timedelta(days=1) <= datetime.utcnow().date(): # 시간 비교
            if random.randint(0, 999) == 511:
                money = 5000
                await ctx.reply(f"출석체크 완료! 축하합니다! 0.1% 확률을 뚫고 5,000원을 받았습니다.")
            else:
                money = random.randint(1, 10) * 100
                await ctx.reply(f"출석체크 완료! {money:,}원을 받았습니다.")

            await user_info.add_money(money) # 돈 추가
            await user_info.set_check_time(int(time.time())) # 출석체크 시간 업데이트

        else:
            await ctx.send("출석체크는 하루에 한 번만 가능합니다.")


    @commands.command(
        name="송금",
        description="다른 사람에게 돈을 보냅니다."
    )
    async def send_money(self, ctx: commands.Context, other_user: discord.User, money: int):
        self.logger.info(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")

        user_info = self.bot.database.get_user_info(ctx.author.id)
        other_user_info = self.bot.database.get_user_info(other_user.id)

        if not await user_info.is_valid_user(): # 사용자 등록 여부 확인
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
            return
        elif not await other_user_info.is_valid_user(): # 사용자 등록 여부 확인
            await ctx.reply(f"{other_user.display_name}님은 등록되어 있지 않은 유저입니다.")
            return
        elif other_user.id == ctx.author.id: # 자기 자신에게 돈을 송금하는 경우 예외처리
            await ctx.reply("자기 자신에게 돈을 송금할 수 없습니다.")
            return
        elif money <= 0:
            await ctx.reply("송금 금액은 1원 이상이어야 합니다.")
            return

        user_money = await user_info.get_money() # 돈 정보를 가져옴
        if money > user_money: # 송금이 불가능하면
            await ctx.reply("돈이 부족합니다.")
            return

        await user_info.set_money(user_money - money)
        await other_user_info.add_money(money)
        await ctx.reply(f"{other_user.display_name}님에게 {money:,}원을 송금했습니다.")

    @send_money.error
    async def send_money_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("보낼 사람과 돈을 입력해 주세요.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.reply("보낼 사람을 찾을 수 없습니다.")
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("보낼 사람과 돈은 정수로 입력해 주세요.")
        else:
            await ctx.reply("오류가 발생했습니다.")
            raise error


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Finance(bot))
