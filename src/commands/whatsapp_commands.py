"""
Módulo para processar comandos WhatsApp via WAHA
"""
import logging
from typing import Optional
from src.integrations.whatsapp.utils import send_whatsapp, is_authorized_whatsapp

logger = logging.getLogger(__name__)


def process_whatsapp_message(message_data: dict, sess, add_magnet_func, qb_url: str, jellyfin_manager=None) -> bool:
    try:
        from_number = message_data.get('from', '')
        chat_id = message_data.get('chatId', from_number)
        text = message_data.get('body', '').strip()
        message_type = message_data.get('type', 'text')

        if message_type not in ['text', 'chat']:
            return False
        if not text or not chat_id:
            return False

        logger.info(f"Processando mensagem WhatsApp de {from_number}: {text}")
        is_authorized = is_authorized_whatsapp(from_number)

        if text == "/start" or text.lower() in ("ajuda", "/ajuda"):
            handle_start_command(chat_id)
        elif text in ("/qespaco", "espaço"):
            handle_disk_space_command(chat_id, sess, qb_url)
        elif text in ("/qtorrents", "torrents"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_list_torrents_command(chat_id, sess, qb_url)
        elif text == "/status":
            handle_status_command(chat_id, jellyfin_manager)
        elif text.startswith("/recentes"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_recentes_command(chat_id, jellyfin_manager)
        elif text.startswith("/recent"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_recent_command(chat_id, jellyfin_manager)
        elif text.startswith("/libraries"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_libraries_command(chat_id, jellyfin_manager)
        elif text.startswith("/ytsbr_baixar"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_ytsbr_download_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
        elif text.startswith("/ytsbr_series"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_ytsbr_series_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
        elif text.startswith("/ytsbr_anime"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_ytsbr_anime_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
        elif text.startswith("/ytsbr"):
            if not is_authorized:
                send_whatsapp("❌ Você não tem permissão para executar este comando.", chat_id)
            else:
                handle_ytsbr_command(text, chat_id, from_number, add_magnet_func, sess, qb_url)
        else:
            send_whatsapp("❓ Comando não reconhecido.\n\nEnvie /start para ver os comandos disponíveis.", chat_id)

        return True

    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def handle_start_command(chat_id: str):
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
    try:
        from src.integrations.telegram.utils import get_disk_space_info
        disk_info = get_disk_space_info(sess, qb_url, chat_id)
        disk_info = disk_info.replace('<b>', '*').replace('</b>', '*').replace('<i>', '_').replace('</i>', '_')
        send_whatsapp(disk_info, chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter espaço em disco: {e}")
        send_whatsapp("❌ Erro ao obter informações de espaço em disco.", chat_id)


def handle_list_torrents_command(chat_id: str, sess, qb_url: str):
    try:
        from src.integrations.qbittorrent.client import fetch_torrents, format_bytes
        torrents = fetch_torrents(sess, qb_url)
        if not torrents:
            send_whatsapp("📭 Nenhum torrent encontrado.", chat_id)
            return
        message = f"📦 *Torrents ({len(torrents)} total):*\n\n"
        for t in torrents[:10]:
            name = t.get('name', 'Sem nome')[:40]
            state = t.get('state', 'N/A')
            progress = t.get('progress', 0) * 100
            message += f"• {name}\n  Estado: {state} | {progress:.1f}%\n"
        if len(torrents) > 10:
            message += f"\n... e mais {len(torrents) - 10} torrents"
        send_whatsapp(message, chat_id)
    except Exception as e:
        logger.error(f"Erro ao listar torrents: {e}")
        send_whatsapp("❌ Erro ao listar torrents.", chat_id)


def handle_status_command(chat_id: str, jellyfin_manager):
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
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    try:
        items = jellyfin_manager.get_recently_added(limit=10)
        if items:
            message = "🎬 *Itens Recentes:*\n\n"
            for item in items:
                name = item.get('Name', 'Sem nome')
                year = item.get('ProductionYear', '')
                item_type = item.get('Type', 'N/A')
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
    if not jellyfin_manager:
        send_whatsapp("❌ Jellyfin não configurado.", chat_id)
        return
    try:
        items = jellyfin_manager.get_recently_added(limit=5)
        if items:
            for item in items:
                name = item.get('Name', 'Sem nome')
                year = item.get('ProductionYear', '')
                item_type = item.get('Type', 'N/A')
                overview = item.get('Overview', 'Sem descrição')[:200]
                message = f"\n🎬 *{name}*\n📅 Ano: {year if year else 'N/A'}\n📺 Tipo: {item_type}\n📝 Sinopse: {overview}..."
                send_whatsapp(message, chat_id)
        else:
            send_whatsapp("📭 Nenhum item recente encontrado.", chat_id)
    except Exception as e:
        logger.error(f"Erro ao obter itens recentes: {e}")
        send_whatsapp("❌ Erro ao obter itens recentes.", chat_id)


def handle_libraries_command(chat_id: str, jellyfin_manager):
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
    try:
        from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("movie", chat_id, user_id)
        else:
            handle_ytsbr_search(parts[1], "movie", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR: {e}")
        send_whatsapp("❌ Erro ao buscar filmes.", chat_id)


def handle_ytsbr_series_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    try:
        from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("series", chat_id, user_id)
        else:
            handle_ytsbr_search(parts[1], "series", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR séries: {e}")
        send_whatsapp("❌ Erro ao buscar séries.", chat_id)


def handle_ytsbr_anime_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    try:
        from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            handle_ytsbr_popular("anime", chat_id, user_id)
        else:
            handle_ytsbr_search(parts[1], "anime", chat_id, user_id)
    except Exception as e:
        logger.error(f"Erro no comando YTSBR anime: {e}")
        send_whatsapp("❌ Erro ao buscar animes.", chat_id)


def handle_ytsbr_download_command(text: str, chat_id: str, user_id: str, add_magnet_func, sess, qb_url: str):
    try:
        from src.commands.ytsbr_commands import handle_ytsbr_download_by_number
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
