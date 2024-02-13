from discord.ext import commands
from discord.utils import stream_supports_colour, _ColourFormatter

import os
import dotenv
import logging
from logging.handlers import TimedRotatingFileHandler
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
file_handler = TimedRotatingFileHandler(
    filename=f"./logs/{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log",
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter(
        fmt="[{asctime}] {levelname:<8} <{name}> [{funcName} | {lineno}] >> {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )
)
file_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)


# 디버그 파일 로그 설정
file_handler = TimedRotatingFileHandler(
    filename=f"./logs/debug/{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log",
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8"
)
file_handler.setFormatter(
    logging.Formatter(
        fmt="[{asctime}] {levelname:<8} <{name}> [{funcName} | {lineno}] >> {message}",
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
    description="Cog및 bot_setting을 리로드합니다.",
)
@commands.is_owner()
async def reload_cog(ctx: commands.Context[Bot]):
    bot.logger.info(f"{ctx.author}({ctx.author.id}) | {ctx.command}: {ctx.message.content}")
    await ctx.defer()

    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.reload_extension(f"src.cogs.{filename[:-3]}")
            bot.logger.info(f"리로드 완료: src.cogs.{filename[:-3]}")

    if bot.bot_setting is not None:
        await bot.bot_setting.update_setting() # bot_setting 업데이트

    await ctx.send("리로드를 완료했습니다.")

@reload_cog.error
async def reload_cog_error(ctx: commands.Context[Bot], error: commands.CommandError):
    if isinstance(error, commands.NotOwner):
        await ctx.reply("이 명령어는 관리자만 사용할 수 있습니다.")
        ctx.command_failed = False

bot.run(
    token=os.environ.get("DISCORD_BOT_TOKEN"),
    log_handler=stream_handler,
    log_level=logging.DEBUG,
)