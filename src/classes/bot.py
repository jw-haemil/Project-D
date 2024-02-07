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
            host=os.environ.get("MYSQL_HOST"),
            port=os.environ.get("MYSQL_PORT"),
            loop=self.loop
        )
        await self.database.auth(
            user=os.environ.get("MYSQL_USER"),
            password=os.environ.get("MYSQL_PASSWORD"),
            database=os.environ.get("MYSQL_DB_NAME"),
        )

        # Cog 관련 코드
        for filename in os.listdir("./src/cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"src.cogs.{filename[:-3]}")

        # await self.tree.sync()

    async def on_ready(self):
        self.logger.info(f"{self.user} 봇 준비 완료")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(os.environ.get("BOT_ACTIVITY")), # 봇 상태 메시지 설정
        )

    async def on_message(self, message: discord.Message):
        if message.guild is None: # DM은 무시
            return

        await self.process_commands(message) # 명령어 처리

    async def on_command_error(self, ctx: commands.Context["Bot"], error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound): # 사용자가 잘못된 명령어를 입력했을 때
            pass
        elif isinstance(error, NotRegisteredUser):
            await ctx.reply("사용자 등록을 먼저 해 주세요.")
        else:
            if self.extra_events.get('on_command_error', None):
                return

            # error_handler 무시
            # command = ctx.command
            # if command and command.has_error_handler():
            #     return

            cog = ctx.cog
            if cog and cog.has_error_handler():
                return

            self.logger.error('Ignoring exception in command %s', ctx.command, exc_info=error)

    async def close(self) -> None:
        if self.database is not None:
            await self.database.close()
        await super().close()


class Cog(commands.Cog):
    """project-d의 기반이 되는 코드 객체"""

    def __init__(self, bot: Bot):
        self.bot = bot
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