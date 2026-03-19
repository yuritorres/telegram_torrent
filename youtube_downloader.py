"""Backward-compatibility shim – use src.integrations.youtube directly."""
from src.integrations.youtube.downloader import YouTubeDownloader
from src.integrations.youtube.utils import format_duration, format_filesize, is_youtube_url

__all__ = ["YouTubeDownloader", "format_duration", "format_filesize", "is_youtube_url"]
