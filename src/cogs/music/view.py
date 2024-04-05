import discord
from discord.ext import commands
from discord.ui import View, Button, Select

from typing import TYPE_CHECKING

from .types import ControlButtonDict, QueuePageButtonDict, SearchViewButtonDict, FFMPEG_OPTIONS

if TYPE_CHECKING:
    from .music import Music
    from src.classes.bot import Bot
    from src.classes.youtube_search import YoutubeSearchAPI, Snippet


class SearchView(View):
    # TODO: 검색결과 받아서 SearchView를 구현
    def __init__(
        self,
        cog: "Music",
        context: commands.Context["Bot"],
        search_api: "YoutubeSearchAPI",
        snippets: list["Snippet"],
        timeout: int = 180
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
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
                        value=n,
                    ) for n, snippet in enumerate(snippets)
                ],
                row=1
            ),
        }

        for key, value in self.items.items():
            self.add_item(value)
            value.callback = getattr(self, f"on_{key}")

    async def update_search_result(self, interaction: discord.Interaction):
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
                value=n,
            ) for n, snippet in enumerate(self.snippets)
        ]

        await interaction.response.edit_message(embed=embed, view=self)

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
        await self.update_search_result(interaction)

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
        await self.update_search_result(interaction)

    async def on_cancel(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return
        self.stop()
        await interaction.response.edit_message(view=None)

    async def on_search(self, interaction: discord.Interaction):
        if self.context.author != interaction.user:
            return

        # 캐시에 저장된 동영상 정보를 가져와서 플레이리스트에 추가
        music = (await self.search_api.search(
            query=self.snippets[0].query,
            page_token=self.snippets[0].current_page_token
        ))[int(interaction.data['values'][0])].to_music_info()

        await self.cog.music_playlist.add_music(
            guild_id=interaction.guild.id,
            music=music
        )

        if interaction.user.voice is None:
            await interaction.response.send_message("먼저 음성 채널에 들어가주세요.", ephemeral=True)
            return

        bot_voice_client = self.cog._get_bot_voice_client(interaction)
        if bot_voice_client is None:
            await interaction.user.voice.channel.connect(self_deaf=True)
        bot_voice_client: discord.VoiceClient = bot_voice_client or self.cog._get_bot_voice_client(interaction)

        # 음악이 재생중이거나 일시정지 상태라면 플레이리스트에 추가
        if bot_voice_client.is_playing() or bot_voice_client.is_paused():
            embed = discord.Embed(
                title="음악 추가",
                description=f"[{music.title}]({music.video_url})가\n플레이리스트에 추가되었습니다.",
                color=discord.Color.random()
            )
            await interaction.response.edit_message(
                content="이미 재생중인 음악이 있어 플레이리스트에 추가되었습니다.",
                embed=embed,
                view=None
            )
            return

        await interaction.response.edit_message(content="잠시만 기다려 주세요...", view=None)
        # 음악 재생
        embed = discord.Embed(
            title="음악 재생",
            description=f"[{music.title}]({music.video_url})를 재생합니다.",
            color=discord.Color.random()
        )
        bot_voice_client.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    await music.get_stream_url(),
                    **FFMPEG_OPTIONS
                ),
                volume=1.0
            ),
            after=lambda e: self.cog.bot.loop.create_task(self.cog._after_next_music(e, self.context, bot_voice_client, music))
        )
        await interaction.followup.edit_message(message_id=interaction.message.id, content=None, embed=embed)


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
        audio_source: discord.PCMVolumeTransformer = self.cog._get_bot_voice_client(interaction).source
        if audio_source is None:
            return

        # embed = interaction.message.embeds[0]
        # TODO: Embed에서 볼륨 조절 반영

        self.items['volum_down'].disabled = False
        if audio_source.volume <= 2.0:
            audio_source.volume += 0.1
        else:
            audio_source.volume = 2.0
            self.items['volum_up'].disabled = True

        await interaction.response.defer()

    async def on_volum_down(self, interaction: discord.Interaction):
        audio_source: discord.PCMVolumeTransformer = self.cog._get_bot_voice_client(interaction).source
        if audio_source is None:
            return

        # embed = interaction.message.embeds[0]
        # TODO: Embed에서 볼륨 조절 반영

        self.items['volum_up'].disabled = False
        if audio_source.volume >= 0.1:
            audio_source.volume -= 0.1
        else:
            audio_source.volume = 0.0
            self.items['volum_down'].disabled = True

        await interaction.response.defer()

    async def on_next(self, interaction: discord.Interaction):
        # TODO: 다음 곡 재생
        ...

    async def on_prev(self, interaction: discord.Interaction):
        # TODO: 이전 곡 재생
        ...

    async def on_play(self, interaction: discord.Interaction):
        bot_voice_client = self.cog._get_bot_voice_client(interaction)
        if bot_voice_client is None:
            return

        self.items['stop'].style = discord.ButtonStyle.grey
        if bot_voice_client.is_paused():
            self.items['play'].style = discord.ButtonStyle.green
            bot_voice_client.resume()
        else:
            self.items['play'].style = discord.ButtonStyle.grey
            bot_voice_client.pause()

        await interaction.response.edit_message(view=self)

    async def on_stop(self, interaction: discord.Interaction):
        bot_voice_client = self.cog._get_bot_voice_client(interaction)
        if bot_voice_client is None:
            return

        if bot_voice_client.is_playing():
            self.items['play'].style = discord.ButtonStyle.grey
            self.items['stop'].style = discord.ButtonStyle.red
            bot_voice_client.stop()
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

    async def on_prev(self, interaction: discord.Interaction):
        ...

    async def on_next(self, interaction: discord.Interaction):
        ...
