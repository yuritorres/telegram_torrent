"""Backward-compatibility shim – use src.integrations.jellyfin.JellyfinNotifier directly."""
from src.integrations.jellyfin.notifier import JellyfinNotifier

__all__ = ["JellyfinNotifier"]
