"""Backward-compatibility shim – use src.integrations.jellyfin directly."""
from src.integrations.jellyfin.client import JellyfinClient
from src.integrations.jellyfin.formatter import JellyfinFormatter
from src.integrations.jellyfin.manager import JellyfinManager

__all__ = ["JellyfinClient", "JellyfinFormatter", "JellyfinManager"]
