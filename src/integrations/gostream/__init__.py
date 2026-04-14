"""
GoStream Python - BitTorrent Streaming Engine com FUSE

Implementação em Python da tecnologia GoStream para streaming
direto de torrents via filesystem virtual FUSE.

Componentes principais:
- BTEngine: Engine BitTorrent usando libtorrent
- FUSEFilesystem: Camada FUSE para apresentar arquivos como locais
- NativeBridge: Ponte zero-copy entre FUSE e engine
- ReadAheadCache: Cache de pré-leitura em RAM
- StreamingAPI: API REST para controle e monitoramento
"""

from .bt_engine import BTEngine, TorrentInfo, PieceInfo
from .fuse_filesystem import FUSEFilesystem, VirtualFileNode
from .native_bridge import NativeBridge, StreamHandle
from .read_ahead_cache import ReadAheadCache
from .streaming_api import create_api_app, StreamingAPI
from .config import GoStreamConfig
from .manager import GoStreamManager, create_gostream

__version__ = "0.1.0"
__all__ = [
    "BTEngine",
    "TorrentInfo",
    "PieceInfo",
    "FUSEFilesystem",
    "VirtualFileNode",
    "NativeBridge",
    "StreamHandle",
    "ReadAheadCache",
    "create_api_app",
    "StreamingAPI",
    "GoStreamConfig",
    "GoStreamManager",
    "create_gostream",
]
