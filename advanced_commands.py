"""Backward-compatibility shim – use src.commands.telegram_commands directly."""
from src.commands.telegram_commands import (
    handle_stats_command,
    handle_history_command,
    handle_graph_command,
    handle_sync_command,
    handle_sync_status_command,
    handle_priority_command,
    handle_remove_command,
)

__all__ = [
    "handle_stats_command", "handle_history_command", "handle_graph_command",
    "handle_sync_command", "handle_sync_status_command",
    "handle_priority_command", "handle_remove_command",
]
