import discord
from discord.ext import commands

from src.classes.bot import Bot, Cog
from .view import ControlView


class Music(Cog):
    async def cog_before_invoke(self, ctx: commands.Context[Bot]):
        if ctx.invoked_subcommand is not None:
            self.logger.info(f"{ctx.author}({ctx.author.id}) | {ctx.command} | {ctx.message.content}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # 봇이 음성 채널에 없을 경우
        bot_voice_client = set([member.guild.voice_client]) & set(self.bot.voice_clients) or None
        if bot_voice_client is None:
            return

        voice_client: discord.VoiceClient = bot_voice_client.pop()
        if len(voice_client.channel.members) == 1: # 봇만 남았을 경우
            await voice_client.disconnect()

    @commands.group(
        name="음악",
        aliases=["노래", "ㅇㅇ", "ㄴㄹ"],
        description="음악 관련 명령어 입니다."
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
        description="음성 채널에 연결합니다."
    )
    async def connect(self, ctx: commands.Context[Bot]):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.reply("음성 채널에 들어가주세요.")
            return
        elif ctx.voice_client in set(self.bot.voice_clients):
            await ctx.reply("이미 연결되어 있습니다.")
            return

        await voice_channel.connect(self_deaf=True)
        await ctx.message.reply(f"<#{voice_channel.id}> 채널에 연결되었습니다.")

    @music.command(
        name="나가기",
        aliases=["끊기", "ㄴㄱㄱ", "ㄲㄱ", "ㄱㄱ"],
        description="음성 채널에서 나갑니다."
    )
    async def disconnect(self, ctx: commands.Context[Bot]):
        if ctx.voice_client is None:
            await ctx.reply("음성 채널에 들어가 있지 않습니다.")
            return

        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction("👌")

    @music.command(
        name="재생",
        aliases=["ㅈㅅ"],
        description="음악을 재생합니다."
    )
    async def play(self, ctx: commands.Context[Bot], url: str):
        if ctx.voice_client is None:
            await ctx.reply("음성 채널에 들어가 있지 않습니다.")
            return

        bot_voice_client = set([ctx.guild.voice_client]) & set(self.bot.voice_clients) or None
        if bot_voice_client is None:
            await ctx.voice_client.connect(self_deaf=True)

        # TODO: 음악 재생 코드 작성

    @music.command(
        name="컨트롤",
        aliases=["제어", "리모컨", "ㅋㅌㄹ", "ㅈㅇ", "ㄻㅋ", "ㄹㅁㅋ"],
        description="음악을 제어합니다."
    )
    async def control(self, ctx: commands.Context[Bot]):
        if ctx.voice_client is None:
            await ctx.reply("음성 채널에 들어가 있지 않습니다.")
            return

        await ctx.send(view=ControlView(self))

    @music.command(
        name="재생목록",
        aliases=["큐", "플레이리스트", "ㅈㅅㅁㄹ", "ㅋ", "ㅍㄹㄹㅅㅌ"],
        description="재생목록을 보냅니다."
    )
    async def playlist(self, ctx: commands.Context[Bot]):
        if ctx.voice_client is None:
            await ctx.reply("음성 채널에 들어가 있지 않습니다.")
            return

        # TODO: 재생목록 코드 작성
