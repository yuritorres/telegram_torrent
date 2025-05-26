"""
YouTube Video Downloader

This module provides functionality to download YouTube videos and can be used in multiple ways:
1. As a command-line tool
2. As a Python module in other applications
3. Integrated with Telegram bots

--------------------------
Features
--------------------------
- Download videos with progress tracking
- Get video information (title, duration, thumbnail, etc.)
- Support for different resolutions and formats
- Callback system for real-time updates
- Background downloading support

--------------------------
Basic Usage
--------------------------
# Basic download
from youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader()

# Get video info
video_info = downloader.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Download with progress callback
def progress_callback(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = (bytes_downloaded / total_size) * 100
    print(f"Download progress: {percent:.1f}%")

downloader.download_video(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_path="./downloads",
    on_progress=progress_callback
)

# For Telegram integration, see the TelegramBotExample class below
"""

import os
import io
import time
import asyncio
import threading
import logging
import subprocess
from typing import Callable, Dict, Optional, Tuple, Union, Any
from urllib.parse import urlparse, parse_qs
from urllib.error import HTTPError
from dataclasses import dataclass
from enum import Enum
import tempfile

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pytube import YouTube, Stream
from pytube.exceptions import RegexMatchError, VideoUnavailable, PytubeError
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    keywords: list[str]
    streams: list[Dict]
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
        if 'youtu.be' in url:
            return url.split('/')[-1].split('?')[0]
        
        parsed = urlparse(url)
        if parsed.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [''])[0]
            if parsed.path.startswith('/embed/'):
                return parsed.path.split('/')[2]
        return ""
    
    def get_video_info(self, url: str) -> Optional[dict]:
        """
        Get video information using yt-dlp.
        Returns a dict with info or None if failed.
        """
        try:
            # Clean and validate URL
            orig_url = url
            if 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            elif 'youtube.com/shorts/' in url:
                video_id = url.split('/shorts/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            logger.info(f"[get_video_info] URL final passada ao yt-dlp: {url}")
            # Use yt-dlp to fetch video info
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                url
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                return info
            else:
                logger.error(f"yt-dlp info error: {result.stderr}")
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
        in_memory: bool = False
    ) -> Tuple[bool, Union[str, bytes]]:
        """
        Download a YouTube video using yt-dlp.
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
            # Get video info
            video_info = self.get_video_info(url)
            if not video_info:
                error_msg = "Não foi possível obter informações do vídeo. Tente outro link ou verifique se o vídeo está disponível."
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg
            # Atualiza info no status
            with self.lock:
                if download_id in self.active_downloads:
                    self.active_downloads[download_id]['info'] = {
                        'title': video_info.get('title', ''),
                        'author': video_info.get('uploader', ''),
                        'length': video_info.get('duration', 0),
                        'views': video_info.get('view_count', 0),
                        'default_filename': video_info.get('title', 'video') + ".mp4"
                    }
            # Monta nome do arquivo
            safe_title = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in video_info.get('title', 'video'))
            filename = f"{safe_title[:100]}_{download_id}.mp4"
            file_path = os.path.join(output_path, filename)
            # Monta comando yt-dlp
            cmd = [
                'yt-dlp',
                '-f', f"bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4/best",
                '-o', file_path,
                url
            ]
            if resolution:
                cmd = [
                    'yt-dlp',
                    '-f', f"bestvideo[height<={resolution.replace('p','')}][ext=mp4]+bestaudio[ext=m4a]/mp4/best[height<={resolution.replace('p','')}]/best",
                    '-o', file_path,
                    url
                ]
            logger.info(f"[download_video] Executando: {' '.join(cmd)}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0 and os.path.exists(file_path):
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
                error_msg = f"Falha ao baixar o vídeo: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else 'Erro desconhecido'}"
                with self.lock:
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id].update({
                            'status': DownloadStatus.FAILED,
                            'error': error_msg
                        })
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
                   self.active_downloads[download_id]['status'] != DownloadStatus.COMPLETED:
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
                # Wrapper to adapt the callbacks
                def progress_callback(stream, chunk, bytes_remaining):
                    if on_progress:
                        total = stream.filesize
                        downloaded = total - bytes_remaining
                        progress = (downloaded / total) * 100
                        on_progress(download_id, progress)
                
                def complete_callback(file_path):
                    if on_complete:
                        on_complete(download_id, file_path)
                
                def error_callback(dl_id, error_msg):
                    if on_error:
                        on_error(dl_id, error_msg)
                
                self.download_video(
                    url=url,
                    output_path=output_path,
                    resolution=resolution,
                    on_progress=progress_callback,
                    on_complete=complete_callback,
                    on_error=error_callback,
                    download_id=download_id
                )
            except Exception as e:
                logger.error(f"Error in download thread: {e}", exc_info=True)
        
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
                # Note: Actual cancellation would require implementing with requests.Session()
                # For now, we just mark it as cancelled
                return True
        return False


class TelegramBotExample:
    """Example class showing how to integrate with a Telegram bot."""
    
    def __init__(self, bot_token: str, download_dir: str = "downloads"):
        """
        Initialize with your Telegram bot token.
        
        Args:
            bot_token: Your Telegram bot token
            download_dir: Directory to save downloaded videos
        """
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
        self.downloader = YouTubeDownloader(download_dir=download_dir)
        self.active_downloads: Dict[str, Dict] = {}
        
        # Initialize Telegram bot
        self.application = Application.builder().token(bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("download", self.download))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            "Olá! Envie-me um link do YouTube para baixar o vídeo.\n"
            "Comandos disponíveis:\n"
            "/download <url> - Baixar vídeo\n"
            "/status <id> - Ver status do download"
        )
    
    async def download(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /download command."""
        if not context.args:
            await update.message.reply_text("Por favor, forneça uma URL do YouTube.")
            return
            
        url = context.args[0]
        video_id = self.downloader.get_video_id(url)
        
        if not video_id:
            await update.message.reply_text("URL do YouTube inválida.")
            return
            
        # Get video info
        video_info = self.downloader.get_video_info(url)
        if not video_info:
            await update.message.reply_text("Não foi possível obter informações do vídeo.")
            return
            
        # Send video info
        message = await update.message.reply_text(
            f"📺 *{video_info.get('title', 'Título não disponível')}*\n"
            f"👤 *Canal:* {video_info.get('uploader', 'Desconhecido')}\n"
            f"⏱ *Duração:* {video_info.get('duration', 'N/A')} segundos\n"
            f"📊 *Visualizações:* {video_info.get('view_count', 0):,}\n"
            f"📅 *Publicado em:* {video_info.get('upload_date', 'Data desconhecida')}\n"
            f"\n📥 *Baixando vídeo...*",
            parse_mode='Markdown'
        )
        
        # Store message info for updates
        self.active_downloads[video_id] = {
            'message_id': message.message_id,
            'chat_id': update.effective_chat.id,
            'title': video_info.get('title', 'Vídeo sem título'),
            'url': url,
            'video_info': video_info
        }
        
        # Start download in background
        asyncio.create_task(self.download_and_send_video(video_id, message))
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /status command."""
        if not context.args:
            await update.message.reply_text("Por favor, forneça um ID de download.")
            return
            
        download_id = context.args[0]
        status = self.downloader.get_download_status(download_id)
        
        if not status:
            await update.message.reply_text("Download não encontrado ou já concluído.")
            return
            
        await update.message.reply_text(
            f"Status do download:\n"
            f"📌 {status['info']['title']}\n"
            f"📊 Progresso: {status.get('progress', 0):.1f}%\n"
            f"🔄 Status: {status['status'].value}"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle any other text message as a YouTube URL."""
        url = update.message.text
        if "youtube.com" in url or "youtu.be" in url:
            await self.download(update, context)
    

    async def download_and_send_video(self, video_id: str, message) -> None:
        """Download video to disk and then send to Telegram."""
        if video_id not in self.active_downloads:
            return
            
        download_info = self.active_downloads[video_id]
        url = download_info['url']
        temp_path = None
        
        try:
            # Create downloads directory if it doesn't exist
            os.makedirs(self.downloader.download_dir, exist_ok=True)
            
            # Update status to downloading
            await self.application.bot.edit_message_text(
                chat_id=download_info['chat_id'],
                message_id=download_info['message_id'],
                text=(
                    f"📥 *Baixando vídeo...*\n\n"
                    f"📺 *{download_info['title']}*\n"
                    f"⏳ Aguarde, preparando download..."
                ),
                parse_mode='Markdown'
            )
            
            # Download the video using yt-dlp
            video_info = download_info['video_info']
            
            # Create a temporary file with .mp4 extension
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Build yt-dlp command with more reliable options
                cmd = [
                    'yt-dlp',
                    '-f', 'best[ext=mp4][filesize<50M]',  # Try to get best MP4 under 50MB
                    '--merge-output-format', 'mp4',
                    '--output', temp_path,
                    '--no-playlist',
                    '--no-warnings',
                    '--no-call-home',
                    '--newline',
                    '--no-check-certificate',
                    '--prefer-ffmpeg',
                    '--ffmpeg-location', 'ffmpeg',
                    '--force-overwrites',
                    '--retries', '3',
                    '--fragment-retries', '3',
                    '--buffer-size', '16K',
                    '--http-chunk-size', '1M',
                    video_info.get('webpage_url', url)
                ]
                
                logger.info(f"Starting download with command: {' '.join(cmd)}")
                
                # Run yt-dlp with a timeout
                try:
                    process = await asyncio.wait_for(
                        asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        ),
                        timeout=300  # 5 minutes timeout for the download
                    )
                except asyncio.TimeoutError:
                    raise Exception("O download demorou muito tempo e foi cancelado")
                
                # Monitor progress
                last_update = 0
                start_time = time.time()
                last_size = 0
                
                while True:
                    # Check process status
                    if process.returncode is not None:
                        if process.returncode != 0:
                            error_output = await process.stderr.read()
                            error_msg = error_output.decode('utf-8', 'ignore')
                            logger.error(f"yt-dlp error: {error_msg}")
                            
                            # Try to get a more specific error message
                            if "Video unavailable" in error_msg:
                                raise Exception("Vídeo indisponível ou restrito")
                            elif "Private video" in error_msg:
                                raise Exception("Este vídeo é privado")
                            elif "Sign in" in error_msg:
                                raise Exception("Este vídeo requer login ou é restrito por idade")
                            else:
                                raise Exception(f"Erro ao baixar o vídeo (código {process.returncode})")
                        break
                    
                    # Update progress every 3 seconds
                    current_time = time.time()
                    if current_time - last_update >= 3 and os.path.exists(temp_path):
                        try:
                            file_size = os.path.getsize(temp_path)
                            file_size_mb = file_size / (1024 * 1024)
                            elapsed = int(current_time - start_time)
                            
                            # Calculate download speed
                            if last_size > 0 and elapsed > 0:
                                speed = (file_size - last_size) / (1024 * (current_time - last_update))
                                speed_str = f"{speed:.1f} KB/s"
                            else:
                                speed_str = "Calculando..."
                            
                            last_size = file_size
                            last_update = current_time
                            
                            await self.application.bot.edit_message_text(
                                chat_id=download_info['chat_id'],
                                message_id=download_info['message_id'],
                                text=(
                                    f"📥 *Baixando vídeo...*\n\n"
                                    f"📺 *{download_info['title']}*\n"
                                    f"💾 {file_size_mb:.1f}MB baixados\n"
                                    f"⚡ {speed_str} • 🕒 {elapsed}s"
                                ),
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.warning(f"Error updating progress: {e}")
                    
                    await asyncio.sleep(1)  # Check every second
                
                # Check if file exists and has content
                if not os.path.exists(temp_path):
                    raise Exception("Falha ao baixar o vídeo: arquivo não encontrado")
                
                # Wait a moment to ensure the file is fully written
                await asyncio.sleep(2)
                
                file_size = os.path.getsize(temp_path)
                if file_size == 0:
                    raise Exception("Falha ao baixar o vídeo: arquivo vazio")
                    
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    raise Exception("O vídeo é muito grande para ser enviado pelo Telegram (limite de 50MB)")
                
                # Verify the file is a valid video
                try:
                    # Try to open and read a small portion of the file
                    with open(temp_path, 'rb') as f:
                        header = f.read(100)  # Read first 100 bytes to verify
                        if not header:
                            raise Exception("Arquivo de vídeo inválido")
                except Exception as e:
                    raise Exception(f"Erro ao verificar o arquivo de vídeo: {str(e)}")
                
                # Send the video
                try:
                    with open(temp_path, 'rb') as video_file:
                        await self.application.bot.send_video(
                            chat_id=download_info['chat_id'],
                            video=video_file,
                            caption=f"✅ *Download concluído!*\n📌 {download_info['title']}",
                            supports_streaming=True,
                            filename=f"{download_info['title'][:50]}.mp4",
                            parse_mode='Markdown',
                            read_timeout=60,
                            write_timeout=60,
                            connect_timeout=60,
                            pool_timeout=60
                        )
                except Exception as e:
                    raise Exception(f"Erro ao enviar o vídeo: {str(e)}")
                
                # Delete progress message
                await message.delete()
                
            except Exception as e:
                logger.error(f"Error downloading/sending video: {e}", exc_info=True)
                await message.edit_text(
                    f"❌ *Erro ao processar o vídeo*\n\n"
                    f"`{str(e)}`\n\n"
                    f"Título: {download_info.get('title', 'Desconhecido')}",
                    parse_mode='Markdown'
                )
                raise
                
            finally:
                # Clean up
                if video_id in self.active_downloads:
                    del self.active_downloads[video_id]
                
                # Remove temporary file if it exists
                if temp_path and isinstance(temp_path, str) and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Error removing temporary file {temp_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in download_and_send_video: {e}", exc_info=True)
            await message.edit_text(
                f"❌ *Erro inesperado ao processar o vídeo*\n\n"
                f"`{str(e)}`\n\n"
                f"Título: {download_info.get('title', 'Desconhecido')}",
                parse_mode='Markdown'
            )
        finally:
            # Clean up
            if video_id in self.active_downloads:
                del self.active_downloads[video_id]
            # Remove temporary file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Error removing temporary file {temp_path}: {e}")
    
    async def on_download_progress(self, download_id: str, stream, chunk: bytes, bytes_remaining: int) -> None:
        """Update progress message."""
        try:
            if download_id not in self.active_downloads:
                return
                
            total_size = stream.filesize
            if total_size <= 0:
                return
                
            bytes_downloaded = total_size - bytes_remaining
            progress = (bytes_downloaded / total_size) * 100
            
            download_info = self.active_downloads[download_id]
            
            # Update progress every 5% or if download is complete
            if progress % 5 < 0.1 or bytes_remaining == 0:
                try:
                    await self.application.bot.edit_message_text(
                        chat_id=download_info['chat_id'],
                        message_id=download_info['message_id'],
                        text=(
                            f"📥 Baixando: {download_info.get('title', 'Vídeo')}\n"
                            f"📊 {progress:.1f}% concluído\n"
                            f"📦 {bytes_downloaded/1024/1024:.1f}MB de {total_size/1024/1024:.1f}MB"
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error updating progress: {e}")
        except Exception as e:
            logger.error(f"Error in on_download_progress: {e}")
    
    async def on_download_complete(self, download_id: str, result, message) -> None:
        """Legacy method kept for compatibility."""
        pass
    
    async def on_download_error(self, download_id: str, error: str, message) -> None:
        """Handle download errors."""
        try:
            if isinstance(message, str):
                # If message is just a message ID
                chat_id = self.active_downloads.get(download_id, {}).get('chat_id')
                if chat_id:
                    await self.application.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message,
                        text=f"❌ Erro no download: {error}"
                    )
            else:
                # If message is a message object
                try:
                    await message.edit_text(f"❌ Erro no download: {error}")
                except Exception as e:
                    logger.error(f"Error updating error message: {e}")
                    try:
                        await message.reply_text(f"❌ Erro no download: {error}")
                    except Exception as e:
                        logger.error(f"Error replying with error message: {e}")
        except Exception as e:
            logger.error(f"Error in on_download_error: {e}")
        finally:
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
    
    def run(self) -> None:
        """Start the bot."""
        self.application.run_polling()


def main():
    """Command-line interface for the YouTube Downloader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download videos from YouTube.')
    parser.add_argument('url', nargs='?', help='YouTube video URL')
    parser.add_argument('-o', '--output', default='downloads', 
                       help='Output directory (default: downloads)')
    parser.add_argument('-r', '--resolution', 
                       help='Preferred resolution (e.g., 720p, 1080p)')
    parser.add_argument('--telegram', action='store_true',
                       help='Run as Telegram bot')
    parser.add_argument('--token', help='Telegram bot token')
    
    args = parser.parse_args()
    
    if args.telegram:
        if not args.token:
            print("Erro: Token do bot Telegram não fornecido. Use --token SEU_TOKEN")
            return
            
        print("Iniciando bot do Telegram...")
        bot = TelegramBotExample(args.token, download_dir=args.output)
        bot.run()
    elif args.url:
        downloader = YouTubeDownloader(download_dir=args.output)
        
        def on_progress(stream, chunk, bytes_remaining):
            total = stream.filesize
            downloaded = total - bytes_remaining
            percent = (downloaded / total) * 100
            print(f"\rProgresso: {percent:.1f}%", end="", flush=True)
        
        print(f"Baixando: {args.url}")
        success, result = downloader.download_video(
            args.url,
            output_path=args.output,
            resolution=args.resolution,
            on_progress=on_progress
        )
        
        if success:
            print(f"\nDownload concluído: {result}")
        else:
            print(f"\nErro: {result}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
