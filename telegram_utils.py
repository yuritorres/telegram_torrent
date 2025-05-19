import requests
import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

def send_telegram(msg, chat_id=None):
    if chat_id is None:
        chat_id = TG_CHAT_ID
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    resp = requests.post(url, data=data)
    resp.raise_for_status()

def process_messages(sess, last_update_id, add_magnet_func, qb_url):
    import re
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    params = {'offset': last_update_id + 1, 'timeout': 0}
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data.get('ok', False):
            return last_update_id
        updates = data.get('result', [])
        new_last_id = last_update_id
        for update in updates:
            update_id = update['update_id']
            message = update.get('message', {})
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id')
            if text and chat_id:
                if text.strip() == "/start":
                    send_telegram("👋 Olá! Seja bem-vindo ao bot de torrents no Telegram. Envie um link magnet para começar o download.", chat_id)
                    new_last_id = max(new_last_id, update_id)
                    continue
                if text.strip() == "/qespaco":
                    try:
                        import shutil
                        total, used, free = shutil.disk_usage("/")
                        def format_bytes(size):
                            for unit in ['B','KB','MB','GB','TB']:
                                if size < 1024:
                                    return f"{size:.2f} {unit}"
                                size /= 1024
                        msg = f"💾 <b>Espaço em disco:</b>\nTotal: {format_bytes(total)}\nUsado: {format_bytes(used)}\nLivre: {format_bytes(free)}"
                        send_telegram(msg, chat_id)
                    except Exception as e:
                        send_telegram(f"❌ Erro ao obter espaço em disco: {str(e)}", chat_id)
                    new_last_id = max(new_last_id, update_id)
                    continue
                magnet_regex = r'magnet:\?xt=urn:btih:[0-9a-f]{40}.*'
                magnets = re.findall(magnet_regex, text, re.IGNORECASE)
                valid_magnets = [m for m in magnets if m.startswith("magnet:")]
                for magnet in valid_magnets:
                    try:
                        add_magnet_func(sess, qb_url, magnet)
                        from urllib.parse import urlparse, parse_qs
                        parsed_magnet = urlparse(magnet)
                        query_params = parse_qs(parsed_magnet.query)
                        torrent_name = query_params.get('dn', [magnet])[0]
                        send_telegram(f"✅ <b>Magnet adicionado:</b>\n{torrent_name}", chat_id)
                    except requests.exceptions.HTTPError as e:
                        error_msg = f"Erro no qBittorrent: {e.response.text}"
                        send_telegram(f"❌ {error_msg}", chat_id)
                    except Exception as e:
                        send_telegram(f"❌ Erro ao processar magnet: {str(e)}", chat_id)
            new_last_id = max(new_last_id, update_id)
        return new_last_id
    except Exception as e:
        send_telegram(f"⚠️ Erro no processamento de mensagens: {str(e)}")
        return last_update_id