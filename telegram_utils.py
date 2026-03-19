"""Backward-compatibility shim – use src.integrations.telegram directly."""
from src.integrations.telegram.client import (
    send_telegram, send_and_expire_status, delete_message,
    answer_callback_query, send_video_to_telegram, set_bot_commands,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, AUTHORIZED_USERS, EXPIRAR_MSG,
)
from src.integrations.telegram.keyboards import get_main_keyboard
from src.integrations.telegram.utils import (
    format_bytes, get_disk_space_info, get_recent_items_detailed,
    list_torrents, handle_pause_all_torrents, handle_resume_all_torrents,
)
from src.integrations.telegram.handlers import process_messages, process_youtube_download

__all__ = [
    "send_telegram", "send_and_expire_status", "delete_message",
    "answer_callback_query", "send_video_to_telegram", "set_bot_commands",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "AUTHORIZED_USERS", "EXPIRAR_MSG",
    "get_main_keyboard",
    "format_bytes", "get_disk_space_info", "get_recent_items_detailed",
    "list_torrents", "handle_pause_all_torrents", "handle_resume_all_torrents",
    "process_messages", "process_youtube_download",
]
