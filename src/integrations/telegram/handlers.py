import requests
import re
import logging
import time
import asyncio
import os
from typing import Optional
from src.core.config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USERS
from src.integrations.telegram.client import send_telegram, answer_callback_query, send_video_to_telegram
from src.integrations.telegram.utils import (
    get_disk_space_info,
    list_torrents,
    get_recent_items_detailed,
    handle_pause_all_torrents,
    handle_resume_all_torrents,
)

logger = logging.getLogger(__name__)


async def process_youtube_download(url: str, chat_id: str) -> None:
    from src.integrations.youtube.downloader import YouTubeDownloader
    from src.integrations.youtube.utils import format_duration, format_filesize
    from src.core.config import REMOVE_AFTER_SEND

    downloader = YouTubeDownloader(download_dir="downloads")
    try:
        send_telegram("🔍 Obtendo informações do vídeo...", chat_id, use_keyboard=True)
        video_info = downloader.get_video_info(url)
        if not video_info:
            send_telegram("❌ Não foi possível obter informações do vídeo. Verifique se o link está correto.", chat_id, use_keyboard=True)
            return

        title = video_info.get('title', 'Título não disponível')
        author = video_info.get('uploader', 'Canal desconhecido')
        duration = video_info.get('duration', 0)
        views = video_info.get('view_count', 0)
        upload_date = video_info.get('upload_date', 'Data desconhecida')

        if upload_date and upload_date != 'Data desconhecida':
            try:
                from datetime import datetime
                date_obj = datetime.strptime(upload_date, '%Y%m%d')
                upload_date = date_obj.strftime('%d/%m/%Y')
            except Exception:
                pass

        video_info_text = f"""
📺 *{title}*

👤 *Canal:* {author}
⏱ *Duração:* {format_duration(duration)}
📊 *Visualizações:* {views:,}
📅 *Publicado:* {upload_date}

📥 *Iniciando download...*"""
        send_telegram(video_info_text, chat_id, parse_mode="Markdown", use_keyboard=True)

        def on_complete(download_id, file_path):
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 50 * 1024 * 1024:
                    send_telegram(f"❌ O vídeo é muito grande para ser enviado pelo Telegram ({format_filesize(file_size)}). Limite: 50MB", chat_id, use_keyboard=True)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    return
                send_video_to_telegram(file_path, chat_id, title)
                if REMOVE_AFTER_SEND:
                    try:
                        os.remove(file_path)
                        logger.info(f"Arquivo removido após envio: {file_path}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo {file_path}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar arquivo baixado: {e}")
                send_telegram(f"❌ Erro ao processar o arquivo baixado: {str(e)}", chat_id, use_keyboard=True)

        def on_error(download_id, error_msg):
            send_telegram(f"❌ Erro no download: {error_msg}", chat_id, use_keyboard=True)

        download_id = downloader.download_video_async(
            url=url,
            output_path="downloads",
            on_complete=on_complete,
            on_error=on_error,
            max_filesize="50M",
        )

        await asyncio.sleep(2)
        last_progress_update = 0
        max_wait_time = 600
        start_time = time.time()

        while True:
            status = downloader.get_download_status(download_id)
            if not status:
                break
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                send_telegram("⏰ Download cancelado por timeout (10 minutos)", chat_id, use_keyboard=True)
                downloader.cancel_download(download_id)
                break
            if status['status'].value in ['completed', 'failed', 'cancelled']:
                break
            if current_time - last_progress_update >= 10:
                elapsed = int(current_time - status['start_time'])
                send_telegram(f"📥 *Baixando...* ⏱ {elapsed}s", chat_id, parse_mode="Markdown", use_keyboard=True)
                last_progress_update = current_time
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Erro no processo de download do YouTube: {e}")
        send_telegram(f"❌ Erro inesperado: {str(e)}", chat_id, use_keyboard=True)


def process_messages(sess, last_update_id: int, add_magnet_func, qb_url: str, jellyfin_manager=None, sync_manager=None, stats_manager=None, docker_manager=None, multi_instance_manager=None) -> int:
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
                new_last_id = max(new_last_id, update_id)

                if 'callback_query' in update:
                    callback_query = update['callback_query']
                    callback_id = callback_query.get('id')
                    callback_data = callback_query.get('data', '')
                    chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
                    user_id = str(callback_query.get('from', {}).get('id', ''))

                    if not chat_id or not user_id:
                        continue
                    is_authorized = not AUTHORIZED_USERS or user_id in AUTHORIZED_USERS
                    if not is_authorized:
                        answer_callback_query(callback_id, "❌ Você não tem permissão para usar este bot.")
                        continue
                    answer_callback_query(callback_id)

                    if callback_data == 'torrent_refresh':
                        list_torrents(sess, qb_url, chat_id)
                    elif callback_data == 'torrent_pause_all':
                        handle_pause_all_torrents(sess, qb_url, chat_id)
                    elif callback_data == 'torrent_resume_all':
                        handle_resume_all_torrents(sess, qb_url, chat_id)
                    elif callback_data == 'torrent_details':
                        help_text = """
<b>📋 AJUDA - GERENCIADOR DE TORRENTS</b>

<b>Botões disponíveis:</b>
• 🔄 <b>Atualizar Lista</b> - Atualiza a lista de torrents
• ⏸️ <b>Pausar Todos</b> - Pausa todos os torrents ativos
• ▶️ <b>Retomar Todos</b> - Retoma todos os torrents pausados
• 📋 <b>Detalhes</b> - Mostra esta mensagem de ajuda

<b>Estados dos torrents:</b>
• 📥 <b>Downloads Ativos</b> - Torrents sendo baixados
• ⏸️ <b>Pausados</b> - Torrents pausados manualmente
• ✅ <b>Finalizados/Seeding</b> - Torrents completos
• ❌ <b>Com Erro</b> - Torrents com problemas

<b>Comandos úteis:</b>
• /qtorrents - Listar torrents
• /qespaco - Ver espaço em disco
"""
                        send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
                    continue

                message = update.get('message', {})
                text = message.get('text', '').strip()
                chat_id = message.get('chat', {}).get('id')
                user_id = str(message.get('from', {}).get('id', ''))

                if not text or not chat_id or not user_id:
                    continue

                is_authorized = not AUTHORIZED_USERS or user_id in AUTHORIZED_USERS

                keyboard_command_map = {
                    "📊 Status do Servidor": "/status",
                    "📦 Listar Torrents": "/qtorrents",
                    "💾 Espaço em Disco": "/qespaco",
                    "🎬 Itens Recentes": "/recent",
                    "🎭 Recentes Detalhado": "/recentes",
                    "📚 Bibliotecas": "/libraries",
                    "🎥 YouTube": "/youtube",
                    "🎬 Buscar Filmes": "/ytsbr",
                    "📺 Buscar Séries": "/ytsbr_series",
                    "🎌 Buscar Animes": "/ytsbr_anime",
                    "❓ Ajuda": "/start",
                }
                text = keyboard_command_map.get(text, text)

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
                    - /youtube - Baixar vídeo do YouTube
                    
                    Ou use os botões abaixo para navegar facilmente!"""
                    send_telegram(WELCOME_MESSAGE, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue

                elif text == "/qespaco":
                    if multi_instance_manager:
                        # Modo multi-instância: mostrar espaço de todas as instâncias
                        from src.commands.multi_instance_commands import handle_instances_command
                        handle_instances_command(chat_id)
                    else:
                        # Modo instância única
                        disk_info = get_disk_space_info(sess, qb_url, chat_id)
                        send_telegram(disk_info, chat_id, parse_mode="HTML", use_keyboard=True)
                    continue

                elif text == "/qtorrents":
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id)
                        continue
                    
                    if multi_instance_manager:
                        # Modo multi-instância: listar torrents de todas as instâncias
                        from src.commands.multi_instance_commands import handle_torrents_multi_command
                        handle_torrents_multi_command(chat_id)
                    else:
                        # Modo instância única
                        list_torrents(sess, qb_url, chat_id)
                    continue

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

                elif text == "/youtube":
                    if not is_authorized:
                        send_telegram("Você não tem permissão para executar este comando.", chat_id, use_keyboard=True)
                        continue
                    youtube_help = """
🎥 *Download de Vídeos do YouTube*

*Como usar:*
• Envie um link do YouTube após este comando
• Exemplo: `/youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ`
• Ou simplesmente envie o link do YouTube diretamente

*Formatos suportados:*
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/shorts/...

*Limitações:*
• Tamanho máximo: 50MB
• Apenas vídeos públicos
• Sem playlists (apenas vídeos individuais)

📝 *Dica:* Você pode enviar o link diretamente sem usar o comando!"""
                    send_telegram(youtube_help, chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue

                elif text.startswith("/stats"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_stats_command
                    parts = text.split()
                    hours = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 24
                    handle_stats_command(stats_manager, chat_id, hours)
                    continue

                elif text.startswith("/history"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_history_command
                    parts = text.split()
                    days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 7
                    handle_history_command(stats_manager, chat_id, days)
                    continue

                elif text == "/sync":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_sync_command
                    handle_sync_command(sync_manager, chat_id)
                    continue

                elif text == "/sync_status":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_sync_status_command
                    handle_sync_status_command(sync_manager, chat_id)
                    continue

                elif text.startswith("/priority"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_priority_command
                    parts = text.split()
                    torrent_hash = parts[1] if len(parts) > 1 else None
                    priority = parts[2] if len(parts) > 2 else None
                    handle_priority_command(sess, qb_url, chat_id, torrent_hash, priority)
                    continue

                elif text.startswith("/remove"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.telegram_commands import handle_remove_command
                    parts = text.split()
                    torrent_hash = parts[1] if len(parts) > 1 else None
                    delete_files = len(parts) > 2 and parts[2].lower() == 'delete'
                    handle_remove_command(sess, qb_url, chat_id, torrent_hash, delete_files)
                    continue

                elif text == "/instances":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.multi_instance_commands import handle_instances_command
                    handle_instances_command(chat_id)
                    continue

                elif text == "/torrents_multi":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.multi_instance_commands import handle_torrents_multi_command
                    handle_torrents_multi_command(chat_id)
                    continue

                elif text == "/refresh_storage":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.multi_instance_commands import handle_refresh_storage_command
                    handle_refresh_storage_command(chat_id)
                    continue

                elif text == "/reconnect_instances":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.multi_instance_commands import handle_reconnect_instances_command
                    handle_reconnect_instances_command(chat_id)
                    continue

                elif text == "/docker_list":
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_list_command
                    handle_docker_list_command(docker_manager, chat_id)
                    continue

                elif text.startswith("/docker_start"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_start_command
                    parts = text.split(maxsplit=1)
                    container_name = parts[1] if len(parts) > 1 else None
                    handle_docker_start_command(docker_manager, chat_id, container_name)
                    continue

                elif text.startswith("/docker_stop"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_stop_command
                    parts = text.split(maxsplit=1)
                    container_name = parts[1] if len(parts) > 1 else None
                    handle_docker_stop_command(docker_manager, chat_id, container_name)
                    continue

                elif text.startswith("/docker_restart"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_restart_command
                    parts = text.split(maxsplit=1)
                    container_name = parts[1] if len(parts) > 1 else None
                    handle_docker_restart_command(docker_manager, chat_id, container_name)
                    continue

                elif text.startswith("/docker_stats"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_stats_command
                    parts = text.split(maxsplit=1)
                    container_name = parts[1] if len(parts) > 1 else None
                    handle_docker_stats_command(docker_manager, chat_id, container_name)
                    continue

                elif text.startswith("/docker_logs"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.docker_commands import handle_docker_logs_command
                    parts = text.split()
                    container_name = parts[1] if len(parts) > 1 else None
                    tail = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30
                    handle_docker_logs_command(docker_manager, chat_id, container_name, tail)
                    continue

                elif text.startswith("/ytsbr_baixar"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_download_by_number
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        send_telegram("❌ Use: `/ytsbr_baixar [número]`\nExemplo: `/ytsbr_baixar 1`", chat_id, parse_mode="Markdown", use_keyboard=True)
                    else:
                        try:
                            number = int(parts[1])
                            handle_ytsbr_download_by_number(number, user_id, chat_id, add_magnet_func, sess, qb_url)
                        except ValueError:
                            send_telegram("❌ Número inválido. Use apenas números.\n\n*Exemplo:* `/ytsbr_baixar 1`", chat_id, parse_mode="Markdown", use_keyboard=True)
                    continue

                elif text.startswith("/ytsbr_generos"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_genres
                    handle_ytsbr_genres("movie", chat_id)
                    continue

                elif text.startswith("/ytsbr_genero"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_by_genre
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        send_telegram("❌ Use: `/ytsbr_genero [nome do gênero]`\nExemplo: `/ytsbr_genero acao`\n\nPara ver gêneros disponíveis: `/ytsbr_generos`", chat_id, parse_mode="Markdown", use_keyboard=True)
                    else:
                        handle_ytsbr_by_genre(parts[1], "movie", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_series_generos"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_genres
                    handle_ytsbr_genres("series", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_series_genero"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_by_genre
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        send_telegram("❌ Use: `/ytsbr_series_genero [nome do gênero]`\nExemplo: `/ytsbr_series_genero drama`\n\nPara ver gêneros disponíveis: `/ytsbr_series_generos`", chat_id, parse_mode="Markdown", use_keyboard=True)
                    else:
                        handle_ytsbr_by_genre(parts[1], "series", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_anime_generos"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_genres
                    handle_ytsbr_genres("anime", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_anime_genero"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_by_genre
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        send_telegram("❌ Use: `/ytsbr_anime_genero [nome do gênero]`\nExemplo: `/ytsbr_anime_genero acao`\n\nPara ver gêneros disponíveis: `/ytsbr_anime_generos`", chat_id, parse_mode="Markdown", use_keyboard=True)
                    else:
                        handle_ytsbr_by_genre(parts[1], "anime", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        handle_ytsbr_popular("movie", chat_id, user_id)
                    else:
                        handle_ytsbr_search(parts[1], "movie", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_series"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        handle_ytsbr_popular("series", chat_id, user_id)
                    else:
                        handle_ytsbr_search(parts[1], "series", chat_id, user_id)
                    continue

                elif text.startswith("/ytsbr_anime"):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para usar este comando.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_search, handle_ytsbr_popular
                    parts = text.split(maxsplit=1)
                    if len(parts) == 1:
                        handle_ytsbr_popular("anime", chat_id, user_id)
                    else:
                        handle_ytsbr_search(parts[1], "anime", chat_id, user_id)
                    continue

                elif "ytsbr.com/" in text and any(x in text for x in ["/filme/", "/serie/", "/anime/"]):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para baixar torrents.", chat_id, use_keyboard=True)
                        continue
                    from src.commands.ytsbr_commands import handle_ytsbr_details
                    url_match = re.search(r'https?://ytsbr\.com/(?:filme|serie|anime)/[^\s]+', text)
                    if url_match:
                        handle_ytsbr_details(url_match.group(0), chat_id, add_magnet_func, sess, qb_url)
                    continue

                from src.integrations.youtube.utils import is_youtube_url
                if is_youtube_url(text):
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para baixar vídeos do YouTube.", chat_id, use_keyboard=True)
                        continue
                    try:
                        asyncio.create_task(process_youtube_download(text, chat_id))
                    except Exception as e:
                        logger.error(f"Erro ao processar download do YouTube: {e}")
                        send_telegram(f"❌ Erro ao processar o vídeo do YouTube: {str(e)}", chat_id, use_keyboard=True)
                    continue

                magnet_regex = r'magnet:\?xt=urn:btih:[0-9a-fA-F]{40}.*'
                magnets = re.findall(magnet_regex, text, re.IGNORECASE)
                for magnet in magnets:
                    if not is_authorized:
                        send_telegram("❌ Você não tem permissão para adicionar torrents.", chat_id)
                        continue
                    try:
                        send_telegram("⏳ Adicionando torrent, aguarde...", chat_id)
                        
                        if multi_instance_manager:
                            from src.commands.multi_instance_commands import handle_add_magnet_multi
                            handle_add_magnet_multi(magnet, chat_id)
                        else:
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

        return new_last_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição para a API do Telegram: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado em process_messages: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return last_update_id
    except Exception as e:
        logger.error(f"Erro inesperado em process_messages: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return last_update_id
