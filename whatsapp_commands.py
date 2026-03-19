"""Backward-compatibility shim – use src.commands.whatsapp_commands directly."""
from src.commands.whatsapp_commands import process_whatsapp_message

__all__ = ["process_whatsapp_message"]
