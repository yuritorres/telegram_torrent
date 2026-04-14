"""
Native Bridge - Zero-copy streaming pipeline

Implementação da ponte nativa similar ao NativeClient/NativeReader do GoStream.
Conecta a camada FUSE com o engine BitTorrent via pipes em memória,
eliminando overhead de rede e serialização HTTP.
"""

import io
import time
import logging
import threading
from typing import Optional, BinaryIO, Callable, Dict, Tuple
from dataclasses import dataclass, field
from threading import Lock, Thread, Event, Condition
from queue import Queue, Empty, Full

logger = logging.getLogger(__name__)


@dataclass
class StreamHandle:
    """Handle para um stream ativo"""
    info_hash: str
    file_index: int
    file_offset: int  # Offset do arquivo dentro do torrent
    file_size: int
    current_position: int = 0
    is_open: bool = True
    priority_mode: bool = False
    created_at: float = field(default_factory=time.time)
    last_read: float = field(default_factory=time.time)
    bytes_read: int = 0
    
    @property
    def remaining(self) -> int:
        """Bytes restantes para leitura"""
        return self.file_size - self.current_position


class StreamPump:
    """
    Bomba de dados para streaming.
    
    Similar ao NativePumpState do GoStream, gerencia o fluxo
    de dados entre o engine BitTorrent e o handle FUSE.
    """
    
    def __init__(self, handle: StreamHandle, bt_engine, cache,
                 buffer_size: int = 1024 * 1024,  # 1MB default
                 read_ahead_trigger: int = 256 * 1024):  # 256KB trigger
        """
        Inicializa a bomba de streaming
        
        Args:
            handle: StreamHandle com informações do stream
            bt_engine: Instância do BTEngine
            cache: Instância do ReadAheadCache
            buffer_size: Tamanho do buffer circular
            read_ahead_trigger: Quanto buffer deve ter antes de pré-buscar mais
        """
        self.handle = handle
        self.bt_engine = bt_engine
        self.cache = cache
        self.buffer_size = buffer_size
        self.read_ahead_trigger = read_ahead_trigger
        
        # Buffer circular com Queue
        self._buffer = Queue(maxsize=buffer_size)
        self._buffer_lock = Lock()
        self._buffered_size = 0
        
        # Controle de fluxo
        self._pause_event = Event()
        self._pause_event.set()  # Inicia pausado
        self._shutdown_event = Event()
        self._error: Optional[Exception] = None
        
        # Threads
        self._pump_thread: Optional[Thread] = None
        self._read_ahead_thread: Optional[Thread] = None
        
        # Read-ahead tracking
        self._last_read_ahead_piece: int = -1
        
        # Condition para notificar quando dados disponíveis
        self._data_available = Condition(self._buffer_lock)
    
    def start(self):
        """Inicia a bomba de dados"""
        self._pump_thread = Thread(target=self._pump_loop, daemon=True)
        self._pump_thread.start()
        
        self._read_ahead_thread = Thread(target=self._read_ahead_loop, daemon=True)
        self._read_ahead_thread.start()
        
        self._pause_event.clear()  # Despausa
        logger.debug(f"StreamPump iniciado para {self.handle.info_hash[:8]}")
    
    def stop(self):
        """Para a bomba de dados"""
        self._shutdown_event.set()
        self._pause_event.set()  # Desbloqueia se pausado
        
        # Limpa buffer para desbloquear threads
        with self._buffer_lock:
            while not self._buffer.empty():
                try:
                    self._buffer.get_nowait()
                except Empty:
                    break
        
        if self._pump_thread:
            self._pump_thread.join(timeout=5)
        if self._read_ahead_thread:
            self._read_ahead_thread.join(timeout=5)
        
        logger.debug(f"StreamPump parado para {self.handle.info_hash[:8]}")
    
    def _pump_loop(self):
        """Loop principal que bombeia dados do BT para o buffer"""
        while not self._shutdown_event.is_set():
            # Aguarda se pausado
            if self._pause_event.is_set():
                time.sleep(0.01)
                continue
            
            try:
                # Verifica se há espaço no buffer
                with self._buffer_lock:
                    if self._buffered_size >= self.buffer_size:
                        time.sleep(0.001)
                        continue
                
                # Calcula próxima posição a ler
                absolute_offset = self.handle.file_offset + self.handle.current_position
                
                # Obtém informações do torrent
                info = self.bt_engine.get_torrent_info(self.handle.info_hash)
                if not info:
                    raise RuntimeError("Torrent não encontrado")
                
                piece_length = info.piece_length
                piece_index = absolute_offset // piece_length
                piece_offset = absolute_offset % piece_length
                
                # Tenta obter do cache primeiro
                data = self.cache.get(self.handle.info_hash, piece_index)
                
                if data is None:
                    # Busca do engine BitTorrent
                    data = self.bt_engine.read_piece(self.handle.info_hash, piece_index)
                    
                    if data is None:
                        # Peça não disponível ainda, aguarda
                        time.sleep(0.05)
                        continue
                    
                    # Coloca no cache
                    self.cache.put(self.handle.info_hash, piece_index, data)
                
                # Extrai dados relevantes da peça
                remaining_in_piece = len(data) - piece_offset
                to_read = min(
                    remaining_in_piece,
                    self.handle.remaining,
                    64 * 1024  # Lê em chunks de 64KB
                )
                
                chunk = data[piece_offset:piece_offset + to_read]
                
                # Adiciona ao buffer
                try:
                    self._buffer.put(chunk, timeout=0.1)
                    with self._buffer_lock:
                        self._buffered_size += len(chunk)
                        self.handle.current_position += len(chunk)
                        self.handle.bytes_read += len(chunk)
                        self.handle.last_read = time.time()
                        
                        # Notifica que há dados disponíveis
                        self._data_available.notify_all()
                except Full:
                    # Buffer cheio, aguarda
                    time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Erro no pump loop: {e}")
                self._error = e
                break
    
    def _read_ahead_loop(self):
        """Loop de pré-busca para manter buffer cheio"""
        while not self._shutdown_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.05)
                continue
            
            try:
                # Verifica se precisa de mais read-ahead
                with self._buffer_lock:
                    if self._buffered_size >= self.read_ahead_trigger:
                        time.sleep(0.01)
                        continue
                
                # Calcula próximas peças para pré-buscar
                absolute_offset = self.handle.file_offset + self.handle.current_position
                
                info = self.bt_engine.get_torrent_info(self.handle.info_hash)
                if not info:
                    time.sleep(0.1)
                    continue
                
                piece_length = info.piece_length
                current_piece = absolute_offset // piece_length
                
                # Pré-busca próximas 5 peças
                for i in range(1, 6):
                    next_piece = current_piece + i
                    if next_piece >= info.num_pieces:
                        break
                    
                    # Verifica se já está no cache
                    if self.cache.get(self.handle.info_hash, next_piece) is None:
                        # Adiciona à fila de pré-busca
                        self.cache.queue_prefetch(self.handle.info_hash, next_piece)
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.warning(f"Erro no read-ahead: {e}")
                time.sleep(0.1)
    
    def read(self, size: int) -> bytes:
        """
        Lê dados do buffer.
        
        Args:
            size: Quantidade máxima de bytes a ler
            
        Returns:
            Dados lidos (pode ser menos que size)
        """
        if self._error:
            raise self._error
        
        result = bytearray()
        remaining = size
        
        # Aguarda dados disponíveis
        with self._buffer_lock:
            timeout = time.time() + 30  # 30s timeout
            while self._buffered_size == 0 and not self._shutdown_event.is_set():
                if time.time() > timeout:
                    raise TimeoutError("Timeout aguardando dados do stream")
                self._data_available.wait(timeout=0.1)
        
        # Lê do buffer
        while remaining > 0 and not self._buffer.empty():
            try:
                chunk = self._buffer.get_nowait()
                to_copy = min(len(chunk), remaining)
                result.extend(chunk[:to_copy])
                
                with self._buffer_lock:
                    self._buffered_size -= len(chunk)
                
                remaining -= to_copy
                
                # Se sobrou dados no chunk, guarda para próxima leitura
                if to_copy < len(chunk):
                    leftover = chunk[to_copy:]
                    # Reinsere no início do buffer
                    temp_queue = Queue()
                    temp_queue.put(leftover)
                    while not self._buffer.empty():
                        temp_queue.put(self._buffer.get())
                    self._buffer = temp_queue
                    with self._buffer_lock:
                        self._buffered_size += len(leftover)
                
            except Empty:
                break
        
        return bytes(result)
    
    def seek(self, position: int):
        """Move posição de leitura"""
        if position < 0 or position > self.handle.file_size:
            raise ValueError(f"Posição inválida: {position}")
        
        # Pausa durante seek
        self._pause_event.set()
        
        # Limpa buffer
        with self._buffer_lock:
            while not self._buffer.empty():
                try:
                    self._buffer.get_nowait()
                except Empty:
                    break
            self._buffered_size = 0
        
        self.handle.current_position = position
        self._last_read_ahead_piece = -1
        
        # Despausa
        self._pause_event.clear()
    
    def pause(self):
        """Pausa a bomba"""
        self._pause_event.set()
    
    def resume(self):
        """Resume a bomba"""
        self._pause_event.clear()
    
    def is_buffer_healthy(self) -> bool:
        """Verifica se o buffer tem dados suficientes"""
        with self._buffer_lock:
            return self._buffered_size >= self.read_ahead_trigger // 2


class NativeBridge:
    """
    Ponte nativa entre FUSE e BitTorrent engine.
    
    Equivalente ao NativeClient/NativeReader do GoStream.
    Gerencia handles de stream e conecta FUSE ao BTEngine
    via pipes em memória (zero-network overhead).
    """
    
    def __init__(self, bt_engine, cache, config):
        """
        Inicializa a ponte nativa
        
        Args:
            bt_engine: Instância do BTEngine
            cache: Instância do ReadAheadCache
            config: GoStreamConfig
        """
        self.bt_engine = bt_engine
        self.cache = cache
        self.config = config
        
        # Handles ativos: handle_id -> StreamPump
        self._handles: Dict[str, StreamPump] = {}
        self._handles_lock = Lock()
        self._handle_counter = 0
        
        # Torrents acordados (wake/probe)
        self._woken_torrents: Dict[str, float] = {}
        
        logger.info("NativeBridge inicializado")
    
    def _generate_handle_id(self) -> str:
        """Gera ID único para handle"""
        with self._handles_lock:
            self._handle_counter += 1
            return f"handle_{self._handle_counter}_{int(time.time() * 1000)}"
    
    def wake_torrent(self, info_hash: str) -> bool:
        """
        'Acorda' um torrent para streaming.
        
        Similar ao Wake do GoStream, garante que o torrent
        esteja ativo e com peças prioritárias disponíveis.
        
        Args:
            info_hash: Hash do torrent
            
        Returns:
            True se sucesso
        """
        info = self.bt_engine.get_torrent_info(info_hash)
        if not info:
            logger.warning(f"Torrent {info_hash[:8]} não encontrado para wake")
            return False
        
        # Marca como acordado
        self._woken_torrents[info_hash] = time.time()
        
        # Configura peças iniciais com alta prioridade
        self.bt_engine._set_streaming_priorities(info_hash)
        
        logger.debug(f"Torrent {info_hash[:8]} acordado")
        return True
    
    def probe_torrent(self, info_hash: str, file_index: int = 0) -> Optional[Tuple[int, int]]:
        """
        'Sonda' um torrent para obter informações de arquivo.
        
        Similar ao Probe do GoStream, retorna offset e tamanho
        do arquivo dentro do torrent.
        
        Args:
            info_hash: Hash do torrent
            file_index: Índice do arquivo
            
        Returns:
            (offset, size) ou None
        """
        info = self.bt_engine.get_torrent_info(info_hash)
        if not info or file_index >= len(info.files):
            return None
        
        file_info = info.files[file_index]
        return (file_info['offset'], file_info['size'])
    
    def open_file(self, info_hash: str, file_index: int = 0) -> Optional[str]:
        """
        Abre um arquivo para streaming.
        
        Args:
            info_hash: Hash do torrent
            file_index: Índice do arquivo no torrent
            
        Returns:
            Handle ID para operações subsequentes
        """
        # Acorda torrent se necessário
        if info_hash not in self._woken_torrents:
            self.wake_torrent(info_hash)
        
        # Obtém informações do arquivo
        probe_result = self.probe_torrent(info_hash, file_index)
        if not probe_result:
            logger.error(f"Não foi possível sondar arquivo {file_index} do torrent {info_hash[:8]}")
            return None
        
        file_offset, file_size = probe_result
        
        # Cria handle
        handle = StreamHandle(
            info_hash=info_hash,
            file_index=file_index,
            file_offset=file_offset,
            file_size=file_size
        )
        
        handle_id = self._generate_handle_id()
        
        # Cria e inicia pump
        pump = StreamPump(
            handle=handle,
            bt_engine=self.bt_engine,
            cache=self.cache,
            buffer_size=self.config.stream_buffer_size
        )
        pump.start()
        
        with self._handles_lock:
            self._handles[handle_id] = pump
        
        logger.info(f"Arquivo aberto: {info_hash[:8]}[{file_index}] -> {handle_id}")
        return handle_id
    
    def close_file(self, handle_id: str) -> bool:
        """Fecha um handle de arquivo"""
        with self._handles_lock:
            if handle_id not in self._handles:
                return False
            
            pump = self._handles[handle_id]
            del self._handles[handle_id]
        
        pump.stop()
        logger.debug(f"Handle fechado: {handle_id}")
        return True
    
    def read(self, handle_id: str, size: int) -> bytes:
        """Lê dados de um handle"""
        with self._handles_lock:
            if handle_id not in self._handles:
                raise ValueError(f"Handle não encontrado: {handle_id}")
            pump = self._handles[handle_id]
        
        return pump.read(size)
    
    def seek(self, handle_id: str, position: int):
        """Move posição de leitura"""
        with self._handles_lock:
            if handle_id not in self._handles:
                raise ValueError(f"Handle não encontrado: {handle_id}")
            pump = self._handles[handle_id]
        
        pump.seek(position)
    
    def set_priority_mode(self, handle_id: str, enabled: bool):
        """Ativa/desativa modo prioridade para um handle"""
        with self._handles_lock:
            if handle_id not in self._handles:
                return
            
            pump = self._handles[handle_id]
            pump.handle.priority_mode = enabled
            
            # Propaga para BT engine
            self.bt_engine.set_priority_mode(pump.handle.info_hash, enabled)
    
    def get_stats(self, handle_id: str) -> Optional[dict]:
        """Retorna estatísticas de um handle"""
        with self._handles_lock:
            if handle_id not in self._handles:
                return None
            
            pump = self._handles[handle_id]
            handle = pump.handle
            
            return {
                'info_hash': handle.info_hash,
                'file_index': handle.file_index,
                'file_size': handle.file_size,
                'current_position': handle.current_position,
                'progress': handle.current_position / handle.file_size if handle.file_size > 0 else 0,
                'bytes_read': handle.bytes_read,
                'priority_mode': handle.priority_mode,
                'is_buffer_healthy': pump.is_buffer_healthy(),
            }
    
    def list_handles(self) -> list:
        """Lista todos os handles ativos"""
        with self._handles_lock:
            return [
                {
                    'handle_id': hid,
                    'info_hash': pump.handle.info_hash,
                    'file_index': pump.handle.file_index,
                    'file_size': pump.handle.file_size,
                    'current_position': pump.handle.current_position,
                }
                for hid, pump in self._handles.items()
            ]
    
    def close_all(self):
        """Fecha todos os handles"""
        with self._handles_lock:
            handles_to_close = list(self._handles.items())
            self._handles.clear()
        
        for handle_id, pump in handles_to_close:
            pump.stop()
        
        logger.info(f"Todos os handles fechados ({len(handles_to_close)})")
