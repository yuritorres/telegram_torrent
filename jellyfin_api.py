import aiohttp
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JellyfinAPI:
    def __init__(self, server_url: str, username: str, password: str):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token = None
        self.user_id = None
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self):
        """Autentica no servidor Jellyfin"""
        auth_data = {
            "Username": self.username,
            "Pw": self.password
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": 'MediaBrowser Client="JellyfinTelegramBot", Device="Python", DeviceId="telegram-bot", Version="1.0.0"'
        }
        
        try:
            async with self.session.post(
                f"{self.server_url}/Users/authenticatebyname",
                json=auth_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data['AccessToken']
                    self.user_id = data['User']['Id']
                    logger.info("Autenticação no Jellyfin bem-sucedida")
                else:
                    raise Exception(f"Falha na autenticação: {response.status}")
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            raise
    
    def get_headers(self):
        """Retorna headers para requisições autenticadas"""
        return {
            "X-Emby-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    async def get_libraries(self):
        """Obtém todas as bibliotecas do usuário"""
        try:
            async with self.session.get(
                f"{self.server_url}/Users/{self.user_id}/Views",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['Items']
                return []
        except Exception as e:
            logger.error(f"Erro ao obter bibliotecas: {e}")
            return []
    
    async def get_recent_items(self, limit: int = 20):
        """Obtém itens recentemente adicionados"""
        try:
            params = {
                "Limit": limit,
                "Recursive": "true",
                "IncludeItemTypes": "Movie,Series,Episode",
                "SortBy": "DateCreated",
                "SortOrder": "Descending",
                "Fields": "Overview,Genres,DateCreated,UserData"
            }
            
            async with self.session.get(
                f"{self.server_url}/Users/{self.user_id}/Items",
                headers=self.get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['Items']
                return []
        except Exception as e:
            logger.error(f"Erro ao obter itens recentes: {e}")
            return []
    
    async def get_item_details(self, item_id: str):
        """Obtém detalhes de um item específico"""
        try:
            async with self.session.get(
                f"{self.server_url}/Users/{self.user_id}/Items/{item_id}",
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do item: {e}")
            return None
    
    async def mark_watched(self, item_id: str):
        """Marca um item como assistido"""
        try:
            async with self.session.post(
                f"{self.server_url}/Users/{self.user_id}/PlayedItems/{item_id}",
                headers=self.get_headers()
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Erro ao marcar como assistido: {e}")
            return False
    
    async def mark_unwatched(self, item_id: str):
        """Marca um item como não assistido"""
        try:
            async with self.session.delete(
                f"{self.server_url}/Users/{self.user_id}/PlayedItems/{item_id}",
                headers=self.get_headers()
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Erro ao marcar como não assistido: {e}")
            return False
    
    async def search_items(self, query: str, limit: int = 10):
        """Busca itens por nome"""
        try:
            params = {
                "searchTerm": query,
                "Limit": limit,
                "IncludeItemTypes": "Movie,Series,Episode",
                "Fields": "Overview,Genres,UserData"
            }
            
            async with self.session.get(
                f"{self.server_url}/Users/{self.user_id}/Items",
                headers=self.get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['Items']
                return []
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
