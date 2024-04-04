from discord.ui import Button, Select
from typing import TypedDict


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


FFMPEG_OPTIONS = {"options": "-vn"}
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
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]
}
