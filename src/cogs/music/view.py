import discord
from discord.ext import commands
from discord.ui import View, Button, Select

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ControlButtonDict, QueuePageButtonDict, SearchViewButtonDict
    from .music import Music
    from src.classes.bot import Bot
    from src.classes.youtube_search import YoutubeSearchAPI, Snippet


class SearchView(View):
    # TODO: 검색결과 받아서 SearchView를 구현
    def __init__(
        self,
        context: commands.Context["Bot"],
        search_api: "YoutubeSearchAPI",
        snippets: list["Snippet"],
        timeout: int = 180
    ):
        super().__init__(timeout=timeout)
        self.context = context
        self.search_api = search_api
        self.current_page = 0
        self.result_size = len(snippets)
        self.max_page = 3
        self.snippets = snippets
        self.items: SearchViewButtonDict = {
            "prev": Button(emoji="⬅️", row=0, disabled=True),
            "next": Button(emoji="➡️", row=0),
            "cancel": Button(emoji="❌", row=0),
            "search": Select(
                placeholder=f"검색 결과 (Page {self.current_page + 1}/{self.max_page})",
                options=[
                    discord.SelectOption(
                        label=f"{(n + 1) + (self.result_size * self.current_page)}. {snippet.title}",
                        description=f"{snippet.channel_title} | {snippet.video_duration}",
                        value=snippet.video_url,
                    ) for n, snippet in enumerate(snippets)
                ],
                row=1
            ),
        }

        for key, value in self.items.items():
            self.add_item(value)
            value.callback = getattr(self, f"on_{key}")

    async def on_prev(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return

        # 첫 페이지일 때 이전 버튼 비활성화
        self.items['next'].disabled = False
        if self.current_page - 1 <= 0:
            self.items['prev'].disabled = True

        # 이전 검색 결과를 가져옴
        self.current_page -= 1
        self.snippets = await self.search_api.search(
            query=self.snippets[0].query,
            page_token=self.snippets[0].prev_page_token,
            current_page_token=self.snippets[0].current_page_token,
        )

        # 검색 결과를 업데이트
        embed = interaction.message.embeds[0]
        embed.clear_fields()
        for n, snippet in enumerate(self.snippets):
            embed.add_field(
                name=f"{(n + 1) + (self.result_size * self.current_page)}. {snippet.title}",
                value=f"[{snippet.channel_title}]({snippet.channel_url}) | {snippet.video_duration}",
                inline=False
            )
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_page}")

        self.items['search'].placeholder = f"검색 결과 (Page {self.current_page + 1}/{self.max_page})"
        self.items['search'].options = [
            discord.SelectOption(
                label=f"{(n + 1) + (self.result_size * self.current_page)}. {snippet.title}",
                description=f"{snippet.channel_title} | {snippet.video_duration}",
                value=snippet.video_url,
            ) for n, snippet in enumerate(self.snippets)
        ]

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_next(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return

        # 마지막 페이지일 때 다음 버튼 비활성화
        self.items['prev'].disabled = False
        if self.current_page + 1 >= self.max_page - 1:
            self.items['next'].disabled = True

        # 다음 검색 결과를 가져옴
        self.current_page += 1
        self.snippets = await self.search_api.search(
            query=self.snippets[0].query,
            page_token=self.snippets[0].next_page_token,
            current_page_token=self.snippets[0].current_page_token,
        )

        # 검색 결과를 업데이트
        embed = interaction.message.embeds[0]
        embed.clear_fields()
        for n, snippet in enumerate(self.snippets):
            embed.add_field(
                name=f"{(n + 1) + (self.result_size * self.current_page)}. {snippet.title}",
                value=f"[{snippet.channel_title}]({snippet.channel_url}) | {snippet.video_duration}",
                inline=False
            )
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_page}")

        self.items['search'].placeholder = f"검색 결과 (Page {self.current_page + 1}/{self.max_page})"
        self.items['search'].options = [
            discord.SelectOption(
                label=f"{(n + 1) + (self.result_size * self.current_page)}. {snippet.title}",
                description=f"{snippet.channel_title} | {snippet.video_duration}",
                value=snippet.video_url,
            ) for n, snippet in enumerate(self.snippets)
        ]

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_cancel(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return
        self.stop()
        await interaction.response.edit_message(view=None)

    async def on_search(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return
        # TODO: 선택한 옵션을 Music Cog에 전달


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

    async def on_volum_up(self, interaction: discord.Interaction):
        ...

    async def on_volum_down(self, interaction: discord.Interaction):
        ...

    async def on_next(self, interaction: discord.Interaction):
        ...

    async def on_prev(self, interaction: discord.Interaction):
        ...

    async def on_play(self, interaction: discord.Interaction):
        bot_voice_client = self.cog._get_bot_voice_client(interaction)
        if bot_voice_client is None:
            return

        if bot_voice_client.is_paused():
            await bot_voice_client.pause()
            await interaction.response.defer()
        else:
            await bot_voice_client.resume()
            await interaction.response.defer()

    async def on_stop(self, interaction: discord.Interaction):
        bot_voice_client = self.cog._get_bot_voice_client(interaction)
        if bot_voice_client is None:
            return

        if bot_voice_client.is_playing():
            await bot_voice_client.stop()
            await interaction.response.defer()

    async def on_loop(self, interaction: discord.Interaction):
        ...

    async def on_shuffle(self, interaction: discord.Interaction):
        ...


class QueuePageView(View):
    def __init__(self, cog: "Music", timeout: int = 180):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.items: QueuePageButtonDict = {
            "prev": Button(emoji="⬅️", row=0),
            "next": Button(emoji="➡️", row=0),
        }

        for key, value in self.items.items():
            self.add_item(value)
            value.callback = getattr(self, f"on_{key}")

        self.embed = discord.Embed(title="재생목록", color=discord.Color.random())

    async def on_prev(self, interaction: discord.Interaction):
        ...

    async def on_next(self, interaction: discord.Interaction):
        ...
