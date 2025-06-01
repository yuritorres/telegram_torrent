import requests
import os
import re
import logging
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Union, Callable
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AUTHORIZED_USERS = [uid.strip() for uid in os.getenv('AUTHORIZED_USERS', '').split(',') if uid.strip()]

def set_bot_commands():
    """
    Define os comandos do menu do bot no Telegram.
    """
    commands = [
        {"command": "start", "description": "Iniciar o bot"},
        {"command": "qespaco", "description": "Mostrar espaço em disco"},
        {"command": "qtorrents", "description": "Listar torrents"},
        {"command": "recent", "description": "Ver itens recentes do Jellyfin"},
        {"command": "libraries", "description": "Listar bibliotecas do Jellyfin"},
        {"command": "status", "description": "Status do servidor Jellyfin"}
    ]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    try:
        resp = requests.post(url, json={"commands": commands}, timeout=10)
        resp.raise_for_status()
        logger.info("Comandos do bot registrados com sucesso no Telegram.")
    except Exception as e:
        logger.error(f"Erro ao registrar comandos do bot: {e}")

EXPIRAR_MSG = int(os.getenv('EXPIRAR_MSG', 30))

def send_and_expire_status(msg: str, chat_id: Optional[Union[str, int]] = None, parse_mode: str = "HTML", expirar: int = None) -> bool:
    """
    Envia uma mensagem de status do qBittorrent e agenda a exclusão após expirar segundos.
    """
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
        # Agenda a exclusão
        threading.Timer(expirar, delete_message, args=(chat_id, message_id)).start()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de status: {e}")
        return False

def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=10)
    except Exception as e:
        logger.error(f"Erro ao apagar mensagem: {e}")

def get_main_keyboard() -> dict:
    """
    Cria um teclado personalizado com os principais comandos.
    
    Returns:
        dict: Teclado personalizado no formato da API do Telegram
    """
    keyboard = {
        'keyboard': [
            [{'text': '📊 Status do Servidor'}],
            [{'text': '📦 Listar Torrents'}, {'text': '💾 Espaço em Disco'}],
            [{'text': '🎬 Itens Recentes'}, {'text': '📚 Bibliotecas'}],
            [{'text': '❓ Ajuda'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    return keyboard

def send_telegram(msg: str, chat_id: Optional[Union[str, int]] = None, parse_mode: str = "HTML", reply_markup: dict = None, use_keyboard: bool = False) -> bool:
    """
    Envia uma mensagem para o Telegram.
    
    Args:
        msg: A mensagem a ser enviada
        chat_id: ID do chat do destinatário (opcional, usa TELEGRAM_CHAT_ID se não fornecido)
        parse_mode: Modo de análise da mensagem (HTML ou Markdown)
        reply_markup: Dicionário de botões inline (opcional)
        use_keyboard: Se True, adiciona o teclado personalizado à mensagem
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token do bot do Telegram não configurado")
        return False
        
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
        if not chat_id:
            logger.error("Nenhum chat_id fornecido e TELEGRAM_CHAT_ID não configurado")
            return False
    
    # Sanitiza a mensagem para evitar erros de formatação HTML
    if parse_mode and parse_mode.upper() == "HTML":
        # Verifica se há tags HTML não fechadas
        open_tags = re.findall(r'<([a-z]+)[^<>]*>', msg, re.IGNORECASE)
        close_tags = re.findall(r'</([a-z]+)>', msg, re.IGNORECASE)
        
        # Se houver tags não fechadas, remove a formatação HTML
        if len(open_tags) != len(close_tags):
            parse_mode = None
    
    # Limita o tamanho da mensagem para evitar erros
    if len(msg) > 4096:
        msg = msg[:4093] + "..."
    
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
        # Tenta enviar novamente sem formatação HTML se ocorrer erro
        if parse_mode and parse_mode.upper() == "HTML":
            return send_telegram(msg, chat_id, parse_mode=None)
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar mensagem para o Telegram: {e}")
        return False

# Função format_bytes movida para qbittorrent_api.py para evitar duplicação

def get_disk_space_info(sess, qb_url: str, chat_id: int) -> str:
    """
    Obtém informações sobre o espaço em disco do servidor qBittorrent.
    
    Args:
        sess: Sessão de autenticação do qBittorrent
        qb_url: URL base da API do qBittorrent
        chat_id: ID do chat para envio de mensagens de erro
        
    Returns:
        str: Mensagem formatada com as informações de espaço em disco
    """
    try:
        if sess is None:
            return "❌ Não conectado ao qBittorrent."
            
        # Importa as funções consolidadas
        from qbittorrent_api import get_transfer_info, format_bytes
        
        # Obtém informações de transferência que incluem espaço em disco
        transfer_info = get_transfer_info(sess, qb_url)
        if not transfer_info:
            return "❌ Não foi possível obter informações de transferência."
            
        free_space = transfer_info.get("free_space_on_disk", 0)
        
        # Se temos informação de espaço livre, tenta obter o total
        if free_space > 0:
            # Tenta obter o caminho de salvamento para calcular espaço total
            try:
                prefs_resp = sess.get(f"{qb_url}/api/v2/app/preferences")
                prefs_resp.raise_for_status()
                prefs_data = prefs_resp.json()
                save_path = prefs_data.get('save_path')
                
                if save_path:
                    import os
                    import shutil
                    if os.path.exists(save_path):
                        disk_usage = shutil.disk_usage(save_path)
                        total = disk_usage.total
                        used = total - free_space
                        
                        return (
                            f"💾 <b>Espaço em disco:</b>\n"
                            f"Total: {format_bytes(total)}\n"
                            f"Usado: {format_bytes(used)}\n"
                            f"Disponível: {format_bytes(free_space)}"
                        )
            except Exception:
                pass
                
            # Fallback: apenas espaço livre
            return f"💾 <b>Espaço disponível:</b> {format_bytes(free_space)}"
        
        return "❌ Informações de espaço em disco não disponíveis."
            
    except Exception as e:
        return f"❌ Erro ao obter informações de espaço em disco: {str(e)}"

def list_torrents(sess, qb_url: str) -> str:
    """
    Lista todos os torrents ativos, pausados, finalizados e parados.
    
    Args:
        sess: Sessão de autenticação do qBittorrent
        qb_url: URL base da API do qBittorrent
        
    Returns:
        str: Mensagem formatada com a lista de torrents
    """
    try:
        if sess is None:
            return "❌ Não conectado ao qBittorrent."
            
        from qbittorrent_api import fetch_torrents
        torrents = fetch_torrents(sess, qb_url)
        
        ativos = []
        pausados = []
        finalizados = []
        parados = []
        
        for t in torrents:
            estado = t.get('state', '')
            nome = t.get('name', 'Sem nome')
            progresso = t.get('progress', 0) * 100
            
            if estado in ['downloading', 'stalledDL', 'checkingDL', 'queuedDL', 'forcedDL']:
                ativos.append(f"{nome} ({progresso:.1f}%)")
            elif estado in ['pausedDL', 'pausedUP']:
                pausados.append(nome)
            elif estado in ['uploading', 'seeding', 'finished', 'stalledUP', 'checkingUP', 'forcedUP']:
                finalizados.append(nome)
            elif estado in ['stalledDL', 'stalledUP', 'error', 'missingFiles', 'unknown']:
                parados.append(f"{nome} ({estado})")
        
        msg_parts = []
        
        if ativos:
            msg_parts.append("<b>📦 Torrents Ativos:</b>\n" + "\n".join(f"• {t}" for t in ativos))
        else:
            msg_parts.append("<b>📦 Torrents Ativos:</b> Nenhum")
            
        if pausados:
            msg_parts.append("\n<b>⏸️ Torrents Pausados:</b>\n" + "\n".join(f"• {t}" for t in pausados))
            
        if finalizados:
            msg_parts.append("\n<b>✅ Torrents Finalizados:</b>\n" + "\n".join(f"• {t}" for t in finalizados))
            
        if parados:
            msg_parts.append("\n<b>❌ Torrents com Erro/Parados:</b>\n" + "\n".join(f"• {t}" for t in parados))
        
        return "\n".join(msg_parts) if msg_parts else "Nenhum torrent encontrado."
        
    except Exception as e:
        return f"❌ Erro ao listar torrents: {str(e)}"

def process_messages(sess, last_update_id: int, add_magnet_func: callable, qb_url: str, jellyfin_manager=None) -> int:
    """
    Processa as mensagens recebidas do Telegram.
    
    Args:
        sess: Sessão de autenticação do qBittorrent
        last_update_id: ID da última atualização processada
        add_magnet_func: Função para adicionar um magnet link
        qb_url: URL base da API do qBittorrent
        jellyfin_manager: Instância do JellyfinManager (opcional)
        
    Returns:
        int: ID da última atualização processada
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Token do bot do Telegram não configurado")
        return last_update_id
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {'offset': last_update_id + 1, 'timeout': 10}
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get('ok', False):
            logger.error(f"Resposta inesperada da API do Telegram: {data}")
            return last_update_id
            
        updates = data.get('result', [])
        new_last_id = last_update_id
        
        for update in updates:
            try:
                update_id = update.get('update_id')
                if update_id is None:
                    continue
                    
                message = update.get('message', {})
                text = message.get('text', '').strip()
                chat_id = message.get('chat', {}).get('id')
                user_id = str(message.get('from', {}).get('id', ''))
                
                if not text or not chat_id or not user_id:
                    continue
                    
                # Atualiza o ID da última mensagem processada
                new_last_id = max(new_last_id, update_id)
                
                is_authorized = not AUTHORIZED_USERS or user_id in AUTHORIZED_USERS
                
                keyboard_command_map = {
                    "📊 Status do Servidor": "/status",
                    "📦 Listar Torrents": "/qtorrents",
                    "💾 Espaço em Disco": "/qespaco",
                    "🎬 Itens Recentes": "/recent",
                    "📚 Bibliotecas": "/libraries",
                    "❓ Ajuda": "/start"
                }
                
                text = keyboard_command_map.get(text, text)
                
                # Processa comandos
                if text == "/start" or text == "❓ Ajuda":
                    WELCOME_MESSAGE = """
                    🤖 *Bem-vindo ao Bot de Gerenciamento de Mídia* 🤖
                    
                    *Comandos disponíveis:*
                    - /start - Mostrar esta mensagem
                    - /qespaco - Mostrar espaço em disco
                    - /qtorrents - Listar torrents ativos
                    - /recent - Ver itens recentes do Jellyfin
                    - /libraries - Listar bibliotecas do Jellyfin
                    - /status - Status do servidor Jellyfin
                    
                    Ou use os botões abaixo para navegar facilmente!"""
                    send_telegram(WELCOME_MESSAGE, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue
                    
                elif text == "/qespaco":
                    disk_info = get_disk_space_info(sess, qb_url, chat_id)
                    send_telegram(disk_info, chat_id, parse_mode="HTML", use_keyboard=True)
                    continue
                    
                elif text == "/qtorrents":
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id)
                        continue
                    
                    torrents_list = list_torrents(sess, qb_url)
                    send_telegram(torrents_list, chat_id, parse_mode="HTML", use_keyboard=True)
                    continue
                
                # Comandos do Jellyfin
                elif text == "/recent" and jellyfin_manager:
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id, use_keyboard=True)
                        continue
                    recent_text = jellyfin_manager.get_recent_items_text()
                    send_telegram(recent_text, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue
                
                elif text == "/libraries" and jellyfin_manager:
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id, use_keyboard=True)
                        continue
                    libraries_text = jellyfin_manager.get_libraries_text()
                    send_telegram(libraries_text, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue
                
                elif text == "/status" and jellyfin_manager:
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id, use_keyboard=True)
                        continue
                    status_text = jellyfin_manager.get_status_text()
                    send_telegram(status_text, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue
                
                # Processa links magnet
                magnet_regex = r'magnet:\?xt=urn:btih:[0-9a-fA-F]{40}.*'
                magnets = re.findall(magnet_regex, text, re.IGNORECASE)
                
                for magnet in magnets:
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para adicionar torrents.", chat_id)
                        continue
                        
                    try:
                        send_telegram("⏳ Adicionando torrent, aguarde...", chat_id)
                        result = add_magnet_func(sess, qb_url, magnet)
                        if result:
                            send_telegram("✅ Torrent adicionado com sucesso!", chat_id)
                        else:
                            send_telegram("❌ Falha ao adicionar o torrent.", chat_id)
                    except Exception as e:
                        send_telegram(f"❌ Erro ao adicionar torrent: {str(e)}", chat_id)
                
            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição para a API do Telegram: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado em process_messages: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return new_last_id