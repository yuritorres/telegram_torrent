import os
from dotenv import load_dotenv

load_dotenv()

# qBittorrent
QB_URL = os.getenv('QB_URL', 'http://localhost:8080')
QB_USER = os.getenv('QB_USER', 'admin')
QB_PASS = os.getenv('QB_PASS', 'adminadmin')
INTERVALO = int(os.getenv('INTERVALO', 30))
QBITTORRENT_STORAGE_PATH = os.getenv('QBITTORRENT_STORAGE_PATH', '/')

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AUTHORIZED_USERS = [uid.strip() for uid in os.getenv('AUTHORIZED_USERS', '').split(',') if uid.strip()]
EXPIRAR_MSG = int(os.getenv('EXPIRAR_MSG', 30))

# Jellyfin
JELLYFIN_URL = os.getenv('JELLYFIN_URL')
JELLYFIN_USERNAME = os.getenv('JELLYFIN_USERNAME')
JELLYFIN_PASSWORD = os.getenv('JELLYFIN_PASSWORD')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY')
JELLYFIN_NOTIFICATIONS_ENABLED = os.getenv('JELLYFIN_NOTIFICATIONS_ENABLED', 'False').lower() in ('true', '1', 't')
JELLYFIN_NOTIFICATION_INTERVAL = int(os.getenv('JELLYFIN_NOTIFICATION_INTERVAL', 1800))

# WhatsApp (WAHA)
WAHA_URL = os.getenv('WAHA_URL', 'http://localhost:3000')
WAHA_API_KEY = os.getenv('WAHA_API_KEY', 'local-dev-key-123')
WAHA_SESSION = os.getenv('WAHA_SESSION', 'default')
AUTHORIZED_WHATSAPP_NUMBERS = [n.strip() for n in os.getenv('AUTHORIZED_WHATSAPP_NUMBERS', '').split(',') if n.strip()]
AUTHORIZED_WHATSAPP_GROUP = os.getenv('AUTHORIZED_WHATSAPP_GROUP', '').strip()
WAHA_DASHBOARD_USERNAME = os.getenv('WAHA_DASHBOARD_USERNAME', 'admin')
WAHA_DASHBOARD_PASSWORD = os.getenv('WAHA_DASHBOARD_PASSWORD', 'admin123')
WAHA_SWAGGER_USERNAME = os.getenv('WAHA_SWAGGER_USERNAME', 'admin')
WAHA_SWAGGER_PASSWORD = os.getenv('WAHA_SWAGGER_PASSWORD', 'swagger123')

# YouTube
YOUTUBE_DOWNLOAD_DIR = os.getenv('YOUTUBE_DOWNLOAD_DIR', 'downloads')
REMOVE_AFTER_SEND = os.getenv('REMOVE_AFTER_SEND', 'True').lower() in ('true', '1', 't')

# Sync
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 30))
AUTO_SCAN_JELLYFIN = os.getenv('AUTO_SCAN_JELLYFIN', 'True').lower() in ('true', '1', 't')
