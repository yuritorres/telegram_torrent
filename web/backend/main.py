#!/usr/bin/env python3
"""
Web API Backend for Telegram Torrent Manager
FastAPI-based REST API with WebSocket support
Self-contained: no imports from the main project's src package.
"""
import os
import json
import yaml
import requests as req_lib
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
import psutil
import platform
import socket

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    generate_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from telegram_storage import TelegramStorageService
from user_manager import UserManager
from middleware import (
    RequestIDMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
)
from health import health_monitor, HealthResponse
from shutdown import shutdown_manager

# ---------------------------------------------------------------------------
# Configuration (read directly from environment variables)
# ---------------------------------------------------------------------------
QB_NAMES = os.getenv('QB_NAMES', 'default')
QB_URLS = os.getenv('QB_URLS', os.getenv('QB_URL', 'http://localhost:8080'))
QB_USERS = os.getenv('QB_USERS', os.getenv('QB_USER', 'admin'))
QB_PASSWORDS = os.getenv('QB_PASSWORDS', os.getenv('QB_PASS', 'adminadmin'))

JELLYFIN_URL = os.getenv('JELLYFIN_URL', '')
JELLYFIN_USERNAME = os.getenv('JELLYFIN_USERNAME', '')
JELLYFIN_PASSWORD = os.getenv('JELLYFIN_PASSWORD', '')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY', '')


def parse_jellyfin_accounts() -> List[Dict]:
    urls = [u.strip() for u in JELLYFIN_URL.split(',') if u.strip()]
    usernames = [u.strip() for u in JELLYFIN_USERNAME.split(',') if u.strip()]
    passwords = [p.strip() for p in JELLYFIN_PASSWORD.split(',') if p.strip()]
    api_keys = [k.strip() for k in JELLYFIN_API_KEY.split(',') if k.strip()]
    accounts = []
    for i in range(len(urls)):
        accounts.append({
            'url': urls[i],
            'username': usernames[i] if i < len(usernames) else '',
            'password': passwords[i] if i < len(passwords) else '',
            'api_key': api_keys[i] if i < len(api_keys) else '',
        })
    return accounts


JELLYFIN_ACCOUNTS = parse_jellyfin_accounts()
JELLYFIN_MULTI_ACCOUNT = len(JELLYFIN_ACCOUNTS) > 1


def parse_qb_instances() -> List[Dict]:
    names = [n.strip() for n in QB_NAMES.split(',') if n.strip()]
    urls = [u.strip() for u in QB_URLS.split(',') if u.strip()]
    users = [u.strip() for u in QB_USERS.split(',') if u.strip()]
    passwords = [p.strip() for p in QB_PASSWORDS.split(',') if p.strip()]
    instances = []
    for i in range(len(urls)):
        instances.append({
            'name': names[i] if i < len(names) else f'instance-{i+1}',
            'url': urls[i],
            'username': users[i] if i < len(users) else 'admin',
            'password': passwords[i] if i < len(passwords) else 'adminadmin',
        })
    return instances


QB_INSTANCES = parse_qb_instances()
QB_MULTI_INSTANCE = len(QB_INSTANCES) > 1

# GoStream Configuration
GOSTREAM_ENABLED = os.getenv('GOSTREAM_ENABLED', 'false').lower() == 'true'
GOSTREAM_API_HOST = os.getenv('GOSTREAM_API_HOST', 'localhost')
GOSTREAM_API_PORT = int(os.getenv('GOSTREAM_API_PORT', '8090'))
GOSTREAM_MOUNT_PATH = os.getenv('GOSTREAM_MOUNT_PATH', '/mnt/gostream')
GOSTREAM_WEBHOOK_PORT = int(os.getenv('GOSTREAM_WEBHOOK_PORT', '5001'))

# ---------------------------------------------------------------------------
# GoStream Client
# ---------------------------------------------------------------------------

class GoStreamClient:
    """Client for GoStream BitTorrent Streaming Engine"""
    
    def __init__(self, host: str = 'localhost', port: int = 8090, mount_path: str = '/mnt/gostream'):
        self.base_url = f"http://{host}:{port}"
        self.mount_path = mount_path
        self.enabled = GOSTREAM_ENABLED
    
    def is_available(self) -> bool:
        """Check if GoStream API is available"""
        if not self.enabled:
            return False
        try:
            resp = req_lib.get(f"{self.base_url}/api/health", timeout=2)
            return resp.status_code == 200 and resp.json().get('success', False)
        except Exception:
            return False
    
    def list_torrents(self) -> List[Dict]:
        """List all torrents from GoStream"""
        try:
            resp = req_lib.get(f"{self.base_url}/api/torrents", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('torrents', [])
        except Exception as e:
            logger.error(f"GoStream list_torrents error: {e}")
        return []
    
    def get_torrent(self, info_hash: str) -> Optional[Dict]:
        """Get torrent details"""
        try:
            resp = req_lib.get(f"{self.base_url}/api/torrents/{info_hash}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('torrent')
        except Exception as e:
            logger.error(f"GoStream get_torrent error: {e}")
        return None
    
    def add_torrent(self, magnet_link: str, save_path: str = None) -> Optional[str]:
        """Add torrent via magnet link"""
        try:
            data = {"magnet": magnet_link}
            if save_path:
                data["save_path"] = save_path
            resp = req_lib.post(f"{self.base_url}/api/torrents/add", json=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success'):
                    return result.get('info_hash')
        except Exception as e:
            logger.error(f"GoStream add_torrent error: {e}")
        return None
    
    def remove_torrent(self, info_hash: str, delete_files: bool = False) -> bool:
        """Remove torrent"""
        try:
            data = {"delete_files": delete_files}
            resp = req_lib.post(f"{self.base_url}/api/torrents/{info_hash}/remove", json=data, timeout=10)
            if resp.status_code == 200:
                return resp.json().get('success', False)
        except Exception as e:
            logger.error(f"GoStream remove_torrent error: {e}")
        return False
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            resp = req_lib.get(f"{self.base_url}/api/cache/stats", timeout=5)
            if resp.status_code == 200:
                return resp.json().get('stats', {})
        except Exception as e:
            logger.error(f"GoStream cache stats error: {e}")
        return {}
    
    def set_priority_mode(self, info_hash: str, enabled: bool = True) -> bool:
        """Enable/disable priority mode for torrent"""
        try:
            data = {"enabled": enabled}
            resp = req_lib.post(f"{self.base_url}/api/torrents/{info_hash}/priority", json=data, timeout=5)
            if resp.status_code == 200:
                return resp.json().get('success', False)
        except Exception as e:
            logger.error(f"GoStream priority mode error: {e}")
        return False
    
    def get_streaming_files(self, info_hash: str) -> List[Dict]:
        """Retorna lista de arquivos streamáveis de um torrent"""
        try:
            # Usa o endpoint específico de arquivos
            resp = requests.get(f"{self.base_url}/api/torrents/{info_hash}/files", timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Failed to get files from GoStream API: {resp.status_code}")
                return []
            
            data = resp.json()
            if not data.get('success'):
                return []
            
            files = data.get('files', [])
            # Filtra apenas arquivos de vídeo
            video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
            streamable = []
            for f in files:
                path = f.get('path', '')
                if any(path.lower().endswith(ext) for ext in video_exts):
                    streamable.append({
                        'name': os.path.basename(path),
                        'path': path,
                        'size': f.get('size', 0),
                        'offset': f.get('offset', 0)
                    })
            return streamable
        except Exception as e:
            logger.error(f"Error getting streaming files: {e}")
            return []

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        return name[:255]
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

# Initialize GoStream client
gostream_client = GoStreamClient(
    host=GOSTREAM_API_HOST,
    port=GOSTREAM_API_PORT,
    mount_path=GOSTREAM_MOUNT_PATH
)

# ---------------------------------------------------------------------------
# Lightweight qBittorrent helpers (no external src dependency)
# ---------------------------------------------------------------------------

def qb_login(url: str, user: str, password: str) -> Optional[req_lib.Session]:
    session = req_lib.Session()
    try:
        resp = session.post(
            f"{url}/api/v2/auth/login",
            data={"username": user, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
        if resp.text == "Ok.":
            logger.info(f"qBittorrent login OK: {url}")
            return session
        logger.error(f"qBittorrent login failed ({url}): {resp.text}")
        return None
    except Exception as e:
        logger.error(f"qBittorrent connection error ({url}): {e}")
        return None


def qb_fetch_torrents(session: req_lib.Session, url: str) -> List[Dict]:
    try:
        resp = session.get(f"{url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error fetching torrents from {url}: {e}")
        return []


def qb_add_magnet(session: req_lib.Session, url: str, magnet: str) -> bool:
    try:
        resp = session.post(f"{url}/api/v2/torrents/add", data={"urls": magnet}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error adding magnet: {e}")
        return False


def qb_action(session: req_lib.Session, url: str, action: str, torrent_hash: str, **extra) -> bool:
    try:
        data = {"hashes": torrent_hash, **extra}
        resp = session.post(f"{url}/api/v2/torrents/{action}", data=data, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error {action} torrent {torrent_hash}: {e}")
        return False


def qb_get_storage_info(session: req_lib.Session, url: str) -> Dict:
    """Obtém informações de armazenamento de uma instância do qBittorrent"""
    try:
        # Obter informações do servidor
        resp = session.get(f"{url}/api/v2/sync/maindata", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        server_state = data.get("server_state", {})
        free_space = server_state.get("free_space_on_disk", 0)
        
        # Obter todos os torrents para calcular espaço usado
        torrents_resp = session.get(f"{url}/api/v2/torrents/info", timeout=10)
        torrents_resp.raise_for_status()
        torrents = torrents_resp.json()
        
        # Somar o tamanho de todos os torrents
        used_space = sum(torrent.get("size", 0) for torrent in torrents)
        total_space = free_space + used_space
        
        return {
            "total": total_space,
            "used": used_space,
            "free": free_space,
        }
    except Exception as e:
        logger.error(f"Error getting storage info from {url}: {e}")
        return {"total": 0, "used": 0, "free": 0}

# ---------------------------------------------------------------------------
# Lightweight Jellyfin helpers
# ---------------------------------------------------------------------------

class JellyfinClient:
    """Cliente individual para uma conta Jellyfin"""
    def __init__(self, url: str, username: str = '', password: str = '', api_key: str = ''):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.access_token = None
        self.user_id = None
        self.session = req_lib.Session()
        self._available = False

        if self.url:
            if username and password:
                self._authenticate(username, password)
            if self.api_key or self.access_token:
                self._available = True

    def _headers(self) -> Dict:
        h = {'Content-Type': 'application/json'}
        token = self.api_key or self.access_token
        if token:
            h['X-Emby-Token'] = token
        return h

    def _authenticate(self, username: str, password: str):
        try:
            auth_header = 'MediaBrowser Client="TelegramTorrent", Device="Server", DeviceId="unique-device-id", Version="1.0.0"'
            resp = self.session.post(
                f"{self.url}/Users/authenticatebyname",
                headers={
                    'Content-Type': 'application/json',
                    'X-Emby-Authorization': auth_header
                },
                json={'Username': username, 'Password': password},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get('AccessToken')
            self.user_id = data.get('User', {}).get('Id')
            logger.info("Jellyfin authentication OK")
        except Exception as e:
            logger.error(f"Jellyfin auth error: {e}")
            try:
                logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            except:
                pass

    def is_available(self) -> bool:
        return self._available

    def get_libraries(self) -> List[Dict]:
        if not self._available:
            return []
        try:
            resp = self.session.get(f"{self.url}/Library/VirtualFolders", headers=self._headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Jellyfin libraries error: {e}")
            return []

    def get_recent_items(self, limit: int = 10) -> List[Dict]:
        if not self._available:
            return []
        params = {
            'Limit': limit,
            'Recursive': True,
            'IncludeItemTypes': 'Movie,Series',
            'SortBy': 'DateCreated',
            'SortOrder': 'Descending',
        }
        try:
            endpoint = f"/Users/{self.user_id}/Items" if self.user_id else "/Items"
            resp = self.session.get(f"{self.url}{endpoint}", headers=self._headers(), params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get('Items', [])
        except Exception as e:
            logger.error(f"Jellyfin recent items error: {e}")
            return []

    def get_item(self, item_id: str) -> Optional[Dict]:
        if not self._available:
            return None
        try:
            endpoint = f"/Users/{self.user_id}/Items/{item_id}" if self.user_id else f"/Items/{item_id}"
            resp = self.session.get(f"{self.url}{endpoint}", headers=self._headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Jellyfin get item error: {e}")
            return None

    def get_seasons(self, series_id: str) -> List[Dict]:
        if not self._available:
            return []
        try:
            params = {}
            if self.user_id:
                params['userId'] = self.user_id
            resp = self.session.get(
                f"{self.url}/Shows/{series_id}/Seasons",
                headers=self._headers(), params=params, timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get('Items', [])
        except Exception as e:
            logger.error(f"Jellyfin get seasons error: {e}")
            return []

    def get_episodes(self, series_id: str, season_id: str = None) -> List[Dict]:
        if not self._available:
            return []
        try:
            params = {'Recursive': True}
            if self.user_id:
                params['userId'] = self.user_id
            if season_id:
                params['seasonId'] = season_id
            resp = self.session.get(
                f"{self.url}/Shows/{series_id}/Episodes",
                headers=self._headers(), params=params, timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get('Items', [])
        except Exception as e:
            logger.error(f"Jellyfin get episodes error: {e}")
            return []

    def get_playback_info(self, item_id: str) -> Optional[Dict]:
        if not self._available:
            return None
        try:
            params = {}
            if self.user_id:
                params['userId'] = self.user_id
            resp = self.session.get(
                f"{self.url}/Items/{item_id}/PlaybackInfo",
                headers=self._headers(), params=params, timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Jellyfin playback info error: {e}")
            return None

    def get_stream_url(self, item_id: str, audio_stream_index: int = None) -> str:
        token = self.api_key or self.access_token or ''
        # Always request transcoded/decoded stream from Jellyfin
        # Jellyfin will automatically transcode EAC3 to AAC for browser compatibility
        # static=false allows Jellyfin to transcode when needed
        url = f"{self.url}/Videos/{item_id}/stream?static=false&api_key={token}&AudioCodec=aac&AudioBitrate=384000&MaxAudioChannels=2&VideoCodec=h264,hevc&VideoBitrate=120000000"
        if audio_stream_index is not None:
            url += f"&AudioStreamIndex={audio_stream_index}"
        return url

    def get_transcode_url(self, item_id: str, audio_stream_index: int = None) -> str:
        # Same as get_stream_url - always use transcoded output
        return self.get_stream_url(item_id, audio_stream_index)

    def get_subtitle_url(self, item_id: str, media_source_id: str, index: int) -> str:
        token = self.api_key or self.access_token or ''
        return f"{self.url}/Videos/{item_id}/{media_source_id}/Subtitles/{index}/0/Stream.vtt?api_key={token}"

    def get_image_url(self, item_id: str, image_type: str = 'Primary', max_width: int = 300) -> str:
        token = self.api_key or self.access_token or ''
        return f"{self.url}/Items/{item_id}/Images/{image_type}?maxWidth={max_width}&api_key={token}"


class JellyfinHelper:
    """Gerenciador de múltiplas contas Jellyfin para o web backend"""
    def __init__(self):
        self.clients: List[JellyfinClient] = []
        self.multi_account = JELLYFIN_MULTI_ACCOUNT
        
        for account in JELLYFIN_ACCOUNTS:
            url = account.get('url')
            if url:
                client = JellyfinClient(
                    url=url,
                    username=account.get('username', ''),
                    password=account.get('password', ''),
                    api_key=account.get('api_key', '')
                )
                if client.is_available():
                    self.clients.append(client)
                    logger.info(f"Jellyfin client initialized: {url}")
        
        if not self.clients:
            logger.warning("No Jellyfin accounts configured or available")
        else:
            logger.info(f"JellyfinHelper initialized with {len(self.clients)} account(s)")
    
    @property
    def client(self) -> Optional[JellyfinClient]:
        """Retorna o primeiro cliente disponível (compatibilidade)"""
        return self.clients[0] if self.clients else None
    
    def is_available(self) -> bool:
        return len(self.clients) > 0
    
    def get_libraries(self) -> List[Dict]:
        all_libraries = []
        for client in self.clients:
            try:
                libraries = client.get_libraries()
                for lib in libraries:
                    lib['_jellyfin_url'] = client.url
                all_libraries.extend(libraries)
            except Exception as e:
                logger.error(f"Error getting libraries from {client.url}: {e}")
        return all_libraries
    
    def get_recent_items(self, limit: int = 10) -> List[Dict]:
        all_items = []
        num_clients = len(self.clients)
        
        if num_clients == 0:
            return []
        
        # Busca mais itens de cada servidor para garantir variedade após ordenação
        per_client_limit = max(limit, limit * 2 // num_clients) if num_clients > 1 else limit
        
        for client in self.clients:
            try:
                items = client.get_recent_items(per_client_limit)
                for item in items:
                    item['_jellyfin_url'] = client.url
                all_items.extend(items)
            except Exception as e:
                logger.error(f"Error getting recent items from {client.url}: {e}")
        
        # Ordena por data de criação e retorna mais itens quando há múltiplos servidores
        all_items.sort(key=lambda x: x.get('DateCreated', ''), reverse=True)
        final_limit = limit * num_clients if num_clients > 1 else limit
        return all_items[:final_limit]
    
    def get_item(self, item_id: str, server_url: str = None) -> Optional[Dict]:
        """Busca um item específico. Se server_url for fornecido, busca apenas naquele servidor."""
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        
        for client in clients_to_search:
            try:
                item = client.get_item(item_id)
                if item:
                    item['_jellyfin_url'] = client.url
                    return item
            except Exception as e:
                logger.error(f"Error getting item from {client.url}: {e}")
        return None
    
    def get_seasons(self, series_id: str, server_url: str = None) -> List[Dict]:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        
        for client in clients_to_search:
            try:
                seasons = client.get_seasons(series_id)
                if seasons:
                    for season in seasons:
                        season['_jellyfin_url'] = client.url
                    return seasons
            except Exception as e:
                logger.error(f"Error getting seasons from {client.url}: {e}")
        return []
    
    def get_episodes(self, series_id: str, season_id: str = None, server_url: str = None) -> List[Dict]:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        
        for client in clients_to_search:
            try:
                episodes = client.get_episodes(series_id, season_id)
                if episodes:
                    for episode in episodes:
                        episode['_jellyfin_url'] = client.url
                    return episodes
            except Exception as e:
                logger.error(f"Error getting episodes from {client.url}: {e}")
        return []
    
    def get_playback_info(self, item_id: str, server_url: str = None) -> Optional[Dict]:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        
        for client in clients_to_search:
            try:
                info = client.get_playback_info(item_id)
                if info:
                    return info
            except Exception as e:
                logger.error(f"Error getting playback info from {client.url}: {e}")
        return None
    
    def get_stream_url(self, item_id: str, server_url: str = None, audio_stream_index: int = None) -> str:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        if clients_to_search:
            return clients_to_search[0].get_stream_url(item_id, audio_stream_index)
        return ''
    
    def get_transcode_url(self, item_id: str, server_url: str = None, audio_stream_index: int = None) -> str:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        if clients_to_search:
            return clients_to_search[0].get_transcode_url(item_id, audio_stream_index)
        return ''
    
    def get_subtitle_url(self, item_id: str, media_source_id: str, index: int, server_url: str = None) -> str:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        if clients_to_search:
            return clients_to_search[0].get_subtitle_url(item_id, media_source_id, index)
        return ''
    
    def get_image_url(self, item_id: str, image_type: str = 'Primary', max_width: int = 300, server_url: str = None) -> str:
        clients_to_search = [c for c in self.clients if c.url == server_url] if server_url else self.clients
        if clients_to_search:
            return clients_to_search[0].get_image_url(item_id, image_type, max_width)
        return ''

# ---------------------------------------------------------------------------
# Docker Management (using advanced DockerManager)
# ---------------------------------------------------------------------------

from docker_manager import DockerManager

def init_docker_manager() -> Optional[DockerManager]:
    """Initialize Docker manager with error handling"""
    try:
        import docker
        client = docker.from_env()
        manager = DockerManager(client)
        logger.info("Docker manager initialized")
        return manager
    except Exception as e:
        logger.warning(f"Docker not available: {e}")
        return None

# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------

from user_manager import UserManager

class AppState:
    def __init__(self):
        self.qb_sessions: List[Dict] = []
        self.jellyfin: Optional[JellyfinHelper] = None
        self.docker: Optional[DockerManager] = None
        self.telegram_storage: Optional[TelegramStorageService] = None
        self.user_manager: Optional[UserManager] = None
        self.gostream: Optional[GoStreamClient] = None

app_state = AppState()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Web API Backend...")
    logger.info(f"Application version: {health_monitor.version}")
    
    # Setup signal handlers for graceful shutdown
    shutdown_manager.setup_signal_handlers()

    # Initialize qBittorrent sessions
    for inst in QB_INSTANCES:
        session = qb_login(inst['url'], inst['username'], inst['password'])
        app_state.qb_sessions.append({
            'name': inst['name'],
            'url': inst['url'],
            'session': session,
        })
        if session:
            logger.info(f"qBittorrent connected: {inst['name']} ({inst['url']})")

    # Initialize Jellyfin
    try:
        app_state.jellyfin = JellyfinHelper()
        if app_state.jellyfin.is_available():
            logger.info(f"Jellyfin initialized with {len(app_state.jellyfin.clients)} account(s)")
    except Exception as e:
        logger.error(f"Jellyfin init error: {e}")

    # Initialize Docker Manager
    try:
        app_state.docker = init_docker_manager()
        if app_state.docker and app_state.docker.is_available():
            system_info = app_state.docker.get_system_info()
            if system_info:
                logger.info(f"Docker manager initialized: {system_info['containers']} containers, "
                          f"Docker {system_info['docker_version']}")
    except Exception as e:
        logger.error(f"Docker init error: {e}")

    # Initialize Telegram Storage
    try:
        app_state.telegram_storage = TelegramStorageService()
        logger.info("Telegram Storage initialized")
    except Exception as e:
        logger.error(f"Telegram Storage init error: {e}")

    # Initialize User Manager
    try:
        app_state.user_manager = UserManager()
        logger.info("User Manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize User Manager: {e}")

    # Initialize GoStream client reference
    try:
        app_state.gostream = gostream_client
        if gostream_client.is_available():
            logger.info(f"GoStream connected at {GOSTREAM_API_HOST}:{GOSTREAM_API_PORT}")
        elif GOSTREAM_ENABLED:
            logger.warning(f"GoStream enabled but not available at {GOSTREAM_API_HOST}:{GOSTREAM_API_PORT}")
        else:
            logger.info("GoStream disabled (GOSTREAM_ENABLED=false)")
    except Exception as e:
        logger.error(f"GoStream init error: {e}")

    # Start background tasks
    broadcast_task = asyncio.create_task(broadcast_updates())
    
    # Register cleanup handlers
    async def cleanup():
        logger.info("Cleaning up resources...")
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        # Close qBittorrent sessions
        for inst in app_state.qb_sessions:
            if inst['session']:
                inst['session'].close()
        logger.info("Cleanup completed")
    
    shutdown_manager.register_handler(cleanup)
    
    logger.info("Web API Backend started successfully")
    logger.info(f"Uptime tracking started at {datetime.now().isoformat()}")
    
    yield
    
    # Graceful shutdown
    logger.info("Shutting down Web API Backend...")
    await shutdown_manager.shutdown()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Telegram Torrent Manager API",
    description="Web-based management interface for torrent and media server",
    version="1.0.0",
    lifespan=lifespan,
)

# Include advanced Docker routes
import docker_routes
docker_routes.set_app_state(app_state)
app.include_router(docker_routes.router)

# Add middlewares in correct order (last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# ---------------------------------------------------------------------------
# GoStream Routes
# ---------------------------------------------------------------------------

@app.get("/api/gostream/status")
async def gostream_status(current_user: Dict = Depends(get_current_user_optional)):
    """Get GoStream status and availability"""
    is_available = gostream_client.is_available()
    return {
        "enabled": GOSTREAM_ENABLED,
        "available": is_available,
        "api_host": GOSTREAM_API_HOST,
        "api_port": GOSTREAM_API_PORT,
        "mount_path": GOSTREAM_MOUNT_PATH,
    }

@app.get("/api/gostream/torrents")
async def gostream_list_torrents(current_user: Dict = Depends(get_current_user_optional)):
    """List all GoStream torrents"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        torrents = gostream_client.list_torrents()
        return {"success": True, "torrents": torrents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing GoStream torrents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gostream/torrents/{info_hash}")
async def gostream_get_torrent(info_hash: str, current_user: Dict = Depends(get_current_user_optional)):
    """Get GoStream torrent details with streamable files"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        torrent = gostream_client.get_torrent(info_hash)
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        # Get streamable files
        streamable_files = gostream_client.get_streaming_files(info_hash)
        
        return {
            "success": True,
            "torrent": torrent,
            "streamable_files": streamable_files,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GoStream torrent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gostream/torrents/add")
async def gostream_add_torrent(magnet_link: str, current_user: Dict = Depends(get_current_user)):
    """Add torrent to GoStream via magnet link"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        info_hash = gostream_client.add_torrent(magnet_link)
        if not info_hash:
            raise HTTPException(status_code=500, detail="Failed to add torrent")
        
        return {
            "success": True,
            "info_hash": info_hash,
            "message": "Torrent added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding GoStream torrent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/gostream/torrents/{info_hash}")
async def gostream_remove_torrent(info_hash: str, delete_files: bool = False, current_user: Dict = Depends(get_current_user)):
    """Remove torrent from GoStream"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        success = gostream_client.remove_torrent(info_hash, delete_files)
        if not success:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        return {"success": True, "message": "Torrent removed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing GoStream torrent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gostream/torrents/{info_hash}/priority")
async def gostream_set_priority(info_hash: str, enabled: bool = True, current_user: Dict = Depends(get_current_user)):
    """Set priority mode for GoStream torrent"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        success = gostream_client.set_priority_mode(info_hash, enabled)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set priority mode")
        
        return {
            "success": True,
            "info_hash": info_hash,
            "priority_mode": enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting GoStream priority: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gostream/cache/stats")
async def gostream_cache_stats(current_user: Dict = Depends(get_current_user_optional)):
    """Get GoStream cache statistics"""
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        stats = gostream_client.get_cache_stats()
        return {"success": True, "stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GoStream cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gostream/stream/{info_hash}/{file_index}")
async def gostream_stream_proxy(
    info_hash: str, 
    file_index: int, 
    request: Request,
    current_user: Dict = Depends(get_current_user_optional)
):
    """
    Proxy stream from GoStream FUSE filesystem.
    This endpoint serves video files directly from the FUSE mount.
    """
    try:
        if not gostream_client.is_available():
            raise HTTPException(status_code=503, detail="GoStream not available")
        
        # Get torrent and verify file exists
        torrent = gostream_client.get_torrent(info_hash)
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")
        
        files = torrent.get('files', [])
        if file_index >= len(files):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = files[file_index]
        
        # Get streaming files info
        streamable = gostream_client.get_streaming_files(info_hash)
        stream_info = next((s for s in streamable if s['index'] == file_index), None)
        
        if not stream_info:
            raise HTTPException(status_code=404, detail="Streamable file not found")
        
        # Activate priority mode when streaming starts
        gostream_client.set_priority_mode(info_hash, True)
        
        # Build the actual file path from FUSE mount
        file_path = stream_info['direct_path']
        
        # Check if file exists and get its size
        import os
        if not os.path.exists(file_path):
            # File might not be fully mounted yet, return streaming URL from GoStream API
            # Redirect to the actual streaming via GoStream
            return {
                "success": True,
                "stream_type": "gostream_direct",
                "info_hash": info_hash,
                "file_index": file_index,
                "file_name": stream_info['name'],
                "file_size": stream_info['size'],
                "priority_mode": True,
                "message": "Use the Jellyfin integration or mount point for streaming"
            }
        
        # File exists, serve it directly
        file_size = os.path.getsize(file_path)
        
        # Handle range requests for video streaming
        range_header = request.headers.get('range')
        
        if range_header:
            # Parse range header
            range_value = range_header.replace('bytes=', '').split('-')
            start = int(range_value[0]) if range_value[0] else 0
            end = int(range_value[1]) if range_value[1] else file_size - 1
            
            # Read file chunk
            with open(file_path, 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)
            
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(len(data)),
                'Content-Type': 'video/mp4',
            }
            
            return StreamingResponse(
                iter([data]),
                status_code=206,
                headers=headers,
                media_type="video/mp4"
            )
        else:
            # Full file request (for small files or direct download)
            def file_generator():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        yield chunk
            
            headers = {
                'Accept-Ranges': 'bytes',
                'Content-Length': str(file_size),
                'Content-Type': 'video/mp4',
                'Content-Disposition': f'inline; filename="{stream_info["name"]}"',
            }
            
            return StreamingResponse(
                file_generator(),
                headers=headers,
                media_type="video/mp4"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming GoStream file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def broadcast_updates():
    while True:
        try:
            torrents_data = get_all_torrents()
            if torrents_data:
                await ws_manager.broadcast({
                    "type": "torrents_update",
                    "data": torrents_data,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        await asyncio.sleep(5)


def get_all_torrents() -> List[Dict]:
    all_torrents = []
    for inst in app_state.qb_sessions:
        if inst['session'] is None:
            continue
        torrents = qb_fetch_torrents(inst['session'], inst['url'])
        for t in torrents:
            t['instance'] = inst['name']
        all_torrents.extend(torrents)
    return all_torrents


def get_first_session():
    for inst in app_state.qb_sessions:
        if inst['session'] is not None:
            return inst
    return None

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class PasswordHashRequest(BaseModel):
    password: str

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"name": "Telegram Torrent Manager API", "version": "1.0.0", "status": "running"}


@app.get("/api/health", response_model=HealthResponse)
@app.head("/api/health")
async def health_check(include_system: bool = False):
    """
    Comprehensive health check endpoint
    Returns application health status, uptime, and service availability
    """
    qb_connected = any(i['session'] is not None for i in app_state.qb_sessions)
    jellyfin_connected = app_state.jellyfin is not None and app_state.jellyfin.is_available()
    docker_available = app_state.docker is not None and app_state.docker.is_available()
    telegram_storage_available = app_state.telegram_storage is not None
    
    return health_monitor.get_health_status(
        qb_connected=qb_connected,
        jellyfin_connected=jellyfin_connected,
        docker_available=docker_available,
        telegram_storage_available=telegram_storage_available,
        include_system=include_system
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.post("/api/auth/generate-hash")
async def generate_hash(request: PasswordHashRequest):
    """Generate password hash for configuration (utility endpoint)"""
    return {"password_hash": generate_password_hash(request.password)}


@app.get("/api/auth/verify")
async def verify_auth(current_user: Dict = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {"authenticated": True, "username": current_user["username"]}


@app.get("/api/system/status")
async def get_system_status(current_user: Dict = Depends(get_current_user)):
    connected_qb = any(i['session'] is not None for i in app_state.qb_sessions)
    
    # Coletar informações de armazenamento de todas as instâncias
    total_storage = 0
    used_storage = 0
    free_storage = 0
    
    for inst in app_state.qb_sessions:
        if inst['session'] is not None:
            storage_info = qb_get_storage_info(inst['session'], inst['url'])
            total_storage += storage_info['total']
            used_storage += storage_info['used']
            free_storage += storage_info['free']
    
    return {
        "qbittorrent": {
            "connected": connected_qb,
            "multi_instance": QB_MULTI_INSTANCE,
            "instances": len(QB_INSTANCES),
        },
        "jellyfin": {
            "connected": app_state.jellyfin is not None and app_state.jellyfin.is_available(),
            "url": JELLYFIN_URL,
        },
        "docker": {
            "available": app_state.docker is not None and app_state.docker.is_available(),
        },
        "storage": {
            "total": total_storage,
            "used": used_storage,
            "free": free_storage,
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/torrents")
async def get_torrents(current_user: Dict = Depends(get_current_user)):
    try:
        torrents = get_all_torrents()
        active = [t for t in torrents if t.get('state') in ['downloading', 'uploading', 'stalledDL', 'stalledUP']]
        paused = [t for t in torrents if t.get('state') == 'pausedDL']
        completed = [t for t in torrents if t.get('state') in ['uploading', 'pausedUP']]
        error = [t for t in torrents if 'error' in t.get('state', '').lower()]
        return {
            "total": len(torrents),
            "active": len(active),
            "paused": len(paused),
            "completed": len(completed),
            "error": len(error),
            "torrents": torrents,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/torrents/add")
async def add_torrent(magnet_link: str, current_user: Dict = Depends(get_current_user)):
    try:
        inst = get_first_session()
        if inst:
            result = qb_add_magnet(inst['session'], inst['url'], magnet_link)
            return {"success": result, "instance": inst['name']}
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/torrents/{torrent_hash}/pause")
async def pause_torrent(torrent_hash: str, current_user: Dict = Depends(get_current_user)):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'pause', torrent_hash)
    return {"success": ok}


@app.post("/api/torrents/{torrent_hash}/resume")
async def resume_torrent(torrent_hash: str, current_user: Dict = Depends(get_current_user)):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'resume', torrent_hash)
    return {"success": ok}


@app.delete("/api/torrents/{torrent_hash}")
async def delete_torrent(torrent_hash: str, delete_files: bool = False, current_user: Dict = Depends(get_current_user)):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'delete', torrent_hash, deleteFiles=str(delete_files).lower())
    return {"success": ok}


@app.get("/api/jellyfin/libraries")
async def get_jellyfin_libraries(current_user: Dict = Depends(get_current_user)):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"libraries": app_state.jellyfin.get_libraries()}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/recent")
async def get_jellyfin_recent(limit: int = 10, current_user: Dict = Depends(get_current_user)):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_recent_items(limit=limit)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/items/{item_id}")
async def get_jellyfin_item(item_id: str, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        item = app_state.jellyfin.get_item(item_id, server_url)
        if item:
            return item
        raise HTTPException(status_code=404, detail="Item not found")
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/shows/{series_id}/seasons")
async def get_jellyfin_seasons(series_id: str, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_seasons(series_id, server_url)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/shows/{series_id}/episodes")
async def get_jellyfin_episodes(series_id: str, season_id: str = None, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_episodes(series_id, season_id, server_url)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/image/{item_id}")
async def get_jellyfin_image(item_id: str, type: str = "Primary", maxWidth: int = 300, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    image_url = jf.get_image_url(item_id, image_type=type, max_width=maxWidth, server_url=server_url)
    if not image_url:
        raise HTTPException(status_code=404, detail="Image not found - server not available")
    try:
        resp = req_lib.get(image_url, stream=True, timeout=30)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Image not found")
        resp.raise_for_status()
        return StreamingResponse(
            resp.iter_content(chunk_size=65536),
            media_type=resp.headers.get('Content-Type', 'image/jpeg'),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/jellyfin/playback-info/{item_id}")
async def get_jellyfin_playback_info(item_id: str, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    info = app_state.jellyfin.get_playback_info(item_id, server_url)
    if info:
        return info
    raise HTTPException(status_code=404, detail="Playback info not found")


@app.get("/api/jellyfin/subtitles/{item_id}/{media_source_id}/{index}")
async def get_jellyfin_subtitle(item_id: str, media_source_id: str, index: int, server_url: str = None, current_user: Dict = Depends(get_current_user)):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    sub_url = jf.get_subtitle_url(item_id, media_source_id, index, server_url)
    if not sub_url:
        raise HTTPException(status_code=404, detail="Subtitle not found - server not available")
    try:
        resp = req_lib.get(sub_url, stream=True, timeout=30)
        resp.raise_for_status()
        return StreamingResponse(
            resp.iter_content(chunk_size=65536),
            media_type='text/vtt',
            headers={'Content-Disposition': f'inline; filename="subtitle_{index}.vtt"'},
        )
    except Exception as e:
        logger.error(f"Jellyfin subtitle error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/jellyfin/stream/{item_id}")
async def stream_jellyfin(item_id: str, request: Request, audioStreamIndex: int = None, server_url: str = None, token: str = None, transcode: bool = False, current_user: Dict = Depends(get_current_user_optional)):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    
    # If transcode is requested, use transcoding endpoint
    if transcode:
        stream_url = jf.get_transcode_url(item_id, server_url=server_url, audio_stream_index=audioStreamIndex)
    else:
        stream_url = jf.get_stream_url(item_id, server_url=server_url, audio_stream_index=audioStreamIndex)
    
    headers = {}
    if 'range' in request.headers:
        headers['Range'] = request.headers['range']
    try:
        resp = req_lib.get(stream_url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()
        response_headers = {}
        for key in ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges']:
            if key in resp.headers:
                response_headers[key] = resp.headers[key]
        return StreamingResponse(
            resp.iter_content(chunk_size=1024 * 1024),
            status_code=resp.status_code,
            headers=response_headers,
        )
    except Exception as e:
        logger.error(f"Jellyfin stream error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/docker/containers")
async def get_docker_containers(
    all: bool = True,
    status: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """List Docker containers with enhanced information"""
    if not app_state.docker or not app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    
    filters = {}
    if status:
        filters['status'] = status
    
    containers = app_state.docker.list_containers(all=all, filters=filters if filters else None)
    return {
        "containers": containers,
        "total": len(containers),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/docker/containers/{container_name}/logs")
async def get_docker_container_logs(container_name: str, current_user: Dict = Depends(get_current_user)):
    if not app_state.docker or not app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    
    logs = app_state.docker.get_container_logs(container_name)
    return {
        "logs": logs,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/docker/images")
async def get_docker_images(current_user: Dict = Depends(get_current_user)):
    if not app_state.docker or not app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    
    images = app_state.docker.list_images()
    return {
        "images": images,
        "total": len(images),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/docker/volumes")
async def get_docker_volumes(current_user: Dict = Depends(get_current_user)):
    if not app_state.docker or not app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    
    volumes = app_state.docker.list_volumes()
    return {
        "volumes": volumes,
        "total": len(volumes),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/docker/containers/{container_name}/start")
async def start_container(container_name: str, current_user: Dict = Depends(get_current_user)):
    if app_state.docker and app_state.docker.is_available():
        ok, msg = app_state.docker.start_container(container_name)
        return {"success": ok, "message": msg}
    raise HTTPException(status_code=503, detail="Docker not available")


@app.post("/api/docker/containers/{container_name}/stop")
async def stop_container(container_name: str, current_user: Dict = Depends(get_current_user)):
    if app_state.docker and app_state.docker.is_available():
        ok, msg = app_state.docker.stop_container(container_name)
        return {"success": ok, "message": msg}
    raise HTTPException(status_code=503, detail="Docker not available")


# ---------------------------------------------------------------------------
# AppStore Helper
# ---------------------------------------------------------------------------

class AppStoreHelper:
    def __init__(self):
        self.base_path = Path(__file__).parent / "appstore_data"
        self.apps_path = self.base_path / "apps"
        self.categories_file = self.base_path / "category-list.json"
        
    def get_categories(self) -> List[Dict]:
        try:
            if self.categories_file.exists():
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            return []
    
    def get_all_apps(self) -> List[Dict]:
        apps = []
        try:
            if not self.apps_path.exists():
                return []
            
            for app_file in self.apps_path.glob("*.json"):
                with open(app_file, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
                    apps.append(app_data)
            
            return sorted(apps, key=lambda x: x.get('name', ''))
        except Exception as e:
            logger.error(f"Error loading apps: {e}")
            return []
    
    def get_app_by_id(self, app_id: str) -> Optional[Dict]:
        try:
            app_file = self.apps_path / f"{app_id}.json"
            if app_file.exists():
                with open(app_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading app {app_id}: {e}")
            return None
    
    def get_featured_apps(self) -> List[Dict]:
        all_apps = self.get_all_apps()
        return [app for app in all_apps if app.get('featured', False)]
    
    def get_apps_by_category(self, category: str) -> List[Dict]:
        all_apps = self.get_all_apps()
        return [app for app in all_apps if app.get('category') == category]
    
    def install_app(self, app_id: str, docker_helper) -> tuple[bool, str]:
        try:
            app = self.get_app_by_id(app_id)
            if not app:
                return False, f"App {app_id} not found"
            
            if not docker_helper or not docker_helper.is_available():
                return False, "Docker not available"
            
            compose_data = app.get('compose', {})
            if not compose_data:
                return False, "No compose configuration found"
            
            # Create docker-compose.yml in temp location
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            compose_dir = temp_dir / f"appstore_{app_id}"
            compose_dir.mkdir(parents=True, exist_ok=True)
            compose_file = compose_dir / "docker-compose.yml"
            
            # Replace variables
            compose_str = yaml.dump(compose_data)
            compose_str = compose_str.replace('$AppID', app_id)
            compose_str = compose_str.replace('$PUID', '1000')
            compose_str = compose_str.replace('$PGID', '1000')
            compose_str = compose_str.replace('$TZ', 'UTC')
            
            with open(compose_file, 'w') as f:
                f.write(compose_str)
            
            # Use docker compose to deploy (modern Docker Desktop syntax)
            import subprocess
            result = subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"App {app['name']} installed successfully"
            else:
                return False, f"Installation failed: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error installing app {app_id}: {e}")
            return False, str(e)

# ---------------------------------------------------------------------------
# AppStore Routes
# ---------------------------------------------------------------------------

@app.get("/api/appstore/categories")
async def get_appstore_categories(current_user: Dict = Depends(get_current_user)):
    appstore = AppStoreHelper()
    return {"categories": appstore.get_categories()}

@app.get("/api/appstore/apps")
async def get_appstore_apps(category: Optional[str] = None, featured: Optional[bool] = None, current_user: Dict = Depends(get_current_user)):
    appstore = AppStoreHelper()
    
    if featured:
        apps = appstore.get_featured_apps()
    elif category:
        apps = appstore.get_apps_by_category(category)
    else:
        apps = appstore.get_all_apps()
    
    return {"apps": apps}

@app.get("/api/appstore/apps/{app_id}")
async def get_appstore_app(app_id: str, current_user: Dict = Depends(get_current_user)):
    appstore = AppStoreHelper()
    app = appstore.get_app_by_id(app_id)
    
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    return app

@app.post("/api/appstore/apps/{app_id}/install")
async def install_appstore_app(app_id: str, current_user: Dict = Depends(get_current_user)):
    appstore = AppStoreHelper()
    success, message = appstore.install_app(app_id, app_state.docker)
    
    if success:
        return {"success": True, "message": message}
    else:
        raise HTTPException(status_code=500, detail=message)

@app.post("/api/appstore/apps/{app_id}/uninstall")
async def uninstall_appstore_app(app_id: str, current_user: Dict = Depends(get_current_user)):
    if not app_state.docker or not app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        # Stop and remove containers with the app name
        import subprocess
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        compose_dir = temp_dir / f"appstore_{app_id}"
        
        result = subprocess.run(
            ['docker', 'compose', '-p', app_id, 'down'],
            capture_output=True,
            text=True,
            cwd=str(compose_dir)
        )
        
        if result.returncode == 0:
            return {"success": True, "message": f"App {app_id} uninstalled"}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# File Manager Routes
# ---------------------------------------------------------------------------

from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import shutil

# Base directory for file manager (downloads folder)
FILE_MANAGER_BASE = Path(os.getenv('FILE_MANAGER_PATH', './downloads'))
FILE_MANAGER_BASE.mkdir(parents=True, exist_ok=True)

@app.get("/api/files/list")
async def list_files(path: str = "", current_user: Dict = Depends(get_current_user)):
    """List files and directories in the specified path"""
    try:
        target_path = FILE_MANAGER_BASE / path
        
        # Security: prevent path traversal
        if not str(target_path.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        items = []
        for item in sorted(target_path.iterdir()):
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item.relative_to(FILE_MANAGER_BASE)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception as e:
                logger.error(f"Error reading item {item}: {e}")
                continue
        
        return {
            "current_path": path,
            "items": items,
            "total": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = "",
    current_user: Dict = Depends(get_current_user)
):
    """Upload a file to the specified path"""
    try:
        target_dir = FILE_MANAGER_BASE / path
        
        # Security: prevent path traversal
        if not str(target_dir.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "filename": file.filename,
            "path": str(file_path.relative_to(FILE_MANAGER_BASE)),
            "size": file_path.stat().st_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/download")
async def download_file(path: str, current_user: Dict = Depends(get_current_user)):
    """Download a file"""
    try:
        file_path = FILE_MANAGER_BASE / path
        
        # Security: prevent path traversal
        if not str(file_path.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/delete")
async def delete_file(path: str, current_user: Dict = Depends(get_current_user)):
    """Delete a file or directory"""
    try:
        target_path = FILE_MANAGER_BASE / path
        
        # Security: prevent path traversal and deletion of base directory
        if not str(target_path.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if target_path == FILE_MANAGER_BASE:
            raise HTTPException(status_code=403, detail="Cannot delete base directory")
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        
        return {"success": True, "message": f"Deleted {path}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/create-folder")
async def create_folder(path: str, name: str, current_user: Dict = Depends(get_current_user)):
    """Create a new folder"""
    try:
        target_dir = FILE_MANAGER_BASE / path / name
        
        # Security: prevent path traversal
        if not str(target_dir.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if target_dir.exists():
            raise HTTPException(status_code=400, detail="Folder already exists")
        
        target_dir.mkdir(parents=True, exist_ok=False)
        
        return {
            "success": True,
            "path": str(target_dir.relative_to(FILE_MANAGER_BASE)),
            "name": name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/rename")
async def rename_file(path: str, new_name: str, current_user: Dict = Depends(get_current_user)):
    """Rename a file or directory"""
    try:
        old_path = FILE_MANAGER_BASE / path
        new_path = old_path.parent / new_name
        
        # Security: prevent path traversal
        if not str(old_path.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        if not str(new_path.resolve()).startswith(str(FILE_MANAGER_BASE.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not old_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
        
        if new_path.exists():
            raise HTTPException(status_code=400, detail="Target name already exists")
        
        old_path.rename(new_path)
        
        return {
            "success": True,
            "old_path": path,
            "new_path": str(new_path.relative_to(FILE_MANAGER_BASE)),
            "new_name": new_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# Telegram File Editor Routes
# ---------------------------------------------------------------------------

class FileCreateRequest(BaseModel):
    filename: str
    content: str
    file_type: str = "text"

class FileUpdateRequest(BaseModel):
    content: str

@app.get("/api/editor/files")
async def list_telegram_files(current_user: Dict = Depends(get_current_user)):
    """List all files stored in Telegram"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    try:
        files = app_state.telegram_storage.list_files()
        return {"files": files, "total": len(files)}
    except Exception as e:
        logger.error(f"Error listing Telegram files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/editor/files")
async def create_telegram_file(request: FileCreateRequest, current_user: Dict = Depends(get_current_user)):
    """Create a new file and save to Telegram"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    if not app_state.telegram_storage.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )
    
    try:
        result = app_state.telegram_storage.save_file(
            filename=request.filename,
            content=request.content,
            file_type=request.file_type
        )
        
        if result:
            return {"success": True, "file": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to save file to Telegram")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Telegram file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/editor/files/{file_id}")
async def get_telegram_file(file_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a file from Telegram"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    try:
        result = app_state.telegram_storage.get_file(file_id)
        
        if result:
            return {
                "success": True,
                "content": result['content'],
                "metadata": result['metadata']
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error getting Telegram file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/editor/files/{file_id}")
async def update_telegram_file(file_id: str, request: FileUpdateRequest, current_user: Dict = Depends(get_current_user)):
    """Update a file in Telegram"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    try:
        result = app_state.telegram_storage.update_file(file_id, request.content)
        
        if result:
            return {"success": True, "file": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to update file")
    except Exception as e:
        logger.error(f"Error updating Telegram file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/editor/files/{file_id}")
async def delete_telegram_file(file_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a file from Telegram"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    try:
        result = app_state.telegram_storage.delete_file(file_id)
        
        if result:
            return {"success": True, "message": "File deleted"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error deleting Telegram file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/editor/files/search/{query}")
async def search_telegram_files(query: str, current_user: Dict = Depends(get_current_user)):
    """Search files by filename"""
    if not app_state.telegram_storage:
        raise HTTPException(status_code=503, detail="Telegram Storage not available")
    
    try:
        results = app_state.telegram_storage.search_files(query)
        return {"files": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Error searching Telegram files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# System Information Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/system/info")
async def get_system_info(current_user: Dict = Depends(get_current_user)):
    """Get system information including CPU, memory, OS, and uptime"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        boot_time = psutil.boot_time()
        uptime = datetime.now().timestamp() - boot_time
        
        cpu_info = platform.processor() or f"{psutil.cpu_count()} cores"
        
        return {
            "cpu": cpu_info,
            "cpu_usage": round(cpu_percent, 1),
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "free": memory.available,
                "used_percent": round(memory.percent, 1)
            },
            "os": f"{platform.system()} {platform.release()}",
            "platform": platform.platform(),
            "uptime": int(uptime),
            "hostname": socket.gethostname()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/network")
async def get_network_info(current_user: Dict = Depends(get_current_user)):
    """Get network interface information"""
    try:
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for iface_name, addrs in net_if_addrs.items():
            if iface_name.startswith('lo'):
                continue
                
            iface_info = {
                "name": iface_name,
                "status": "up" if net_if_stats.get(iface_name) and net_if_stats[iface_name].isup else "down",
                "ip": None,
                "mac": None
            }
            
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    iface_info["ip"] = addr.address
                elif addr.family == psutil.AF_LINK:
                    iface_info["mac"] = addr.address
            
            if iface_info["ip"] or iface_info["mac"]:
                interfaces.append(iface_info)
        
        return {
            "interfaces": interfaces,
            "dns": {
                "primary": "8.8.8.8",
                "secondary": "8.8.4.4"
            }
        }
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/storage")
async def get_storage_info(current_user: Dict = Depends(get_current_user)):
    """Get storage/disk information"""
    try:
        disks = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            if partition.fstype and partition.mountpoint:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round(usage.percent, 1)
                    }
                    
                    if usage.percent > 90:
                        disk_info["health"] = "critical"
                    elif usage.percent > 70:
                        disk_info["health"] = "warning"
                    else:
                        disk_info["health"] = "good"
                    
                    disks.append(disk_info)
                except (PermissionError, OSError):
                    continue
        
        return {"disks": disks}
    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# User Management Endpoints
# ---------------------------------------------------------------------------

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = 'user'

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@app.get("/api/users")
async def get_users(current_user: Dict = Depends(get_current_user)):
    """Get all users"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        users = app_state.user_manager.get_all_users()
        return {"users": users, "total": len(users)}
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Get user by ID"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        user = app_state.user_manager.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users")
async def create_user(request: UserCreateRequest, current_user: Dict = Depends(get_current_user)):
    """Create a new user"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        user = app_state.user_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role
        )
        return {"success": True, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, request: UserUpdateRequest, current_user: Dict = Depends(get_current_user)):
    """Update user information"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        user = app_state.user_manager.update_user(user_id, **update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a user"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        success = app_state.user_manager.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/change-password")
async def change_password(user_id: str, request: PasswordChangeRequest, current_user: Dict = Depends(get_current_user)):
    """Change user password"""
    if not app_state.user_manager:
        raise HTTPException(status_code=503, detail="User Manager not available")
    
    try:
        success = app_state.user_manager.change_password(
            user_id=user_id,
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WS message: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
