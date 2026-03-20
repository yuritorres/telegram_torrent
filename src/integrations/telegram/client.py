import requests
import re
import logging
import json
import threading
from typing import Optional, Union
from dotenv import load_dotenv
from src.core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, EXPIRAR_MSG, AUTHORIZED_USERS

load_dotenv()
logger = logging.getLogger(__name__)


def set_bot_commands() -> None:
    commands = [
        {"command": "start", "description": "Iniciar o bot"},
        {"command": "qespaco", "description": "Mostrar espaço em disco"},
        {"command": "qtorrents", "description": "Listar torrents"},
        {"command": "recent", "description": "Ver itens recentes do Jellyfin"},
        {"command": "recentes", "description": "Ver itens recentemente adicionados (detalhado)"},
        {"command": "libraries", "description": "Listar bibliotecas do Jellyfin"},
        {"command": "status", "description": "Status do servidor Jellyfin"},
        {"command": "youtube", "description": "Baixar vídeo do YouTube"},
        {"command": "stats", "description": "Estatísticas de banda e downloads"},
        {"command": "history", "description": "Histórico de downloads"},
        {"command": "sync", "description": "Sincronizar com Jellyfin"},
        {"command": "priority", "description": "Gerenciar prioridade de torrents"},
        {"command": "docker_list", "description": "Listar containers Docker"},
        {"command": "docker_start", "description": "Iniciar container Docker"},
        {"command": "docker_stop", "description": "Parar container Docker"},
        {"command": "docker_restart", "description": "Reiniciar container Docker"},
        {"command": "docker_stats", "description": "Estatísticas de container"},
        {"command": "docker_logs", "description": "Ver logs de container"},
    ]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    try:
        resp = requests.post(url, json={"commands": commands}, timeout=10)
        resp.raise_for_status()
        logger.info("Comandos do bot registrados com sucesso no Telegram.")
    except Exception as e:
        logger.error(f"Erro ao registrar comandos do bot: {e}")


def send_and_expire_status(msg: str, chat_id: Optional[Union[str, int]] = None, parse_mode: str = "HTML", expirar: int = None) -> bool:
    if expirar is None:
        expirar = EXPIRAR_MSG
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token do bot do Telegram não configurado")
        return False
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
        if not chat_id:
            logger.error("Nenhum chat_id fornecido e TELEGRAM_CHAT_ID não configurado")
            return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": parse_mode}
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        message_id = resp.json()["result"]["message_id"]
        threading.Timer(expirar, delete_message, args=(chat_id, message_id)).start()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de status: {e}")
        return False


def delete_message(chat_id, message_id) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=10)
    except Exception as e:
        logger.error(f"Erro ao apagar mensagem: {e}")


def send_telegram(msg: str, chat_id: Optional[Union[str, int]] = None, parse_mode: str = "HTML", reply_markup: dict = None, use_keyboard: bool = False) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token do bot do Telegram não configurado")
        return False
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
        if not chat_id:
            logger.error("Nenhum chat_id fornecido e TELEGRAM_CHAT_ID não configurado")
            return False

    if parse_mode and parse_mode.upper() == "HTML":
        open_tags = re.findall(r'<([a-z]+)[^<>]*>', msg, re.IGNORECASE)
        close_tags = re.findall(r'</([a-z]+)>', msg, re.IGNORECASE)
        if len(open_tags) != len(close_tags):
            parse_mode = None

    if len(msg) > 4096:
        msg = msg[:4093] + "..."

    from src.integrations.telegram.keyboards import get_main_keyboard

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": str(chat_id), "text": msg}
    if parse_mode:
        data["parse_mode"] = parse_mode
    if reply_markup:
        data["reply_markup"] = reply_markup
    elif use_keyboard:
        data["reply_markup"] = get_main_keyboard()

    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar mensagem para o Telegram: {e}")
        if parse_mode and parse_mode.upper() == "HTML":
            return send_telegram(msg, chat_id, parse_mode=None)
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar mensagem para o Telegram: {e}")
        return False


def answer_callback_query(callback_id: str, text: str = None) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao responder callback query: {e}")
        return False


def send_video_to_telegram(file_path: str, chat_id: str, title: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token do bot do Telegram não configurado")
        return False

    from src.integrations.telegram.keyboards import get_main_keyboard

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    try:
        with open(file_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'chat_id': chat_id,
                'caption': f"✅ *Download concluído!*\n📌 {title}",
                'parse_mode': 'Markdown',
                'supports_streaming': True,
                'reply_markup': json.dumps(get_main_keyboard()),
            }
            resp = requests.post(url, files=files, data=data, timeout=120)
            resp.raise_for_status()
            logger.info(f"Vídeo enviado com sucesso: {title}")
            return True
    except Exception as e:
        logger.error(f"Erro ao enviar vídeo para o Telegram: {e}")
        send_telegram(f"❌ Erro ao enviar o vídeo: {str(e)}", chat_id, use_keyboard=True)
        return False
