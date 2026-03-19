import requests
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


def login_qb(qb_url: str, qb_user: str, qb_pass: str) -> Optional[requests.Session]:
    session = requests.Session()
    try:
        resp = session.post(
            f"{qb_url}/api/v2/auth/login",
            data={"username": qb_user, "password": qb_pass},
            timeout=10,
        )
        resp.raise_for_status()
        if resp.text == "Ok.":
            logger.info("Login no qBittorrent realizado com sucesso.")
            return session
        logger.error(f"Falha no login no qBittorrent: {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Erro ao conectar ao qBittorrent: {e}")
        return None


def fetch_torrents(sess: requests.Session, qb_url: str) -> List[Dict]:
    try:
        resp = sess.get(f"{qb_url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao buscar torrents: {e}")
        return []


def summarize_torrents(torrents: List[Dict]) -> str:
    if not torrents:
        return "Nenhum torrent encontrado."
    lines = []
    for t in torrents:
        name = t.get("name", "Sem nome")
        progress = t.get("progress", 0) * 100
        state = t.get("state", "unknown")
        size = format_bytes(t.get("size", 0))
        lines.append(f"• {name} | {progress:.1f}% | {state} | {size}")
    return "\n".join(lines)


def add_magnet(sess: requests.Session, qb_url: str, magnet: str) -> bool:
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/add",
            data={"urls": magnet},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Magnet adicionado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar magnet: {e}")
        return False


def pause_torrent(sess: requests.Session, qb_url: str, torrent_hash: str) -> bool:
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/pause",
            data={"hashes": torrent_hash},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao pausar torrent {torrent_hash}: {e}")
        return False


def resume_torrent(sess: requests.Session, qb_url: str, torrent_hash: str) -> bool:
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/resume",
            data={"hashes": torrent_hash},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao retomar torrent {torrent_hash}: {e}")
        return False


def delete_torrent(sess: requests.Session, qb_url: str, torrent_hash: str, delete_files: bool = False) -> bool:
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/delete",
            data={"hashes": torrent_hash, "deleteFiles": str(delete_files).lower()},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao deletar torrent {torrent_hash}: {e}")
        return False


def set_torrent_priority(sess: requests.Session, qb_url: str, torrent_hash: str, priority: str) -> bool:
    priority_map = {
        "top": "topPrio",
        "bottom": "bottomPrio",
        "increase": "increasePrio",
        "decrease": "decreasePrio",
    }
    endpoint = priority_map.get(priority)
    if not endpoint:
        logger.error(f"Prioridade inválida: {priority}")
        return False
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/{endpoint}",
            data={"hashes": torrent_hash},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao definir prioridade do torrent {torrent_hash}: {e}")
        return False


def set_torrent_location(sess: requests.Session, qb_url: str, torrent_hash: str, location: str) -> bool:
    try:
        resp = sess.post(
            f"{qb_url}/api/v2/torrents/setLocation",
            data={"hashes": torrent_hash, "location": location},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao definir localização do torrent {torrent_hash}: {e}")
        return False


def get_torrent_info(sess: requests.Session, qb_url: str, torrent_hash: str) -> Optional[Dict]:
    try:
        resp = sess.get(
            f"{qb_url}/api/v2/torrents/info",
            params={"hashes": torrent_hash},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        return results[0] if results else None
    except Exception as e:
        logger.error(f"Erro ao obter informações do torrent {torrent_hash}: {e}")
        return None


def get_transfer_info(sess: requests.Session, qb_url: str) -> Optional[Dict]:
    try:
        resp = sess.get(f"{qb_url}/api/v2/transfer/info", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao obter informações de transferência: {e}")
        return None


def format_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
