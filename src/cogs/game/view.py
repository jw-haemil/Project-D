import discord

import random

from src.classes.bot import Cog


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

    def __init__(self, message: discord.Message, users: dict[int, discord.Member], bet: int):
        super().__init__() # const
        self.message = message
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

    async def on_timeout(self):
        message = await self.message.fetch()
        content = message.content.split("\n")
        winner = self.users[self.X] if self.current_player == self.O else self.users[self.O]
        content[-1] = f"시간이 초과되어 {winner.mention}님이 우승하였습니다."
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="\n".join(content), view=self)

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


class TicTacToeAcceptView(discord.ui.View):
    def __init__(self, cog: Cog, admin: discord.Member, another: discord.Member, bet: int):
        super().__init__()
        self._cog = cog
        self._admin = admin
        self._another = another
        self._bet = bet

    @discord.ui.button(label="거절", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self._another: # 초대를 받은 사람이 맞는지 확인
            return

        await interaction.response.edit_message(content="초대가 거절되었습니다.", view=None)

    @discord.ui.button(label="수락", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self._another: # 초대를 받은 사람이 맞는지 확인
            return

        game_order = dict(zip([TicTacToeView.X, TicTacToeView.O], random.sample([self._admin, self._another], 2))) # 게임 순서
        content = (
            f"O: {game_order[TicTacToeView.O].mention}",
            f"X: {game_order[TicTacToeView.X].mention}",
            f"우승 금액: {self._bet*2:,}원" if self._bet > 0 else None,
            f"\n{game_order[TicTacToeView.X].mention}님이 선공입니다."
        )
        await interaction.response.edit_message(content="\n".join(c for c in content if c is not None), view=TicTacToeView(interaction.message, game_order, self._bet))
