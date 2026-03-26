import os
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv
from src.integrations.jellyfin.client import JellyfinClient
from src.integrations.jellyfin.formatter import JellyfinFormatter
from src.core.config import JELLYFIN_ACCOUNTS_LIST, JELLYFIN_MULTI_ACCOUNT_ENABLED

load_dotenv()
logger = logging.getLogger(__name__)


class JellyfinManager:
    """Gerenciador principal do Jellyfin para integração com Telegram (suporta múltiplas contas)"""

    def __init__(self):
        self.clients: List[JellyfinClient] = []
        self.known_items = set()
        self.multi_account_enabled = JELLYFIN_MULTI_ACCOUNT_ENABLED
        
        # Inicializa clientes para cada conta configurada
        for account in JELLYFIN_ACCOUNTS_LIST:
            url = account.get('url')
            username = account.get('username')
            password = account.get('password')
            api_key = account.get('api_key')
            
            if url:
                client = JellyfinClient(url, username, password, api_key)
                if username and password:
                    if client.authenticate():
                        self.clients.append(client)
                        logger.info(f"Cliente Jellyfin autenticado: {url}")
                    else:
                        logger.warning(f"Falha na autenticação do Jellyfin: {url}")
                elif api_key:
                    self.clients.append(client)
                    logger.info(f"Cliente Jellyfin configurado com API Key: {url}")
        
        if not self.clients:
            logger.warning("Nenhuma conta Jellyfin configurada ou disponível")
        else:
            logger.info(f"JellyfinManager inicializado com {len(self.clients)} conta(s)")
    
    @property
    def client(self) -> Optional[JellyfinClient]:
        """Retorna o primeiro cliente disponível (compatibilidade com código legado)"""
        return self.clients[0] if self.clients else None

    def is_available(self) -> bool:
        """Verifica se há pelo menos uma conta Jellyfin disponível"""
        return len(self.clients) > 0

    def get_recently_added(self, limit: int = 10) -> List[Dict]:
        """Obtém itens recentes de todas as contas Jellyfin"""
        if not self.is_available():
            return []
        
        all_items = []
        for client in self.clients:
            try:
                items = client.get_recently_added(limit)
                # Adiciona informação da URL do servidor para identificação
                for item in items:
                    item['_jellyfin_url'] = client.url
                all_items.extend(items)
            except Exception as e:
                logger.error(f"Erro ao obter itens recentes de {client.url}: {e}")
        
        # Ordena por data de criação (mais recentes primeiro)
        all_items.sort(key=lambda x: x.get('DateCreated', ''), reverse=True)
        return all_items[:limit]

    def get_libraries(self) -> List[Dict]:
        """Obtém bibliotecas de todas as contas Jellyfin"""
        if not self.is_available():
            return []
        
        all_libraries = []
        for client in self.clients:
            try:
                libraries = client.get_libraries()
                # Adiciona informação da URL do servidor
                for lib in libraries:
                    lib['_jellyfin_url'] = client.url
                all_libraries.extend(libraries)
            except Exception as e:
                logger.error(f"Erro ao obter bibliotecas de {client.url}: {e}")
        
        return all_libraries

    def get_server_info(self) -> Optional[Dict]:
        """Obtém informações do primeiro servidor (compatibilidade)"""
        if not self.is_available():
            return None
        return self.clients[0].get_system_info()
    
    def get_all_servers_info(self) -> List[Dict]:
        """Obtém informações de todos os servidores Jellyfin"""
        if not self.is_available():
            return []
        
        servers_info = []
        for client in self.clients:
            try:
                info = client.get_system_info()
                if info:
                    info['_jellyfin_url'] = client.url
                    servers_info.append(info)
            except Exception as e:
                logger.error(f"Erro ao obter info do servidor {client.url}: {e}")
        
        return servers_info

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
        """Obtém status de todas as contas Jellyfin"""
        if not self.is_available():
            return "❌ Jellyfin não configurado ou indisponível."
        
        try:
            status_parts = []
            for idx, client in enumerate(self.clients, 1):
                try:
                    libraries = client.get_libraries()
                    recent_items = client.get_recently_added(1)
                    
                    if self.multi_account_enabled:
                        status_parts.append(f"🟢 **Servidor Jellyfin #{idx}**")
                    else:
                        status_parts.append(f"🟢 **Status do Servidor Jellyfin**")
                    
                    status_parts.append(f"🌐 Servidor: {client.url}")
                    if client.username:
                        status_parts.append(f"👤 Usuário: {client.username}")
                    status_parts.append(f"📚 Bibliotecas: {len(libraries)}")
                    status_parts.append(f"🆕 Último item: {recent_items[0].get('Name', 'N/A') if recent_items else 'N/A'}")
                    status_parts.append("✅ Conexão OK")
                    
                    if idx < len(self.clients):
                        status_parts.append("")  # Linha em branco entre servidores
                except Exception as e:
                    logger.error(f"Erro ao obter status de {client.url}: {e}")
                    status_parts.append(f"❌ Erro no servidor {client.url}: {str(e)}")
            
            return "\n".join(status_parts)
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return f"❌ Erro de conexão: {str(e)}"
