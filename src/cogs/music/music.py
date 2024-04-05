import discord
from discord.ext import commands

import asyncio
import re
import yt_dlp

from src.classes.bot import Bot, Cog
from src.classes.youtube_search import YoutubeSearchAPI
from .view import ControlView, QueuePageView, SearchView
from .types import YTDL_OPTIONS, FFMPEG_OPTIONS
from .playlist import MusicPlaylist, MusicHistory, MusicInfo


class Music(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.music_playlist = MusicPlaylist(redis=bot.redis_cache)
        self.music_history = MusicHistory(redis=bot.redis_cache)

    def _get_bot_voice_client(self, guild: discord.abc.GuildChannel) -> discord.VoiceClient | None:
        """
        봇의 음성 클라이언트를 가져오는 메서드입니다.

        Parameters:
            guild (discord.abc.GuildChannel): GuildChannel이 있는 겍체

        Returns:
            discord.VoiceClient | None: 음성 클라이언트 객체 또는 None
        """
        return _result.pop() if (_result := {guild.guild.voice_client} & set(self.bot.voice_clients)) else None


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        bot_voice_client = self._get_bot_voice_client(member)
        if (
            member.bot or # member가 봇일 경우
            bot_voice_client is None or # 봇이 음성 채널에 연결되어 있지 않을 경우
            not any(channel.channel == bot_voice_client.channel for channel in (before, after)) # 봇이 있는 음성 채널에서 발생한 이벤트가 아닌 경우
        ):
            return

        if len([user for user in bot_voice_client.channel.members if not user.bot]) == 0: # 유저가 없을 경우
            await bot_voice_client.disconnect()


    @commands.group(
        name="음악",
        aliases=["노래", "ㅇㅇ", "ㄴㄹ"],
        description="음악 관련 명령어 입니다.",
        usage="음악 [명령어]"
    )
    async def music(self, ctx: commands.Context[Bot]):
        if ctx.invoked_subcommand is not None: # subcommand가 있는 경우
            return

        group: commands.Group = ctx.command
        embed = discord.Embed(title=group.name, description=group.description, color=discord.Color.random())
        for cmd in group.commands:
            embed.add_field(
                name=cmd.name,
                value=cmd.description,
                inline=False
            )
        embed.set_footer(text=f"{ctx.clean_prefix}{group.name} [명령어]로 사용 가능합니다.")
        await ctx.send(embed=embed)


    @music.command(
        name="연결",
        aliases=["ㅇㄱ"],
        description="음성 채널에 연결합니다.",
        usage="음악 연결 [음성채널]"
    )
    async def connect(self, ctx: commands.Context[Bot], channel: discord.VoiceChannel = None):
        # voice_channel 설정
        user_voice_channel = None
        if channel is None:
            if ctx.author.voice is not None:
                user_voice_channel = ctx.author.voice.channel
        else:
            user_voice_channel = channel

        # 음성 채널 연결
        if user_voice_channel is None:
            await ctx.reply("먼저 음성 채널에 들어가주세요.")
            return

        bot_voice_client = self._get_bot_voice_client(ctx)
        if bot_voice_client is not None:
            if bot_voice_client.channel == user_voice_channel:
                await ctx.reply("이미 연결되어 있습니다.")
                return
            elif (
                (_number_of_user := len([user for user in bot_voice_client.channel.members if not user.bot])) == 0 or
                (_number_of_user >= 1 and not bot_voice_client.is_playing() and not bot_voice_client.is_paused())
            ):
                await bot_voice_client.channel.guild.change_voice_state(channel=user_voice_channel, self_deaf=True)
                await ctx.message.reply(f"<#{user_voice_channel.id}> 채널로 이동했습니다.")
                return
            elif bot_voice_client.is_playing() or bot_voice_client.is_paused():
                await ctx.reply("다른 음성 채널에서 봇이 사용 중입니다.")
                return
            else:
                self.logger.warning("Unknown error occurred.")
                await bot_voice_client.disconnect()

        await user_voice_channel.connect(self_deaf=True)
        await ctx.message.reply(f"<#{user_voice_channel.id}> 채널에 연결되었습니다.")

    @connect.error
    async def connect_error(self, ctx: commands.Context[Bot], error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.reply("음성 채널을 찾을 수 없습니다.")
            ctx.command_failed = False


    @music.command(
        name="나가기",
        aliases=["끊기", "ㄴㄱㄱ", "ㄲㄱ", "ㄱㄱ"],
        description="음성 채널에서 나갑니다.",
        usage="음악 나가기"
    )
    async def disconnect(self, ctx: commands.Context[Bot]):
        bot_voice_client = self._get_bot_voice_client(ctx)
        if bot_voice_client is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다.")
            return
        elif (
            ctx.voice_client is None and
            len([user for user in bot_voice_client.channel.members if not user.bot]) >= 1 and
            bot_voice_client.is_playing()
        ):
            await ctx.reply("음악을 듣고 있는 사람이 있어 나갈 수 없습니다.")
            return

        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction("👌")


    async def _after_next_music(
        self,
        expt: Exception | None,
        context: commands.Context[Bot],
        bot_voice_client: discord.VoiceClient,
        prev_music: MusicInfo
    ):
        if expt is not None:
            self.logger.error(expt)
            return

        await self.music_history.add_music(context.guild.id, prev_music)
        new_music = await self.music_playlist.pop_music(context.guild.id)

        if new_music is None or not bot_voice_client.is_connected():
            return

        bot_voice_client.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    await new_music.get_stream_url(),
                    **FFMPEG_OPTIONS
                ),
                volume=bot_voice_client.source.volume if bot_voice_client.source is not None else .75
            ),
            after=lambda e: self.bot.loop.create_task(self._after_next_music(e, context, bot_voice_client, new_music))
        )

    @music.command(
        name="재생",
        aliases=["ㅈㅅ"],
        description="음악을 재생합니다.",
        usage="음악 재생 [검색어 | URL]"
    )
    async def play(self, ctx: commands.Context[Bot], *, query: str = None):
        # TODO: 검색 후 채널 연걸
        async def connect_voice_channel() -> discord.VoiceClient:
            bot_voice_client = self._get_bot_voice_client(ctx)
            if bot_voice_client is None:
                await ctx.author.voice.channel.connect(self_deaf=True)
            return bot_voice_client or self._get_bot_voice_client(ctx)

        if ctx.author.voice is None:
            await ctx.reply("먼저 음성 채널에 들어가주세요.")
            return

        # 플레이리스트에서 음악을 가져와서 재생
        if query is None:
            music = await self.music_playlist.pop_music(ctx.guild.id)
            if music is None:
                await ctx.reply("플레이리스트가 비어있습니다. 검색어 또는 URL을 입력해주세요.")
                return

            if ctx.author.voice is None:
                await ctx.reply("먼저 음성 채널에 들어가주세요.")
                return

            message = await ctx.send("잠시만 기다려주세요...")
            bot_voice_client = await connect_voice_channel()
            bot_voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        await music.get_stream_url(),
                        **FFMPEG_OPTIONS
                    ),
                    volume=0.75
                ),
                after=lambda e: self.bot.loop.create_task(self._after_next_music(e, ctx, bot_voice_client, music))
            )

            embed = discord.Embed(
                title="음악 재생",
                description=f"[{music.title}]({music.video_url})를 재생합니다.",
                color=discord.Color.random()
            )
            await message.edit(content=None, embed=embed)
            return

        # TODO: 만약 플레이리스트 URL이면 재생목록에 바로 추가하는 코드 작성
        # query가 URL인 경우
        search_flag = False
        if re.match(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+", query):
            def _get_music_info():
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                    return ydl.extract_info(query, download=False)

            message = await ctx.send("잠시만 기다려주세요...")
            music_info = await self.bot.loop.run_in_executor(None, _get_music_info)
            if music_info is not None:
                search_flag = True
                if ctx.author.voice is None:
                    await message.edit(content="먼저 음성 채널에 들어가주세요.")
                    return
                bot_voice_client = await connect_voice_channel()

                await self.music_playlist.add_music(
                    guild_id=ctx.guild.id,
                    music=(music_info := MusicInfo(
                        _name=music_info['title'],
                        _video_id=music_info['id'],
                        _channel_title=music_info['uploader'],
                        _channel_id=music_info['uploader_id'],
                        _duration=music_info['duration'],
                        _stream_url=music_info['url']
                    ))
                )

                # 음악이 재생중이거나 일시정지 중인 경우 플레이리스트에 추가
                if bot_voice_client.is_playing() or bot_voice_client.is_paused():
                    embed = discord.Embed(
                        title="음악 추가",
                        description=f"[{music_info.title}]({music_info.video_url})가\n플레이리스트에 추가했습니다.",
                        color=discord.Color.random()
                    )
                    await message.edit(content="이미 재생중인 음악이 있어 플레이리스트에 추가되었습니다.", embed=embed)
                    return

                # 음악 재생
                bot_voice_client.play(
                    discord.PCMVolumeTransformer(
                        discord.FFmpegPCMAudio(
                            await music_info.get_stream_url(),
                            **FFMPEG_OPTIONS
                        ),
                        volume=0.75
                    ),
                    after=lambda e: self.bot.loop.create_task(self._after_next_music(e, ctx, bot_voice_client, music_info))
                )

                embed = discord.Embed(
                    title="음악 재생",
                    description=f"[{music_info.title}]({music_info.video_url})를 재생합니다.",
                    color=discord.Color.random()
                )
                await message.edit(content=None, embed=embed)

        if search_flag: # query가 올바른 URL인 경우
            return

        # 검색기능
        search_api = YoutubeSearchAPI(redis_cache=self.bot.redis_cache)
        snippets = await search_api.search(query=query, max_results=5)

        # SearchView 관련 코드
        search_view = SearchView(cog=self, context=ctx, search_api=search_api, snippets=snippets)
        async def search_view_on_timeout(_search_view: SearchView, _message: discord.Message):
            _search_view.stop()
            try:
                message = await _message.fetch()
            except discord.NotFound:
                return
            await message.edit(view=None)

        # 검색결과 Embed
        embed = discord.Embed(
            title="검색결과",
            description=f"검색어: {query}",
            timestamp=ctx.message.created_at,
            url=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
            color=discord.Color.random()
        )
        for n, snippet in enumerate(snippets):
            embed.add_field(
                name=f"{(n + 1) + (search_view.result_size * search_view.current_page)}. {snippet.title}",
                value=f"[{snippet.channel_title}]({snippet.channel_url}) | {snippet.video_duration}",
                inline=False
            )
        embed.set_footer(text=f"Page {search_view.current_page + 1}/{search_view.max_page}")

        message = await ctx.send(embed=embed, view=search_view)
        search_view.on_timeout = lambda: search_view_on_timeout(search_view, message)


    @music.command(
        name="컨트롤",
        aliases=["제어", "리모컨", "ㅋㅌㄹ", "ㅈㅇ", "ㄻㅋ", "ㄹㅁㅋ"],
        description="음악을 제어합니다.",
        usage="음악 컨트롤"
    )
    async def control(self, ctx: commands.Context[Bot]):
        bot_voice_client = self._get_bot_voice_client(ctx)
        if bot_voice_client is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다.")
            return

        await ctx.send(view=ControlView(self))


    @music.command(
        name="볼륨",
        aliases=["소리", "ㅂㄹ", "ㅅㄹ"],
        description="음악의 볼륨을 조절합니다.",
        usage="음악 볼륨 [볼륨%]"
    )
    async def volume(self, ctx: commands.Context[Bot], volume: int = None):
        bot_voice_client = self._get_bot_voice_client(ctx)
        if bot_voice_client is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다.")
            return

        if volume is None:
            await ctx.reply(f"현재 볼륨: {bot_voice_client.source.volume * 100}%")
            return

        if not 0 <= volume <= 200:
            await ctx.reply("볼륨은 0% ~ 200% 사이로 설정 가능합니다.")
            return

        # TODO: DB에 볼륨 저장해서 불러오기
        # bot_voice_client.source.volume = volume / 100
        await ctx.message.add_reaction("👌")

    @music.group(
        name="재생목록",
        aliases=["큐", "플레이리스트", "ㅈㅅㅁㄹ", "ㅋ", "ㅍㄹㄹㅅㅌ"],
        description="재생목록을 보냅니다.",
        usage="음악 재생목록"
    )
    async def playlist(self, ctx: commands.Context[Bot]):
        if ctx.invoked_subcommand is not None: # subcommand가 있는 경우
            return

        if ctx.subcommand_passed is None:
            await ctx.send(view=QueuePageView(self))
            return

        group: commands.Group = ctx.command
        embed = discord.Embed(
            title=f"{group.full_parent_name} {group.name}",
            description=group.description,
            color=discord.Color.random()
        )
        for cmd in group.commands:
            embed.add_field(
                name=cmd.name,
                value=cmd.description,
                inline=False
            )
        embed.set_footer(text=f"{ctx.clean_prefix}{group.full_parent_name} {group.name} [명령어]로 사용 가능합니다.")
        await ctx.send(embed=embed)

