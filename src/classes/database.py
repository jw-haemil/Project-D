import asyncio
import aiomysql
import logging


class DataSQL():
    def __init__(self, host: str, port: int, loop: asyncio.AbstractEventLoop = None):
        """데이터베이스

        Args:
            host (str): 호스트
            port (int): 포트
            loop (asyncio.AbstractEventLoop, optional): 비동기 작업을 위한 eventloop Defaults to None.
        """
        self.host = host
        self.port = int(port)
        self.loop = loop
    
    async def auth(self, user: str, password: str, database: str, autocommit: bool = True) -> bool:
        """mysql서버에 접속합니다.

        Args:
            user (str): user 이름
            password (str): 접속 비밀번호
            autocommit (bool, optional): 변경내용 자동반영. Defaults to True.
        
        Return:
            bool: 접속 성공 여부.
        """
        self.__auth_user = user
        self.__auth_password = password
        self.__auth_database = database
        self.__auth_autocommit = autocommit

        try:
            self.pool: aiomysql.Pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=user,
                password=password,
                db=database,
                loop=self.loop,
                autocommit=autocommit
            )
        except aiomysql.MySQLError as e:
            self.pool = None
            logging.getLogger("discord").error(e)
            return False
        else:
            return True
    
    async def close(self) -> bool:
        if hasattr(self, "pool") and self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            return True
        return False
    
    async def _query(self, query: str, args: tuple = None, fetch: bool = False) -> list:
        # TODO: 쿼리 실행 시 로그 처리
        async with self.pool.acquire() as conn: # poll에 접속
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                if fetch:
                    return await cur.fetchall()
                else:
                    return None