import discord
from discord.ext import commands

import random
from typing import Literal, Optional

from src.classes import command_checks
from src.classes.bot import Bot, Cog


class TicTacToeButton(discord.ui.Button["TicTacToeView"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.gray, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view

        if interaction.user != view.users[view.current_player]: # 본인이 맞는지 확인
            return

        state = view.board[self.y][self.x]
        if state in (view.X, view.O): # 빈 칸인지 확인
            return

        match view.current_player:
            case view.X:
                self.style = discord.ButtonStyle.red
                self.label = "X"
                view.board[self.y][self.x] = view.X
                view.current_player = view.O
            case view.O:
                self.style = discord.ButtonStyle.green
                self.label = "O"
                view.board[self.y][self.x] = view.O
                view.current_player = view.X

        winner = view.check_board_winner()
        if winner is None:
            content = f"{view.users[view.current_player].mention}님의 차례 입니다."
        else:
            content = "비겼습니다." if winner == view.Tie else f"{view.users[winner].mention}님이 승리하셨습니다."

            for child in view.children:
                child.disabled = True

            view.stop()

        message = interaction.message.content.split("\n")
        message[-1] = content
        await interaction.response.edit_message(content="\n".join(message), view=view)


class TicTacToeView(discord.ui.View):
    children: list[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, users: dict[int, discord.Member], bet: int):
        super().__init__()
        self.users = users
        self.bet = bet

        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # If we"re here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None


class Game(Cog):
    @commands.command(
        name="동전던지기",
        aliases=["동전", "동전뒤집기", "ㄷㅈ"],
        description="금액을 걸고 동전 던지기 게임을 시작합니다."
    )
    @command_checks.is_registered()
    async def coin_flip(self, ctx: commands.Context[Bot], face: Literal["앞", "뒤"], money: int | Literal["올인", "모두"]):
        user_info = self.database.get_user_info(ctx.author.id)

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
            if money == 1 or random.random() < self.bot_setting.coinflip_total_loss_prob:
                await user_info.add_money(-money) # 돈 차감
                await ctx.reply(f"안타깝게도 {random_face}면이 나와 배팅한 돈의 전부({-money:,}원)를 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")
            else:
                await user_info.add_money(-(money//2)) # 돈 차감
                await ctx.reply(f"안타깝게도 {random_face}면이 나와 배팅한 돈의 절반({-(money//2):,}원)을 잃었습니다. (현재 자산: {await user_info.get_money():,}원)")

    @coin_flip.error
    async def coin_flip_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("동전의 면과 베팅금액을 입력해 주세요.")
            ctx.command_failed = False

        elif isinstance(error, commands.BadLiteralArgument):
            await ctx.reply("**앞** 또는 **뒤** 중에 하나를 입력해 주세요.")
            ctx.command_failed = False

        elif isinstance(error, commands.BadUnionArgument):
            await ctx.reply("베팅금액은 정수 또는 `올인`, `모두`로 입력해 주세요.")
            ctx.command_failed = False


    @commands.command(
        name="틱택토",
        aliases=["ㅌㅌㅌ", "ttt"],
        description="틱택토 게임을 합니다.",
    )
    @command_checks.is_registered()
    async def tic_tac_toe(self, ctx: commands.Context[Bot], another: Optional[discord.Member] = None, bet: int = 0):
        # TODO: 중복참가 불가능하게 하기
        # TODO: 참가 수락 버튼 만들기

        if another is None or another == ctx.author:
            await ctx.reply("아직 완성되지 않은 기능 입니다.")
            return

        user_info = self.database.get_user_info(ctx.author.id)
        another_info = self.database.get_user_info(another.id)

        if not await another_info.is_valid_user():
            await ctx.reply(f"{another.display_name}님은 등록되어 있지 않은 유저입니다.")
            return

        elif (user_money := await user_info.get_money()) < bet:
            await ctx.reply(f"돈이 부족합니다. (현재 자산: {user_money:,}원)")
            return

        elif await another_info.get_money() < bet:
            await ctx.reply(f"{another.display_name}님의 돈이 부족합니다.")
            return

        game_order = dict(zip([TicTacToeView.X, TicTacToeView.O], random.sample([ctx.author, another], 2)))
        content = (
            f"O: {game_order[TicTacToeView.O].mention}",
            f"X: {game_order[TicTacToeView.X].mention}",
            f"우승 금액: {bet*2:,}원" if bet > 0 else None,
            f"\n{game_order[TicTacToeView.X].mention}님이 선공입니다."
        )
        await ctx.send("\n".join([c for c in content if c is not None]), view=TicTacToeView(game_order, bet))

    @tic_tac_toe.error
    async def tic_tac_toe_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        ...


async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Game(bot))
