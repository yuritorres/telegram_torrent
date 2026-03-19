"""Backward-compatibility shim – use src.integrations.qbittorrent.monitor_torrents directly."""
from src.integrations.qbittorrent.monitor import monitor_torrents

__all__ = ["monitor_torrents"]
