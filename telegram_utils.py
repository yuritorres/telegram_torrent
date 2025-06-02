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
        {"command": "recentes", "description": "Ver itens recentemente adicionados (detalhado)"},
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
            [{'text': '🎬 Itens Recentes'}, {'text': '🎭 Recentes Detalhado'}],
            [{'text': '📚 Bibliotecas'}, {'text': '❓ Ajuda'}]
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

def format_bytes(size: int) -> str:
    """
    Formata um tamanho em bytes para uma string legível.
    
    Args:
        size: Tamanho em bytes
        
    Returns:
        str: String formatada (ex: "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def get_recent_items_detailed(jellyfin_manager, limit: int = 10) -> str:
    """
    Obtém itens recentemente adicionados com informações detalhadas.
    
    Args:
        jellyfin_manager: Instância do JellyfinManager
        limit: Número máximo de itens a retornar
        
    Returns:
        str: Mensagem formatada com informações detalhadas dos itens recentes
    """
    if not jellyfin_manager or not jellyfin_manager.is_available():
        return "❌ Jellyfin não configurado ou indisponível."
    
    try:
        items = jellyfin_manager.client.get_recently_added(limit)
        if not items:
            return "📥 Nenhum item recente encontrado."
        
        messages = []
        messages.append("🎬 **Itens recentemente adicionados (detalhado):**\n")
        
        for i, item in enumerate(items, 1):
            # Informações básicas
            name = item.get('Name', 'Sem título')
            item_type = item.get('Type', 'Desconhecido')
            year = item.get('ProductionYear', '')
            
            # Gêneros
            genres = item.get('Genres', [])
            genres_text = ', '.join(genres[:3]) if genres else 'N/A'
            
            # Avaliação
            rating = item.get('CommunityRating')
            rating_text = f"⭐ {rating:.1f}" if rating else "⭐ N/A"
            
            # Data de criação
            date_created = item.get('DateCreated', '')
            if date_created:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                    date_text = date_obj.strftime('%d/%m/%Y')
                except:
                    date_text = 'N/A'
            else:
                date_text = 'N/A'
            
            # Sinopse
            overview = item.get('Overview', '')
            if overview and len(overview) > 150:
                overview = overview[:150] + "..."
            
            # Link web
            web_link = jellyfin_manager.client.get_web_link(item['Id'])
            
            # Monta a mensagem do item
            item_msg = f"**{i}. {name}**"
            if year:
                item_msg += f" ({year})"
            item_msg += f"\n📺 Tipo: {item_type}"
            item_msg += f"\n{rating_text}"
            item_msg += f"\n🎭 Gêneros: {genres_text}"
            item_msg += f"\n📅 Adicionado: {date_text}"
            
            if overview:
                item_msg += f"\n\n_{overview}_"
            
            item_msg += f"\n🔗 [Ver no Jellyfin]({web_link})"
            
            messages.append(item_msg)
        
        return "\n\n".join(messages)
        
    except Exception as e:
        logger.error(f"Erro ao obter itens recentes detalhados: {e}")
        return f"❌ Erro ao buscar itens recentes: {str(e)}"


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
            
        # Obtém o caminho de salvamento padrão do qBittorrent
        prefs_resp = sess.get(f"{qb_url}/api/v2/app/preferences")
        prefs_resp.raise_for_status()
        prefs_data = prefs_resp.json()
        save_path = prefs_data.get('save_path')
        
        if not save_path:
            return "❌ Caminho de salvamento do qBittorrent não encontrado."
            
        # Tenta obter informações do disco via API do qBittorrent
        try:
            drive_info_resp = sess.get(f"{qb_url}/api/v2/app/drive_info", params={"path": save_path})
            drive_info_resp.raise_for_status()
            drive_info = drive_info_resp.json()
            total = drive_info.get('total')
            free = drive_info.get('free')
            used = total - free if total is not None and free is not None else None
            
            if total is not None and used is not None and free is not None:
                return f"💾 Espaço em disco:\nTotal: {format_bytes(total)}\nUsado: {format_bytes(used)}\nLivre: {format_bytes(free)}"
                
        except Exception as e:
            # Se for erro 404, tenta usar fallback para /sync/maindata
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                try:
                    maindata_resp = sess.get(f"{qb_url}/api/v2/sync/maindata", params={"rid": 0})
                    maindata_resp.raise_for_status()
                    maindata = maindata_resp.json()
                    server_state = maindata.get('server_state', {})
                    free = server_state.get('free_space_on_disk')
                    
                    if free is not None:
                        # Tenta obter o total do sistema de arquivos local
                        import os
                        if save_path and os.path.exists(save_path):
                            try:
                                import shutil
                                disk_usage = shutil.disk_usage(save_path)
                                total = disk_usage.total
                                used = total - free if free is not None else None
                                
                                if total is not None and used is not None:
                                    return f"💾 Espaço em disco (local):\nTotal: {format_bytes(total)}\nUsado: {format_bytes(used)}\nLivre: {format_bytes(free)}"
                            except Exception:
                                pass
                        
                        return f"💾 Espaço livre no disco: {format_bytes(free)}"
                except Exception as inner_e:
                    return f"❌ Erro ao obter espaço em disco: {str(inner_e)}"
            
            return f"❌ Erro ao obter espaço em disco: {str(e)}"
            
    except Exception as e:
        return f"❌ Erro ao obter informações de espaço em disco: {str(e)}"
    
    return "❌ Não foi possível obter as informações de espaço em disco."

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
                    "🎭 Recentes Detalhado": "/recentes",
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
                    - /recentes - Ver itens recentemente adicionados (detalhado)
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
                
                elif text == "/recentes" and jellyfin_manager:
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id, use_keyboard=True)
                        continue
                    send_telegram("🔍 Buscando itens recentemente adicionados...", chat_id, use_keyboard=True)
                    recent_detailed = get_recent_items_detailed(jellyfin_manager, 8)
                    send_telegram(recent_detailed, chat_id, parse_mode="Markdown", use_keyboard=True)
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