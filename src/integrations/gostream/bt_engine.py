"""
BitTorrent Engine usando libtorrent

Implementação do engine BitTorrent similar ao GoStorm do GoStream.
Suporta streaming, priorização de peças e modo responsivo.
"""

import os
import time
import json
import hashlib
import logging
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, BinaryIO, Set
from threading import Lock, Thread, Event
from queue import Queue, Empty
from enum import Enum

try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
except ImportError:
    LIBTORRENT_AVAILABLE = False
    logging.warning("libtorrent não disponível. Instale com: pip install libtorrent")

logger = logging.getLogger(__name__)


class TorrentState(Enum):
    """Estados do torrent"""
    UNKNOWN = "unknown"
    CHECKING_FILES = "checking_files"
    DOWNLOADING_METADATA = "downloading_metadata"
    DOWNLOADING = "downloading"
    FINISHED = "finished"
    SEEDING = "seeding"
    ALLOCATING = "allocating"
    CHECKING_RESUME_DATA = "checking_resume_data"


def _convert_lt_state(state) -> str:
    """Converte estado do libtorrent para string"""
    if hasattr(state, 'name'):
        return str(state.name).lower()
    elif isinstance(state, str):
        return state.lower()
    else:
        return str(state).lower().replace('libtorrent.states.', '').replace('states.', '')


@dataclass
class PieceInfo:
    """Informações sobre uma peça do torrent"""
    index: int
    size: int
    downloaded: bool = False
    priority: int = 4  # 0-7, onde 7 é máxima prioridade
    
    def __hash__(self):
        return self.index


@dataclass 
class TorrentInfo:
    """Informações sobre um torrent"""
    info_hash: str
    name: str
    save_path: str
    total_size: int
    num_pieces: int
    piece_length: int
    state: TorrentState = field(default_factory=lambda: TorrentState.UNKNOWN)
    progress: float = 0.0
    download_rate: int = 0
    upload_rate: int = 0
    num_peers: int = 0
    num_seeds: int = 0
    files: List[dict] = field(default_factory=list)
    is_priority: bool = False
    added_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    
    @property
    def info_hash_v1(self) -> str:
        """Retorna info hash no formato v1"""
        return self.info_hash


class BTEngine:
    """
    Engine BitTorrent usando libtorrent-rasterbar.
    
    Equivalente ao GoStorm do GoStream, mas em Python.
    Gerencia torrents, sessão BitTorrent e streaming.
    """
    
    def __init__(self, config):
        """
        Inicializa o engine BitTorrent
        
        Args:
            config: GoStreamConfig com as configurações
        """
        self.config = config
        self.session: Optional[lt.session] = None
        self.torrents: Dict[str, lt.torrent_handle] = {}  # info_hash -> handle
        self.torrent_info: Dict[str, TorrentInfo] = {}
        self._lock = Lock()
        self._shutdown_event = Event()
        self._alert_thread: Optional[Thread] = None
        self._piece_readers: Dict[str, Dict[int, Queue]] = {}  # info_hash -> {piece_index: queue}
        
        # Adaptive Shield
        self._corruption_count: Dict[str, int] = {}
        self._shield_active: Dict[str, bool] = {}
        self._strict_mode: Dict[str, bool] = {}
        
        # Callbacks
        self._on_piece_finished: Optional[Callable[[str, int], None]] = None
        self._on_torrent_added: Optional[Callable[[str], None]] = None
        self._on_torrent_removed: Optional[Callable[[str], None]] = None
        
        if not LIBTORRENT_AVAILABLE:
            raise RuntimeError("libtorrent não está instalado. Instale com: pip install libtorrent")
    
    def start(self) -> bool:
        """Inicia a sessão BitTorrent"""
        try:
            # Cria sessão com settings pack
            # Configurações válidas do libtorrent
            settings = {
                'listen_interfaces': f'0.0.0.0:{self.config.listen_port_start}-{self.config.listen_port_end}',
                'connections_limit': self.config.max_connections_per_torrent,
                'connection_speed': 50,
                'rate_limit_ip_overhead': True,
            }
            
            if self.config.download_rate_limit > 0:
                settings['download_rate_limit'] = self.config.download_rate_limit * 1024
            if self.config.upload_rate_limit > 0:
                settings['upload_rate_limit'] = self.config.upload_rate_limit * 1024
            
            self.session = lt.session(settings)
            
            # Configura DHT
            if self.config.enable_dht:
                self.session.start_dht()
                self.session.add_dht_router("router.utorrent.com", 6881)
                self.session.add_dht_router("router.bittorrent.com", 6881)
                self.session.add_dht_router("dht.transmissionbt.com", 6881)
            
            # Configura LSD, UPnP, NAT-PMP
            if self.config.enable_lsd:
                self.session.start_lsd()
            if self.config.enable_upnp:
                self.session.start_upnp()
            if self.config.enable_natpmp:
                self.session.start_natpmp()
            
            # Inicia thread de alertas
            self._alert_thread = Thread(target=self._process_alerts, daemon=True)
            self._alert_thread.start()
            
            logger.info(f"BTEngine iniciado na porta {self.config.listen_port_start}-{self.config.listen_port_end}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar BTEngine: {e}")
            return False
    
    def stop(self):
        """Para a sessão BitTorrent"""
        self._shutdown_event.set()
        
        if self._alert_thread:
            self._alert_thread.join(timeout=5)
        
        if self.session:
            # Para todos os torrents
            for info_hash, handle in self.torrents.items():
                try:
                    handle.pause()
                    logger.info(f"Torrent {info_hash[:8]} pausado")
                except Exception as e:
                    logger.warning(f"Erro ao pausar torrent {info_hash[:8]}: {e}")
            
            self.session.pause()
            time.sleep(1)
            
        logger.info("BTEngine parado")
    
    def _process_alerts(self):
        """Processa alertas do libtorrent em background"""
        while not self._shutdown_event.is_set():
            if not self.session:
                time.sleep(0.1)
                continue
            
            alerts = self.session.pop_alerts()
            for alert in alerts:
                self._handle_alert(alert)
            
            time.sleep(0.01)  # 10ms
    
    def _handle_alert(self, alert):
        """Processa um alerta específico"""
        alert_type = type(alert).__name__
        
        if alert_type == 'piece_finished_alert':
            info_hash = str(alert.handle.info_hash())
            piece_index = alert.piece_index
            
            # Notifica readers
            with self._lock:
                if info_hash in self._piece_readers and piece_index in self._piece_readers[info_hash]:
                    self._piece_readers[info_hash][piece_index].put(True)
            
            # Callback
            if self._on_piece_finished:
                self._on_piece_finished(info_hash, piece_index)
        
        elif alert_type == 'torrent_added_alert':
            info_hash = str(alert.handle.info_hash())
            logger.info(f"Torrent adicionado: {info_hash[:8]}")
            
            if self._on_torrent_added:
                self._on_torrent_added(info_hash)
        
        elif alert_type == 'torrent_removed_alert':
            info_hash = str(alert.handle.info_hash())
            logger.info(f"Torrent removido: {info_hash[:8]}")
            
            if self._on_torrent_removed:
                self._on_torrent_removed(info_hash)
        
        elif alert_type == 'hash_failed_alert':
            info_hash = str(alert.handle.info_hash())
            piece_index = alert.piece_index
            
            # Adaptive Shield
            if self.config.adaptive_shield_enabled:
                self._handle_corruption(info_hash, piece_index)
        
        elif alert_type == 'state_changed_alert':
            info_hash = str(alert.handle.info_hash())
            with self._lock:
                if info_hash in self.torrents:
                    self._update_torrent_info(info_hash)
    
    def _handle_corruption(self, info_hash: str, piece_index: int):
        """Manipula detecção de corrupção (Adaptive Shield)"""
        with self._lock:
            if info_hash not in self._corruption_count:
                self._corruption_count[info_hash] = 0
            
            self._corruption_count[info_hash] += 1
            
            if self._corruption_count[info_hash] >= self.config.corruption_threshold:
                if not self._strict_mode.get(info_hash, False):
                    logger.warning(f"Adaptive Shield ativado para {info_hash[:8]} (corrupções: {self._corruption_count[info_hash]})")
                    self._strict_mode[info_hash] = True
                    self._shield_active[info_hash] = True
    
    def add_torrent(self, magnet_link: str, save_path: Optional[str] = None, 
                    priorities: Optional[List[int]] = None) -> Optional[str]:
        """
        Adiciona um torrent via magnet link
        
        Args:
            magnet_link: Link magnet do torrent
            save_path: Caminho para salvar (usa config padrão se None)
            priorities: Lista de prioridades por arquivo
            
        Returns:
            info_hash do torrent ou None em caso de erro
        """
        try:
            if save_path is None:
                save_path = self.config.cache_dir
            
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            # Parse magnet link
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = save_path
            params.flags |= lt.torrent_flags.sequential_download if not self.config.responsive_mode else 0
            
            # Adiciona torrent
            handle = self.session.add_torrent(params)
            info_hash = str(handle.info_hash())
            
            with self._lock:
                self.torrents[info_hash] = handle
                self.torrent_info[info_hash] = TorrentInfo(
                    info_hash=info_hash,
                    name="",
                    save_path=save_path,
                    total_size=0,
                    num_pieces=0,
                    piece_length=0,
                    state=TorrentState.DOWNLOADING_METADATA
                )
                self._piece_readers[info_hash] = {}
            
            # Aguarda metadata (timeout de 30s)
            timeout = time.time() + 30
            while not handle.has_metadata() and time.time() < timeout:
                time.sleep(0.1)
            
            if handle.has_metadata():
                torrent = handle.get_torrent_file()
                with self._lock:
                    info = self.torrent_info[info_hash]
                    info.name = torrent.name()
                    info.total_size = torrent.total_size()
                    info.num_pieces = torrent.num_pieces()
                    info.piece_length = torrent.piece_length()
                    info.files = [{'path': f.path, 'size': f.size, 'offset': f.offset} 
                                 for f in torrent.files()]
                
                logger.info(f"Metadata recebida: {torrent.name()} ({info_hash[:8]})")
                
                # Aplica prioridades se especificado
                if priorities:
                    for i, prio in enumerate(priorities):
                        if i < len(info.files):
                            handle.file_priority(i, prio)
                
                # Configura modo streaming - prioriza peças do início
                self._set_streaming_priorities(info_hash)
                
                return info_hash
            else:
                logger.warning(f"Timeout aguardando metadata para {info_hash[:8]}")
                return info_hash  # Retorna mesmo assim, pode completar depois
            
        except Exception as e:
            logger.error(f"Erro ao adicionar torrent: {e}")
            return None
    
    def add_torrent_file(self, torrent_path: str, save_path: Optional[str] = None) -> Optional[str]:
        """Adiciona um torrent via arquivo .torrent"""
        try:
            if save_path is None:
                save_path = self.config.cache_dir
            
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            # Lê arquivo torrent
            with open(torrent_path, 'rb') as f:
                torrent_data = f.read()
            
            info = lt.torrent_info(torrent_data)
            params = {
                'ti': info,
                'save_path': save_path,
            }
            
            handle = self.session.add_torrent(params)
            info_hash = str(handle.info_hash())
            
            with self._lock:
                self.torrents[info_hash] = handle
                self.torrent_info[info_hash] = TorrentInfo(
                    info_hash=info_hash,
                    name=info.name(),
                    save_path=save_path,
                    total_size=info.total_size(),
                    num_pieces=info.num_pieces(),
                    piece_length=info.piece_length(),
                    files=[{'path': f.path, 'size': f.size, 'offset': f.offset} 
                          for f in info.files()],
                    state=TorrentState.DOWNLOADING
                )
                self._piece_readers[info_hash] = {}
            
            self._set_streaming_priorities(info_hash)
            
            logger.info(f"Torrent file adicionado: {info.name()} ({info_hash[:8]})")
            return info_hash
            
        except Exception as e:
            logger.error(f"Erro ao adicionar arquivo torrent: {e}")
            return None
    
    def remove_torrent(self, info_hash: str, delete_files: bool = False) -> bool:
        """Remove um torrent da sessão"""
        try:
            with self._lock:
                if info_hash not in self.torrents:
                    return False
                
                handle = self.torrents[info_hash]
                self.session.remove_torrent(handle, 1 if delete_files else 0)
                
                del self.torrents[info_hash]
                del self.torrent_info[info_hash]
                if info_hash in self._piece_readers:
                    del self._piece_readers[info_hash]
            
            logger.info(f"Torrent {info_hash[:8]} removido (delete_files={delete_files})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover torrent: {e}")
            return False
    
    def _set_streaming_priorities(self, info_hash: str):
        """Configura prioridades para streaming (primeiras peças primeiro)"""
        with self._lock:
            if info_hash not in self.torrents:
                return
            
            handle = self.torrents[info_hash]
            info = self.torrent_info.get(info_hash)
            
            if not info or info.num_pieces == 0:
                return
            
            # Prioriza as primeiras peças (para streaming do início do arquivo)
            num_pieces_to_prioritize = min(50, info.num_pieces // 10)
            
            for i in range(num_pieces_to_prioritize):
                handle.piece_priority(i, 7)  # Máxima prioridade
            
            # Restante com prioridade normal
            for i in range(num_pieces_to_prioritize, info.num_pieces):
                handle.piece_priority(i, 4)
    
    def read_piece(self, info_hash: str, piece_index: int, 
                   timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Lê uma peça específica do torrent
        
        Args:
            info_hash: Hash do torrent
            piece_index: Índice da peça
            timeout: Timeout em segundos (usa config padrão se None)
            
        Returns:
            Dados da peça ou None se não disponível
        """
        if timeout is None:
            timeout = self.config.piece_timeout
        
        with self._lock:
            if info_hash not in self.torrents:
                return None
            
            handle = self.torrents[info_hash]
            
            # Verifica se peça está disponível
            if handle.have_piece(piece_index):
                piece = handle.read_piece(piece_index)
                if piece:
                    return bytes(piece)
            
            # Requisita peça com alta prioridade
            handle.piece_priority(piece_index, 7)
            handle.set_piece_deadline(piece_index, 0, lt.deadline_flags.alert_when_available)
            
            # Cria queue para esperar pela peça
            if piece_index not in self._piece_readers[info_hash]:
                self._piece_readers[info_hash][piece_index] = Queue()
            
            piece_queue = self._piece_readers[info_hash][piece_index]
        
        # Aguarda peça ficar disponível
        try:
            piece_queue.get(timeout=timeout)
            
            # Tenta ler novamente
            with self._lock:
                if info_hash in self.torrents:
                    piece = handle.read_piece(piece_index)
                    if piece:
                        return bytes(piece)
        except Empty:
            logger.warning(f"Timeout lendo peça {piece_index} do torrent {info_hash[:8]}")
        
        return None
    
    def read_at(self, info_hash: str, offset: int, size: int) -> Optional[bytes]:
        """
        Lê dados de um torrent em uma posição específica
        
        Args:
            info_hash: Hash do torrent
            offset: Posição inicial em bytes
            size: Quantidade de bytes a ler
            
        Returns:
            Dados lidos ou None
        """
        with self._lock:
            if info_hash not in self.torrent_info:
                return None
            
            info = self.torrent_info[info_hash]
            handle = self.torrents[info_hash]
        
        if not info or info.piece_length == 0:
            return None
        
        piece_length = info.piece_length
        start_piece = offset // piece_length
        end_piece = (offset + size - 1) // piece_length
        
        result = bytearray()
        current_offset = offset
        remaining = size
        
        for piece_index in range(start_piece, min(end_piece + 1, info.num_pieces)):
            piece_data = self.read_piece(info_hash, piece_index)
            
            if piece_data is None:
                logger.warning(f"Não foi possível ler peça {piece_index}")
                return None
            
            # Calcula offset dentro da peça
            piece_offset = current_offset - (piece_index * piece_length)
            piece_remaining = piece_length - piece_offset
            
            # Quantidade a copiar desta peça
            to_copy = min(remaining, piece_remaining, len(piece_data) - piece_offset)
            
            result.extend(piece_data[piece_offset:piece_offset + to_copy])
            
            current_offset += to_copy
            remaining -= to_copy
        
        return bytes(result)
    
    def get_torrent_info(self, info_hash: str) -> Optional[TorrentInfo]:
        """Retorna informações sobre um torrent"""
        with self._lock:
            if info_hash in self.torrent_info:
                self._update_torrent_info(info_hash)
                return self.torrent_info[info_hash]
        return None
    
    def _update_torrent_info(self, info_hash: str):
        """Atualiza informações do torrent"""
        if info_hash not in self.torrents:
            return
        
        handle = self.torrents[info_hash]
        status = handle.status()
        
        info = self.torrent_info[info_hash]
        info.state = TorrentState(_convert_lt_state(status.state))
        info.progress = status.progress
        info.download_rate = status.download_rate
        info.upload_rate = status.upload_rate
        info.num_peers = status.num_peers
        info.num_seeds = status.num_seeds
        info.last_access_time = time.time()
    
    def list_torrents(self) -> List[TorrentInfo]:
        """Lista todos os torrents"""
        with self._lock:
            for info_hash in self.torrents:
                self._update_torrent_info(info_hash)
            return list(self.torrent_info.values())
    
    def set_priority_mode(self, info_hash: str, enabled: bool = True):
        """Ativa/desativa modo prioridade para um torrent"""
        with self._lock:
            if info_hash in self.torrent_info:
                self.torrent_info[info_hash].is_priority = enabled
                
                if enabled:
                    logger.info(f"Priority Mode ativado para {info_hash[:8]}")
                    # Aumenta prioridade de todas as peças
                    if info_hash in self.torrents:
                        handle = self.torrents[info_hash]
                        for i in range(handle.get_torrent_info().num_pieces()):
                            handle.piece_priority(i, 7)
                else:
                    logger.info(f"Priority Mode desativado para {info_hash[:8]}")
                    self._set_streaming_priorities(info_hash)
    
    def on_piece_finished(self, callback: Callable[[str, int], None]):
        """Registra callback para quando uma peça é completada"""
        self._on_piece_finished = callback
    
    def on_torrent_added(self, callback: Callable[[str], None]):
        """Registra callback para quando um torrent é adicionado"""
        self._on_torrent_added = callback
    
    def on_torrent_removed(self, callback: Callable[[str], None]):
        """Registra callback para quando um torrent é removido"""
        self._on_torrent_removed = callback
    
    def get_session_stats(self) -> dict:
        """Retorna estatísticas da sessão"""
        if not self.session:
            return {}
        
        stats = self.session.status()
        return {
            'download_rate': stats.download_rate,
            'upload_rate': stats.upload_rate,
            'num_peers': stats.num_peers,
            'dht_nodes': stats.dht_nodes if self.config.enable_dht else 0,
            'has_incoming_connections': stats.has_incoming_connections,
        }
