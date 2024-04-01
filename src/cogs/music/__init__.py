from src.classes.bot import Bot
from .music import Music

async def setup(bot: Bot): # setup 함수로 명령어 추가
    await bot.add_cog(Music(bot))
