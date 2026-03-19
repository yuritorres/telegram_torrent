"""Backward-compatibility shim – use src.services.SyncManager directly."""
from src.services.sync_service import SyncManager

__all__ = ["SyncManager"]
