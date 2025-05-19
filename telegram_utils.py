import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

AUTHORIZED_USERS = os.getenv('AUTHORIZED_USERS', '').split(',') if os.getenv('AUTHORIZED_USERS') else []

def send_telegram(msg, chat_id=None):
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    resp = requests.post(url, data=data)
    resp.raise_for_status()

#Telegram Jellyfin
from jellyfin_telegram import process_jellyfin_command

def process_messages(sess, last_update_id, add_magnet_func, qb_url):
    import re
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
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
            user_id = message.get('from', {}).get('id')
            if text and chat_id:
                # Comandos Jellyfin
                if process_jellyfin_command(text, chat_id):
                    new_last_id = max(new_last_id, update_id)
                    continue
                # Verifica se o usuário está autorizado para comandos críticos
                is_authorized = not AUTHORIZED_USERS or str(user_id) in AUTHORIZED_USERS
                if text.strip() == "/start":
                    send_telegram("👋 Olá! Seja bem-vindo ao bot de torrents no Telegram. Envie um link magnet para começar o download.", chat_id)
                    new_last_id = max(new_last_id, update_id)
                    continue
                if text.strip() == "/qespaco":
                    try:
                        import shutil
                        total, used, free = shutil.disk_usage(qbittorrent_storage_path)
                        def format_bytes(size):
                            for unit in ['B','KB','MB','GB','TB']:
                                if size < 1024:
                                    return f"{size:.2f} {unit}"
                                size /= 1024
                        msg = f"💾 <b>Espaço em disco:</b>\nTotal: {format_bytes(total)}\nUsado: {format_bytes(used)}\nLivre: {format_bytes(free)}"
                        send_telegram(msg, chat_id)
                    except Exception:
                        send_telegram("❌ Erro ao obter espaço em disco.", chat_id)
                    new_last_id = max(new_last_id, update_id)
                    continue
                if text.strip() == "/qtorrents":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para executar este comando.", chat_id)
                        new_last_id = max(new_last_id, update_id)
                        continue
                    try:
                        if sess is None:
                            send_telegram("❌ Não conectado ao qBittorrent.", chat_id)
                        else:
                            from qbittorrent_api import fetch_torrents
                            torrents = fetch_torrents(sess, qb_url)
                            ativos = []
                            pausados = []
                            finalizados = []
                            parados = []
                            for t in torrents:
                                estado = t.get('state','')
                                nome = t.get('name','')
                                if estado in ['downloading','stalledDL','checkingDL','queuedDL','forcedDL']:
                                    ativos.append(nome)
                                elif estado in ['pausedDL','pausedUP']:
                                    pausados.append(nome)
                                elif estado in ['uploading','seeding','finished','stalledUP','checkingUP','forcedUP']:
                                    finalizados.append(nome)
                                elif estado in ['stalledDL','stalledUP','error','missingFiles','unknown']:
                                    parados.append(nome)
                            msg = "<b>Torrents Ativos:</b>\n" + ("\n".join(ativos) if ativos else "Nenhum")
                            msg += "\n\n<b>Torrents Pausados:</b>\n" + ("\n".join(pausados) if pausados else "Nenhum")
                            msg += "\n\n<b>Torrents Finalizados:</b>\n" + ("\n".join(finalizados) if finalizados else "Nenhum")
                            msg += "\n\n<b>Torrents Parados:</b>\n" + ("\n".join(parados) if parados else "Nenhum")
                            send_telegram(msg, chat_id)
                    except Exception:
                        send_telegram("❌ Erro ao listar torrents.", chat_id)
                    new_last_id = max(new_last_id, update_id)
                    continue
                magnet_regex = r'magnet:\?xt=urn:btih:[0-9a-f]{40}.*'
                magnets = re.findall(magnet_regex, text, re.IGNORECASE)
                valid_magnets = [m for m in magnets if m.startswith("magnet:")]
                for magnet in valid_magnets:
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para adicionar torrents.", chat_id)
                        continue
                    try:
                        add_magnet_func(sess, qb_url, magnet)
                        from urllib.parse import urlparse, parse_qs
                        parsed_magnet = urlparse(magnet)
                        query_params = parse_qs(parsed_magnet.query)
                        torrent_name = query_params.get('dn', [magnet])[0]
                        send_telegram(f"✅ <b>Magnet adicionado:</b>\n{torrent_name}", chat_id)
                    except requests.exceptions.HTTPError:
                        send_telegram("❌ Erro no qBittorrent ao adicionar magnet.", chat_id)
                    except Exception:
                        send_telegram("❌ Erro ao processar magnet.", chat_id)
            new_last_id = max(new_last_id, update_id)
        return new_last_id
    except Exception:
        send_telegram("⚠️ Erro no processamento de mensagens.")
        return last_update_id