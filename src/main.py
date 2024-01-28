import os
import dotenv
import logging

from classes.bot import Bot

dotenv.load_dotenv() # .env 파일 로드


bot = Bot()



bot.run(
    token=os.environ.get("DISCORD_BOT_TOKEN"),
    log_level=logging.INFO
)