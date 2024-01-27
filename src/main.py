import os
import dotenv

from classes.bot import Bot

dotenv.load_dotenv() # .env 파일 로드

    
bot = Bot()



bot.run(os.environ.get("DISCORD_BOT_TOKEN"))