import discord
from discord.ext import commands

import random
from datetime import datetime, timedelta

from src.classes import command_checks
from src.classes.bot import Bot, Cog


class Finance(Cog):
    @commands.command(
        name="자산정보",
        aliases=["돈", "자산", "잔액", "잔고", "ㄷ"],
        description="내 자산, 타인의 자산을 확인합니다.",
        usage="자산정보 [유저명]"
    )
    async def asset_info(self, ctx: commands.Context[Bot], other_user: discord.Member = None):
        user = ctx.author if other_user is None or other_user == ctx.author else other_user
        user_info = self.database.get_user_info(user.id)

        if not await user_info.is_valid_user():
            if user is ctx.author:
                await ctx.reply("사용자 등록을 먼저 해 주세요.")
            else:
                await ctx.reply(f"{other_user.display_name}님은 등록되어 있지 않은 유저입니다.")
            return

        embed = discord.Embed(
            title=f"{user.display_name}님의 자산정보",
            color=discord.Color.random()
        )
        embed.add_field(name="자산", value=f"{await user_info.get_money():,}원")
        await ctx.reply(embed=embed)

    @asset_info.error
    async def asset_info_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.reply("사용자를 다시한번 확인해 주세요.")
            ctx.command_failed = False


    @commands.command(
        name="랭킹",
        aliases=["순위", "ㄹㅋ"],
        description="자산 순위를 확인합니다.",
        usage="랭킹"
    )
    async def ranking(self, ctx: commands.Context[Bot]):
        info = tuple( # db에서 유저정보 가져오기
            map(
                lambda x: tuple(map(int, x)),
                await self.database._query(
                    f"SELECT id, money FROM user_info WHERE id IN ({','.join(['%s'] * len(ctx.guild.members))});",
                    [member.id for member in ctx.guild.members],
                    fetch=True
                )
            )
        )
        info = sorted(info, key=lambda x: x[1], reverse=True)[:10] # 돈 순으로 정렬

        embed = discord.Embed(
            title="자산랭킹",
            color=discord.Color.random()
        )
        embed.set_footer(text="랭킹은 최대 10명으로 제한됩니다.")
        for n, (id, money) in enumerate(info):
            user = ctx.guild.get_member(id)
            embed.add_field(name=f"{n+1}위", value=f"{user.display_name} ({money:,}원)", inline=False)

        await ctx.reply(embed=embed)


    @commands.command(
        name="돈받기",
        aliases=["ㄷㅂㄱ", "지원금", "ㅊㅊ", "출첵", "출석체크"],
        description="일정시간마다 돈을 받습니다.",
        usage="돈받기"
    )
    @command_checks.is_registered() # 사용자 등록 여부 확인
    async def attendance(self, ctx: commands.Context[Bot]):
        user_info = self.database.get_user_info(ctx.author.id)

        cooldown = timedelta(hours=self.bot_setting.attendance_cooldown)
        check_time = datetime.utcfromtimestamp(await user_info.get_check_time()) # 출석체크 시간 가져오기
        if (check_time + cooldown) <= datetime.utcnow(): # 시간 비교
            if random.random() < self.bot_setting.attendance_bonus_money_prob:
                money = self.bot_setting.attendance_bonus_money
                message = f"축하합니다!🎉 {self.bot_setting.attendance_bonus_money_prob*100}% 확률을 뚫고 {money:,}원을 받았습니다."
            else:
                money = random.randint(
                    self.bot_setting.attendance_random_money_min,
                    self.bot_setting.attendance_random_money_max
                ) * self.bot_setting.attendance_multiple # 돈 추출
                message = f"{money:,}원을 받았습니다."
            message += f"\n다음 돈받기 시간은 <t:{int((datetime.now() + cooldown).timestamp())}:T> 입니다."

            await user_info.add_money(money) # 돈 추가
            await user_info.set_check_time(int(datetime.now().timestamp())) # 출석체크 시간 업데이트
            await ctx.reply(message)

        else:
            remaining_time = (check_time + cooldown) - datetime.utcnow() # 남은 시간 계산
            hours, remainder = map(int, divmod(remaining_time.total_seconds(), 3600))
            minutes, seconds = map(int, divmod(remainder, 60))
            await ctx.reply(f"돈받기를 하려면 {hours}시간 {minutes}분 {seconds}초를 더 기다려야 합니다.\n다음 돈받기 시간은 <t:{int((check_time + cooldown).timestamp())}:T> 입니다.")


    @commands.command(
        name="송금",
        aliases=["ㅅㄱ"],
        description="다른 사람에게 돈을 보냅니다.",
        usage="송금 [유저명] [금액]"
    )
    @command_checks.is_registered() # 사용자 등록 여부 확인
    async def send_money(self, ctx: commands.Context[Bot], other_user: discord.Member, money: int):
        user_info = self.database.get_user_info(ctx.author.id)
        other_user_info = self.database.get_user_info(other_user.id)

        if not await other_user_info.is_valid_user(): # 사용자 등록 여부 확인
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
    async def send_money_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("보낼 사람과 돈을 입력해 주세요.")
            ctx.command_failed = False

        elif isinstance(error, commands.BadArgument):
            await ctx.reply("보낼 사람과 돈을 다시한번 확인해 주세요.")
            ctx.command_failed = False


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Finance(bot))
