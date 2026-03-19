import os
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SyncManager:
    """Gerenciador de sincronização entre qBittorrent e Jellyfin"""

    def __init__(self, qb_session, qb_url: str, jellyfin_manager, notification_callback=None):
        self.qb_session = qb_session
        self.qb_url = qb_url
        self.jellyfin_manager = jellyfin_manager
        self.notification_callback = notification_callback

        self.completed_torrents: Set[str] = set()
        self.processing_queue: List[Dict] = []
        self.sync_interval = int(os.getenv('SYNC_INTERVAL', 30))
        self.auto_scan_enabled = os.getenv('AUTO_SCAN_JELLYFIN', 'True').lower() in ('true', '1', 't')
        self.running = False
        self.thread = None

        logger.info(f"SyncManager inicializado (intervalo: {self.sync_interval}s, auto-scan: {self.auto_scan_enabled})")

    def start(self):
        if self.running:
            logger.warning("SyncManager já está em execução")
            return
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        logger.info("SyncManager iniciado")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("SyncManager parado")

    def _sync_loop(self):
        from src.integrations.qbittorrent.client import fetch_torrents

        previous_state: Dict[str, Dict] = {}

        while self.running:
            try:
                current_torrents = fetch_torrents(self.qb_session, self.qb_url)

                for torrent in current_torrents:
                    torrent_hash = torrent['hash']
                    current_state = torrent['state']
                    name = torrent['name']
                    save_path = torrent.get('save_path', '')

                    download_states = ['downloading', 'stalledDL', 'checkingDL', 'pausedDL', 'queuedDL', 'forcedDL', 'metaDL']
                    completion_states = ['uploading', 'seeding', 'finished', 'stalledUP', 'checkingUP', 'forcedUP', 'pausedUP']

                    if torrent_hash in previous_state:
                        prev_state = previous_state[torrent_hash]['state']
                        if prev_state in download_states and current_state in completion_states:
                            if torrent_hash not in self.completed_torrents:
                                self._handle_completed_torrent(torrent_hash, name, save_path)
                                self.completed_torrents.add(torrent_hash)

                    previous_state[torrent_hash] = {
                        'state': current_state,
                        'name': name,
                        'save_path': save_path,
                    }

                self._process_queue()
                time.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Erro no loop de sincronização: {e}")
                time.sleep(10)

    def _handle_completed_torrent(self, torrent_hash: str, name: str, save_path: str):
        logger.info(f"Torrent concluído detectado: {name}")
        if self.notification_callback:
            self.notification_callback(f"✅ <b>Download Concluído:</b>\n{name}")
        if self.auto_scan_enabled and self.jellyfin_manager and self.jellyfin_manager.is_available():
            self.processing_queue.append({
                'hash': torrent_hash,
                'name': name,
                'save_path': save_path,
                'timestamp': datetime.now(),
                'scan_attempted': False,
            })
            logger.info(f"Torrent adicionado à fila de processamento: {name}")

    def _process_queue(self):
        if not self.processing_queue:
            return
        for item in self.processing_queue[:]:
            if not item['scan_attempted']:
                success = self._trigger_jellyfin_scan(item['name'], item['save_path'])
                item['scan_attempted'] = True
                if success:
                    if self.notification_callback:
                        self.notification_callback(
                            f"📚 <b>Biblioteca Atualizada:</b>\n{item['name']}\n\n"
                            f"O conteúdo estará disponível no Jellyfin em breve!"
                        )
                    self.processing_queue.remove(item)
                    logger.info(f"Item processado e removido da fila: {item['name']}")

    def _trigger_jellyfin_scan(self, name: str, save_path: str) -> bool:
        try:
            if not self.jellyfin_manager or not self.jellyfin_manager.is_available():
                logger.warning("Jellyfin não disponível para scan")
                return False
            result = self.jellyfin_manager.client._make_request('/Library/Refresh', method='POST')
            if result is not None:
                logger.info(f"Scan da biblioteca Jellyfin iniciado para: {name}")
                return True
            logger.error(f"Falha ao iniciar scan da biblioteca para: {name}")
            return False
        except Exception as e:
            logger.error(f"Erro ao disparar scan do Jellyfin: {e}")
            return False

    def get_sync_status(self) -> Dict:
        return {
            'running': self.running,
            'completed_count': len(self.completed_torrents),
            'queue_size': len(self.processing_queue),
            'auto_scan_enabled': self.auto_scan_enabled,
            'sync_interval': self.sync_interval,
        }

    def manual_sync(self, torrent_name: Optional[str] = None) -> str:
        try:
            if not self.jellyfin_manager or not self.jellyfin_manager.is_available():
                return "❌ Jellyfin não disponível"
            result = self.jellyfin_manager.client._make_request('/Library/Refresh', method='POST')
            if result is not None:
                msg = "✅ Sincronização manual iniciada"
                if torrent_name:
                    msg += f"\n📁 Torrent: {torrent_name}"
                logger.info(msg)
                return msg
            return "❌ Falha ao iniciar sincronização"
        except Exception as e:
            logger.error(f"Erro na sincronização manual: {e}")
            return f"❌ Erro: {str(e)}"
