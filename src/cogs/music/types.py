import asyncio
from yt_dlp import YoutubeDL
from datetime import timedelta

from discord.ui import Button, Select
from typing import TypedDict, TYPE_CHECKING


class ControlButtonDict(TypedDict):
    volum_up: Button
    volum_down: Button
    next: Button
    prev: Button
    play: Button
    stop: Button
    loop: Button
    shuffle: Button

class QueuePageButtonDict(TypedDict):
    prev: Button
    next: Button

class SearchViewButtonDict(TypedDict):
    prev: Button
    next: Button
    cancel: Button
    search: Select


FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "no_warnings": True,
    "extract_audio": True,
    "audioformat": "mp3",
    "extract_flat": True,
    "skip_download": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]
}


class MusicInfo:
    def __init__(
        self,
        _name: str,
        _video_id: str,
        _channel_title: str,
        _channel_id: str,
        _duration: int,
        _stream_url: str = None
    ):
        self._name = _name
        self._video_id = _video_id
        self._channel_title = _channel_title
        self._channel_id = _channel_id
        self._duration = _duration
        self._stream_url = _stream_url

    async def get_stream_url(self) -> str:
        if self._stream_url is not None:
            return self._stream_url

        def _get_stream_url():
            with YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(self.video_url, download=False)
                return info['url']
        return await asyncio.get_event_loop().run_in_executor(None, _get_stream_url)

    @property
    def title(self) -> str:
        return self._name

    @property
    def video_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self._video_id}"

    @property
    def thumbnail(self) -> str:
        return f"https://i.ytimg.com/vi/{self._video_id}/maxresdefault.jpg"

    @property
    def video_duration(self) -> "TimeDelta":
        return TimeDelta(timedelta(seconds=self._duration))

    @property
    def author(self) -> str:
        return self._channel_title

    @property
    def author_url(self) -> str:
        return f"https://www.youtube.com/channel/{self._channel_id}"


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
