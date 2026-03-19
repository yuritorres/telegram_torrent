"""
Utilitários para processamento de mensagens WhatsApp via WAHA
"""
import logging
import os
from typing import Optional, Dict, Any
from src.integrations.whatsapp.client import WAHAApi

logger = logging.getLogger(__name__)

WAHA_URL = os.getenv('WAHA_URL', 'http://localhost:3000')
WAHA_API_KEY = os.getenv('WAHA_API_KEY', 'local-dev-key-123')
WAHA_SESSION = os.getenv('WAHA_SESSION', 'default')
AUTHORIZED_WHATSAPP_NUMBERS = os.getenv('AUTHORIZED_WHATSAPP_NUMBERS', '').split(',')

waha_client: Optional[WAHAApi] = None


def init_waha_client() -> Optional[WAHAApi]:
    global waha_client
    if not WAHA_URL or not WAHA_API_KEY:
        logger.warning("WAHA_URL ou WAHA_API_KEY não configurados")
        return None
    try:
        waha_client = WAHAApi(WAHA_URL, WAHA_API_KEY, WAHA_SESSION)
        if waha_client.check_health():
            logger.info("Cliente WAHA inicializado com sucesso")
            status = waha_client.get_session_status()
            if status:
                logger.info(f"Sessão WhatsApp status: {status.get('status', 'unknown')}")
            else:
                logger.warning("Sessão WhatsApp não encontrada. Inicie uma sessão manualmente.")
            return waha_client
        else:
            logger.error("API WAHA não está respondendo")
            return None
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente WAHA: {e}")
        return None


def send_whatsapp(text: str, chat_id: str, parse_mode: str = None) -> bool:
    global waha_client
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return False
    try:
        clean_text = text.replace('*', '').replace('_', '').replace('`', '')
        return waha_client.send_text(chat_id, clean_text)
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False


def is_authorized_whatsapp(phone_number: str) -> bool:
    if not AUTHORIZED_WHATSAPP_NUMBERS or AUTHORIZED_WHATSAPP_NUMBERS == ['']:
        return True
    clean_number = phone_number.split('@')[0] if '@' in phone_number else phone_number
    clean_number = ''.join(filter(str.isdigit, clean_number))
    for authorized in AUTHORIZED_WHATSAPP_NUMBERS:
        clean_authorized = ''.join(filter(str.isdigit, authorized))
        if clean_number == clean_authorized or clean_number.endswith(clean_authorized) or clean_authorized in clean_number:
            return True
    return False


def format_chat_id(phone_number: str) -> str:
    clean_number = ''.join(filter(str.isdigit, phone_number))
    if '@' not in clean_number:
        return f"{clean_number}@c.us"
    return clean_number


def get_waha_qr_code() -> Optional[str]:
    global waha_client
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return None
    return waha_client.get_qr_code()


def get_waha_session_status() -> Optional[Dict]:
    global waha_client
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return None
    return waha_client.get_session_status()
