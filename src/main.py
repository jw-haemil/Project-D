from discord.ext import commands

import os
import dotenv
import logging

from datetime import datetime

from src.classes.bot import Bot

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
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)


bot = Bot()

# @bot.hybrid_command(
@bot.command(
    name="리로드",
    description="Cog를 리로드합니다.",
)
async def reload_cog(ctx: commands.Context):
    bot.logger.debug(f"{ctx.author}({ctx.author.id}) -> {ctx.message.content}")
    await ctx.defer()

    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.reload_extension(f"src.cogs.{filename[:-3]}")
            bot.logger.debug(f"리로드 완료: src.cogs.{filename[:-3]}")

    await ctx.send("Cog를 리로드했습니다.")

bot.run(
    token=os.environ.get("DISCORD_BOT_TOKEN"),
    log_level=logging.INFO
)