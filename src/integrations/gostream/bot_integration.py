"""
Integração do GoStream com o Bot Telegram

Permite adicionar e gerenciar torrents via GoStream
diretamente através dos comandos do bot.
"""

import os
import logging
from typing import Optional, List

from src.core.config import (
    GOSTREAM_ENABLED, GOSTREAM_MOUNT_PATH, GOSTREAM_CACHE_DIR,
    GOSTREAM_STATE_DIR, GOSTREAM_PORT_START, GOSTREAM_PORT_END,
    GOSTREAM_MAX_CONNECTIONS, GOSTREAM_READ_AHEAD_MB,
    GOSTREAM_CACHE_SHARDS, GOSTREAM_API_ENABLED, GOSTREAM_API_HOST,
    GOSTREAM_API_PORT, GOSTREAM_ENABLE_DHT, GOSTREAM_ENABLE_LSD,
    GOSTREAM_RESPONSIVE_MODE
)

logger = logging.getLogger(__name__)


class GoStreamIntegration:
    """Integração do GoStream com o bot Telegram"""
    
    def __init__(self):
        """Inicializa integração"""
        self.enabled = GOSTREAM_ENABLED
        self.manager = None
        self._initialized = False
        
        if self.enabled:
            try:
                from src.integrations.gostream import GoStreamManager, GoStreamConfig
                
                # Cria configuração a partir das variáveis de ambiente
                config = GoStreamConfig(
                    fuse_mount_path=GOSTREAM_MOUNT_PATH,
                    cache_dir=GOSTREAM_CACHE_DIR,
                    state_dir=GOSTREAM_STATE_DIR,
                    listen_port_start=GOSTREAM_PORT_START,
                    listen_port_end=GOSTREAM_PORT_END,
                    max_connections_per_torrent=GOSTREAM_MAX_CONNECTIONS,
                    read_ahead_budget_mb=GOSTREAM_READ_AHEAD_MB,
                    num_cache_shards=GOSTREAM_CACHE_SHARDS,
                    api_enabled=GOSTREAM_API_ENABLED,
                    api_host=GOSTREAM_API_HOST,
                    api_port=GOSTREAM_API_PORT,
                    enable_dht=GOSTREAM_ENABLE_DHT,
                    enable_lsd=GOSTREAM_ENABLE_LSD,
                    responsive_mode=GOSTREAM_RESPONSIVE_MODE,
                )
                
                self.manager = GoStreamManager(config)
                logger.info("GoStream Integration criada")
                
            except ImportError as e:
                logger.error(f"GoStream não disponível: {e}")
                self.enabled = False
            except Exception as e:
                logger.error(f"Erro ao inicializar GoStream: {e}")
                self.enabled = False
    
    def initialize(self) -> bool:
        """Inicializa GoStream manager"""
        if not self.enabled or not self.manager:
            return False
        
        try:
            success = self.manager.initialize()
            if success:
                self._initialized = True
                logger.info("GoStream inicializado com sucesso")
            return success
        except Exception as e:
            logger.error(f"Erro ao inicializar GoStream: {e}")
            return False
    
    def start(self) -> bool:
        """Inicia serviços GoStream"""
        if not self._initialized or not self.manager:
            return False
        
        try:
            success = self.manager.start()
            if success:
                logger.info("GoStream services iniciados")
            return success
        except Exception as e:
            logger.error(f"Erro ao iniciar GoStream services: {e}")
            return False
    
    def stop(self):
        """Para GoStream"""
        if self.manager:
            self.manager.stop()
            logger.info("GoStream parado")
    
    def add_magnet(self, magnet_link: str, save_path: Optional[str] = None) -> Optional[str]:
        """
        Adiciona torrent via magnet link
        
        Returns:
            info_hash do torrent ou None
        """
        if not self.manager:
            return None
        
        return self.manager.add_torrent(magnet_link, save_path)
    
    def add_torrent_file(self, torrent_path: str, save_path: Optional[str] = None) -> Optional[str]:
        """
        Adiciona torrent via arquivo .torrent
        
        Returns:
            info_hash do torrent ou None
        """
        if not self.manager or not self.manager.bt_engine:
            return None
        
        return self.manager.bt_engine.add_torrent_file(torrent_path, save_path)
    
    def remove_torrent(self, info_hash: str, delete_files: bool = False) -> bool:
        """Remove torrent"""
        if not self.manager:
            return False
        
        return self.manager.remove_torrent(info_hash, delete_files)
    
    def list_torrents(self) -> List[dict]:
        """Lista torrents ativos"""
        if not self.manager or not self.manager.bt_engine:
            return []
        
        torrents = self.manager.bt_engine.list_torrents()
        return [
            {
                'info_hash': t.info_hash,
                'name': t.name,
                'progress': t.progress,
                'state': t.state.value,
                'download_rate': t.download_rate,
                'upload_rate': t.upload_rate,
                'num_peers': t.num_peers,
                'num_seeds': t.num_seeds,
            }
            for t in torrents
        ]
    
    def get_torrent_info(self, info_hash: str) -> Optional[dict]:
        """Obtém informações de um torrent"""
        if not self.manager or not self.manager.bt_engine:
            return None
        
        info = self.manager.bt_engine.get_torrent_info(info_hash)
        if not info:
            return None
        
        return {
            'info_hash': info.info_hash,
            'name': info.name,
            'total_size': info.total_size,
            'progress': info.progress,
            'state': info.state.value,
            'download_rate': info.download_rate,
            'upload_rate': info.upload_rate,
            'num_peers': info.num_peers,
            'files': info.files,
        }
    
    def set_priority_mode(self, info_hash: str, enabled: bool = True):
        """Ativa/desativa modo prioridade"""
        if not self.manager or not self.manager.bt_engine:
            return
        
        self.manager.bt_engine.set_priority_mode(info_hash, enabled)
    
    def get_status(self) -> dict:
        """Retorna status do GoStream"""
        if not self.manager:
            return {'enabled': False}
        
        return {
            'enabled': self.enabled,
            'initialized': self._initialized,
            **self.manager.get_status()
        }
    
    def get_mount_path(self) -> str:
        """Retorna caminho de montagem FUSE"""
        return GOSTREAM_MOUNT_PATH
    
    def is_available(self) -> bool:
        """Verifica se GoStream está disponível"""
        return self.enabled and self._initialized and self.manager is not None


# Instância global
gostream_integration = GoStreamIntegration()


def get_gostream() -> GoStreamIntegration:
    """Retorna instância do GoStream Integration"""
    return gostream_integration
