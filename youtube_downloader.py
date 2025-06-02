#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Video Downloader

This module provides functionality to download YouTube videos and integrates with the Telegram bot.
It uses yt-dlp for reliable video downloading and supports progress tracking.

--------------------------
Features
--------------------------
- Download videos with progress tracking
- Get video information (title, duration, thumbnail, etc.)
- Support for different resolutions and formats
- Callback system for real-time updates
- Background downloading support
- Telegram bot integration

--------------------------
Usage
--------------------------
from youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader()
video_info = downloader.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
success, result = downloader.download_video(url, output_path="./downloads")
"""

import os
import time
import asyncio
import threading
import logging
import subprocess
import json
from typing import Callable, Dict, Optional, Tuple, Union, Any
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class VideoInfo:
    """Container for video information."""
    video_id: str
    title: str
    author: str
    length: int  # in seconds
    views: int
    thumbnail_url: str
    description: str
    publish_date: str
    keywords: list
    default_filename: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easy serialization."""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'author': self.author,
            'length': self.length,
            'views': self.views,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'publish_date': self.publish_date,
            'keywords': self.keywords,
            'default_filename': self.default_filename
        }

class YouTubeDownloader:
    """Main class for handling YouTube downloads with progress tracking."""
    
    def __init__(self, download_dir: str = "downloads"):
        """
        Initialize the YouTube downloader.
        
        Args:
            download_dir: Base directory where videos will be saved
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.active_downloads: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def get_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
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
        """
        Get video information using yt-dlp.
        Returns a dict with info or None if failed.
        """
        try:
            # Clean and validate URL
            if 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            elif 'youtube.com/shorts/' in url:
                video_id = url.split('/shorts/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            
            logger.info(f"[get_video_info] Getting info for URL: {url}")
            
            # Use yt-dlp to fetch video info
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '--no-playlist',
                url
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return info
            else:
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
        on_progress: Optional[Callable[[str, float], None]] = None,
        on_complete: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        download_id: Optional[str] = None,
        max_filesize: str = "50M"
    ) -> Tuple[bool, Union[str, bytes]]:
        """
        Download a YouTube video using yt-dlp.
        
        Args:
            url: YouTube video URL
            output_path: Directory to save the video
            resolution: Preferred resolution (e.g., '720p', '1080p')
            on_progress: Progress callback function
            on_complete: Completion callback function
            on_error: Error callback function
            download_id: Unique identifier for this download
            max_filesize: Maximum file size (e.g., '50M', '100M')
            
        Returns:
            Tuple of (success: bool, result: str)
        """
        if output_path is None:
            output_path = self.download_dir

        download_id = download_id or self.get_video_id(url)
        
        with self.lock:
            self.active_downloads[download_id] = {
                'status': DownloadStatus.DOWNLOADING,
                'progress': 0.0,
                'start_time': time.time(),
                'info': None
            }
        
        try:
            # Get video info first
            video_info = self.get_video_info(url)
            if not video_info:
                error_msg = "Não foi possível obter informações do vídeo. Verifique se o link está correto e o vídeo está disponível."
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg
            
            # Update info in status
            with self.lock:
                if download_id in self.active_downloads:
                    self.active_downloads[download_id]['info'] = {
                        'title': video_info.get('title', ''),
                        'author': video_info.get('uploader', ''),
                        'length': video_info.get('duration', 0),
                        'views': video_info.get('view_count', 0),
                        'default_filename': video_info.get('title', 'video') + ".mp4"
                    }
            
            # Create safe filename
            safe_title = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in video_info.get('title', 'video'))
            filename = f"{safe_title[:100]}_{download_id}.mp4"
            file_path = os.path.join(output_path, filename)
            
            # Build yt-dlp command
            cmd = [
                'yt-dlp',
                '-f', f"best[ext=mp4][filesize<{max_filesize}]/bestvideo[ext=mp4][filesize<{max_filesize}]+bestaudio[ext=m4a]/mp4/best[filesize<{max_filesize}]",
                '--merge-output-format', 'mp4',
                '-o', file_path,
                '--no-playlist',
                '--no-warnings',
                '--retries', '3',
                '--fragment-retries', '3',
                url
            ]
            
            if resolution:
                height = resolution.replace('p', '')
                cmd[2] = f"best[ext=mp4][height<={height}][filesize<{max_filesize}]/bestvideo[ext=mp4][height<={height}][filesize<{max_filesize}]+bestaudio[ext=m4a]/mp4/best[height<={height}][filesize<{max_filesize}]"
            
            logger.info(f"[download_video] Executing: {' '.join(cmd)}")
            
            # Execute download
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
                            'file_path': file_path
                        })
                
                if on_complete:
                    on_complete(download_id, file_path)
                
                return True, file_path
            else:
                logger.error(f"yt-dlp download error: {proc.stderr}")
                
                # Parse error message for user-friendly response
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
                        self.active_downloads[download_id].update({
                            'status': DownloadStatus.FAILED,
                            'error': error_msg
                        })
                
                if on_error:
                    on_error(download_id, error_msg)
                
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "O download demorou muito tempo e foi cancelado (timeout de 10 minutos)."
            logger.error(f"Download timeout for {url}")
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
            # Clean up failed downloads
            with self.lock:
                if download_id in self.active_downloads and \
                   self.active_downloads[download_id]['status'] not in [DownloadStatus.COMPLETED]:
                    del self.active_downloads[download_id]
    
    def download_video_async(
        self,
        url: str,
        output_path: Optional[str] = None,
        resolution: Optional[str] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
        on_complete: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        download_id: Optional[str] = None,
        max_filesize: str = "50M"
    ) -> str:
        """
        Start a download in a background thread and return immediately.
        
        Args:
            Same as download_video()
            
        Returns:
            Download ID that can be used to track progress
        """
        download_id = download_id or self.get_video_id(url)
        
        def download_wrapper():
            try:
                self.download_video(
                    url=url,
                    output_path=output_path,
                    resolution=resolution,
                    on_progress=on_progress,
                    on_complete=on_complete,
                    on_error=on_error,
                    download_id=download_id,
                    max_filesize=max_filesize
                )
            except Exception as e:
                logger.error(f"Error in download thread: {e}", exc_info=True)
                if on_error:
                    on_error(download_id, f"Erro na thread de download: {str(e)}")
        
        # Start download in a daemon thread
        thread = threading.Thread(target=download_wrapper, daemon=True)
        thread.start()
        
        return download_id
    
    def get_download_status(self, download_id: str) -> Optional[Dict]:
        """
        Get the status of a download.
        
        Args:
            download_id: The ID of the download
            
        Returns:
            Dictionary with download status or None if not found
        """
        with self.lock:
            return self.active_downloads.get(download_id)
    
    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel an active download.
        
        Args:
            download_id: The ID of the download to cancel
            
        Returns:
            True if download was cancelled, False if not found
        """
        with self.lock:
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['status'] = DownloadStatus.CANCELLED
                return True
        return False
    
    def get_active_downloads(self) -> Dict[str, Dict]:
        """
        Get all active downloads.
        
        Returns:
            Dictionary of active downloads
        """
        with self.lock:
            return self.active_downloads.copy()
    
    def cleanup_completed_downloads(self) -> int:
        """
        Remove completed downloads from active list.
        
        Returns:
            Number of downloads cleaned up
        """
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


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_filesize(bytes_size: int) -> str:
    """
    Format file size in bytes to human readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a valid YouTube URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if it's a YouTube URL, False otherwise
    """
    youtube_domains = [
        'youtube.com',
        'www.youtube.com',
        'youtu.be',
        'm.youtube.com'
    ]
    
    try:
        parsed = urlparse(url.lower())
        return any(domain in parsed.netloc for domain in youtube_domains)
    except Exception:
        return False


if __name__ == "__main__":
    # Simple test
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        downloader = YouTubeDownloader()
        
        print(f"Getting info for: {url}")
        info = downloader.get_video_info(url)
        
        if info:
            print(f"Title: {info.get('title')}")
            print(f"Author: {info.get('uploader')}")
            print(f"Duration: {format_duration(info.get('duration', 0))}")
            print(f"Views: {info.get('view_count', 0):,}")
            
            print("\nStarting download...")
            success, result = downloader.download_video(url)
            
            if success:
                print(f"Download completed: {result}")
            else:
                print(f"Download failed: {result}")
        else:
            print("Failed to get video info")
    else:
        print("Usage: python youtube_downloader.py <youtube_url>")