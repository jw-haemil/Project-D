import os
import aiohttp
import isodate
import logging
from datetime import timedelta

from src.classes.redis_cache import RedisCache

logger = logging.getLogger("discord.classes.YoutubeSearchAPI")


class YoutubeSearchAPI:
    def __init__(self, redis_cache: RedisCache):
        self.redis_cache = redis_cache
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.search_url = "https://www.googleapis.com/youtube/v3/search"
        self.video_url = "https://www.googleapis.com/youtube/v3/videos"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        *,
        page_token: str = None,
        current_page_token: str = None,
    ) -> list["Snippet"]:
        """검색어에 대한 동영상 정보를 반환합니다."""
        query_cache = await self.redis_cache.get_cache_to_json(
            key=f"{query}:{page_token}"
        )
        if query_cache is not None:
            logger.debug(f"Cache hit: {query}:{page_token}")
            return [Snippet(item) for item in query_cache]

        async with aiohttp.ClientSession() as session:
            params = {
                "key": self.api_key,
                "part": "snippet",
                "q": query,
                "maxResults": max_results,
                "type": "video",
                "fields": "items/id,nextPageToken",
                "order": "relevance"
            }
            # 다음 페이지 검색
            if page_token is not None:
                params['pageToken'] = page_token

            # query에 대한 검색 결과
            async with session.get(url=self.search_url, params=params) as response:
                search_snippet: dict = await response.json()

            # 검색 결과에 대한 동영상 정보
            async with session.get(
                url=self.video_url,
                params = {
                    "key": self.api_key,
                    "part": "snippet,contentDetails",
                    "id": ",".join([item['id']['videoId'] for item in search_snippet['items']]),
                    "fields": "items(snippet(title,channelTitle,channelId),contentDetails/duration)"
                }
            ) as response:
                video_snippet: dict = await response.json()

        # 검색 결과와 동영상 정보를 합쳐서 캐시에 저장
        result_snippets: list[dict[str, str | dict[str, str]]] = list(map(
            lambda search, video: search | video | {
                "query": query,
                "nextPageToken": search_snippet['nextPageToken'],
                "currentPageToken": page_token if page_token is not None else "FirstPage",
                "prevPageToken": current_page_token,
            },
            search_snippet['items'], video_snippet['items']
        ))
        await self.redis_cache.set_cache_from_json(f"{query}:{page_token if page_token is not None else 'FirstPage'}", result_snippets, expire=24*3600)
        return [Snippet(snippet) for snippet in result_snippets]


class TimeDelta:
    def __init__(self, duration: timedelta):
        self.duration = duration

    @property
    def total_seconds(self) -> int:
        return self.duration.seconds

    @property
    def days(self) -> int:
        return self.duration.days

    @property
    def hours(self) -> int:
        return self.duration.seconds // 3600

    @property
    def minutes(self) -> int:
        return self.duration.seconds // 60 % 60

    @property
    def seconds(self) -> int:
        return self.duration.seconds % 60

    def __str__(self):
        return f"{self.hours:02}:{self.minutes:02}:{self.seconds:02}"

class Snippet:
    def __init__(self, snippet: dict):
        self.snippet = snippet

    @property
    def query(self) -> str:
        """검색어를 반환합니다."""
        return self.snippet['query']

    @property
    def video_duration(self) -> TimeDelta:
        """동영상의 길이를 반환합니다."""
        return TimeDelta(isodate.parse_duration(self.snippet['contentDetails']['duration']))

    @property
    def channel_id(self) -> str:
        """채널의 ID를 반환합니다."""
        return self.snippet['snippet']['channelId']

    @property
    def channel_title(self) -> str:
        """채널의 이름을 반환합니다."""
        return self.snippet['snippet']['channelTitle']

    @property
    def channel_url(self) -> str:
        """채널의 URL을 반환합니다."""
        return f"https://www.youtube.com/channel/{self.channel_id}"

    @property
    def title(self) -> str:
        """동영상의 제목을 반환합니다."""
        return self.snippet['snippet']['title']

    @property
    def video_id(self) -> str:
        """동영상의 ID를 반환합니다."""
        return self.snippet['id']['videoId']

    @property
    def video_url(self) -> str:
        """동영상의 URL을 반환합니다."""
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def next_page_token(self) -> str:
        """다음 페이지의 토큰을 반환합니다."""
        return self.snippet['nextPageToken']

    @property
    def current_page_token(self) -> str:
        """현재 페이지의 토큰을 반환합니다."""
        return self.snippet['currentPageToken']

    @property
    def prev_page_token(self) -> str | None:
        """이전 페이지의 토큰을 반환합니다."""
        return self.snippet['prevPageToken']
