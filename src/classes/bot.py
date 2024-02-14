import discord
from discord.ext import commands

import os
import logging

from src.classes.database import DataSQL
from src.classes.errors import NotRegisteredUser


class Bot(commands.Bot):
    """project-d의 기반이 되는 봇"""

    def __init__(self):
        self.logger = logging.getLogger("discord.classes.Bot") # 로깅 설정
        self.database = None
        self.bot_setting = None

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=";", # 봇 접두사
            intents=intents, # 봇 기능 설정
            help_command=HelpCommand()
        )

    async def setup_hook(self):
        # 데이터베이스 관련 코드
        self.database = DataSQL(
            host=os.getenv("MYSQL_HOST"),
            port=os.getenv("MYSQL_PORT"),
            loop=self.loop
        )
        await self.database.auth(
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB_NAME"),
        )

        if self.database.pool is not None:
            self.bot_setting = await self.database.get_bot_setting()

        # Cog 관련 코드
        for filename in os.listdir("./src/cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"src.cogs.{filename[:-3]}")

        GUILD_ID = discord.Object(id=os.getenv("DISCORD_GUILD_ID"))
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)

    async def on_ready(self):
        self.logger.info(f"{self.user} 봇 준비 완료")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(os.getenv("BOT_ACTIVITY")), # 봇 상태 메시지 설정
        )

    async def on_message(self, message: discord.Message):
        if message.guild is None: # DM은 무시
            return

        await self.process_commands(message) # 명령어 처리

    async def on_command_error(self, ctx: commands.Context["Bot"], error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound): # 사용자가 잘못된 명령어를 입력했을 때
            return

        elif isinstance(error, NotRegisteredUser):
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
            return

        elif isinstance(error, discord.DiscordServerError):
            await ctx.reply("오류가 발생했습니다.")
            self.logger.warning(error)
            return

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.NotFound):
                await ctx.reply("오류가 발생했습니다.")
                self.logger.warning(error.original.args[0])
                return

        if ctx.command_failed:
            await ctx.reply("오류가 발생했습니다.")
            self.logger.error("Ignoring exception in command %s", ctx.command, exc_info=error)

    async def close(self) -> None:
        if self.database is not None:
            await self.database.close()
        await super().close()


class Cog(commands.Cog):
    """project-d의 기반이 되는 코드 객체"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.database = bot.database
        self.bot_setting = bot.bot_setting
        self.logger = logging.getLogger(f"discord.cog.{self.__class__.__name__}")

        self.bot.logger.debug(f"Cog {self.__class__.__name__} loaded")

    # 명령어가 실행되기 전 실행되는 함수
    async def cog_before_invoke(self, ctx: commands.Context[Bot]):
        self.logger.info(f"{ctx.author}({ctx.author.id}) | {ctx.command} | {ctx.message.content}")


class HelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(
            color=discord.Color.random(),
            description=""
        )
        for page in self.paginator.pages:
            embed.description += page

        await destination.send(embed=embed)