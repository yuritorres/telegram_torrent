import os
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv
from src.integrations.jellyfin.client import JellyfinClient
from src.integrations.jellyfin.formatter import JellyfinFormatter

load_dotenv()
logger = logging.getLogger(__name__)


class JellyfinManager:
    """Gerenciador principal do Jellyfin para integração com Telegram"""

    def __init__(self):
        self.url = os.getenv('JELLYFIN_URL')
        self.username = os.getenv('JELLYFIN_USERNAME')
        self.password = os.getenv('JELLYFIN_PASSWORD')
        self.api_key = os.getenv('JELLYFIN_API_KEY')
        self.client: Optional[JellyfinClient] = None
        self.known_items = set()

        if self.url:
            self.client = JellyfinClient(self.url, self.username, self.password, self.api_key)
            if self.username and self.password:
                self.client.authenticate()

    def is_available(self) -> bool:
        return self.client is not None and (self.api_key or self.client.access_token)

    def get_recently_added(self, limit: int = 10) -> List[Dict]:
        if not self.is_available():
            return []
        return self.client.get_recently_added(limit)

    def get_libraries(self) -> List[Dict]:
        if not self.is_available():
            return []
        return self.client.get_libraries()

    def get_server_info(self) -> Optional[Dict]:
        if not self.is_available():
            return None
        return self.client.get_system_info()

    def get_recent_items_text(self, limit: int = 10) -> str:
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        try:
            items = self.client.get_recently_added(limit)
            if not items:
                return "📥 Nenhum item recente encontrado."
            messages = []
            for item in items:
                web_link = self.client.get_web_link(item['Id'])
                message = JellyfinFormatter.format_telegram_message(item, web_link)
                messages.append(message)
            return "🎬 **Itens recentemente adicionados:**\n\n" + "\n\n".join(messages)
        except Exception as e:
            logger.error(f"Erro ao obter itens recentes: {e}")
            return f"❌ Erro ao buscar itens recentes: {str(e)}"

    def get_libraries_text(self) -> str:
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        try:
            libraries = self.client.get_libraries()
            if not libraries:
                return "❌ Nenhuma biblioteca encontrada."
            text = "📚 **Bibliotecas Disponíveis:**\n\n"
            for lib in libraries:
                name = lib.get('Name', 'N/A')
                lib_type = lib.get('CollectionType', 'N/A')
                text += f"• {name} ({lib_type})\n"
            return text
        except Exception as e:
            logger.error(f"Erro ao obter bibliotecas: {e}")
            return f"❌ Erro ao buscar bibliotecas: {str(e)}"

    def get_status_text(self) -> str:
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        try:
            libraries = self.client.get_libraries()
            recent_items = self.client.get_recently_added(1)
            status_text = f"""🟢 **Status do Servidor Jellyfin**

🌐 Servidor: {self.url}
👤 Usuário: {self.username}
📚 Bibliotecas: {len(libraries)}
🆕 Último item: {recent_items[0].get('Name', 'N/A') if recent_items else 'N/A'}

✅ Conexão OK"""
            return status_text
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return f"❌ Erro de conexão: {str(e)}"
