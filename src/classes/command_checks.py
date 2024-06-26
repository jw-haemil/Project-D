from discord.ext import commands

import logging

from src.classes.bot import Bot
from src.classes.errors import NotRegisteredUser

logger = logging.getLogger("discord.classes.Checks")


def is_registered():
    """DB에 사용자가 등록되어있는지 확인"""
    async def predicate(ctx: commands.Context[Bot]):
        if ctx.invoked_with == "help": # help 명령어 실행시 체크 안함.
            return False

        logger.debug(f"Checking if {ctx.author.id} is registered")
        info = ctx.bot.database.get_user_info(ctx.author.id)
        if await info.is_valid_user():
            return True
        else:
            raise NotRegisteredUser("등록되어 있지 않은 유저")

    return commands.check(predicate)
