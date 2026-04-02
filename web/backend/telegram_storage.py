"""
Telegram Storage Service
Stores and retrieves files directly from Telegram using the Bot API
"""
import os
import requests
import logging
import json
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


class TelegramStorageService:
    """Service to store and retrieve files from Telegram"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Local metadata storage (maps file_id to metadata)
        _base_dir = Path(__file__).parent / "appstore_data"
        self.metadata_file = _base_dir / "telegram_files_metadata.json"
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """Load file metadata from local storage"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save file metadata to local storage"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def is_configured(self) -> bool:
        """Check if Telegram credentials are configured"""
        return bool(self.bot_token and self.chat_id)
    
    def save_file(self, filename: str, content: str, file_type: str = "text") -> Optional[Dict]:
        """
        Save a file to Telegram
        
        Args:
            filename: Name of the file
            content: File content (text)
            file_type: Type of file (text, code, markdown, etc.)
        
        Returns:
            Dict with file_id and metadata, or None if failed
        """
        if not self.is_configured():
            raise ValueError("Telegram credentials (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) are not configured")
        
        try:
            # Create temporary file
            temp_path = Path(__file__).parent / "appstore_data" / f"temp_{filename}"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Send to Telegram
            url = f"{self.base_url}/sendDocument"
            
            with open(temp_path, 'rb') as f:
                files = {'document': (filename, f, 'text/plain')}
                data = {
                    'chat_id': self.chat_id,
                    'caption': f"📄 {filename}\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
                
                resp = requests.post(url, files=files, data=data, timeout=60)
                if resp.status_code != 200:
                    logger.error(f"Telegram API error: {resp.status_code} - {resp.text}")
                resp.raise_for_status()
                result = resp.json()
            
            # Clean up temp file
            temp_path.unlink()
            
            if result.get('ok'):
                document = result['result']['document']
                file_id = document['file_id']
                
                # Store metadata
                self.metadata[file_id] = {
                    'filename': filename,
                    'file_type': file_type,
                    'file_id': file_id,
                    'file_size': document.get('file_size', 0),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'message_id': result['result']['message_id']
                }
                self._save_metadata()
                
                logger.info(f"File saved to Telegram: {filename} (file_id: {file_id})")
                return self.metadata[file_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving file to Telegram: {e}")
            raise
    
    def get_file(self, file_id: str) -> Optional[Dict]:
        """
        Retrieve a file from Telegram
        
        Args:
            file_id: Telegram file_id
        
        Returns:
            Dict with 'content' and 'metadata', or None if failed
        """
        try:
            # Get file path from Telegram
            url = f"{self.base_url}/getFile"
            resp = requests.get(url, params={'file_id': file_id}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            
            if not result.get('ok'):
                return None
            
            file_path = result['result']['file_path']
            
            # Download file content
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            download_resp = requests.get(download_url, timeout=60)
            download_resp.raise_for_status()
            
            content = download_resp.text
            metadata = self.metadata.get(file_id, {})
            
            return {
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error retrieving file from Telegram: {e}")
            return None
    
    def update_file(self, file_id: str, content: str) -> Optional[Dict]:
        """
        Update a file in Telegram (creates new version)
        
        Args:
            file_id: Original file_id
            content: New content
        
        Returns:
            New file metadata, or None if failed
        """
        try:
            metadata = self.metadata.get(file_id)
            if not metadata:
                logger.error(f"File not found: {file_id}")
                return None
            
            filename = metadata['filename']
            file_type = metadata.get('file_type', 'text')
            
            # Delete old message
            self.delete_file(file_id)
            
            # Save new version
            return self.save_file(filename, content, file_type)
            
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Telegram
        
        Args:
            file_id: Telegram file_id
        
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata = self.metadata.get(file_id)
            if not metadata:
                return False
            
            message_id = metadata.get('message_id')
            if message_id:
                url = f"{self.base_url}/deleteMessage"
                data = {
                    'chat_id': self.chat_id,
                    'message_id': message_id
                }
                resp = requests.post(url, json=data, timeout=30)
                resp.raise_for_status()
            
            # Remove from metadata
            del self.metadata[file_id]
            self._save_metadata()
            
            logger.info(f"File deleted from Telegram: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def list_files(self) -> List[Dict]:
        """
        List all files stored in Telegram
        
        Returns:
            List of file metadata
        """
        files = []
        for file_id, metadata in self.metadata.items():
            files.append({
                'file_id': file_id,
                'filename': metadata.get('filename', 'unknown'),
                'file_type': metadata.get('file_type', 'text'),
                'file_size': metadata.get('file_size', 0),
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at')
            })
        
        # Sort by updated_at (most recent first)
        files.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return files
    
    def search_files(self, query: str) -> List[Dict]:
        """
        Search files by filename
        
        Args:
            query: Search query
        
        Returns:
            List of matching file metadata
        """
        query_lower = query.lower()
        results = []
        
        for file_id, metadata in self.metadata.items():
            filename = metadata.get('filename', '').lower()
            if query_lower in filename:
                results.append({
                    'file_id': file_id,
                    'filename': metadata.get('filename', 'unknown'),
                    'file_type': metadata.get('file_type', 'text'),
                    'file_size': metadata.get('file_size', 0),
                    'created_at': metadata.get('created_at'),
                    'updated_at': metadata.get('updated_at')
                })
        
        results.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return results
