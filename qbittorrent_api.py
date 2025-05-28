import requests
import re
from urllib.parse import urlparse, parse_qs

import logging

logger = logging.getLogger(__name__)

def login_qb(qb_url, qb_user, qb_pass):
    sess = requests.Session()
    data = {"username": qb_user, "password": qb_pass}
    try:
        resp = sess.post(f"{qb_url}/api/v2/auth/login", data=data)
        resp.raise_for_status()
        if resp.text != "Ok.":
            logger.error("Falha no login do qBittorrent")
            raise Exception("Falha no login do qBittorrent")
        return sess
    except Exception as e:
        logger.error(f"Erro ao autenticar no qBittorrent: {e}")
        raise
def fetch_torrents(sess, qb_url):
    resp = sess.get(f"{qb_url}/api/v2/torrents/info")
    resp.raise_for_status()
    return resp.json()

def resumo_torrents(torrents):
    lines = []
    for t in torrents:
        name = t["name"][:50]
        status = t["state"]
        prog = round(t["progress"] * 100, 1)
        dl = round(t["dlspeed"] / 1024, 1)
        up = round(t["upspeed"] / 1024, 1)
        lines.append(f"<b>{name}</b> — {status}, {prog}% ↓{dl}KB/s ↑{up}KB/s")
    return "\n".join(lines) or "Nenhum torrent ativo."

def add_magnet(sess, qb_url, magnet_url):
    data = {"urls": magnet_url}
    resp = sess.post(f"{qb_url}/api/v2/torrents/add", data=data)
    resp.raise_for_status()
    return resp

def get_disk_space_info(sess, qb_url):
    """
    Obtém informações de espaço em disco do servidor qBittorrent.
    """
    try:
        resp = sess.get(f"{qb_url}/api/v2/transfer/info")
        resp.raise_for_status()
        info = resp.json()
        free_space = info.get("free_space_on_disk", 0)
        total_space = info.get("total_disk_space", 0)
        used_space = total_space - free_space
        def format_bytes(size):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} PB"
        return (
            f"💾 <b>Espaço em disco:</b>\n"
            f"Total: {format_bytes(total_space)}\n"
            f"Usado: {format_bytes(used_space)}\n"
            f"Disponível: {format_bytes(free_space)}"
        )
    except Exception as e:
        return f"❌ Erro ao obter espaço em disco: {e}"