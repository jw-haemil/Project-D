from discord.ext import commands
from discord.utils import stream_supports_colour, _ColourFormatter

import os
import dotenv
import logging
from datetime import datetime

from src.classes.bot import Bot

dotenv.load_dotenv() # .env 파일 로드


# 스트림 로그 설정
stream_handler = logging.StreamHandler()
if isinstance(stream_handler, logging.StreamHandler) and stream_supports_colour(stream_handler.stream):
    formatter = _ColourFormatter()
else:
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}",
        dt_fmt,
        style="{"
    )
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)


# 파일 로그 설정
file_handler = logging.FileHandler(
    filename=f"./logs/{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log",
    encoding="utf-8",
    mode="w"
)
file_handler.setFormatter(
    logging.Formatter(
        fmt="[{asctime}] {levelname:<8}: <{name}> [{funcName} | {lineno}] >> {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )
)
file_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(file_handler)


bot = Bot()

# @bot.hybrid_command(
@bot.command(
    name="리로드",
    description="Cog를 리로드합니다.",
)
async def reload_cog(ctx: commands.Context):
    bot.logger.info(f"{ctx.author}({ctx.author.id}) | {ctx.command}: {ctx.message.content}")
    await ctx.defer()

    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.reload_extension(f"src.cogs.{filename[:-3]}")
            bot.logger.info(f"리로드 완료: src.cogs.{filename[:-3]}")

    await ctx.send("Cog를 리로드했습니다.")

bot.run(
    token=os.environ.get("DISCORD_BOT_TOKEN"),
    log_handler=stream_handler,
    log_level=logging.DEBUG,
)