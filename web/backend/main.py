#!/usr/bin/env python3
"""
Web API Backend for Telegram Torrent Manager
FastAPI-based REST API with WebSocket support
Self-contained: no imports from the main project's src package.
"""
import os
import requests as req_lib
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ---------------------------------------------------------------------------
# Lightweight Jellyfin helpers
# ---------------------------------------------------------------------------

class JellyfinHelper:
    def __init__(self):
        self.url = JELLYFIN_URL.rstrip('/') if JELLYFIN_URL else ''
        self.api_key = JELLYFIN_API_KEY
        self.access_token = None
        self.user_id = None
        self.session = req_lib.Session()
        self._available = False

        if self.url:
            if JELLYFIN_USERNAME and JELLYFIN_PASSWORD:
                self._authenticate(JELLYFIN_USERNAME, JELLYFIN_PASSWORD)
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
            resp = self.session.post(
                f"{self.url}/Users/authenticatebyname",
                headers={'Content-Type': 'application/json'},
                json={'Username': username, 'Pw': password},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get('AccessToken')
            self.user_id = data.get('User', {}).get('Id')
            logger.info("Jellyfin authentication OK")
        except Exception as e:
            logger.error(f"Jellyfin auth error: {e}")

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
        url = f"{self.url}/Videos/{item_id}/stream?static=true&api_key={token}"
        if audio_stream_index is not None:
            url += f"&audioStreamIndex={audio_stream_index}"
        return url

    def get_subtitle_url(self, item_id: str, media_source_id: str, index: int) -> str:
        token = self.api_key or self.access_token or ''
        return f"{self.url}/Videos/{item_id}/{media_source_id}/Subtitles/{index}/0/Stream.vtt?api_key={token}"

    def get_image_url(self, item_id: str, image_type: str = 'Primary', max_width: int = 300) -> str:
        token = self.api_key or self.access_token or ''
        return f"{self.url}/Items/{item_id}/Images/{image_type}?maxWidth={max_width}&api_key={token}"

# ---------------------------------------------------------------------------
# Lightweight Docker helpers
# ---------------------------------------------------------------------------

class DockerHelper:
    def __init__(self):
        self.client = None
        self._available = False
        try:
            import docker
            self.client = docker.from_env()
            self._available = True
            logger.info("Docker client initialized")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")

    def is_available(self) -> bool:
        return self._available and self.client is not None

    def list_containers(self) -> List[Dict]:
        if not self.is_available():
            return []
        try:
            containers = self.client.containers.list(all=True)
            return [{
                'id': c.short_id,
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else 'unknown',
                'created': c.attrs['Created'],
            } for c in containers]
        except Exception as e:
            logger.error(f"Docker list error: {e}")
            return []

    def start_container(self, name: str):
        if not self.is_available():
            return False, "Docker not available"
        try:
            c = self.client.containers.get(name)
            c.start()
            return True, f"Container '{c.name}' started"
        except Exception as e:
            return False, str(e)

    def stop_container(self, name: str):
        if not self.is_available():
            return False, "Docker not available"
        try:
            c = self.client.containers.get(name)
            c.stop(timeout=10)
            return True, f"Container '{c.name}' stopped"
        except Exception as e:
            return False, str(e)

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

class AppState:
    def __init__(self):
        self.qb_sessions: List[Dict] = []
        self.jellyfin: Optional[JellyfinHelper] = None
        self.docker: Optional[DockerHelper] = None

app_state = AppState()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Web API Backend...")

    for inst in QB_INSTANCES:
        session = qb_login(inst['url'], inst['username'], inst['password'])
        app_state.qb_sessions.append({
            'name': inst['name'],
            'url': inst['url'],
            'session': session,
        })

    try:
        app_state.jellyfin = JellyfinHelper()
        if app_state.jellyfin.is_available():
            logger.info("Jellyfin initialized")
    except Exception as e:
        logger.error(f"Jellyfin init error: {e}")

    try:
        app_state.docker = DockerHelper()
        if app_state.docker.is_available():
            logger.info("Docker initialized")
    except Exception as e:
        logger.error(f"Docker init error: {e}")

    asyncio.create_task(broadcast_updates())
    yield
    logger.info("Shutting down Web API Backend...")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Telegram Torrent Manager API",
    description="Web-based management interface for torrent and media server",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"name": "Telegram Torrent Manager API", "version": "1.0.0", "status": "running"}


@app.get("/api/system/status")
async def get_system_status():
    connected_qb = any(i['session'] is not None for i in app_state.qb_sessions)
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
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/torrents")
async def get_torrents():
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
async def add_torrent(magnet_link: str):
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
async def pause_torrent(torrent_hash: str):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'pause', torrent_hash)
    return {"success": ok}


@app.post("/api/torrents/{torrent_hash}/resume")
async def resume_torrent(torrent_hash: str):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'resume', torrent_hash)
    return {"success": ok}


@app.delete("/api/torrents/{torrent_hash}")
async def delete_torrent(torrent_hash: str, delete_files: bool = False):
    inst = get_first_session()
    if not inst:
        raise HTTPException(status_code=503, detail="qBittorrent not connected")
    ok = qb_action(inst['session'], inst['url'], 'delete', torrent_hash, deleteFiles=str(delete_files).lower())
    return {"success": ok}


@app.get("/api/jellyfin/libraries")
async def get_jellyfin_libraries():
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"libraries": app_state.jellyfin.get_libraries()}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/recent")
async def get_jellyfin_recent(limit: int = 10):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_recent_items(limit=limit)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/items/{item_id}")
async def get_jellyfin_item(item_id: str):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        item = app_state.jellyfin.get_item(item_id)
        if item:
            return item
        raise HTTPException(status_code=404, detail="Item not found")
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/shows/{series_id}/seasons")
async def get_jellyfin_seasons(series_id: str):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_seasons(series_id)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/shows/{series_id}/episodes")
async def get_jellyfin_episodes(series_id: str, season_id: str = None):
    if app_state.jellyfin and app_state.jellyfin.is_available():
        return {"items": app_state.jellyfin.get_episodes(series_id, season_id)}
    raise HTTPException(status_code=503, detail="Jellyfin not available")


@app.get("/api/jellyfin/image/{item_id}")
async def get_jellyfin_image(item_id: str, type: str = "Primary", maxWidth: int = 300):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    image_url = jf.get_image_url(item_id, type, maxWidth)
    try:
        resp = req_lib.get(image_url, stream=True, timeout=30)
        resp.raise_for_status()
        return StreamingResponse(
            resp.iter_content(chunk_size=65536),
            media_type=resp.headers.get('Content-Type', 'image/jpeg'),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/jellyfin/playback-info/{item_id}")
async def get_jellyfin_playback_info(item_id: str):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    info = app_state.jellyfin.get_playback_info(item_id)
    if info:
        return info
    raise HTTPException(status_code=404, detail="Playback info not found")


@app.get("/api/jellyfin/subtitles/{item_id}/{media_source_id}/{index}")
async def get_jellyfin_subtitle(item_id: str, media_source_id: str, index: int):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    sub_url = jf.get_subtitle_url(item_id, media_source_id, index)
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
async def stream_jellyfin(item_id: str, request: Request, audioStreamIndex: int = None):
    if not app_state.jellyfin or not app_state.jellyfin.is_available():
        raise HTTPException(status_code=503, detail="Jellyfin not available")
    jf = app_state.jellyfin
    stream_url = jf.get_stream_url(item_id, audio_stream_index=audioStreamIndex)
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
async def get_docker_containers():
    if app_state.docker and app_state.docker.is_available():
        return {"containers": app_state.docker.list_containers()}
    raise HTTPException(status_code=503, detail="Docker not available")


@app.post("/api/docker/containers/{container_name}/start")
async def start_container(container_name: str):
    if app_state.docker and app_state.docker.is_available():
        ok, msg = app_state.docker.start_container(container_name)
        return {"success": ok, "message": msg}
    raise HTTPException(status_code=503, detail="Docker not available")


@app.post("/api/docker/containers/{container_name}/stop")
async def stop_container(container_name: str):
    if app_state.docker and app_state.docker.is_available():
        ok, msg = app_state.docker.stop_container(container_name)
        return {"success": ok, "message": msg}
    raise HTTPException(status_code=503, detail="Docker not available")


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
