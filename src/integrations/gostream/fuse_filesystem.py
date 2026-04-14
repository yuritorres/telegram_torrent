"""
FUSE Virtual Filesystem

Implementação da camada FUSE similar à do GoStream.
Apresenta arquivos torrent como arquivos MKV locais.
"""

import os
import time
import errno
import logging
import stat
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from threading import Lock

# Tenta importar fusepy (bindings FUSE para Python)
try:
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
    FUSE_AVAILABLE = True
except ImportError:
    FUSE_AVAILABLE = False
    # Classes stubs para quando fusepy não está disponível
    class FuseOSError(Exception):
        pass
    class Operations:
        pass
    class LoggingMixIn:
        pass
    FUSE = None
    
    logging.warning("fusepy não disponível. Instale com: pip install fusepy")

logger = logging.getLogger(__name__)


@dataclass
class VirtualFileNode:
    """Nó de arquivo virtual no FUSE"""
    name: str
    size: int
    info_hash: str
    file_index: int
    is_directory: bool = False
    children: Optional[Dict[str, 'VirtualFileNode']] = None
    
    # Atributos FUSE
    st_mode: int = 0
    st_ino: int = 0
    st_dev: int = 0
    st_nlink: int = 1
    st_uid: int = 0
    st_gid: int = 0
    st_size: int = 0
    st_atime: float = 0
    st_mtime: float = 0
    st_ctime: float = 0
    
    def __post_init__(self):
        if self.is_directory:
            self.st_mode = stat.S_IFDIR | 0o755
            self.children = self.children or {}
        else:
            self.st_mode = stat.S_IFREG | 0o644
            self.st_size = self.size
            now = time.time()
            self.st_atime = now
            self.st_mtime = now
            self.st_ctime = now


class MkvHandle:
    """
    Handle para leitura de arquivo virtual MKV.
    
    Similar ao MkvHandle do GoStream, gerencia o estado
    de leitura de um arquivo via NativeBridge.
    """
    
    def __init__(self, info_hash: str, file_index: int, file_size: int,
                 native_bridge, cache):
        """
        Inicializa handle
        
        Args:
            info_hash: Hash do torrent
            file_index: Índice do arquivo
            file_size: Tamanho do arquivo
            native_bridge: Instância do NativeBridge
            cache: Instância do ReadAheadCache
        """
        self.info_hash = info_hash
        self.file_index = file_index
        self.file_size = file_size
        self.native_bridge = native_bridge
        self.cache = cache
        
        # Handle do native bridge
        self.handle_id: Optional[str] = None
        
        # Posição atual
        self.position = 0
        
        # Flag de aberto
        self.is_open = False
    
    def open(self) -> bool:
        """Abre arquivo para leitura"""
        self.handle_id = self.native_bridge.open_file(self.info_hash, self.file_index)
        if self.handle_id:
            self.is_open = True
            logger.debug(f"MkvHandle aberto: {self.info_hash[:8]}[{self.file_index}]")
            return True
        return False
    
    def close(self):
        """Fecha arquivo"""
        if self.handle_id:
            self.native_bridge.close_file(self.handle_id)
            self.is_open = False
            logger.debug(f"MkvHandle fechado: {self.handle_id}")
    
    def read(self, size: int) -> bytes:
        """Lê dados do arquivo"""
        if not self.is_open or not self.handle_id:
            raise FuseOSError(errno.EIO)
        
        # Verifica cache primeiro para peças completas
        info = self.native_bridge.bt_engine.get_torrent_info(self.info_hash)
        if info and info.piece_length > 0:
            absolute_offset = self._get_file_offset() + self.position
            piece_length = info.piece_length
            piece_index = absolute_offset // piece_length
            
            # Se leitura alinhada em peça, tenta cache
            if size == piece_length or size <= piece_length:
                cached = self.cache.get(self.info_hash, piece_index)
                if cached:
                    piece_offset = absolute_offset % piece_length
                    data = cached[piece_offset:piece_offset + size]
                    self.position += len(data)
                    return data
        
        # Lê via native bridge
        try:
            data = self.native_bridge.read(self.handle_id, size)
            self.position += len(data)
            return data
        except Exception as e:
            logger.error(f"Erro na leitura: {e}")
            raise FuseOSError(errno.EIO)
    
    def seek(self, position: int):
        """Move posição de leitura"""
        if position < 0 or position > self.file_size:
            raise FuseOSError(errno.EINVAL)
        
        if self.handle_id:
            self.native_bridge.seek(self.handle_id, position)
        self.position = position
    
    def _get_file_offset(self) -> int:
        """Obtém offset do arquivo dentro do torrent"""
        probe = self.native_bridge.probe_torrent(self.info_hash, self.file_index)
        return probe[0] if probe else 0


class FUSEFilesystem(Operations, LoggingMixIn):
    """
    Filesystem virtual FUSE.
    
    Apresenta arquivos torrent como arquivos MKV locais.
    Similar ao FUSE layer do GoStream.
    """
    
    def __init__(self, bt_engine, native_bridge, cache, mount_point: str):
        """
        Inicializa filesystem
        
        Args:
            bt_engine: Instância do BTEngine
            native_bridge: Instância do NativeBridge
            cache: Instância do ReadAheadCache
            mount_point: Ponto de montagem FUSE
        """
        self.bt_engine = bt_engine
        self.native_bridge = native_bridge
        self.cache = cache
        self.mount_point = mount_point
        
        # Estrutura de diretórios virtual
        self.root = VirtualFileNode(
            name="",
            size=0,
            info_hash="",
            file_index=0,
            is_directory=True
        )
        
        # Handles de arquivos abertos
        self._file_handles: Dict[int, MkvHandle] = {}
        self._handle_counter = 0
        self._handles_lock = Lock()
        
        # Inicializa estrutura
        self._rebuild_tree()
        
        logger.info(f"FUSEFilesystem inicializado em {mount_point}")
    
    def _rebuild_tree(self):
        """Reconstrói árvore de diretórios virtual"""
        self.root = VirtualFileNode(
            name="",
            size=0,
            info_hash="",
            file_index=0,
            is_directory=True
        )
        
        # Obtém todos os torrents
        torrents = self.bt_engine.list_torrents()
        
        for torrent in torrents:
            # Cria diretório para cada torrent
            safe_name = self._sanitize_filename(torrent.name)
            dir_node = VirtualFileNode(
                name=safe_name,
                size=0,
                info_hash=torrent.info_hash,
                file_index=0,
                is_directory=True
            )
            
            # Adiciona arquivos
            for i, file_info in enumerate(torrent.files):
                file_path = file_info['path']
                file_size = file_info['size']
                
                # Nome do arquivo
                file_name = Path(file_path).name
                safe_file_name = self._sanitize_filename(file_name)
                
                # Extensão .mkv para compatibilidade com media servers
                if not safe_file_name.endswith(('.mkv', '.mp4', '.avi', '.mov')):
                    safe_file_name += '.mkv'
                
                file_node = VirtualFileNode(
                    name=safe_file_name,
                    size=file_size,
                    info_hash=torrent.info_hash,
                    file_index=i
                )
                
                # Adiciona ao diretório do torrent
                dir_node.children[safe_file_name] = file_node
            
            self.root.children[safe_name] = dir_node
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza nome de arquivo para ser válido"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:255]  # Limita tamanho
    
    def _get_node(self, path: str) -> Optional[VirtualFileNode]:
        """Obtém nó pelo path"""
        if path == '/':
            return self.root
        
        parts = path.strip('/').split('/')
        current = self.root
        
        for part in parts:
            if not current.is_directory or not current.children:
                return None
            
            if part not in current.children:
                return None
            
            current = current.children[part]
        
        return current
    
    def _get_info_hash_from_path(self, path: str) -> Optional[str]:
        """Extrai info_hash de um path"""
        node = self._get_node(path)
        if node and not node.is_directory:
            return node.info_hash
        return None
    
    # === FUSE Operations ===
    
    def getattr(self, path: str, fh=None) -> dict:
        """Retorna atributos de arquivo/diretório"""
        node = self._get_node(path)
        
        if not node:
            # Se não encontrou, tenta rebuild (pode ser torrent novo)
            self._rebuild_tree()
            node = self._get_node(path)
        
        if not node:
            raise FuseOSError(errno.ENOENT)
        
        return {
            'st_mode': node.st_mode,
            'st_ino': node.st_ino,
            'st_dev': node.st_dev,
            'st_nlink': node.st_nlink,
            'st_uid': node.st_uid,
            'st_gid': node.st_gid,
            'st_size': node.st_size,
            'st_atime': node.st_atime,
            'st_mtime': node.st_mtime,
            'st_ctime': node.st_ctime,
        }
    
    def readdir(self, path: str, fh) -> List[str]:
        """Lista diretório"""
        node = self._get_node(path)
        
        if not node or not node.is_directory:
            raise FuseOSError(errno.ENOENT)
        
        # Atualiza estrutura
        self._rebuild_tree()
        node = self._get_node(path)
        
        # Retorna conteúdo
        entries = ['.', '..']
        if node.children:
            entries.extend(node.children.keys())
        
        return entries
    
    def open(self, path: str, flags) -> int:
        """Abre arquivo"""
        node = self._get_node(path)
        
        if not node or node.is_directory:
            raise FuseOSError(errno.ENOENT)
        
        # Verifica se é leitura
        if flags & os.O_WRONLY or flags & os.O_RDWR:
            raise FuseOSError(errno.EROFS)  # Somente leitura
        
        # Cria handle
        handle = MkvHandle(
            info_hash=node.info_hash,
            file_index=node.file_index,
            file_size=node.size,
            native_bridge=self.native_bridge,
            cache=self.cache
        )
        
        if not handle.open():
            raise FuseOSError(errno.EIO)
        
        # Gera file handle ID
        with self._handles_lock:
            self._handle_counter += 1
            fh_id = self._handle_counter
            self._file_handles[fh_id] = handle
        
        logger.debug(f"Arquivo aberto: {path} (fh={fh_id})")
        return fh_id
    
    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        """Lê dados do arquivo"""
        with self._handles_lock:
            if fh not in self._file_handles:
                raise FuseOSError(errno.EBADF)
            
            handle = self._file_handles[fh]
        
        # Seek para posição
        if handle.position != offset:
            handle.seek(offset)
        
        # Lê dados
        return handle.read(size)
    
    def release(self, path: str, fh: int):
        """Fecha arquivo"""
        with self._handles_lock:
            if fh in self._file_handles:
                handle = self._file_handles[fh]
                del self._file_handles[fh]
                handle.close()
                logger.debug(f"Arquivo fechado: {path} (fh={fh})")
    
    def readlink(self, path: str) -> str:
        """Lê link simbólico"""
        raise FuseOSError(errno.EINVAL)
    
    def mknod(self, path: str, mode, dev):
        """Cria nó especial"""
        raise FuseOSError(errno.EROFS)
    
    def mkdir(self, path: str, mode):
        """Cria diretório"""
        raise FuseOSError(errno.EROFS)
    
    def unlink(self, path: str):
        """Remove arquivo"""
        raise FuseOSError(errno.EROFS)
    
    def rmdir(self, path: str):
        """Remove diretório"""
        raise FuseOSError(errno.EROFS)
    
    def symlink(self, target: str, source: str):
        """Cria link simbólico"""
        raise FuseOSError(errno.EROFS)
    
    def rename(self, old: str, new: str):
        """Renomeia arquivo"""
        raise FuseOSError(errno.EROFS)
    
    def link(self, target: str, source: str):
        """Cria hard link"""
        raise FuseOSError(errno.EROFS)
    
    def chmod(self, path: str, mode):
        """Altera permissões"""
        raise FuseOSError(errno.EROFS)
    
    def chown(self, path: str, uid, gid):
        """Altera proprietário"""
        raise FuseOSError(errno.EROFS)
    
    def truncate(self, path: str, length, fh=None):
        """Trunca arquivo"""
        raise FuseOSError(errno.EROFS)
    
    def write(self, path: str, buf, offset, fh):
        """Escreve no arquivo"""
        raise FuseOSError(errno.EROFS)
    
    def statfs(self, path: str) -> dict:
        """Retorna estatísticas do filesystem"""
        return {
            'f_bsize': 4096,
            'f_frsize': 4096,
            'f_blocks': 1024 * 1024 * 1024,  # 4TB virtual
            'f_bfree': 1024 * 1024 * 512,
            'f_bavail': 1024 * 1024 * 512,
            'f_files': 1000000,
            'f_ffree': 1000000,
            'f_favail': 1000000,
            'f_namemax': 255,
        }
    
    def flush(self, path: str, fh):
        """Flush buffers"""
        return 0
    
    def fsync(self, path: str, fdatasync, fh):
        """Sincroniza dados"""
        return 0
    
    def create(self, path: str, mode, fi=None):
        """Cria arquivo"""
        raise FuseOSError(errno.EROFS)


class FUSEManager:
    """Gerenciador do FUSE filesystem"""
    
    def __init__(self, bt_engine, native_bridge, cache, config):
        """
        Inicializa gerenciador FUSE
        
        Args:
            bt_engine: Instância do BTEngine
            native_bridge: Instância do NativeBridge
            cache: Instância do ReadAheadCache
            config: GoStreamConfig
        """
        self.bt_engine = bt_engine
        self.native_bridge = native_bridge
        self.cache = cache
        self.config = config
        
        self.filesystem: Optional[FUSEFilesystem] = None
        self.fuse_thread: Optional[Thread] = None
        self._shutdown_event = Event()
        
        if not FUSE_AVAILABLE:
            raise RuntimeError("fusepy não está instalado. Instale com: pip install fusepy")
    
    def start(self) -> bool:
        """Inicia o filesystem FUSE"""
        try:
            self.filesystem = FUSEFilesystem(
                self.bt_engine,
                self.native_bridge,
                self.cache,
                self.config.fuse_mount_path
            )
            
            # Inicia FUSE em thread separada
            self.fuse_thread = Thread(
                target=self._run_fuse,
                daemon=True
            )
            self.fuse_thread.start()
            
            logger.info(f"FUSE iniciado em {self.config.fuse_mount_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar FUSE: {e}")
            return False
    
    def _run_fuse(self):
        """Thread que executa o FUSE"""
        try:
            FUSE(
                self.filesystem,
                self.config.fuse_mount_path,
                nothreads=False,
                foreground=False,
                allow_other=True,
                default_permissions=True,
                # nonEmpty=True,  # Permite montar sobre diretório não-vazio
            )
        except Exception as e:
            logger.error(f"Erro no FUSE: {e}")
    
    def stop(self):
        """Para o filesystem FUSE"""
        self._shutdown_event.set()
        
        # Desmonta FUSE
        try:
            import subprocess
            subprocess.run(
                ['fusermount', '-u', self.config.fuse_mount_path],
                capture_output=True,
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Erro ao desmontar FUSE: {e}")
        
        if self.fuse_thread:
            self.fuse_thread.join(timeout=5)
        
        logger.info("FUSE parado")
    
    def refresh(self):
        """Atualiza árvore de diretórios"""
        if self.filesystem:
            self.filesystem._rebuild_tree()
