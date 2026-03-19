"""
Cliente para integração com a API WhatsApp WAHA
"""
import requests
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class WAHAApi:
    """Cliente para interagir com a API WhatsApp WAHA"""

    def __init__(self, base_url: str, api_key: str, session_name: str = "default"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_name = session_name
        self.headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': api_key,
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        url = urljoin(self.base_url, endpoint)
        try:
            response = requests.request(method=method, url=url, headers=self.headers, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição WAHA {method} {endpoint}: {e}")
            return None

    def start_session(self) -> bool:
        try:
            result = self._make_request('POST', '/api/sessions', json={"name": self.session_name})
            if result:
                logger.info(f"Sessão WhatsApp '{self.session_name}' iniciada com sucesso")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão WhatsApp: {e}")
            return False

    def get_session_status(self) -> Optional[Dict]:
        return self._make_request('GET', f'/api/sessions/{self.session_name}')

    def get_qr_code(self) -> Optional[str]:
        try:
            endpoint = f'/api/screenshot?session={self.session_name}'
            url = urljoin(self.base_url, endpoint)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return url
        except Exception as e:
            logger.error(f"Erro ao obter QR code: {e}")
            return None

    def send_text(self, chat_id: str, text: str) -> bool:
        try:
            data = {"session": self.session_name, "chatId": chat_id, "text": text}
            result = self._make_request('POST', '/api/sendText', json=data)
            if result:
                logger.info(f"Mensagem enviada para {chat_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de texto: {e}")
            return False

    def send_image(self, chat_id: str, image_url: str, caption: str = "") -> bool:
        try:
            data = {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {"url": image_url},
                "caption": caption,
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
        try:
            data = {
                "session": self.session_name,
                "chatId": chat_id,
                "file": {"url": file_url, "filename": filename},
                "caption": caption,
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
        result = self._make_request('GET', f'/api/contacts?session={self.session_name}')
        return result if result else []

    def get_chats(self) -> List[Dict]:
        result = self._make_request('GET', f'/api/{self.session_name}/chats')
        return result if result else []

    def logout(self) -> bool:
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
        try:
            response = requests.get(urljoin(self.base_url, '/api/health'), timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao verificar saúde da API WAHA: {e}")
            return False
