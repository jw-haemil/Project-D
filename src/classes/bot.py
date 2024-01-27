import discord
from discord.ext import commands

import os
import logging

from classes.database import DataSQL


class Bot(commands.Bot):
    def __init__(self):
        self.logger = logging.getLogger("discord") # 로깅 설정
        self.database = None
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=";", # 봇 접두사
            intents=intents, # 봇 기능 설정
        )

    async def setup_hook(self):
        # 데이터베이스 관련 코드
        self.database = DataSQL(
            host=os.environ.get("MYSQL_HOST"),
            port=os.environ.get("MYSQL_PORT"),
            loop=self.loop
        )
        if await self.database.auth(
            user=os.environ.get("MYSQL_USER"),
            password=os.environ.get("MYSQL_PASSWORD"),
            database=os.environ.get("MYSQL_DB_NAME"),
        ):
            self.logger.info("Database connection established")
        else:
            self.logger.error("Database connection failed")
        
        # Cog 관련 코드
        for filename in os.listdir("./src/cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        
        # await self.tree.sync()
    
    async def on_ready(self):
        self.logger.info(f"{self.user} 봇 준비 완료")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("봇 테스트"), # 봇 상태 메시지 설정
        )
    
    async def on_message(self, message):
        await self.process_commands(message) # 명령어 처리
    
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound): # 사용자가 잘못된 명령어를 입력했을 때
            pass
    
    async def close(self) -> None:
        if await self.database.close():
            self.logger.info("Database connection closed")

        await super().close()