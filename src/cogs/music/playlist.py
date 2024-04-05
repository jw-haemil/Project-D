from src.classes.redis_cache import RedisCache
from .types import MusicInfo


class MetaMusicControl(type):
    def __new__(cls, name: str, bases: tuple, namespace: dict, key: str = None):
        if len(bases) != 0 and key is None:
            raise ValueError("MusicControl class must have a key attribute")
        namespace['key'] = key
        return super().__new__(cls, name, bases, namespace)

class MusicControl(metaclass=MetaMusicControl):
    key: str

    def __init__(self, redis: RedisCache):
        self.redis = redis

    async def _get_list(self, guild_id: int) -> list[MusicInfo] | None:
        cache = await self.redis.get_cache_to_json(f"{self.key}:{guild_id}")
        if cache is None:
            return None
        return [MusicInfo(**music) for music in cache]

    async def _set_list(self, guild_id: int, playlist: list[MusicInfo]) -> None:
        json_data = [music.__dict__ for music in playlist]
        if len(json_data) == 0:
            await self.redis.delete_cache(f"{self.key}:{guild_id}")
            return
        await self.redis.set_cache_from_json(f"{self.key}:{guild_id}", json_data, expire=12*3600)

    def _lock(self, guild_id: int):
        return self.redis.lock(f"{self.key}:{guild_id}:lock")

    async def pop_music(self, guild_id: int) -> MusicInfo | None:
        """
        리스트에서 음악을 하나 꺼냅니다.

        Parameters:
            guild_id (int): 서버 ID

        Returns:
            Music | None: 꺼낸 음악
        """
        async with self._lock(guild_id):
            playlist = await self._get_list(guild_id)
            if playlist is None:
                return None
            music = playlist.pop(0)
            await self._set_list(guild_id, playlist)
            return music

    async def add_music(self, guild_id: int, music: MusicInfo) -> None:
        """
        음악을 추가합니다.

        Parameters:
            guild_id (int): 서버 ID
            music (Music): 추가할 음악
        """
        async with self._lock(guild_id):
            playlist = await self._get_list(guild_id)
            if playlist is None:
                playlist = []
            playlist.append(music)
            await self._set_list(guild_id, playlist)

    async def remove_music(self, guild_id: int, index: int) -> None:
        """
        특정 인덱스의 음악을 제거합니다.

        Parameters:
            guild_id (int): 서버 ID
            index (int): 제거할 음악의 인덱스
        """
        async with self._lock(guild_id):
            playlist = await self._get_list(guild_id)
            if playlist is None:
                return
            del playlist[index]
            await self._set_list(guild_id, playlist)

    async def clear_list(self, guild_id: int) -> None:
        """
        리스트를 모두 지웁니다.

        Parameters:
            guild_id (int): 서버 ID
        """
        async with self._lock(guild_id):
            await self.redis.delete_cache(f"{self.key}:{guild_id}")

    async def move_music(self, guild_id: int, from_index: int, to_index: int) -> None:
        """
        다른 위치로 음악을 이동합니다.

        Parameters:
            guild_id (int): 서버 ID
            from_index (int): 이동할 음악의 현재 인덱스
            to_index (int): 이동할 음악의 목표 인덱스
        """
        async with self._lock(guild_id):
            playlist = await self._get_list(guild_id)
            if playlist is None:
                return
            playlist.insert(to_index, playlist.pop(from_index))
            await self._set_list(guild_id, playlist)

class MusicPlaylist(MusicControl, key="playlist"): ...
class MusicHistory(MusicControl, key="history"): ...
