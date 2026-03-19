import logging
import re
from datetime import datetime
from typing import Optional, Union
from src.integrations.telegram.client import send_telegram

logger = logging.getLogger(__name__)


def format_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_recent_items_detailed(jellyfin_manager, limit: int = 10) -> str:
    if not jellyfin_manager or not jellyfin_manager.is_available():
        return "❌ Jellyfin não configurado ou indisponível."
    try:
        items = jellyfin_manager.client.get_recently_added(limit)
        if not items:
            return "📥 Nenhum item recente encontrado."

        messages = ["🎬 **Itens recentemente adicionados (detalhado):**\n"]
        for i, item in enumerate(items, 1):
            name = item.get('Name', 'Sem título')
            item_type = item.get('Type', 'Desconhecido')
            year = item.get('ProductionYear', '')
            genres = item.get('Genres', [])
            genres_text = ', '.join(genres[:3]) if genres else 'N/A'
            rating = item.get('CommunityRating')
            rating_text = f"⭐ {rating:.1f}" if rating else "⭐ N/A"
            date_created = item.get('DateCreated', '')
            date_text = 'N/A'
            if date_created:
                try:
                    date_obj = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                    date_text = date_obj.strftime('%d/%m/%Y')
                except Exception:
                    pass
            overview = item.get('Overview', '')
            if overview and len(overview) > 150:
                overview = overview[:150] + "..."
            web_link = jellyfin_manager.client.get_web_link(item['Id'])
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
    try:
        if sess is None:
            return "❌ Não conectado ao qBittorrent."
        prefs_resp = sess.get(f"{qb_url}/api/v2/app/preferences")
        prefs_resp.raise_for_status()
        prefs_data = prefs_resp.json()
        save_path = prefs_data.get('save_path')
        if not save_path:
            return "❌ Caminho de salvamento do qBittorrent não encontrado."
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
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                try:
                    maindata_resp = sess.get(f"{qb_url}/api/v2/sync/maindata", params={"rid": 0})
                    maindata_resp.raise_for_status()
                    maindata = maindata_resp.json()
                    server_state = maindata.get('server_state', {})
                    free = server_state.get('free_space_on_disk')
                    if free is not None:
                        import os
                        import shutil
                        if save_path and os.path.exists(save_path):
                            try:
                                disk_usage = shutil.disk_usage(save_path)
                                total = disk_usage.total
                                used = total - free
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


def list_torrents(sess, qb_url: str, chat_id: Optional[Union[str, int]] = None) -> bool:
    try:
        if sess is None:
            send_telegram("❌ Não conectado ao qBittorrent.", chat_id, use_keyboard=True)
            return False
        from src.integrations.qbittorrent.client import fetch_torrents, format_bytes as fb
        torrents = fetch_torrents(sess, qb_url)
        if not torrents:
            send_telegram("📭 Nenhum torrent encontrado.", chat_id, use_keyboard=True)
            return True

        ativos, pausados, finalizados, parados = [], [], [], []
        MAX_NAME_LENGTH = 50

        for t in torrents:
            estado = t.get('state', '')
            nome = t.get('name', 'Sem nome')
            progresso = t.get('progress', 0) * 100
            hash_torrent = t.get('hash', '')
            size = t.get('size', 0)
            dlspeed = t.get('dlspeed', 0)
            upspeed = t.get('upspeed', 0)
            nome_display = nome if len(nome) <= MAX_NAME_LENGTH else nome[:MAX_NAME_LENGTH] + "..."
            size_str = fb(size)
            speed_info = ""
            if dlspeed > 0:
                speed_info = f" ↓{fb(dlspeed)}/s"
            if upspeed > 0:
                speed_info += f" ↑{fb(upspeed)}/s"
            torrent_info = {
                'name': nome_display, 'hash': hash_torrent,
                'progress': progresso, 'size': size_str,
                'speed': speed_info, 'state': estado,
            }
            if estado in ['downloading', 'stalledDL', 'checkingDL', 'queuedDL', 'forcedDL', 'metaDL']:
                ativos.append(torrent_info)
            elif estado in ['pausedDL', 'pausedUP']:
                pausados.append(torrent_info)
            elif estado in ['uploading', 'seeding', 'stalledUP', 'checkingUP', 'forcedUP', 'queuedUP']:
                finalizados.append(torrent_info)
            elif estado in ['error', 'missingFiles', 'unknown']:
                parados.append(torrent_info)

        total = len(torrents)
        msg_parts = ["<b>📊 GERENCIADOR DE TORRENTS</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                     f"<b>Total:</b> {total} torrent(s)",
                     f"<b>Ativos:</b> {len(ativos)} | <b>Pausados:</b> {len(pausados)} | <b>Finalizados:</b> {len(finalizados)}"]
        if parados:
            msg_parts.append(f"<b>Com Erro:</b> {len(parados)}")
        msg_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        def fmt_line(t_info, show_progress=False):
            line = f"<b>•</b> {t_info['name']}"
            if show_progress:
                line += f"\n   📊 {t_info['progress']:.1f}% | 💾 {t_info['size']}"
                if t_info['speed']:
                    line += f" | {t_info['speed']}"
            else:
                line += f"\n   💾 {t_info['size']}"
            return line

        if ativos:
            msg_parts.append(f"\n<b>📥 DOWNLOADS ATIVOS ({len(ativos)})</b>")
            msg_parts.append("─────────────────────────────")
            for t in ativos[:5]:
                msg_parts.append(fmt_line(t, show_progress=True))
            if len(ativos) > 5:
                msg_parts.append(f"\n<i>... e mais {len(ativos) - 5} torrent(s)</i>")
        if pausados:
            msg_parts.append(f"\n<b>⏸️ PAUSADOS ({len(pausados)})</b>")
            msg_parts.append("─────────────────────────────")
            for t in pausados[:3]:
                msg_parts.append(fmt_line(t))
            if len(pausados) > 3:
                msg_parts.append(f"\n<i>... e mais {len(pausados) - 3} torrent(s)</i>")
        if finalizados:
            msg_parts.append(f"\n<b>✅ FINALIZADOS/SEEDING ({len(finalizados)})</b>")
            msg_parts.append("─────────────────────────────")
            for t in finalizados[:3]:
                msg_parts.append(fmt_line(t))
            if len(finalizados) > 3:
                msg_parts.append(f"\n<i>... e mais {len(finalizados) - 3} torrent(s)</i>")
        if parados:
            msg_parts.append(f"\n<b>❌ COM ERRO ({len(parados)})</b>")
            msg_parts.append("─────────────────────────────")
            for t in parados:
                msg_parts.append(f"<b>•</b> {t['name']}\n   ⚠️ Estado: {t['state']}")
        msg_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        msg_parts.append("<i>💡 Use os botões abaixo para gerenciar torrents</i>")

        inline_keyboard = {
            'inline_keyboard': [
                [
                    {'text': '🔄 Atualizar Lista', 'callback_data': 'torrent_refresh'},
                    {'text': '⏸️ Pausar Todos', 'callback_data': 'torrent_pause_all'},
                ],
                [
                    {'text': '▶️ Retomar Todos', 'callback_data': 'torrent_resume_all'},
                    {'text': '📋 Detalhes', 'callback_data': 'torrent_details'},
                ],
            ]
        }
        message = "\n".join(msg_parts)
        return send_telegram(message, chat_id, parse_mode="HTML", reply_markup=inline_keyboard)
    except Exception as e:
        logger.error(f"Erro ao listar torrents: {e}")
        send_telegram(f"❌ Erro ao listar torrents: {str(e)}", chat_id, use_keyboard=True)
        return False


def handle_pause_all_torrents(sess, qb_url: str, chat_id: int) -> None:
    try:
        if sess is None:
            send_telegram("❌ Não conectado ao qBittorrent.", chat_id, use_keyboard=True)
            return
        from src.integrations.qbittorrent.client import fetch_torrents
        torrents = fetch_torrents(sess, qb_url)
        if not torrents:
            send_telegram("📭 Nenhum torrent encontrado.", chat_id, use_keyboard=True)
            return
        resp = sess.post(f"{qb_url}/api/v2/torrents/pause", data={"hashes": "all"})
        resp.raise_for_status()
        send_telegram(f"⏸️ Todos os torrents foram pausados ({len(torrents)} torrent(s)).", chat_id, use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao pausar todos os torrents: {e}")
        send_telegram(f"❌ Erro ao pausar torrents: {str(e)}", chat_id, use_keyboard=True)


def handle_resume_all_torrents(sess, qb_url: str, chat_id: int) -> None:
    try:
        if sess is None:
            send_telegram("❌ Não conectado ao qBittorrent.", chat_id, use_keyboard=True)
            return
        from src.integrations.qbittorrent.client import fetch_torrents
        torrents = fetch_torrents(sess, qb_url)
        if not torrents:
            send_telegram("📭 Nenhum torrent encontrado.", chat_id, use_keyboard=True)
            return
        resp = sess.post(f"{qb_url}/api/v2/torrents/resume", data={"hashes": "all"})
        resp.raise_for_status()
        send_telegram(f"▶️ Todos os torrents foram retomados ({len(torrents)} torrent(s)).", chat_id, use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao retomar todos os torrents: {e}")
        send_telegram(f"❌ Erro ao retomar torrents: {str(e)}", chat_id, use_keyboard=True)
