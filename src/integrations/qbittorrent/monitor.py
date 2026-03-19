import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def monitor_torrents(
    sess,
    qb_url: str,
    send_notification: Callable[[str], None],
    interval: int = 30,
    send_status: Optional[Callable[[], None]] = None,
    status_interval: int = 3600,
) -> None:
    from src.integrations.qbittorrent.client import fetch_torrents

    known_completed = set()
    last_status_time = 0

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
