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
from typing import Callable, Dict, Optional, Tuple, Union, Any
from urllib.parse import urlparse, parse_qs
from urllib.error import HTTPError
from dataclasses import dataclass
from enum import Enum

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
    
    def get_video_info(self, url: str) -> Optional[YouTube]:
        """
        Get video information without downloading.
        
        Args:
            url: YouTube video URL
            
        Returns:
            YouTube object with video information or None if failed
        """
        try:
            # Clean and validate URL
            orig_url = url
            if 'youtu.be' in url:
                # Convert youtu.be/xxx to youtube.com/watch?v=xxx
                video_id = url.split('/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            elif 'youtube.com/shorts/' in url:
                # Convert shorts URL to regular watch URL
                video_id = url.split('/shorts/')[-1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            # Remove any fragment or extra params not needed
            url = url.split('&')[0]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    yt = YouTube(
                        url,
                        use_oauth=False,
                        allow_oauth_cache=True
                    )
                    _ = yt.title
                    _ = yt.author
                    return yt
                except HTTPError as http_err:
                    if http_err.code == 429:
                        wait_time = (2 ** attempt) * 5
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    logger.error(f"HTTP Error {http_err.code} getting video info for url {url}: {http_err}")
                    return None
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Error getting video info for url {url} (original: {orig_url}) after {max_retries} attempts: {e}", exc_info=True)
                        return None
                    logger.warning(f"Error getting video info for url {url} (original: {orig_url}) (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_video_info for url {url}: {e}", exc_info=True)
            return None


    def download_video(
        self,
        url: str,
        output_path: Optional[str] = None,
        resolution: Optional[str] = None,
        on_progress: Optional[Callable[[Stream, bytes, int], None]] = None,
        on_complete: Optional[Callable[[str, bytes], None]] = None,  # Changed to accept bytes
        on_error: Optional[Callable[[str, str], None]] = None,
        download_id: Optional[str] = None,
        in_memory: bool = True  # New parameter to control if download to memory or file
    ) -> Tuple[bool, Union[str, bytes]]:  # Changed return type to support bytes
        """
        Download a YouTube video with progress tracking.
        
        Args:
            url: YouTube video URL
            output_path: Directory to save the video (defaults to download_dir)
            resolution: Desired resolution (e.g., '720p', '1080p')
            on_progress: Callback for download progress
            on_complete: Callback when download completes successfully (receives file path or bytes)
            on_error: Callback when download fails
            download_id: Optional ID to track this download
            in_memory: If True, download to memory instead of file
            
        Returns:
            Tuple of (success: bool, message: str or bytes)
        """
        if output_path is None:
            output_path = self.download_dir
            
        download_id = download_id or self.get_video_id(url)
        
        # Initialize download info
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
                error_msg = "Could not get video information"
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg
                
            # Update video info in active downloads
            with self.lock:
                if download_id in self.active_downloads:
                    self.active_downloads[download_id]['info'] = {
                        'title': video_info.title,
                        'author': video_info.author,
                        'length': video_info.length,
                        'views': video_info.views,
                        'default_filename': video_info.default_filename
                    }
            
            # Get the best stream based on resolution preference
            if resolution:
                stream = video_info.streams.filter(
                    progressive=True,
                    file_extension='mp4',
                    resolution=resolution
                ).first()
                
                # If preferred resolution not found, try to get the closest one
                if not stream and resolution.endswith('p'):
                    try:
                        res_num = int(resolution[:-1])
                        available_resolutions = sorted(
                            [int(s.resolution[:-1]) for s in video_info.streams.filter(progressive=True, file_extension='mp4') if s.resolution],
                            reverse=True
                        )
                        
                        # Find the closest resolution that's <= requested resolution
                        for res in available_resolutions:
                            if res <= res_num:
                                stream = video_info.streams.filter(
                                    progressive=True,
                                    file_extension='mp4',
                                    resolution=f"{res}p"
                                ).first()
                                if stream:
                                    break
                    except (ValueError, AttributeError):
                        pass
            
            # If still no stream, get the highest resolution
            if not stream:
                stream = video_info.streams.get_highest_resolution()
            
            if not stream:
                error_msg = "No suitable video stream found."
                if on_error:
                    on_error(download_id, error_msg)
                return False, error_msg
            
            # Register progress callback
            if on_progress:
                def progress_callback(stream, chunk, bytes_remaining):
                    total = stream.filesize
                    if total > 0:
                        progress = ((total - bytes_remaining) / total) * 100
                        on_progress(stream, chunk, bytes_remaining)
                
                stream.register_on_progress_callback(progress_callback)
            
            # Start download
            try:
                if in_memory:
                    # Download to memory
                    buffer = io.BytesIO()
                    stream.stream_to_buffer(buffer)
                    buffer.seek(0)
                    
                    # Update status to completed
                    with self.lock:
                        if download_id in self.active_downloads:
                            self.active_downloads[download_id].update({
                                'status': DownloadStatus.COMPLETED,
                                'progress': 100.0
                            })
                    
                    # Call completion callback with bytes
                    if on_complete:
                        on_complete(download_id, buffer.getvalue())
                    
                    return True, buffer.getvalue()
                else:
                    # Create output directory if it doesn't exist
                    os.makedirs(output_path, exist_ok=True)
                    
                    # Determine filename
                    if not filename:
                        filename = video_info.title
                    
                    # Sanitize filename
                    filename = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in filename)
                    if not filename.endswith('.mp4'):
                        filename += '.mp4'
                    
                    file_path = os.path.join(output_path, filename)
                    
                    # Download to file
                    stream.download(
                        output_path=output_path,
                        filename=os.path.basename(file_path),
                        skip_existing=False
                    )
                    
                    # Verify file was downloaded
                    if not os.path.exists(file_path):
                        raise Exception("Downloaded file not found")
                    
                    # Update status to completed
                    with self.lock:
                        if download_id in self.active_downloads:
                            self.active_downloads[download_id].update({
                                'status': DownloadStatus.COMPLETED,
                                'progress': 100.0,
                                'file_path': file_path
                            })
                    
                    # Call completion callback with file path
                    if on_complete:
                        on_complete(download_id, file_path)
                    
                    return True, file_path
                
            except Exception as e:
                error_msg = f"Download failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # Update status to failed
                with self.lock:
                    if download_id in self.active_downloads:
                        self.active_downloads[download_id].update({
                            'status': DownloadStatus.FAILED,
                            'error': error_msg
                        })
                
                # Call error callback
                if on_error:
                    on_error(download_id, error_msg)
                
                return False, error_msg
                
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if on_error:
                on_error(download_id, error_msg)
                
            return False, error_msg
            
        finally:
            # Clean up if download was not successful
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
            f"📺 *{video_info.title}*\n"
            f"👤 {video_info.author}\n"
            f"⏱️ {video_info.length // 60}:{video_info.length % 60:02d}\n"
            f"📊 {video_info.views:,} visualizações\n\n"
            "📥 Iniciando download...",
            parse_mode="Markdown"
        )
        
        # Store message info for updates
        self.active_downloads[video_id] = {
            'message_id': message.message_id,
            'chat_id': update.effective_chat.id,
            'title': video_info.title,
            'url': url
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
    
    async def on_download_progress(self, download_id: str, progress: float) -> None:
        """Update progress message."""
        if download_id not in self.active_downloads:
            return
            
        status = self.downloader.get_download_status(download_id)
        if not status:
            return
            
        try:
            await self.application.bot.edit_message_text(
                chat_id=self.active_downloads[download_id]['chat_id'],
                message_id=self.active_downloads[download_id]['message_id'],
                text=(
                    f"📥 Baixando...\n"
                    f"📌 {status['info']['title']}\n"
                    f"📊 {progress:.1f}% concluído"
                )
            )
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    async def download_and_send_video(self, video_id: str, message) -> None:
        """Download video to disk and then send to Telegram."""
        if video_id not in self.active_downloads:
            return
            
        download_info = self.active_downloads[video_id]
        url = download_info['url']
        
        try:
            # Create downloads directory if it doesn't exist
            os.makedirs(self.downloader.download_dir, exist_ok=True)
            
            # Update status to downloading
            await self.application.bot.edit_message_text(
                chat_id=download_info['chat_id'],
                message_id=download_info['message_id'],
                text=f"📥 Baixando: {download_info['title']}\n🔄 0% concluído"
            )
            
            # Generate a safe filename
            safe_title = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in download_info['title'])
            file_path = os.path.join(self.downloader.download_dir, f"{safe_title[:100]}_{video_id}.mp4")
            
            # Download the video to disk
            success, result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.downloader.download_video(
                    url=url,
                    output_path=self.downloader.download_dir,
                    filename=os.path.basename(file_path),
                    on_progress=lambda s, c, r: asyncio.create_task(
                        self.on_download_progress(video_id, s, c, r)
                    )
                )
            )
            
            if not success or not os.path.exists(file_path):
                raise Exception("Falha ao baixar o vídeo" if not result else result)
            
            # Get video file size
            file_size = os.path.getsize(file_path)
            
            # Check if file is too large for Telegram (max 50MB for bots)
            if file_size > 50 * 1024 * 1024:  # 50MB
                raise Exception("O vídeo é muito grande para ser enviado pelo Telegram (limite de 50MB)")
            
            # Send the video
            with open(file_path, 'rb') as video_file:
                await self.application.bot.send_video(
                    chat_id=download_info['chat_id'],
                    video=video_file,
                    caption=f"✅ Download concluído!\n📌 {download_info['title']}",
                    supports_streaming=True,
                    filename=os.path.basename(file_path)
                )
            
            # Delete progress message
            await message.delete()
            
        except Exception as e:
            logger.error(f"Error downloading/sending video: {e}", exc_info=True)
            await message.edit_text(
                f"❌ Erro ao processar o vídeo: {str(e)}\n"
                f"Título: {download_info.get('title', 'Desconhecido')}"
            )
            
        finally:
            # Clean up
            if video_id in self.active_downloads:
                del self.active_downloads[video_id]
            
            # Remove the downloaded file after sending (optional)
            try:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Error removing temporary file {file_path}: {e}")
    
    async def on_download_progress(self, download_id: str, stream, chunk: bytes, bytes_remaining: int) -> None:
        """Update progress message."""
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
                except Exception:
                    await message.reply_text(f"❌ Erro no download: {error}")
        except Exception as e:
            logger.error(f"Error updating error message: {e}")
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
