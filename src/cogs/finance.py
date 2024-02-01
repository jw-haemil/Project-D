import discord
from discord.ext import commands

import random
from datetime import datetime, timedelta

from src.classes.bot import Bot, Cog


class Finance(Cog):
    @commands.command(
        name="내자산",
        aliases=["돈", "자산", "잔액", "잔고", "ㄷ"],
        description="내 자산, 타인의 자산을 확인합니다."
    )
    async def asset_info(self, ctx: commands.Context, other_user: discord.User = None):
        self.logger.debug(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")

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
            color=discord.Color.random()
        )
        embed.add_field(name="자산", value=f"{await user_info.get_money():,}원")
        await ctx.reply(embed=embed)


    @commands.command(
        name="랭킹",
        aliases=["순위"]
    )
    async def ranking(self, ctx: commands.Context):
        info = tuple( # db에서 유저정보 가져오기
            map(
                lambda x: tuple(map(int, x)),
                await self.bot.database._query(
                    f"select id, money from user_info where id in ({','.join(['%s'] * len(ctx.guild.members))});",
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
        description="돈을 받습니다."
    )
    async def attendance(self, ctx: commands.Context):
        self.logger.debug(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")
        user_info = self.bot.database.get_user_info(ctx.author.id)

        if not await user_info.is_valid_user(): # 사용자 등록 여부 확인
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
            return

        check_time = datetime.utcfromtimestamp(await user_info.get_check_time()) # 출석체크 시간 가져오기
        if (check_time + timedelta(hours=1)) <= datetime.utcnow(): # 시간 비교
            if random.random() < 0.001:
                money = 50000
                message = f"축하합니다!🎉 0.1% 확률을 뚫고 50,000원을 받았습니다."
            else:
                money = random.randint(1, 10) * 1000
                message = f"{money:,}원을 받았습니다."
            message += f"\n다음 돈받기 시간은 <t:{int((datetime.now() + timedelta(hours=1)).timestamp())}:T> 입니다."

            await user_info.add_money(money) # 돈 추가
            await user_info.set_check_time(int(datetime.now().timestamp())) # 출석체크 시간 업데이트
            await ctx.reply(message)

        else:
            await ctx.reply(f"돈받기는 시간당 한 번만 가능합니다.\n다음 돈받기 시간은 <t:{int((check_time + timedelta(hours=10)).timestamp())}:T> 입니다.")


    @commands.command(
        name="송금",
        description="다른 사람에게 돈을 보냅니다."
    )
    async def send_money(self, ctx: commands.Context, other_user: discord.User, money: int):
        self.logger.debug(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")

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
