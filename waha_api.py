"""Backward-compatibility shim – use src.integrations.whatsapp.WAHAApi directly."""
from src.integrations.whatsapp.client import WAHAApi

__all__ = ["WAHAApi"]
