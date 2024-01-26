import discord
from discord.ext import commands

import os
import dotenv
import logging
import asyncio


dotenv.load_dotenv() # .env 파일 로드

logger = logging.getLogger("discord") # 로깅 설정


# 기본적인 봇 설정
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=";", # 봇 접두사
            intents=intents, # 봇 기능 설정
        )

    async def setup_hook(self): ...
        # for filename in os.listdir("./cogs"):
        #     if filename.endswith(".py"):
        #         await bot.load_extension(f"cogs.{filename[:-3]}")
        
        # await self.tree.sync()
    
    async def on_ready(self):
        logger.info(f"{self.user} 봇 준비 완료")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("봇 테스트"), # 봇 상태 메시지 설정
        )
    
    async def on_message(self, message):
        await self.process_commands(message) # 명령어 처리
    
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound): # 사용자가 잘못된 명령어를 입력했을 때
            pass
    
bot = Bot()



bot.run(os.environ.get("DISCORD_BOT_TOKEN"))