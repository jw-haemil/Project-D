from discord.ext import commands

from src.classes.bot import Bot


class CoinFaceConverter(commands.Converter):
    """동전의 면을 입력받아 bool 값으로 변환하는 컨버터"""

    async def convert(self, ctx: commands.Context[Bot], argument: str) -> bool:
        # 앞면: True, 뒷면: False
        if argument in ("앞", "ㅇ"):
            return True
        elif argument in ("뒤", "ㄷ"):
            return False

        raise commands.BadArgument(f"**앞** 또는 **뒤** 중에 하나를 입력해 주세요.") # 입력이 잘못되었을 때

class CoinBetConverter(commands.Converter):
    """베팅 금액을 입력받아 int 값으로 변환하는 컨버터"""

    async def convert(self, ctx: commands.Context[Bot], argument: str) -> int:
        user_info = ctx.bot.database.get_user_info(ctx.author)

        if argument in ("올인", "모두", "ㅇㅇ", "ㅁㄷ"):
            return await user_info.get_money()

        elif argument.endswith("%"):
            if not argument[:-1].isnumeric():
                raise commands.BadArgument("백분율은 정수로 입력해 주세요.")

            percent = int(argument[:-1])
            if not 0 < percent <= 100:
                raise commands.BadArgument("백분율은 1~100 사이의 값이어야 합니다.")
            return (await user_info.get_money()) * percent // 100

        elif argument.isnumeric():
            return int(argument)

        raise commands.BadArgument("베팅금액은 정수 또는 `올인`, `모두`로 입력해 주세요.") # 입력이 잘못되었을 때