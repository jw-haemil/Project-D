import logging
from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from .data_sql import DataSQL

logger = logging.getLogger("discord.bot.database.bot_setting")


class BotSettingColumns(TypedDict):
    attendance_cooldown: int # 출석체크 쿨타임 (시간)
    attendance_bonus_money: int # 출석체크 보너스 돈
    attendance_bonus_money_prob: float # 출석체크 보너스 확률 (%)
    attendance_multiple: int # 출석체크 랜덤값의 배수
    attendance_random_money_min: int # 출석체크 랜덤값의 최소값
    attendance_random_money_max: int # 출석체크 랜덤값의 최대값
    fishing_random_min: int # 낚시에서 물고기가 걸리는 최소시간 (초)
    fishing_random_max: int # 낚시에서 물고기가 걸리는 최대시간 (초)
    fishing_timeout: int # 낚시에서 물고기를 잡는 시간 (초)
    coinflip_total_loss_prob: float # 동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률 (%)
    ticitactoe_game_timeout: int # 틱택토 게임중 일정시간동안 응답이 없을 경우, 게임을 중지할 시간 (초)
    tictactoe_invite_timeout: int # 틱택토 초대시 일정시간동안 응답이 없을 경우, 초대를 만료할 시간 (초)


class BotSetting():
    def __init__(self, database: "DataSQL") -> None:
        self._database = database
        self._settings: BotSettingColumns = {}

    async def update_setting(self):
        """|coro|
        봇 설정을 업데이트합니다.
        """
        async def get_setting(name: str): 
            return (await self._database.select(table="bot_setting", columns=["value"], condition={"name": name}))[0][0]
        logger.debug("Updating bot setting")

        for _name, _type in BotSettingColumns.__annotations__.items():
            self._settings[_name] = _type(await get_setting(_name))

    @property
    def attendance_cooldown(self) -> int:
        """출석체크 쿨타임을 반환합니다.
        단위: 시간

        Returns:
            int: 출석체크 쿨타임
        """
        return self._settings['attendance_cooldown']

    @property
    def attendance_bonus_money(self) -> int:
        """출석체크 보너스 돈을 반환합니다.

        Returns:
            int: 출석체크 보너스 돈
        """
        return self._settings['attendance_bonus_money']

    @property
    def attendance_bonus_money_prob(self) -> float:
        """출석체크 보너스 확률을 반환합니다.

        확률은 0 ~ 1 사이의 값
        
        Returns:
            float: 출석체크 보너스 확률
        """
        return self._settings['attendance_bonus_money_prob'] / 100 # 확률 단위를 % 로 변환합니다.

    @property
    def attendance_multiple(self) -> int:
        """출석체크 랜덤값의 배수를 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 배수
        """
        return self._settings['attendance_multiple']

    @property
    def attendance_random_money_min(self) -> int:
        """출석체크 랜덤값의 최소값을 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 최소값
        """
        return self._settings['attendance_random_money_min']

    @property
    def attendance_random_money_max(self) -> int:
        """출석체크 랜덤값의 최대값을 반환합니다.

        Returns:
            int: 출석체크 랜덤값의 최대값
        """
        return self._settings['attendance_random_money_max']

    @property
    def fishing_random_min(self) -> int:
        """낚시에서 물고기가 걸리는 최소시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기가 걸리는 최소시간
        """
        return self._settings['fishing_random_min']

    @property
    def fishing_random_max(self) -> int:
        """낚시에서 물고기가 걸리는 최대시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기가 걸리는 최대시간
        """
        return self._settings['fishing_random_max']

    @property
    def fishing_timeout(self) -> int:
        """낚시에서 물고기를 잡는 시간을 반환합니다.
        단위: 초

        Returns:
            int: 낚시에서 물고기를 잡는 시간
        """
        return self._settings['fishing_timeout']

    @property
    def coinflip_total_loss_prob(self) -> float:
        """동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률을 반환합니다.

        확률은 0 ~ 1 사이의 값

        Returns:
            float: 동전던지기 실패시, 가지고 있는 돈을 모두 잃을 확률
        """
        return self._settings['coinflip_total_loss_prob'] / 100 # 확률 단위를 % 로 변환합니다.

    @property
    def ticitactoe_game_timeout(self) -> int | None:
        """틱택토 게임중 일정시간동안 응답이 없을 경우, 게임을 중지할 시간을 반환합니다.
        단위: 초

        Returns:
            int: 틱택토 게임중 일정시간동안 응답이 없을 경우, 게임을 중지할 시간
        """
        value = self._settings['ticitactoe_game_timeout']
        return None if value == -1 else value

    @property
    def tictactoe_invite_timeout(self) -> int | None:
        """틱택토 초대시 일정시간동안 응답이 없을 경우, 초대를 만료할 시간을 반환합니다.
        단위: 초

        Returns:
            int: 틱택토 초대시 일정시간동안 응답이 없을 경우, 초대를 만료할 시간
        """
        value = self._settings['tictactoe_invite_timeout']
        return None if value == -1 else value
