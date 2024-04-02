import discord
from discord.ext import commands

import re
import yt_dlp
import requests

from src.classes.bot import Bot, Cog
from .view import ControlView
from .types import YTDL_OPTIONS, FFMPEG_OPTIONS


class Music(Cog):
    async def cog_before_invoke(self, ctx: commands.Context[Bot]):
        if ctx.invoked_subcommand is not None:
            self.logger.info(f"{ctx.author}({ctx.author.id}) | {ctx.command} | {ctx.message.content}")


    def _get_voice_client(self, ctx: commands.Context[Bot]) -> discord.VoiceClient | None:
        return _result.pop() if (_result := set([ctx.guild.voice_client]) & set(self.bot.voice_clients)) else None


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # 봇이 음성 채널에 없을 경우
        bot_voice_client = self._get_voice_client(member)
        if bot_voice_client is None:
            return

        voice_client: discord.VoiceClient = bot_voice_client
        if len(voice_client.channel.members) == 1: # 봇만 남았을 경우
            await voice_client.disconnect()


    @commands.group(
        name="음악",
        aliases=["노래", "ㅇㅇ", "ㄴㄹ"],
        description="음악 관련 명령어 입니다.",
        usage="음악 [명령어]"
    )
    async def music(self, ctx: commands.Context[Bot]):
        if ctx.invoked_subcommand is None:
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

        bot_voice_client = self._get_voice_client(ctx)
        if bot_voice_client is not None:
            if (
                (_number_of_user := len([user for user in bot_voice_client.channel.members if not user.bot])) == 0 or
                (_number_of_user >= 1 and not bot_voice_client.is_playing() and not bot_voice_client.is_paused())
            ):
                await bot_voice_client.move_to(user_voice_channel)
                await ctx.message.reply(f"<#{user_voice_channel.id}> 채널로 이동했습니다.")
                return
            elif bot_voice_client.is_playing() or bot_voice_client.is_paused():
                await ctx.reply("다른 음성 채널에서 봇이 사용 중입니다.")
                return
            elif bot_voice_client.channel == user_voice_channel:
                await ctx.reply("이미 연결되어 있습니다.")
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
        bot_voice_client = self._get_voice_client(ctx)
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


    @music.command(
        name="재생",
        aliases=["ㅈㅅ"],
        description="음악을 재생합니다.",
        usage="음악 재생 [검색어 | URL]"
    )
    async def play(self, ctx: commands.Context[Bot], query: str = None):
        if ctx.voice_client is None:
            ctx.author.voice.channel.connect(self_deaf=True)

        bot_voice_client = _result.pop() if (_result := set([ctx.guild.voice_client]) & set(self.bot.voice_clients)) else None
        if bot_voice_client is None:
            await ctx.voice_client.connect(self_deaf=True)

        if query is None:
            # TODO: 재생목록에서 재생 코드 작성
            ...
        else:
            search_flag = True
            if re.match(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+", query):
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                    music_info = ydl.extract_info(query, download=False)
                    search_flag = music_info is not None

            if search_flag:
                # TODO: 검색 코드 작성
                ...

        # TODO: 음악 재생 코드 작성


    @music.command(
        name="컨트롤",
        aliases=["제어", "리모컨", "ㅋㅌㄹ", "ㅈㅇ", "ㄻㅋ", "ㄹㅁㅋ"],
        description="음악을 제어합니다.",
        usage="음악 컨트롤"
    )
    async def control(self, ctx: commands.Context[Bot]):
        bot_voice_client = self._get_voice_client(ctx)
        if bot_voice_client is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다.")
            return
        elif len(bot_voice_client.channel.members) > 1:
            await ctx.reply("음악을 듣고 있는 사람이 있어 나갈 수 없습니다.")
            return

        await ctx.send(view=ControlView(self))


    @music.group(
        name="재생목록",
        aliases=["큐", "플레이리스트", "ㅈㅅㅁㄹ", "ㅋ", "ㅍㄹㄹㅅㅌ"],
        description="재생목록을 보냅니다.",
        usage="음악 재생목록"
    )
    async def playlist(self, ctx: commands.Context[Bot]):
        bot_voice_client = self._get_voice_client(ctx)
        if bot_voice_client is None:
            await ctx.reply("봇이 음성 채널에 연결되어 있지 않습니다.")
            return
        elif len(bot_voice_client.channel.members) > 1:
            await ctx.reply("음악을 듣고 있는 사람이 있어 나갈 수 없습니다.")
            return

        # TODO: 재생목록 코드 작성
