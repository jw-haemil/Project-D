import aioredis
import logging

logger = logging.getLogger("discord.bot.redis_cache")


class RedisCache:
    def __init__(self, host: str, port: str, db: str):
            """
            RedisCache 클래스의 생성자입니다.

            Parameters:
                host (str): Redis 서버의 호스트 주소입니다.
                port (str): Redis 서버의 포트 번호입니다.
                db (str): Redis 서버의 데이터베이스 번호입니다.
            """
            self.host = host
            self.port = int(port)
            self.db = int(db)

            self.pool = None

    def auth(self, username: str, password: str) -> bool:
            """
            인증을 수행합니다.

            Parameters:
                username (str): 사용자 이름
                password (str): 비밀번호

            Returns:
                bool: 인증 성공 여부
            """
            try:
                self.pool: aioredis.Redis = aioredis.from_url(
                    url=f"redis://{self.host}",
                    port=self.port,
                    username=username,
                    password=password,
                    db=self.db,
                    encoding="utf-8",
                    decode_responses=True
                )
            except aioredis.ConnectionError as e:
                self.pool = None
                logger.error(f"Redis connection failed: {e}")
                return False
            else:
                logger.info("Redis connection established")
                return True

    async def close(self) -> bool:
            """
            Redis 연결을 닫습니다.

            Returns:
                bool: Redis 연결이 성공적으로 닫혔으면 True를 반환하고, 그렇지 않으면 False를 반환합니다.
            """
            if self.pool is not None:
                await self.pool.close()
                logger.info("Redis connection closed")
                return True
            return False

    async def get_cache(self, key: str) -> str | None:
        """
        지정된 키에 대한 캐시 값을 가져옵니다.

        Parameters:
            key (str): 가져올 데이터의 키입니다.

        Returns:
            str | None: 캐시 값 (문자열) 또는 캐시가 없을 경우 None
        """
        if self.pool is not None:
            return await self.pool.get(key)
        return None

    async def set_cache(self, key: str, value: str, expire: int = 600) -> bool:
        """
        지정된 키와 값을 Redis 캐시에 저장합니다.

        Parameters:
            key (str): 저장할 데이터의 키입니다.
            value (str): 저장할 데이터의 값입니다.
            expire (int, optional): 데이터의 만료 시간(초)입니다. 기본값은 600(10분)입니다.

        Returns:
            bool: 캐시 저장에 성공하면 True를 반환합니다.
        """
        if self.pool is not None:
            await self.pool.set(key, value, ex=expire)
            return True
        return False

    async def delete_cache(self, key: str) -> bool:
        """
        지정된 키의 캐시 값을 삭제합니다.

        Parameters:
            key (str): 삭제할 데이터의 키입니다.

        Returns:
            bool: 캐시 삭제에 성공하면 True를 반환합니다.
        """
        if self.pool is not None:
            await self.pool.delete(key)
            return True
        return False

    async def clear_cache(self) -> bool:
        """
        모든 캐시 값을 삭제합니다.

        Returns:
            bool: 캐시 삭제에 성공하면 True를 반환합니다.
        """
        if self.pool is not None:
            await self.pool.flushdb()
            return True
        return False
