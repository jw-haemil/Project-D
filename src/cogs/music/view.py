import discord
from discord.ui import View, Button

from typing import TYPE_CHECKING

from .types import ControlButtonDict, QueuePageButtonDict

if TYPE_CHECKING:
    from .music import Music


class ControlView(View):
    def __init__(self, cog: "Music"):
        super().__init__(timeout=None)
        self.cog = cog
        self.items: ControlButtonDict = {
            "volum_down": Button(emoji="🔉", row=0),
            "volum_up": Button(emoji="🔊", row=0),
            "loop": Button(emoji="🔂", row=0),
            "shuffle": Button(emoji="🔀", row=0),
            "prev": Button(emoji="⏮️", row=1),
            "play": Button(emoji="⏯️", row=1),
            "stop": Button(emoji="⏹️", row=1),
            "next": Button(emoji="⏭️", row=1),
        }

        for key, value in self.items.items():
            self.add_item(value)
            value.callback = getattr(self, f"on_{key}")

    async def on_volum_up(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_volum_down(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_play(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_loop(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_shuffle(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...


class QueuePageView(View):
    def __init__(self, cog: "Music"):
        super().__init__()
        self.cog = cog
        self.items: QueuePageButtonDict = {
            "prev": Button(emoji="⬅️", row=0),
            "next": Button(emoji="➡️", row=0),
        }

        for key, value in self.items.items():
            self.add_item(value)
            value.callback = getattr(self, f"on_{key}")

        self.embed = discord.Embed(title="재생목록", color=discord.Color.random())

    async def on_prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    async def on_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...
