"""Backward-compatibility shim – use src.integrations.qbittorrent directly."""
from src.integrations.qbittorrent.client import (
    login_qb, fetch_torrents, summarize_torrents, add_magnet,
    pause_torrent, resume_torrent, delete_torrent,
    set_torrent_priority, set_torrent_location,
    get_torrent_info, get_transfer_info, format_bytes,
)
from src.integrations.qbittorrent.client import summarize_torrents as resumo_torrents
from src.integrations.qbittorrent.monitor import monitor_torrents

__all__ = [
    "login_qb", "fetch_torrents", "summarize_torrents", "resumo_torrents",
    "add_magnet", "pause_torrent", "resume_torrent", "delete_torrent",
    "set_torrent_priority", "set_torrent_location", "get_torrent_info",
    "get_transfer_info", "format_bytes", "monitor_torrents",
]
