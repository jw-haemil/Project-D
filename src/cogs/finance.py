import discord
from discord.ext import commands

import random
import time
from datetime import datetime, timedelta

from classes.bot import Bot


class Finance(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        name="출석체크",
        aliases=["출첵", "ㅊㅊ"],
        description="출석체크를 합니다."
    )
    async def attendance(self, ctx: commands.Context):
        self.bot.logger.info(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")
        user_info = self.bot.database.get_user_info(ctx.author.id)

        if await user_info.is_valid_user(): # 사용자 등록 여부 확인
            check_time = datetime.utcfromtimestamp(await user_info.get_check_time()) # 출석체크 시간 가져오기
            if check_time.date() + timedelta(days=1) <= datetime.utcnow().date(): # 시간 비교
                if random.randint(0, 999) == 511:
                    money = 5000
                    await ctx.send(f"출석체크 완료! 축하합니다! 0.1% 확률을 뚫고 5,000원을 받았습니다.")
                else:
                    money = random.randint(1, 10) * 100
                    await ctx.send(f"출석체크 완료! {money}원을 받았습니다.")

                await user_info.add_money(money) # 돈 추가
                await user_info.set_check_time(time.time()) # 출석체크 시간 업데이트

            else:
                await ctx.send("출석체크는 하루에 한 번만 가능합니다.")

        else:
            await ctx.send("사용자 등록을 먼저 해 주세요.")


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Finance(bot))
