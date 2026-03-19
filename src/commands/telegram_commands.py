import logging
from typing import Optional
from src.integrations.telegram.client import send_telegram

logger = logging.getLogger(__name__)


def handle_stats_command(stats_manager, chat_id: int, hours: int = 24):
    try:
        if not stats_manager:
            send_telegram("❌ Sistema de estatísticas não disponível.", chat_id, use_keyboard=True)
            return
        stats_text = stats_manager.format_bandwidth_stats(hours)
        send_telegram(stats_text, chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /stats: {e}")
        send_telegram(f"❌ Erro ao obter estatísticas: {str(e)}", chat_id, use_keyboard=True)


def handle_history_command(stats_manager, chat_id: int, days: int = 7):
    try:
        if not stats_manager:
            send_telegram("❌ Sistema de estatísticas não disponível.", chat_id, use_keyboard=True)
            return
        history_text = stats_manager.format_download_history(days)
        send_telegram(history_text, chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /history: {e}")
        send_telegram(f"❌ Erro ao obter histórico: {str(e)}", chat_id, use_keyboard=True)


def handle_graph_command(stats_manager, chat_id: int, hours: int = 24):
    try:
        if not stats_manager:
            send_telegram("❌ Sistema de estatísticas não disponível.", chat_id, use_keyboard=True)
            return
        graph_text = stats_manager.format_activity_graph(hours)
        send_telegram(graph_text, chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /graph: {e}")
        send_telegram(f"❌ Erro ao gerar gráfico: {str(e)}", chat_id, use_keyboard=True)


def handle_sync_command(sync_manager, chat_id: int):
    try:
        if not sync_manager:
            send_telegram("❌ Sistema de sincronização não disponível.", chat_id, use_keyboard=True)
            return
        result = sync_manager.manual_sync()
        send_telegram(result, chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /sync: {e}")
        send_telegram(f"❌ Erro na sincronização: {str(e)}", chat_id, use_keyboard=True)


def handle_sync_status_command(sync_manager, chat_id: int):
    try:
        if not sync_manager:
            send_telegram("❌ Sistema de sincronização não disponível.", chat_id, use_keyboard=True)
            return
        status = sync_manager.get_sync_status()
        status_text = f"""🔄 <b>Status da Sincronização</b>

▶️ <b>Estado:</b> {'Ativo' if status['running'] else 'Inativo'}
✅ <b>Torrents Concluídos:</b> {status['completed_count']}
📋 <b>Fila de Processamento:</b> {status['queue_size']}
🔁 <b>Auto-Scan:</b> {'Habilitado' if status['auto_scan_enabled'] else 'Desabilitado'}
⏱️ <b>Intervalo:</b> {status['sync_interval']}s"""
        send_telegram(status_text, chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /sync_status: {e}")
        send_telegram(f"❌ Erro ao obter status: {str(e)}", chat_id, use_keyboard=True)


def handle_priority_command(sess, qb_url: str, chat_id: int, torrent_hash: str = None, priority: str = None):
    try:
        if not sess:
            send_telegram("❌ Não conectado ao qBittorrent.", chat_id, use_keyboard=True)
            return
        if not torrent_hash or not priority:
            help_text = """⚡ <b>Gerenciamento de Prioridade</b>

<b>Como usar:</b>
<code>/priority [hash] [prioridade]</code>

<b>Prioridades disponíveis:</b>
• <code>top</code> - Move para o topo da fila
• <code>bottom</code> - Move para o final da fila
• <code>increase</code> - Aumenta a prioridade
• <code>decrease</code> - Diminui a prioridade

<b>Exemplo:</b>
<code>/priority abc123def456 top</code>

💡 <b>Dica:</b> Use /qtorrents para ver os hashes dos torrents"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return

        from src.integrations.qbittorrent.client import set_torrent_priority, get_torrent_info
        torrent_info = get_torrent_info(sess, qb_url, torrent_hash)
        if not torrent_info:
            send_telegram(f"❌ Torrent não encontrado: {torrent_hash[:8]}...", chat_id, use_keyboard=True)
            return

        success = set_torrent_priority(sess, qb_url, torrent_hash, priority)
        if success:
            name = torrent_info.get('name', 'Desconhecido')[:50]
            send_telegram(
                f"✅ <b>Prioridade alterada!</b>\n\n📦 {name}\n⚡ Nova prioridade: <code>{priority}</code>",
                chat_id, parse_mode="HTML", use_keyboard=True,
            )
        else:
            send_telegram("❌ Falha ao alterar prioridade.", chat_id, use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /priority: {e}")
        send_telegram(f"❌ Erro ao alterar prioridade: {str(e)}", chat_id, use_keyboard=True)


def handle_remove_command(sess, qb_url: str, chat_id: int, torrent_hash: str = None, delete_files: bool = False):
    try:
        if not sess:
            send_telegram("❌ Não conectado ao qBittorrent.", chat_id, use_keyboard=True)
            return
        if not torrent_hash:
            help_text = """🗑️ <b>Remover Torrents</b>

<b>Como usar:</b>
<code>/remove [hash]</code> - Remove apenas o torrent
<code>/remove [hash] delete</code> - Remove torrent e arquivos

<b>Exemplo:</b>
<code>/remove abc123def456</code>
<code>/remove abc123def456 delete</code>

⚠️ <b>Atenção:</b> A remoção de arquivos é permanente!

💡 <b>Dica:</b> Use /qtorrents para ver os hashes dos torrents"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return

        from src.integrations.qbittorrent.client import delete_torrent, get_torrent_info
        torrent_info = get_torrent_info(sess, qb_url, torrent_hash)
        if not torrent_info:
            send_telegram(f"❌ Torrent não encontrado: {torrent_hash[:8]}...", chat_id, use_keyboard=True)
            return

        name = torrent_info.get('name', 'Desconhecido')[:50]
        success = delete_torrent(sess, qb_url, torrent_hash, delete_files)
        if success:
            action = "removido (arquivos deletados)" if delete_files else "removido (arquivos mantidos)"
            send_telegram(
                f"✅ <b>Torrent {action}!</b>\n\n📦 {name}",
                chat_id, parse_mode="HTML", use_keyboard=True,
            )
        else:
            send_telegram("❌ Falha ao remover torrent.", chat_id, use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /remove: {e}")
        send_telegram(f"❌ Erro ao remover torrent: {str(e)}", chat_id, use_keyboard=True)
