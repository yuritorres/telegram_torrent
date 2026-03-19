import os
import time
import threading
import logging
import subprocess
import json
from typing import Callable, Dict, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs
from enum import Enum

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class YouTubeDownloader:
    """Main class for handling YouTube downloads with progress tracking."""

    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.active_downloads: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def get_video_id(self, url: str) -> str:
        try:
            if 'youtu.be' in url:
                return url.split('/')[-1].split('?')[0]
            parsed = urlparse(url)
            if parsed.hostname in ('www.youtube.com', 'youtube.com'):
                if parsed.path == '/watch':
                    return parse_qs(parsed.query).get('v', [''])[0]
                if parsed.path.startswith('/embed/'):
                    return parsed.path.split('/')[2]
                if parsed.path.startswith('/shorts/'):
                    return parsed.path.split('/')[2]
            return ""
        except Exception as e:
            logger.error(f"Error extracting video ID from {url}: {e}")
            return ""

    def get_video_info(self, url: str) -> Optional[dict]:
        try:
            if 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            elif 'youtube.com/shorts/' in url:
                video_id = url.split('/shorts/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'

            cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist', url]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
            logger.error(f"yt-dlp info error: {result.stderr}")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting video info for {url}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_video_info for url {url}: {e}", exc_info=True)
            return None

    def download_video(
        self,
        url: str,
        output_path: Optional[str] = None,
        resolution: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        download_id: Optional[str] = None,
        max_filesize: str = "50M",
    ) -> Tuple[bool, str]:
        if output_path is None:
            output_path = self.download_dir
        download_id = download_id or self.get_video_id(url)

        with self.lock:
            self.active_downloads[download_id] = {
                'status': DownloadStatus.DOWNLOADING,
                'progress': 0.0,
                'start_time': time.time(),
                'info': None,
            }

        try:
            video_info = self.get_video_info(url)
            if not video_info:
                error_msg = "Não foi possível obter informações do vídeo."
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg

            with self.lock:
                if download_id in self.active_downloads:
                    self.active_downloads[download_id]['info'] = {
                        'title': video_info.get('title', ''),
                        'author': video_info.get('uploader', ''),
                        'length': video_info.get('duration', 0),
                        'views': video_info.get('view_count', 0),
                        'default_filename': video_info.get('title', 'video') + ".mp4",
                    }

            safe_title = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in video_info.get('title', 'video'))
            filename = f"{safe_title[:100]}_{download_id}.mp4"
            file_path = os.path.join(output_path, filename)

            fmt = f"best[ext=mp4][filesize<{max_filesize}]/bestvideo[ext=mp4][filesize<{max_filesize}]+bestaudio[ext=m4a]/mp4/best[filesize<{max_filesize}]"
            if resolution:
                height = resolution.replace('p', '')
                fmt = f"best[ext=mp4][height<={height}][filesize<{max_filesize}]/bestvideo[ext=mp4][height<={height}][filesize<{max_filesize}]+bestaudio[ext=m4a]/mp4/best[height<={height}][filesize<{max_filesize}]"

            cmd = [
                'yt-dlp', '-f', fmt,
                '--merge-output-format', 'mp4',
                '-o', file_path,
                '--no-playlist', '--no-warnings',
                '--retries', '3', '--fragment-retries', '3',
                url,
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)

            if proc.returncode == 0 and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    error_msg = "O arquivo baixado está vazio."
                    if on_error:
                        on_error(download_id, error_msg)
                    return False, error_msg

                with self.lock:
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id].update({
                            'status': DownloadStatus.COMPLETED,
                            'progress': 100.0,
                            'file_path': file_path,
                        })
                if on_complete:
                    on_complete(download_id, file_path)
                return True, file_path
            else:
                error_output = proc.stderr.strip()
                if "Video unavailable" in error_output:
                    error_msg = "Vídeo indisponível ou foi removido."
                elif "Private video" in error_output:
                    error_msg = "Este vídeo é privado."
                elif "Sign in" in error_output or "age" in error_output.lower():
                    error_msg = "Este vídeo requer login ou tem restrição de idade."
                elif "too large" in error_output.lower() or "filesize" in error_output.lower():
                    error_msg = f"O vídeo é muito grande (limite: {max_filesize})."
                else:
                    error_msg = f"Falha ao baixar o vídeo: {error_output.splitlines()[-1] if error_output else 'Erro desconhecido'}"

                with self.lock:
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id].update({'status': DownloadStatus.FAILED, 'error': error_msg})
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "O download demorou muito tempo e foi cancelado (timeout de 10 minutos)."
            if on_error:
                on_error(download_id, error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erro inesperado ao baixar vídeo: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if on_error:
                on_error(download_id, error_msg)
            return False, error_msg
        finally:
            with self.lock:
                if download_id in self.active_downloads and \
                   self.active_downloads[download_id]['status'] not in [DownloadStatus.COMPLETED]:
                    del self.active_downloads[download_id]

    def download_video_async(
        self,
        url: str,
        output_path: Optional[str] = None,
        resolution: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        download_id: Optional[str] = None,
        max_filesize: str = "50M",
    ) -> str:
        download_id = download_id or self.get_video_id(url)

        def download_wrapper():
            try:
                self.download_video(
                    url=url, output_path=output_path, resolution=resolution,
                    on_progress=on_progress, on_complete=on_complete, on_error=on_error,
                    download_id=download_id, max_filesize=max_filesize,
                )
            except Exception as e:
                logger.error(f"Error in download thread: {e}", exc_info=True)
                if on_error:
                    on_error(download_id, f"Erro na thread de download: {str(e)}")

        thread = threading.Thread(target=download_wrapper, daemon=True)
        thread.start()
        return download_id

    def get_download_status(self, download_id: str) -> Optional[Dict]:
        with self.lock:
            return self.active_downloads.get(download_id)

    def cancel_download(self, download_id: str) -> bool:
        with self.lock:
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['status'] = DownloadStatus.CANCELLED
                return True
        return False

    def get_active_downloads(self) -> Dict[str, Dict]:
        with self.lock:
            return self.active_downloads.copy()

    def cleanup_completed_downloads(self) -> int:
        cleaned = 0
        with self.lock:
            completed_ids = [
                dl_id for dl_id, info in self.active_downloads.items()
                if info['status'] in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
            ]
            for dl_id in completed_ids:
                del self.active_downloads[dl_id]
                cleaned += 1
        return cleaned
