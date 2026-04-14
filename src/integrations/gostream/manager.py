"""
GoStream Manager

Orquestra todos os componentes do GoStream:
- BTEngine: Engine BitTorrent
- ReadAheadCache: Cache de pré-leitura
- NativeBridge: Ponte zero-copy
- FUSEFilesystem: Filesystem virtual
- StreamingAPI: API REST
"""

import os
import time
import logging
import signal
import threading
from typing import Optional
from pathlib import Path

from .config import GoStreamConfig
from .bt_engine import BTEngine
from .read_ahead_cache import ReadAheadCache
from .native_bridge import NativeBridge
from .fuse_filesystem import FUSEManager
from .streaming_api import StreamingAPI

logger = logging.getLogger(__name__)


class GoStreamManager:
    """
    Gerenciador principal do GoStream.
    
    Similar ao main do GoStream, orquestra todos os componentes.
    """
    
    def __init__(self, config: Optional[GoStreamConfig] = None):
        """
        Inicializa o GoStream Manager
        
        Args:
            config: Configurações (usa padrão se None)
        """
        self.config = config or GoStreamConfig()
        
        # Componentes
        self.bt_engine: Optional[BTEngine] = None
        self.cache: Optional[ReadAheadCache] = None
        self.native_bridge: Optional[NativeBridge] = None
        self.fuse_manager: Optional[FUSEManager] = None
        self.api: Optional[StreamingAPI] = None
        
        # Estado
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Threads
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stats_thread: Optional[threading.Thread] = None
    
    def initialize(self) -> bool:
        """Inicializa todos os componentes"""
        try:
            logger.info("Inicializando GoStream...")
            
            # 1. Cria diretórios
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
            Path(self.config.state_dir).mkdir(parents=True, exist_ok=True)
            Path(self.config.fuse_mount_path).mkdir(parents=True, exist_ok=True)
            
            # 2. Inicializa Cache
            self.cache = ReadAheadCache(
                num_shards=self.config.num_cache_shards,
                total_budget_bytes=self.config.read_ahead_budget_bytes
            )
            
            # 3. Inicializa BitTorrent Engine
            self.bt_engine = BTEngine(self.config)
            if not self.bt_engine.start():
                logger.error("Falha ao iniciar BTEngine")
                return False
            
            # Conecta callbacks
            self.bt_engine.on_piece_finished(self._on_piece_finished)
            self.bt_engine.on_torrent_added(self._on_torrent_added)
            self.bt_engine.on_torrent_removed(self._on_torrent_removed)
            
            # 4. Inicializa Native Bridge
            self.native_bridge = NativeBridge(
                bt_engine=self.bt_engine,
                cache=self.cache,
                config=self.config
            )
            
            # 5. Inicializa Read-Ahead se há prefetch worker
            if self.bt_engine:
                self.cache.start_prefetch_worker(
                    lambda ih, pi: self.bt_engine.read_piece(ih, pi)
                )
            
            # 6. Inicializa FUSE (opcional)
            if os.name != 'nt':  # FUSE não disponível no Windows nativo
                try:
                    self.fuse_manager = FUSEManager(
                        bt_engine=self.bt_engine,
                        native_bridge=self.native_bridge,
                        cache=self.cache,
                        config=self.config
                    )
                except Exception as e:
                    logger.warning(f"FUSE não disponível: {e}")
                    self.fuse_manager = None
            else:
                logger.info("FUSE desabilitado no Windows")
                self.fuse_manager = None
            
            # 7. Inicializa API
            self.api = StreamingAPI(
                bt_engine=self.bt_engine,
                native_bridge=self.native_bridge,
                cache=self.cache,
                fuse_manager=self.fuse_manager,
                config=self.config
            )
            
            logger.info("GoStream inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar GoStream: {e}")
            return False
    
    def start(self) -> bool:
        """Inicia todos os serviços"""
        if not self.bt_engine:
            logger.error("GoStream não inicializado. Chame initialize() primeiro.")
            return False
        
        try:
            logger.info("Iniciando GoStream services...")
            
            # Inicia FUSE
            if self.fuse_manager:
                if not self.fuse_manager.start():
                    logger.warning("Falha ao iniciar FUSE, continuando sem filesystem virtual")
            
            # Inicia API
            if self.config.api_enabled and self.api:
                if not self.api.start():
                    logger.warning("Falha ao iniciar API REST")
            
            # Inicia threads de manutenção
            self._running = True
            self._shutdown_event.clear()
            
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self._cleanup_thread.start()
            
            self._stats_thread = threading.Thread(
                target=self._stats_loop,
                daemon=True
            )
            self._stats_thread.start()
            
            logger.info("GoStream iniciado e operacional")
            logger.info(f"  - API REST: http://{self.config.api_host}:{self.config.api_port}")
            if self.fuse_manager:
                logger.info(f"  - FUSE Mount: {self.config.fuse_mount_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar GoStream: {e}")
            return False
    
    def stop(self):
        """Para todos os serviços"""
        logger.info("Parando GoStream...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Para threads
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        if self._stats_thread:
            self._stats_thread.join(timeout=5)
        
        # Fecha todos os handles
        if self.native_bridge:
            self.native_bridge.close_all()
        
        # Para API
        if self.api:
            self.api.stop()
        
        # Para FUSE
        if self.fuse_manager:
            self.fuse_manager.stop()
        
        # Para Cache
        if self.cache:
            self.cache.stop()
        
        # Para BitTorrent
        if self.bt_engine:
            self.bt_engine.stop()
        
        logger.info("GoStream parado")
    
    def _cleanup_loop(self):
        """Loop de limpeza periódica"""
        while not self._shutdown_event.is_set():
            try:
                # Remove handles inativos
                if self.native_bridge:
                    handles = self.native_bridge.list_handles()
                    for h in handles:
                        # Fecha handles inativos por mais de 5 minutos
                        if time.time() - h.get('last_access', 0) > 300:
                            # Nota: handles não têm last_access diretamente,
                            # esta é uma simplificação
                            pass
                
                # Remove torrents expirados do cache
                if self.cache and self.bt_engine:
                    # Torrents que não foram acessados recentemente
                    pass  # Implementação futura
                
            except Exception as e:
                logger.error(f"Erro no cleanup loop: {e}")
            
            # Aguarda 30 segundos
            self._shutdown_event.wait(30)
    
    def _stats_loop(self):
        """Loop de estatísticas periódicas"""
        while not self._shutdown_event.is_set():
            try:
                if self.cache:
                    stats = self.cache.get_stats()
                    logger.debug(f"Cache stats: {stats['hit_rate']:.2%} hit rate, "
                               f"{stats['current_size'] / 1024 / 1024:.1f}MB / "
                               f"{stats['total_budget'] / 1024 / 1024:.1f}MB")
                
                if self.bt_engine:
                    session_stats = self.bt_engine.get_session_stats()
                    logger.debug(f"BT stats: {session_stats.get('download_rate', 0) / 1024:.1f}KB/s down, "
                               f"{session_stats.get('upload_rate', 0) / 1024:.1f}KB/s up, "
                               f"{session_stats.get('num_peers', 0)} peers")
                
            except Exception as e:
                logger.error(f"Erro no stats loop: {e}")
            
            # Aguarda 60 segundos
            self._shutdown_event.wait(60)
    
    def _on_piece_finished(self, info_hash: str, piece_index: int):
        """Callback quando uma peça é completada"""
        logger.debug(f"Peça {piece_index} completada para {info_hash[:8]}")
    
    def _on_torrent_added(self, info_hash: str):
        """Callback quando um torrent é adicionado"""
        logger.info(f"Torrent adicionado: {info_hash[:8]}")
        
        # Atualiza FUSE
        if self.fuse_manager:
            self.fuse_manager.refresh()
    
    def _on_torrent_removed(self, info_hash: str):
        """Callback quando um torrent é removido"""
        logger.info(f"Torrent removido: {info_hash[:8]}")
        
        # Remove do cache
        if self.cache:
            self.cache.remove_torrent(info_hash)
        
        # Atualiza FUSE
        if self.fuse_manager:
            self.fuse_manager.refresh()
    
    def add_torrent(self, magnet_link: str, save_path: Optional[str] = None) -> Optional[str]:
        """Adiciona um torrent via magnet link"""
        if not self.bt_engine:
            return None
        
        return self.bt_engine.add_torrent(magnet_link, save_path)
    
    def remove_torrent(self, info_hash: str, delete_files: bool = False) -> bool:
        """Remove um torrent"""
        if not self.bt_engine:
            return False
        
        return self.bt_engine.remove_torrent(info_hash, delete_files)
    
    def get_status(self) -> dict:
        """Retorna status do GoStream"""
        return {
            'running': self._running,
            'bt_engine': self.bt_engine is not None,
            'fuse': self.fuse_manager is not None,
            'api': self.api is not None,
            'torrents': len(self.bt_engine.list_torrents()) if self.bt_engine else 0,
            'streams': len(self.native_bridge.list_handles()) if self.native_bridge else 0,
        }
    
    def wait(self):
        """Aguarda até sinal de término"""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt recebido")
        finally:
            self.stop()


def create_gostream(config: Optional[GoStreamConfig] = None) -> GoStreamManager:
    """
    Factory function para criar instância do GoStream
    
    Args:
        config: Configurações opcionais
        
    Returns:
        GoStreamManager inicializado
    """
    manager = GoStreamManager(config)
    return manager
