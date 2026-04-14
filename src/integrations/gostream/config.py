"""Configurações do GoStream Python"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class GoStreamConfig:
    """Configurações do GoStream BitTorrent Streaming Engine"""
    
    # Paths
    fuse_mount_path: str = field(default_factory=lambda: os.getenv('GOSTREAM_MOUNT_PATH', '/mnt/gostream'))
    cache_dir: str = field(default_factory=lambda: os.getenv('GOSTREAM_CACHE_DIR', './gostream_cache'))
    state_dir: str = field(default_factory=lambda: os.getenv('GOSTREAM_STATE_DIR', './gostream_state'))
    
    # BitTorrent Settings
    listen_port_start: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_PORT_START', 6881)))
    listen_port_end: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_PORT_END', 6889)))
    max_connections_per_torrent: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_MAX_CONNECTIONS', 100)))
    max_upload_slots: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_MAX_UPLOAD_SLOTS', 10)))
    download_rate_limit: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_DOWNLOAD_LIMIT', 0)))  # 0 = unlimited
    upload_rate_limit: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_UPLOAD_LIMIT', 0)))  # 0 = unlimited
    
    # Cache Settings
    read_ahead_budget_mb: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_READ_AHEAD_MB', 512)))
    num_cache_shards: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_CACHE_SHARDS', 32)))
    disk_warmup_quota_mb: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_DISK_WARMUP_MB', 2048)))
    
    # Streaming Settings
    master_concurrency_limit: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_CONCURRENCY_LIMIT', 25)))
    stream_buffer_size: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_BUFFER_SIZE', 1024 * 1024)))  # 1MB
    piece_timeout: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_PIECE_TIMEOUT', 30)))
    
    # API Settings
    api_host: str = field(default_factory=lambda: os.getenv('GOSTREAM_API_HOST', '0.0.0.0'))
    api_port: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_API_PORT', 8090)))
    api_enabled: bool = field(default_factory=lambda: os.getenv('GOSTREAM_API_ENABLED', 'true').lower() == 'true')
    
    # Jellyfin Integration
    jellyfin_webhook_enabled: bool = field(default_factory=lambda: os.getenv('GOSTREAM_JELLYFIN_WEBHOOK', 'true').lower() == 'true')
    jellyfin_webhook_port: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_WEBHOOK_PORT', 5001)))
    
    # Priority Mode
    priority_mode_timeout: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_PRIORITY_TIMEOUT', 3600)))  # 1 hour
    
    # Adaptive Shield (anti-corruption)
    adaptive_shield_enabled: bool = field(default_factory=lambda: os.getenv('GOSTREAM_ADAPTIVE_SHIELD', 'true').lower() == 'true')
    corruption_threshold: int = field(default_factory=lambda: int(os.getenv('GOSTREAM_CORRUPTION_THRESHOLD', 3)))
    
    # Responsive Mode
    responsive_mode: bool = field(default_factory=lambda: os.getenv('GOSTREAM_RESPONSIVE_MODE', 'true').lower() == 'true')
    
    # DHT/Bootstrap
    enable_dht: bool = field(default_factory=lambda: os.getenv('GOSTREAM_ENABLE_DHT', 'true').lower() == 'true')
    enable_lsd: bool = field(default_factory=lambda: os.getenv('GOSTREAM_ENABLE_LSD', 'true').lower() == 'true')
    enable_upnp: bool = field(default_factory=lambda: os.getenv('GOSTREAM_ENABLE_UPNP', 'true').lower() == 'true')
    enable_natpmp: bool = field(default_factory=lambda: os.getenv('GOSTREAM_ENABLE_NATPMP', 'true').lower() == 'true')
    
    def __post_init__(self):
        """Cria diretórios necessários"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)
        Path(self.fuse_mount_path).mkdir(parents=True, exist_ok=True)
    
    @property
    def read_ahead_budget_bytes(self) -> int:
        """Retorna orçamento de read-ahead em bytes"""
        return self.read_ahead_budget_mb * 1024 * 1024
    
    @property
    def disk_warmup_quota_bytes(self) -> int:
        """Retorna quota de disk warmup em bytes"""
        return self.disk_warmup_quota_mb * 1024 * 1024
    
    @property
    def cache_shard_size(self) -> int:
        """Retorna tamanho de cada shard do cache"""
        return self.read_ahead_budget_bytes // self.num_cache_shards
    
    def to_dict(self) -> dict:
        """Converte configuração para dicionário"""
        return {
            'fuse_mount_path': self.fuse_mount_path,
            'cache_dir': self.cache_dir,
            'state_dir': self.state_dir,
            'listen_port_start': self.listen_port_start,
            'listen_port_end': self.listen_port_end,
            'max_connections_per_torrent': self.max_connections_per_torrent,
            'max_upload_slots': self.max_upload_slots,
            'read_ahead_budget_mb': self.read_ahead_budget_mb,
            'num_cache_shards': self.num_cache_shards,
            'disk_warmup_quota_mb': self.disk_warmup_quota_mb,
            'master_concurrency_limit': self.master_concurrency_limit,
            'api_enabled': self.api_enabled,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'jellyfin_webhook_enabled': self.jellyfin_webhook_enabled,
            'adaptive_shield_enabled': self.adaptive_shield_enabled,
            'responsive_mode': self.responsive_mode,
            'enable_dht': self.enable_dht,
        }
