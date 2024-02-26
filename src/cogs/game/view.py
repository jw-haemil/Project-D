import discord

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game


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
            for user in view.users.values():
                if user in view.cog.tic_tac_toe_users:
                    view.cog.tic_tac_toe_users.remove(user) # 게임에 참가중인 유저 목록에서 제거

            if winner == view.Tie:
                content = "비겼습니다."
            else:
                content = f"{view.users[winner].mention}님이 승리하셨습니다."

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

    def __init__(self, cog: "Game", message: discord.Message, users: dict[int, discord.Member]):
        super().__init__(timeout=cog.bot_setting.ticitactoe_game_timeout)
        self.cog = cog
        self.message = message
        self.users = users

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
        for user in self.users.values():
            if user in self.cog.tic_tac_toe_users:
                self.cog.tic_tac_toe_users.remove(user) # 게임에 참가중인 유저 목록에서 제거

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


class TicTacToeInviteView(discord.ui.View):
    def __init__(self, cog: "Game", admin: discord.Member, another: discord.Member):
        super().__init__(timeout=cog.bot_setting.tictactoe_invite_timeout)
        self._cog = cog
        self._admin = admin
        self._another = another

    @discord.ui.button(label="거절", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self._another: # 초대를 받은 사람이 맞는지 확인
            return

        await interaction.response.edit_message(content="초대가 거절되었습니다.", view=None)

    @discord.ui.button(label="수락", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self._another: # 초대를 받은 사람이 맞는지 확인
            return

        if self._another in self._cog.tic_tac_toe_users:
            await interaction.response.send_message("이미 참가중인 게임이 있습니다.", ephemeral=True)
            return
        elif self._admin in self._cog.tic_tac_toe_users:
            await interaction.response.send_message("이미 참가중인 게임이 있는 유저입니다.", ephemeral=True)
            return

        self._cog.tic_tac_toe_users.add(self._admin)
        self._cog.tic_tac_toe_users.add(self._another)

        game_order = dict(zip([TicTacToeView.X, TicTacToeView.O], random.sample([self._admin, self._another], 2))) # 게임 순서
        content = (
            f"O: {game_order[TicTacToeView.O].mention}",
            f"X: {game_order[TicTacToeView.X].mention}",
            f"\n{game_order[TicTacToeView.X].display_name}님이 선공입니다."
        )
        await interaction.response.edit_message(
            content="\n".join(content),
            view=TicTacToeView(self._cog, interaction.message, game_order)
        )
