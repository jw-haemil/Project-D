import discord
from discord.ext import commands

import random
from typing import Literal

from src.classes.bot import Bot, Cog


class Game(Cog):
    @commands.command(
        name="동전던지기",
        aliases=["동전", "동전뒤집기", "ㄷㅈ"],
        description="금액을 걸고 동전 던지기 게임을 시작합니다."
    )
    async def coin_flip(self, ctx: commands.Context, face: Literal["앞", "뒤"], money: int | Literal["올인", "모두"]):
        self.logger.debug(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")

        user_info = self.bot.database.get_user_info(ctx.author.id)
        
        if not await user_info.is_valid_user(): # 사용자 등록 여부 확인
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
            return
        
        money = await user_info.get_money() if money in ("올인", "모두") else money
        if money > (user_money := await user_info.get_money()): # 돈이 부족하면
            await ctx.reply(f"돈이 부족합니다. (현재 자산: {user_money:,}원)")
            return
        elif money <= 0:
            await ctx.reply("베팅금액은 1원 이상이어야 합니다.")
            return

        random_face = random.choice(["앞", "뒤"]) # 랜덤 값 생성
        if random_face == face:
            money = 1 if money == 1 else money//2 # 배팅금액 조정
            await user_info.add_money(money) # 돈 추가
            random_face = "뒷" if random_face == "뒤" else random_face
            await ctx.reply(f"축하합니다! {random_face}면이 나와 {money:,}원을 받았습니다. (현재 자산: {await user_info.get_money():,}원)")
        else:
            random_face = "뒷" if random_face == "뒤" else random_face
            # 확정으로 반 차감, 20% 확률로 모두 잃음
            if money == 1 or random.random() < 0.2:
                await user_info.add_money(-money) # 돈 차감
                await ctx.reply(f"안타깝게도 {random_face}면이 나와 배팅한 돈의 전부({-money:,}원)를 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")
            else:
                await user_info.add_money(-(money//2)) # 돈 차감
                await ctx.reply(f"안타깝게도 {random_face}면이 나와 배팅한 돈의 절반({-(money//2):,}원)을 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")

    @coin_flip.error
    async def coin_flip_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("동전의 면과 베팅금액을 입력해 주세요.")

        elif isinstance(error, commands.BadLiteralArgument):
            await ctx.reply("**앞** 또는 **뒤** 중에 하나를 입력해 주세요.")

        elif isinstance(error, commands.BadUnionArgument):
            await ctx.reply("베팅금액은 정수 또는 `올인`, `모두`로 입력해 주세요.")

        else:
            await ctx.send(f"오류가 발생했습니다.\n```{type(error)}: {error}```")


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Game(bot))
    
