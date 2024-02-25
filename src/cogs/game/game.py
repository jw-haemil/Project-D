import discord
from discord.ext import commands

import random
from typing import Optional

from src.classes import command_checks
from src.classes.bot import Bot, Cog
from .view import TicTacToeInviteView
from .converter import CoinFaceConverter, CoinBetConverter


class Game(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.tic_tac_toe_users: set[discord.Member] = set() # 틱택토 유저 정보 저장

    @commands.command(
        name="동전던지기",
        aliases=["동전", "동전뒤집기", "ㄷㅈ"],
        description="금액을 걸고 동전 던지기 게임을 시작합니다."
    )
    @command_checks.is_registered()
    async def coin_flip(self, ctx: commands.Context[Bot], face: CoinFaceConverter, money: CoinBetConverter):
        user_info = self.database.get_user_info(ctx.author.id)

        money = await user_info.get_money() if money in ("올인", "모두") else money
        if money > (user_money := await user_info.get_money()): # 돈이 부족하면
            await ctx.reply(f"돈이 부족합니다. (현재 자산: {user_money:,}원)")
            return
        elif money <= 0:
            await ctx.reply("베팅금액은 1원 이상이어야 합니다.")
            return

        random_face = bool(random.getrandbits(1)) # 랜덤 값 생성
        if random_face == face:
            money = 1 if money == 1 else money//2 # 배팅금액 조정
            await user_info.add_money(money) # 돈 추가
            face_str = "앞" if random_face else "뒷"
            await ctx.reply(f"축하합니다! {face_str}면이 나와 {money:,}원을 받았습니다. (현재 자산: {await user_info.get_money():,}원)")
        else:
            face_str = "앞" if random_face else "뒷"
            # 확정으로 반 차감, coinflip_total_loss_prob의 확률로 모두 잃음
            if money == 1 or random.random() < self.bot_setting.coinflip_total_loss_prob:
                await user_info.add_money(-money) # 돈 차감
                await ctx.reply(f"안타깝게도 {face_str}면이 나와 배팅한 돈의 전부({-money:,}원)를 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")
            else:
                await user_info.add_money(-(money//2)) # 돈 차감
                await ctx.reply(f"안타깝게도 {face_str}면이 나와 배팅한 돈의 절반({-(money//2):,}원)을 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")

    @coin_flip.error
    async def coin_flip_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("동전의 면과 베팅금액을 입력해 주세요.")
            ctx.command_failed = False

        elif isinstance(error, commands.BadArgument):
            await ctx.reply(error.args[0])
            ctx.command_failed = False


    @commands.command(
        name="틱택토",
        aliases=["ㅌㅌㅌ", "ttt"],
        description="틱택토 게임을 합니다.",
    )
    @command_checks.is_registered()
    async def tic_tac_toe(self, ctx: commands.Context[Bot], another: Optional[discord.Member] = None):
        if ctx.author in self.tic_tac_toe_users:
            await ctx.reply("이미 참가중인 게임이 있습니다.")
            return
        elif another in self.tic_tac_toe_users:
            await ctx.reply("이미 참가중인 게임이 있는 유저입니다.")
            return

        if another is None or another == ctx.author:
            await ctx.reply("아직 완성되지 않은 기능 입니다.")
            return

        another_info = self.database.get_user_info(another.id)
        if not await another_info.is_valid_user():
            await ctx.reply(f"{another.display_name}님은 등록되어 있지 않은 유저입니다.")
            return


        async def view_on_timeout(message: discord.Message):
            await message.edit(content="초대시간이 초과되었습니다.", view=None)

        view = TicTacToeInviteView(self, ctx.author, another)
        message = await ctx.send(
            f"{another.mention}\n{ctx.author.display_name}님이 틱택토 1대1 매치에 초대하였습니다.",
            view=view
        )
        view.on_timeout = lambda: view_on_timeout(message)

    @tic_tac_toe.error
    async def tic_tac_toe_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.reply("올바른 상대를 입력해 주세요.")
            ctx.command_failed = False
