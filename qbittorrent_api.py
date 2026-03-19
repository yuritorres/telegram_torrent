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
import time
from requests.exceptions import HTTPError

def fetch_torrents(sess, qb_url, retries: int = 3, wait_seconds: int = 30):
    """Obtém a lista de torrents do qBittorrent.

    Se ocorrer erro 403 (Forbidden), aguarda *wait_seconds* e tenta novamente
    até *retries* vezes.
    """
    attempt = 0
    while True:
        try:
            resp = sess.get(f"{qb_url}/api/v2/torrents/info")
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 403 and attempt < retries:
                attempt += 1
                logger.warning(
                    f"❗️ Erro 403 ao acessar /torrents/info. Tentativa {attempt}/{retries} em {wait_seconds}s."
                )
                time.sleep(wait_seconds)
                continue
            raise

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

def format_bytes(size: int) -> str:
    """Formata um tamanho em bytes para uma string legível."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def get_transfer_info(sess, qb_url):
    """Obtém informações de transferência do qBittorrent."""
    try:
        resp = sess.get(f"{qb_url}/api/v2/transfer/info")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao obter informações de transferência: {e}")
        return None

def pause_torrent(sess, qb_url, torrent_hash):
    """Pausa um torrent específico.
    
    Args:
        sess: Sessão autenticada do qBittorrent
        qb_url: URL base da API do qBittorrent
        torrent_hash: Hash do torrent a ser pausado
        
    Returns:
        bool: True se pausado com sucesso, False caso contrário
    """
    try:
        data = {"hashes": torrent_hash}
        resp = sess.post(f"{qb_url}/api/v2/torrents/pause", data=data)
        resp.raise_for_status()
        logger.info(f"Torrent {torrent_hash} pausado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao pausar torrent {torrent_hash}: {e}")
        return False

def resume_torrent(sess, qb_url, torrent_hash):
    """Retoma um torrent pausado.
    
    Args:
        sess: Sessão autenticada do qBittorrent
        qb_url: URL base da API do qBittorrent
        torrent_hash: Hash do torrent a ser retomado
        
    Returns:
        bool: True se retomado com sucesso, False caso contrário
    """
    try:
        data = {"hashes": torrent_hash}
        resp = sess.post(f"{qb_url}/api/v2/torrents/resume", data=data)
        resp.raise_for_status()
        logger.info(f"Torrent {torrent_hash} retomado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao retomar torrent {torrent_hash}: {e}")
        return False

def delete_torrent(sess, qb_url, torrent_hash, delete_files=False):
    """Remove um torrent.
    
    Args:
        sess: Sessão autenticada do qBittorrent
        qb_url: URL base da API do qBittorrent
        torrent_hash: Hash do torrent a ser removido
        delete_files: Se True, remove também os arquivos baixados
        
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    try:
        data = {
            "hashes": torrent_hash,
            "deleteFiles": "true" if delete_files else "false"
        }
        resp = sess.post(f"{qb_url}/api/v2/torrents/delete", data=data)
        resp.raise_for_status()
        logger.info(f"Torrent {torrent_hash} removido com sucesso (arquivos deletados: {delete_files})")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover torrent {torrent_hash}: {e}")
        return False

def get_torrent_info(sess, qb_url, torrent_hash):
    """Obtém informações detalhadas de um torrent específico.
    
    Args:
        sess: Sessão autenticada do qBittorrent
        qb_url: URL base da API do qBittorrent
        torrent_hash: Hash do torrent
        
    Returns:
        dict: Informações do torrent ou None em caso de erro
    """
    try:
        resp = sess.get(f"{qb_url}/api/v2/torrents/info", params={"hashes": torrent_hash})
        resp.raise_for_status()
        torrents = resp.json()
        return torrents[0] if torrents else None
    except Exception as e:
        logger.error(f"Erro ao obter informações do torrent {torrent_hash}: {e}")
        return None