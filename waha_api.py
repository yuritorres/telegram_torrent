"""
Módulo para integração com a API WhatsApp WAHA
"""
import requests
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class WAHAApi:
    """Cliente para interagir com a API WhatsApp WAHA"""
    
    def __init__(self, base_url: str, api_key: str, session_name: str = "default"):
        """
        Inicializa o cliente WAHA
        
        Args:
            base_url: URL base da API WAHA (ex: http://localhost:3000)
            api_key: Chave de API para autenticação
            session_name: Nome da sessão WhatsApp (padrão: "default")
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_name = session_name
        self.headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': api_key
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Faz uma requisição HTTP para a API WAHA
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Resposta JSON ou None em caso de erro
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição WAHA {method} {endpoint}: {e}")
            return None
    
    def start_session(self) -> bool:
        """
        Inicia uma sessão WhatsApp
        
        Returns:
            True se a sessão foi iniciada com sucesso
        """
        try:
            data = {"name": self.session_name}
            result = self._make_request('POST', '/api/sessions', json=data)
            
            if result:
                logger.info(f"Sessão WhatsApp '{self.session_name}' iniciada com sucesso")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão WhatsApp: {e}")
            return False
    
    def get_session_status(self) -> Optional[Dict]:
        """
        Obtém o status da sessão WhatsApp
        
        Returns:
            Dicionário com informações da sessão ou None
        """
        return self._make_request('GET', f'/api/sessions/{self.session_name}')
    
    def get_qr_code(self) -> Optional[str]:
        """
        Obtém o QR code para autenticação
        
        Returns:
            URL da imagem do QR code ou None
        """
        try:
            endpoint = f'/api/screenshot?session={self.session_name}'
            url = urljoin(self.base_url, endpoint)
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Retorna a URL completa da imagem
            return url
            
        except Exception as e:
            logger.error(f"Erro ao obter QR code: {e}")
            return None
    
    def send_text(self, chat_id: str, text: str) -> bool:
        """
        Envia uma mensagem de texto
        
        Args:
            chat_id: ID do chat (número@c.us para contatos, número@g.us para grupos)
            text: Texto da mensagem
            
        Returns:
            True se a mensagem foi enviada com sucesso
        """
        try:
            data = {
                "session": self.session_name,
                "chatId": chat_id,
                "text": text
            }
            
            result = self._make_request('POST', '/api/sendText', json=data)
            
            if result:
                logger.info(f"Mensagem enviada para {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de texto: {e}")
            return False
    
    def send_image(self, chat_id: str, image_url: str, caption: str = "") -> bool:
        """
        Envia uma imagem
        
        Args:
            chat_id: ID do chat
            image_url: URL da imagem
            caption: Legenda da imagem (opcional)
            
        Returns:
            True se a imagem foi enviada com sucesso
        """
        try:
            data = {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {
                    "url": image_url
                },
                "caption": caption
            }
            
            result = self._make_request('POST', '/api/sendImage', json=data)
            
            if result:
                logger.info(f"Imagem enviada para {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar imagem: {e}")
            return False
    
    def send_file(self, chat_id: str, file_url: str, filename: str = "", caption: str = "") -> bool:
        """
        Envia um arquivo
        
        Args:
            chat_id: ID do chat
            file_url: URL do arquivo
            filename: Nome do arquivo (opcional)
            caption: Legenda do arquivo (opcional)
            
        Returns:
            True se o arquivo foi enviado com sucesso
        """
        try:
            data = {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {
                    "url": file_url,
                    "filename": filename
                },
                "caption": caption
            }
            
            result = self._make_request('POST', '/api/sendFile', json=data)
            
            if result:
                logger.info(f"Arquivo enviado para {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar arquivo: {e}")
            return False
    
    def get_contacts(self) -> List[Dict]:
        """
        Obtém a lista de contatos
        
        Returns:
            Lista de contatos
        """
        result = self._make_request('GET', f'/api/contacts?session={self.session_name}')
        return result if result else []
    
    def get_chats(self) -> List[Dict]:
        """
        Obtém a lista de chats
        
        Returns:
            Lista de chats
        """
        result = self._make_request('GET', f'/api/{self.session_name}/chats')
        return result if result else []
    
    def logout(self) -> bool:
        """
        Faz logout da sessão WhatsApp
        
        Returns:
            True se o logout foi bem-sucedido
        """
        try:
            result = self._make_request('DELETE', f'/api/sessions/{self.session_name}')
            
            if result is not None:
                logger.info(f"Logout da sessão '{self.session_name}' realizado")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao fazer logout: {e}")
            return False
    
    def check_health(self) -> bool:
        """
        Verifica se a API WAHA está funcionando
        
        Returns:
            True se a API está saudável
        """
        try:
            # Remove autenticação para health check
            response = requests.get(
                urljoin(self.base_url, '/api/health'),
                timeout=5
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erro ao verificar saúde da API WAHA: {e}")
            return False
