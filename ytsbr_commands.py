"""Backward-compatibility shim – use src.commands.ytsbr_commands directly."""
from src.commands.ytsbr_commands import (
    handle_ytsbr_search, handle_ytsbr_details, handle_ytsbr_popular,
    handle_ytsbr_genres, handle_ytsbr_by_genre,
    handle_ytsbr_download_by_number, format_ytsbr_result,
)

__all__ = [
    "handle_ytsbr_search", "handle_ytsbr_details", "handle_ytsbr_popular",
    "handle_ytsbr_genres", "handle_ytsbr_by_genre",
    "handle_ytsbr_download_by_number", "format_ytsbr_result",
]
