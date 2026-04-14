"""
Read-Ahead Cache com sharding

Implementação do cache de pré-leitura similar ao raCache do GoStream.
Usa múltiplos shards para reduzir contenção de locks.
"""

import time
import logging
import threading
from collections import OrderedDict
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from threading import Lock, Thread, Event

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada no cache"""
    key: str  # info_hash:piece_index
    data: bytes
    size: int
    timestamp: float
    access_count: int = 0
    last_access: float


class CacheShard:
    """
    Shard individual do cache.
    Cada shard tem seu próprio lock para reduzir contenção.
    """
    
    def __init__(self, max_size: int):
        """
        Inicializa um shard
        
        Args:
            max_size: Tamanho máximo em bytes
        """
        self.max_size = max_size
        self.current_size = 0
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[bytes]:
        """Obtém uma entrada do cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.access_count += 1
                entry.last_access = time.time()
                
                # Move para o fim (LRU - mais recentemente usado)
                self.cache.move_to_end(key)
                
                self.hit_count += 1
                return entry.data
            
            self.miss_count += 1
            return None
    
    def put(self, key: str, data: bytes) -> bool:
        """Adiciona uma entrada ao cache"""
        size = len(data)
        
        with self.lock:
            # Se já existe, atualiza
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_size -= old_entry.size
                del self.cache[key]
            
            # Verifica se cabe no cache
            if size > self.max_size:
                logger.debug(f"Entrada {key} muito grande para o shard ({size} > {self.max_size})")
                return False
            
            # Libera espaço se necessário
            while self.current_size + size > self.max_size and self.cache:
                self._evict_oldest()
            
            # Adiciona nova entrada
            entry = CacheEntry(
                key=key,
                data=data,
                size=size,
                timestamp=time.time(),
                last_access=time.time()
            )
            
            self.cache[key] = entry
            self.current_size += size
            
            return True
    
    def _evict_oldest(self):
        """Remove a entrada mais antiga (LRU)"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.current_size -= entry.size
            logger.debug(f"Evicted {key} from cache (size: {entry.size})")
    
    def remove(self, key: str) -> bool:
        """Remove uma entrada do cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_size -= entry.size
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Limpa o shard"""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do shard"""
        with self.lock:
            total_access = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_access if total_access > 0 else 0
            
            return {
                'entries': len(self.cache),
                'current_size': self.current_size,
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
            }


class ReadAheadCache:
    """
    Cache de pré-leitura sharded.
    
    Similar ao raCache do GoStream, usa múltiplos shards
    para permitir acesso paralelo com mínima contenção.
    """
    
    def __init__(self, num_shards: int, total_budget_bytes: int):
        """
        Inicializa o cache
        
        Args:
            num_shards: Número de shards (GoStream usa 32)
            total_budget_bytes: Orçamento total de RAM em bytes
        """
        self.num_shards = num_shards
        self.total_budget = total_budget_bytes
        shard_budget = total_budget_bytes // num_shards
        
        self.shards: List[CacheShard] = [
            CacheShard(shard_budget) for _ in range(num_shards)
        ]
        
        self._prefetch_thread: Optional[Thread] = None
        self._prefetch_queue = []
        self._prefetch_lock = Lock()
        self._shutdown_event = Event()
        self._on_prefetch_complete: Optional[Callable[[str], None]] = None
        
        logger.info(f"ReadAheadCache inicializado: {num_shards} shards, "
                   f"{total_budget_bytes // 1024 // 1024}MB total")
    
    def _get_shard_index(self, key: str) -> int:
        """Calcula o índice do shard baseado na key"""
        return hash(key) % self.num_shards
    
    def get(self, info_hash: str, piece_index: int) -> Optional[bytes]:
        """Obtém uma peça do cache"""
        key = f"{info_hash}:{piece_index}"
        shard_idx = self._get_shard_index(key)
        return self.shards[shard_idx].get(key)
    
    def put(self, info_hash: str, piece_index: int, data: bytes) -> bool:
        """Adiciona uma peça ao cache"""
        key = f"{info_hash}:{piece_index}"
        shard_idx = self._get_shard_index(key)
        return self.shards[shard_idx].put(key, data)
    
    def remove(self, info_hash: str, piece_index: int) -> bool:
        """Remove uma peça do cache"""
        key = f"{info_hash}:{piece_index}"
        shard_idx = self._get_shard_index(key)
        return self.shards[shard_idx].remove(key)
    
    def remove_torrent(self, info_hash: str):
        """Remove todas as peças de um torrent do cache"""
        for shard in self.shards:
            with shard.lock:
                keys_to_remove = [k for k in shard.cache.keys() if k.startswith(f"{info_hash}:")]
                for key in keys_to_remove:
                    shard.remove(key)
        
        logger.debug(f"Removido torrent {info_hash[:8]} do cache")
    
    def get_range(self, info_hash: str, start_piece: int, end_piece: int) -> Dict[int, bytes]:
        """Obtém múltiplas peças do cache"""
        result = {}
        for piece_index in range(start_piece, end_piece + 1):
            data = self.get(info_hash, piece_index)
            if data:
                result[piece_index] = data
        return result
    
    def start_prefetch_worker(self, fetch_func: Callable[[str, int], Optional[bytes]]):
        """
        Inicia worker de pré-busca em background
        
        Args:
            fetch_func: Função para buscar peça (info_hash, piece_index) -> data
        """
        self._prefetch_thread = Thread(
            target=self._prefetch_worker,
            args=(fetch_func,),
            daemon=True
        )
        self._prefetch_thread.start()
        logger.info("Prefetch worker iniciado")
    
    def _prefetch_worker(self, fetch_func: Callable[[str, int], Optional[bytes]]):
        """Worker que executa pré-busca em background"""
        while not self._shutdown_event.is_set():
            with self._prefetch_lock:
                if self._prefetch_queue:
                    info_hash, piece_index = self._prefetch_queue.pop(0)
                else:
                    info_hash, piece_index = None, None
            
            if info_hash is not None:
                # Verifica se já está no cache
                if self.get(info_hash, piece_index) is None:
                    # Busca peça
                    data = fetch_func(info_hash, piece_index)
                    if data:
                        self.put(info_hash, piece_index, data)
                        
                        if self._on_prefetch_complete:
                            self._on_prefetch_complete(f"{info_hash}:{piece_index}")
            else:
                # Aguarda se não há trabalho
                time.sleep(0.01)
    
    def queue_prefetch(self, info_hash: str, piece_index: int):
        """Adiciona uma peça à fila de pré-busca"""
        with self._prefetch_lock:
            item = (info_hash, piece_index)
            if item not in self._prefetch_queue:
                self._prefetch_queue.append(item)
                
                # Limita tamanho da fila
                if len(self._prefetch_queue) > 1000:
                    self._prefetch_queue = self._prefetch_queue[-500:]
    
    def queue_prefetch_range(self, info_hash: str, start_piece: int, end_piece: int):
        """Adiciona uma faixa de peças à fila de pré-busca"""
        for piece_index in range(start_piece, end_piece + 1):
            self.queue_prefetch(info_hash, piece_index)
    
    def stop(self):
        """Para o cache e suas threads"""
        self._shutdown_event.set()
        
        if self._prefetch_thread:
            self._prefetch_thread.join(timeout=5)
        
        self.clear()
        logger.info("ReadAheadCache parado")
    
    def clear(self):
        """Limpa todo o cache"""
        for shard in self.shards:
            shard.clear()
        logger.info("Cache limpo")
    
    def get_stats(self) -> dict:
        """Retorna estatísticas completas do cache"""
        total_hits = 0
        total_misses = 0
        total_size = 0
        total_entries = 0
        
        shard_stats = []
        for i, shard in enumerate(self.shards):
            stats = shard.get_stats()
            shard_stats.append({
                'shard': i,
                **stats
            })
            total_hits += stats['hit_count']
            total_misses += stats['miss_count']
            total_size += stats['current_size']
            total_entries += stats['entries']
        
        total_access = total_hits + total_misses
        hit_rate = total_hits / total_access if total_access > 0 else 0
        
        return {
            'num_shards': self.num_shards,
            'total_budget': self.total_budget,
            'current_size': total_size,
            'utilization': total_size / self.total_budget if self.total_budget > 0 else 0,
            'total_entries': total_entries,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'hit_rate': hit_rate,
            'shards': shard_stats,
        }
    
    def on_prefetch_complete(self, callback: Callable[[str], None]):
        """Registra callback para quando prefetch completa"""
        self._on_prefetch_complete = callback
