"""Backward-compatibility shim – use src.integrations.whatsapp directly."""
from src.integrations.whatsapp.utils import (
    init_waha_client, send_whatsapp, is_authorized_whatsapp,
    format_chat_id, get_waha_qr_code, get_waha_session_status,
)
from src.integrations.whatsapp.webhook import create_webhook_app

__all__ = [
    "init_waha_client", "send_whatsapp", "is_authorized_whatsapp",
    "format_chat_id", "get_waha_qr_code", "get_waha_session_status",
    "create_webhook_app",
]
