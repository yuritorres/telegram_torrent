import time
import logging
import json
import os
from typing import Callable, Optional, Set

logger = logging.getLogger(__name__)


def _load_completed_state(state_file: str = "torrent_monitor_state.json") -> Set[str]:
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                known = set(state.get('known_completed', []))
                logger.info(f"Estado carregado: {len(known)} torrents conhecidos")
                return known
    except Exception as e:
        logger.error(f"Erro ao carregar estado dos torrents: {e}")
    return set()


def _save_completed_state(known_completed: Set[str], state_file: str = "torrent_monitor_state.json"):
    try:
        state = {'known_completed': list(known_completed)}
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar estado dos torrents: {e}")


def monitor_torrents(
    sess,
    qb_url: str,
    send_notification: Callable[[str], None],
    interval: int = 30,
    send_status: Optional[Callable[[], None]] = None,
    status_interval: int = 3600,
) -> None:
    from src.integrations.qbittorrent.client import fetch_torrents

    known_completed = _load_completed_state()
    last_status_time = 0
    
    if not known_completed:
        logger.info("Primeira execução: populando torrents conhecidos...")
        try:
            torrents = fetch_torrents(sess, qb_url)
            for t in torrents:
                state = t.get("state", "")
                if state in ("uploading", "seeding", "stalledUP", "forcedUP"):
                    known_completed.add(t.get("hash", ""))
            _save_completed_state(known_completed)
            logger.info(f"Torrents conhecidos inicializados: {len(known_completed)}")
        except Exception as e:
            logger.error(f"Erro ao inicializar torrents conhecidos: {e}")

    logger.info("Monitor de torrents iniciado.")

    while True:
        try:
            torrents = fetch_torrents(sess, qb_url)
            for t in torrents:
                torrent_hash = t.get("hash", "")
                state = t.get("state", "")
                name = t.get("name", "Sem nome")

                if state in ("uploading", "seeding", "stalledUP", "forcedUP") and torrent_hash not in known_completed:
                    known_completed.add(torrent_hash)
                    _save_completed_state(known_completed)
                    msg = f"✅ <b>Download concluído:</b> {name}"
                    send_notification(msg)
                    logger.info(f"Torrent concluído: {name}")

            if send_status:
                current_time = time.time()
                if current_time - last_status_time >= status_interval:
                    send_status()
                    last_status_time = current_time

        except Exception as e:
            logger.error(f"Erro no monitor de torrents: {e}")

        time.sleep(interval)
