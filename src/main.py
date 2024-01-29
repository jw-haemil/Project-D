import os
import dotenv
import logging

from datetime import datetime

from classes.bot import Bot

dotenv.load_dotenv() # .env 파일 로드


# 로그 파일 설정
handler = logging.FileHandler(
    filename=f"./logs/{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log",
    encoding="utf-8",
    mode="w"
)
handler.setFormatter(
    logging.Formatter(
        fmt="[{asctime}] [{levelname:<8}] {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )
)
logging.getLogger().addHandler(handler)


bot = Bot()



bot.run(
    token=os.environ.get("DISCORD_BOT_TOKEN"),
    log_level=logging.INFO
)