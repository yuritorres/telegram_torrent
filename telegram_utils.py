import requests
import os
import re
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Union, Callable

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
    ]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    try:
        resp = requests.post(url, json={"commands": commands}, timeout=10)
        resp.raise_for_status()
        print("Comandos do bot registrados com sucesso no Telegram.")
    except Exception as e:
        print(f"Erro ao registrar comandos do bot: {e}")

def send_telegram(msg: str, chat_id: Optional[Union[str, int]] = None, parse_mode: str = "HTML") -> bool:
    """
    Envia uma mensagem para o Telegram.
    
    Args:
        msg: A mensagem a ser enviada
        chat_id: ID do chat do destinatário (opcional, usa TELEGRAM_CHAT_ID se não fornecido)
        parse_mode: Modo de análise da mensagem (HTML ou Markdown)
        
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Token do bot do Telegram não configurado")
        return False
        
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
        if not chat_id:
            print("❌ Nenhum chat_id fornecido e TELEGRAM_CHAT_ID não configurado")
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
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": str(chat_id), "text": msg}
        
        if parse_mode:
            data["parse_mode"] = parse_mode
            
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar mensagem para o Telegram: {e}")
        # Tenta enviar novamente sem formatação HTML se ocorrer erro
        if parse_mode and parse_mode.upper() == "HTML":
            return send_telegram(msg, chat_id, parse_mode=None)
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar mensagem para o Telegram: {e}")
        return False

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
            msg_parts.append("<b>📥 Torrents Ativos:</b>\n" + "\n".join(f"• {t}" for t in ativos))
        else:
            msg_parts.append("<b>📥 Torrents Ativos:</b> Nenhum")
            
        if pausados:
            msg_parts.append("\n<b>⏸️ Torrents Pausados:</b>\n" + "\n".join(f"• {t}" for t in pausados))
            
        if finalizados:
            msg_parts.append("\n<b>✅ Torrents Finalizados:</b>\n" + "\n".join(f"• {t}" for t in finalizados))
            
        if parados:
            msg_parts.append("\n<b>⚠️  Torrents com Erro/Parados:</b>\n" + "\n".join(f"• {t}" for t in parados))
        
        return "\n".join(msg_parts) if msg_parts else "Nenhum torrent encontrado."
        
    except Exception as e:
        return f"❌ Erro ao listar torrents: {str(e)}"

def process_messages(sess, last_update_id: int, add_magnet_func: callable, qb_url: str) -> int:
    """
    Processa as mensagens recebidas do Telegram.
    
    Args:
        sess: Sessão de autenticação do qBittorrent
        last_update_id: ID da última atualização processada
        add_magnet_func: Função para adicionar um magnet link
        qb_url: URL base da API do qBittorrent
        
    Returns:
        int: ID da última atualização processada
    """
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Token do bot do Telegram não configurado")
        return last_update_id
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {'offset': last_update_id + 1, 'timeout': 10}
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get('ok', False):
            print(f"❌ Resposta inesperada da API do Telegram: {data}")
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
                
                # Verifica se o usuário está autorizado para comandos críticos
                is_authorized = not AUTHORIZED_USERS or user_id in AUTHORIZED_USERS
                
                # Processa comandos
                if text == "/start":
                    welcome_msg = (
                        "👋 *Bem-vindo ao Bot de Gerenciamento de Torrents*\n\n"
                        "📌 *Comandos disponíveis:*\n"
                        "/qespaco - Mostra o espaço em disco\n"
                        "/qtorrents - Lista todos os torrents\n"
                        "\n📥 *Para baixar:*\n"
                        "Envie um link magnet ou .torrent"
                    )
                    send_telegram(welcome_msg, chat_id, parse_mode="Markdown")
                    continue
                    
                elif text == "/qespaco":
                    disk_info = get_disk_space_info(sess, qb_url, chat_id)
                    send_telegram(disk_info, chat_id)
                    continue
                    
                elif text == "/qtorrents":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para executar este comando.", chat_id)
                        continue
                        
                    torrents_list = list_torrents(sess, qb_url)
                    send_telegram(torrents_list, chat_id)
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
                print(f"Erro ao processar mensagem: {e}")
                import traceback
                print(traceback.format_exc())
                
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para a API do Telegram: {e}")
    except Exception as e:
        print(f"Erro inesperado em process_messages: {e}")
        import traceback
        print(traceback.format_exc())
    
    return new_last_id