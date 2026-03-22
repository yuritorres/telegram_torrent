from .client import (
    RedeTorrentApi,
    search_redetorrent,
    get_redetorrent_details,
    get_redetorrent_magnet,
    get_redetorrent_popular,
)
from .commands import (
    handle_redetorrent_search,
    handle_redetorrent_details,
    handle_redetorrent_popular,
    handle_redetorrent_genres,
    handle_redetorrent_by_genre,
    handle_redetorrent_download_by_number,
    format_redetorrent_result,
)

__all__ = [
    "RedeTorrentApi",
    "search_redetorrent",
    "get_redetorrent_details",
    "get_redetorrent_magnet",
    "get_redetorrent_popular",
    "handle_redetorrent_search",
    "handle_redetorrent_details",
    "handle_redetorrent_popular",
    "handle_redetorrent_genres",
    "handle_redetorrent_by_genre",
    "handle_redetorrent_download_by_number",
    "format_redetorrent_result",
]
