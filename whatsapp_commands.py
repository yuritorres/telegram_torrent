"""
Módulo para processar comandos WhatsApp
Similar ao telegram_utils.py mas adaptado para WhatsApp
"""
import logging
from typing import Optional
from waha_utils import send_whatsapp, is_authorized_whatsapp, format_chat_id

logger = logging.getLogger(__name__)


def process_whatsapp_message(message_data: dict, sess, add_magnet_func, qb_url: str, jellyfin_manager=None) -> bool:
    """
    Processa uma mensagem recebida do WhatsApp
    
    Args:
        message_data: Dados da mensagem do webhook
        sess: Sessão de autenticação do qBittorrent
        add_magnet_func: Função para adicionar um magnet link
        qb_url: URL base da API do qBittorrent
        jellyfin_manager: Instância do JellyfinManager (opcional)
        
    Returns:
        bool: True se a mensagem foi processada com sucesso
    """
    try:
        # Extrair informações da mensagem
        from_number = message_data.get('from', '')
        chat_id = message_data.get('chatId', from_number)
        text = message_data.get('body', '').strip()
        message_type = message_data.get('type', 'text')
        
        # Verificar se é mensagem de texto
        if message_type not in ['text', 'chat']:
            logger.info(f"Tipo de mensagem ignorado: {message_type}")
            return False
        
        if not text or not chat_id:
            return False
        
        logger.info(f"Processando mensagem WhatsApp de {from_number}: {text}")
        
        # Verificar autorização
        is_authorized = is_authorized_whatsapp(from_number)
        
        # Processar comandos
        if text == "/start" or text.lower() == "ajuda" or text == "/ajuda":
            handle_start_command(chat_id)
            return True
            
        elif text == "/qespaco" or text.lower() == "espaço":
            handle_disk_space_command(chat_id, sess, qb_url)
            return True
            
        elif text == "/qtorrents" or text.lower() == "torrents":
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_list_torrents_command(chat_id, sess, qb_url)
            return True
            
        elif text == "/status":
            handle_status_command(chat_id, jellyfin_manager)
            return True
            
        elif text.startswith("/recent"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_recent_command(chat_id, jellyfin_manager)
            return True
            
        elif text.startswith("/recentes"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_recentes_command(chat_id, jellyfin_manager)
            return True
            
        elif text.startswith("/libraries"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_libraries_command(chat_id, jellyfin_manager)
            return True
            
        elif text.startswith("/ytsbr"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_ytsbr_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
            return True
            
        elif text.startswith("/ytsbr_series"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_ytsbr_series_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
            return True
            
        elif text.startswith("/ytsbr_anime"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_ytsbr_anime_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
            return True
            
        elif text.startswith("/ytsbr_baixar"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
                return True
            handle_ytsbr_download_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
            return True
            
        else:
            # Comando não reconhecido
            send_whatsapp(
                "❓ Comando não reconhecido.\n\nEnvie /start para ver os comandos disponíveis.",
                chat_id
            )
            return True
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def handle_start_command(chat_id: str):
    """Envia mensagem de boas-vindas"""
    welcome_message = """
🤖 *Bem-vindo ao Bot de Gerenciamento de Mídia* 🤖

*Comandos disponíveis:*

📊 *Servidor:*
• /status - Status do servidor Jellyfin
• /qespaco - Espaço em disco
• /qtorrents - Listar torrents ativos

🎬 *Jellyfin:*
• /recent - Itens recentes
• /recentes - Itens recentes (detalhado)
• /libraries - Listar bibliotecas

🎥 *YTSBR (Filmes/Séries):*
• /ytsbr [termo] - Buscar filmes
• /ytsbr_series [termo] - Buscar séries
• /ytsbr_anime [termo] - Buscar animes
• /ytsbr_baixar [número] - Baixar item

💡 *Dica:* Você pode usar palavras-chave como "torrents", "espaço", "ajuda" sem o /
    """
    send_whatsapp(welcome_message, chat_id)


def handle_disk_space_command(chat_id: str, sess, qb_url: str):
    """Mostra informações de espaço em disco"""
    try:
        from telegram_utils import get_disk_space_info
        disk_info = get_disk_space_info(sess, qb_url, chat_id)
        # Remove HTML tags para WhatsApp
        disk_info = disk_info.replace('<b>', '*').replace('</b>', '*')
        disk_info = disk_info.replace('<i>', '_').replace('</i>', '_')
        send_whatsapp(disk_info, chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter espaço em disco: {e}")
        send_whatsapp("❌ Erro ao obter informações de espaço em disco.", chat_id)


def handle_list_torrents_command(chat_id: str, sess, qb_url: str):
    """Lista torrents ativos"""
    try:
        from telegram_utils import list_torrents
        torrents_list = list_torrents(sess, qb_url)
        # Remove HTML tags para WhatsApp
        torrents_list = torrents_list.replace('<b>', '*').replace('</b>', '*')
        torrents_list = torrents_list.replace('<i>', '_').replace('</i>', '_')
        send_whatsapp(torrents_list, chat_id)
    except Exception as e:
        logger.error(f"Erro ao listar torrents: {e}")
        send_whatsapp("❌ Erro ao listar torrents.", chat_id)


def handle_status_command(chat_id: str, jellyfin_manager):
    """Mostra status do servidor Jellyfin"""
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    
    try:
        status = jellyfin_manager.get_server_info()
        if status:
            message = f"""
📊 *Status do Servidor Jellyfin*

🖥️ *Servidor:* {status.get('ServerName', 'N/A')}
📌 *Versão:* {status.get('Version', 'N/A')}
🆔 *ID:* {status.get('Id', 'N/A')[:8]}...
            """
            send_whatsapp(message, chat_id)
        else:
            send_whatsapp("❌ Não foi possível obter status do servidor.", chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        send_whatsapp("❌ Erro ao obter status do servidor.", chat_id)


def handle_recent_command(chat_id: str, jellyfin_manager):
    """Mostra itens recentes do Jellyfin"""
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    
    try:
        items = jellyfin_manager.get_recently_added(limit=10)
        if items:
            message = "🎬 *Itens Recentes:*\n\n"
            for item in items:
                name = item.get('Name', 'Sem nome')
                item_type = item.get('Type', 'N/A')
                year = item.get('ProductionYear', '')
                message += f"• {name}"
                if year:
                    message += f" ({year})"
                message += f" - {item_type}\n"
            send_whatsapp(message, chat_id)
        else:
            send_whatsapp("📭 Nenhum item recente encontrado.", chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter itens recentes: {e}")
        send_whatsapp("❌ Erro ao obter itens recentes.", chat_id)


def handle_recentes_command(chat_id: str, jellyfin_manager):
    """Mostra itens recentes detalhados"""
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    
    try:
        items = jellyfin_manager.get_recently_added(limit=5)
        if items:
            for item in items:
                name = item.get('Name', 'Sem nome')
                item_type = item.get('Type', 'N/A')
                year = item.get('ProductionYear', '')
                overview = item.get('Overview', 'Sem descrição')[:200]
                
                message = f"""
🎬 *{name}*
📅 Ano: {year if year else 'N/A'}
📺 Tipo: {item_type}
📝 Sinopse: {overview}...
                """
                send_whatsapp(message, chat_id)
        else:
            send_whatsapp("📭 Nenhum item recente encontrado.", chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter itens recentes: {e}")
        send_whatsapp("❌ Erro ao obter itens recentes.", chat_id)


def handle_libraries_command(chat_id: str, jellyfin_manager):
    """Lista bibliotecas do Jellyfin"""
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    
    try:
        libraries = jellyfin_manager.get_libraries()
        if libraries:
            message = "📚 *Bibliotecas Disponíveis:*\n\n"
            for lib in libraries:
                name = lib.get('Name', 'Sem nome')
                lib_type = lib.get('CollectionType', 'N/A')
                message += f"• {name} ({lib_type})\n"
            send_whatsapp(message, chat_id)
        else:
            send_whatsapp("📭 Nenhuma biblioteca encontrada.", chat_id)
    except Exception as e:
        logger.error(f"Erro ao listar bibliotecas: {e}")
        send_whatsapp("❌ Erro ao listar bibliotecas.", chat_id)


def handle_ytsbr_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    """Processa comando de busca YTSBR (filmes)"""
    try:
        from ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("movie", chat_id, user_id)
        else:
            query = parts[1]
            handle_ytsbr_search(query, "movie", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR: {e}")
        send_whatsapp("❌ Erro ao buscar filmes.", chat_id)


def handle_ytsbr_series_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    """Processa comando de busca YTSBR (séries)"""
    try:
        from ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("series", chat_id, user_id)
        else:
            query = parts[1]
            handle_ytsbr_search(query, "series", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR séries: {e}")
        send_whatsapp("❌ Erro ao buscar séries.", chat_id)


def handle_ytsbr_anime_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    """Processa comando de busca YTSBR (animes)"""
    try:
        from ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("anime", chat_id, user_id)
        else:
            query = parts[1]
            handle_ytsbr_search(query, "anime", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR anime: {e}")
        send_whatsapp("❌ Erro ao buscar animes.", chat_id)


def handle_ytsbr_download_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    """Processa comando de download YTSBR"""
    try:
        from ytsbr_commands import handle_ytsbr_download_by_number
        
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            send_whatsapp("❌ Use: /ytsbr_baixar [número]\nExemplo: /ytsbr_baixar 1", chat_id)
        else:
            try:
                number = int(parts[1])
                handle_ytsbr_download_by_number(number, user_id, chat_id, add_magnet_func, sess, qb_url)
            except ValueError:
                send_whatsapp("❌ Número inválido. Use apenas números.\n\nExemplo: /ytsbr_baixar 1", chat_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR download: {e}")
        send_whatsapp("❌ Erro ao processar download.", chat_id)
