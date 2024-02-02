from discord.ext import commands

class CheckErrors(commands.CheckFailure):
    class NotRegisteredUser(commands.CheckFailure): ...


class Checks():
    """명령어 체크"""

    @staticmethod
    def is_registered():
        """DB에 사용자가 등록되어있는지 확인"""
        async def predicate(ctx: commands.Context):
            info = ctx.bot.database.get_user_info(ctx.author.id)
            if await info.is_valid_user():
                return True
            else:
                raise CheckErrors.NotRegisteredUser("등록되어 있지 않은 유저")
        
        return commands.check(predicate)
