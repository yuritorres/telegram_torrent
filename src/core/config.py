import os
from dotenv import load_dotenv

load_dotenv()

# qBittorrent - Configuração Unificada (suporta uma ou múltiplas instâncias)
# Nomes das instâncias (separados por vírgula)
QB_NAMES = os.getenv('QB_NAMES', 'default')
# URLs das instâncias (separadas por vírgula)
QB_URLS = os.getenv('QB_URLS', 'http://localhost:8080')
# Usuários (separados por vírgula, padrão: admin)
QB_USERS = os.getenv('QB_USERS', 'admin')
# Senhas (separadas por vírgula, padrão: adminadmin)
QB_PASSWORDS = os.getenv('QB_PASSWORDS', 'adminadmin')
# Caminhos de armazenamento (separados por vírgula, padrão: /)
QB_STORAGE_PATHS = os.getenv('QB_STORAGE_PATHS', '/')
# Prioridades (separadas por vírgula, padrão: 0)
QB_PRIORITIES = os.getenv('QB_PRIORITIES', '0')
# Intervalo de verificação em segundos
INTERVALO = int(os.getenv('INTERVALO', 30))

# Backward compatibility - mantém variáveis antigas
QB_URL = os.getenv('QB_URL', QB_URLS.split(',')[0].strip())
QB_USER = os.getenv('QB_USER', QB_USERS.split(',')[0].strip())
QB_PASS = os.getenv('QB_PASS', QB_PASSWORDS.split(',')[0].strip())
QBITTORRENT_STORAGE_PATH = os.getenv('QBITTORRENT_STORAGE_PATH', QB_STORAGE_PATHS.split(',')[0].strip())


def parse_qb_instances():
    """Parse qBittorrent instances from comma-separated environment variables"""
    names = [n.strip() for n in QB_NAMES.split(',') if n.strip()]
    urls = [u.strip() for u in QB_URLS.split(',') if u.strip()]
    users = [u.strip() for u in QB_USERS.split(',') if u.strip()]
    passwords = [p.strip() for p in QB_PASSWORDS.split(',') if p.strip()]
    storage_paths = [s.strip() for s in QB_STORAGE_PATHS.split(',') if s.strip()]
    priorities = [p.strip() for p in QB_PRIORITIES.split(',') if p.strip()]
    
    instances = []
    for i in range(len(urls)):
        instance = {
            'name': names[i] if i < len(names) else f'instance-{i+1}',
            'url': urls[i],
            'username': users[i] if i < len(users) else 'admin',
            'password': passwords[i] if i < len(passwords) else 'adminadmin',
            'storage_path': storage_paths[i] if i < len(storage_paths) else '/',
            'priority': int(priorities[i]) if i < len(priorities) and priorities[i].isdigit() else 0,
        }
        instances.append(instance)
    
    return instances


QB_INSTANCES_LIST = parse_qb_instances()
# Multi-instance habilitado se houver mais de uma URL configurada
QB_MULTI_INSTANCE_ENABLED = len(QB_INSTANCES_LIST) > 1

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AUTHORIZED_USERS = [uid.strip() for uid in os.getenv('AUTHORIZED_USERS', '').split(',') if uid.strip()]
EXPIRAR_MSG = int(os.getenv('EXPIRAR_MSG', 30))

# Jellyfin - Configuração Unificada (suporta uma ou múltiplas contas)
# URLs das contas (separadas por vírgula)
JELLYFIN_URL = os.getenv('JELLYFIN_URL', '')
# Usernames (separados por vírgula)
JELLYFIN_USERNAME = os.getenv('JELLYFIN_USERNAME', '')
# Passwords (separadas por vírgula)
JELLYFIN_PASSWORD = os.getenv('JELLYFIN_PASSWORD', '')
# API Keys (separadas por vírgula)
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY', '')
JELLYFIN_NOTIFICATIONS_ENABLED = os.getenv('JELLYFIN_NOTIFICATIONS_ENABLED', 'False').lower() in ('true', '1', 't')
JELLYFIN_NOTIFICATION_INTERVAL = int(os.getenv('JELLYFIN_NOTIFICATION_INTERVAL', 1800))


def parse_jellyfin_accounts():
    """Parse Jellyfin accounts from comma-separated environment variables"""
    urls = [u.strip() for u in JELLYFIN_URL.split(',') if u.strip()]
    usernames = [u.strip() for u in JELLYFIN_USERNAME.split(',') if u.strip()]
    passwords = [p.strip() for p in JELLYFIN_PASSWORD.split(',') if p.strip()]
    api_keys = [k.strip() for k in JELLYFIN_API_KEY.split(',') if k.strip()]
    
    accounts = []
    for i in range(len(urls)):
        account = {
            'url': urls[i],
            'username': usernames[i] if i < len(usernames) else '',
            'password': passwords[i] if i < len(passwords) else '',
            'api_key': api_keys[i] if i < len(api_keys) else '',
        }
        accounts.append(account)
    
    return accounts


JELLYFIN_ACCOUNTS_LIST = parse_jellyfin_accounts()
# Multi-account habilitado se houver mais de uma URL configurada
JELLYFIN_MULTI_ACCOUNT_ENABLED = len(JELLYFIN_ACCOUNTS_LIST) > 1

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
