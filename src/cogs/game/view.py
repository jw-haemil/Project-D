import discord


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
