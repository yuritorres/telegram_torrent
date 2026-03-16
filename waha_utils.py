"""
Módulo de utilidades para processamento de mensagens WhatsApp via WAHA
"""
import logging
import os
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify
from waha_api import WAHAApi

logger = logging.getLogger(__name__)

# Configurações do WhatsApp
WAHA_URL = os.getenv('WAHA_URL', 'http://localhost:3000')
WAHA_API_KEY = os.getenv('WAHA_API_KEY', 'local-dev-key-123')
WAHA_SESSION = os.getenv('WAHA_SESSION', 'default')
AUTHORIZED_WHATSAPP_NUMBERS = os.getenv('AUTHORIZED_WHATSAPP_NUMBERS', '').split(',')

# Cliente WAHA global
waha_client: Optional[WAHAApi] = None


def init_waha_client() -> Optional[WAHAApi]:
    """
    Inicializa o cliente WAHA
    
    Returns:
        Instância do WAHAApi ou None se falhar
    """
    global waha_client
    
    if not WAHA_URL or not WAHA_API_KEY:
        logger.warning("WAHA_URL ou WAHA_API_KEY não configurados")
        return None
    
    try:
        waha_client = WAHAApi(WAHA_URL, WAHA_API_KEY, WAHA_SESSION)
        
        # Verifica se a API está funcionando
        if waha_client.check_health():
            logger.info("Cliente WAHA inicializado com sucesso")
            
            # Tenta obter status da sessão
            status = waha_client.get_session_status()
            if status:
                logger.info(f"Sessão WhatsApp status: {status.get('status', 'unknown')}")
            else:
                logger.warning("Sessão WhatsApp não encontrada. Inicie uma sessão manualmente.")
            
            return waha_client
        else:
            logger.error("API WAHA não está respondendo")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente WAHA: {e}")
        return None


def send_whatsapp(text: str, chat_id: str, parse_mode: str = None) -> bool:
    """
    Envia uma mensagem via WhatsApp
    
    Args:
        text: Texto da mensagem
        chat_id: ID do chat WhatsApp (número@c.us)
        parse_mode: Modo de formatação (não usado no WhatsApp)
        
    Returns:
        True se a mensagem foi enviada com sucesso
    """
    global waha_client
    
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return False
    
    try:
        # Remove formatação Markdown/HTML se presente
        # WhatsApp tem formatação própria
        clean_text = text.replace('*', '').replace('_', '').replace('`', '')
        
        return waha_client.send_text(chat_id, clean_text)
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False


def is_authorized_whatsapp(phone_number: str) -> bool:
    """
    Verifica se um número de telefone está autorizado
    
    Args:
        phone_number: Número de telefone (pode incluir @c.us, @lid, etc)
        
    Returns:
        True se autorizado
    """
    if not AUTHORIZED_WHATSAPP_NUMBERS or AUTHORIZED_WHATSAPP_NUMBERS == ['']:
        # Se não há lista de autorizados, permite todos
        return True
    
    # Remove sufixos do WhatsApp (@c.us, @lid, @g.us, etc) e caracteres especiais
    clean_number = phone_number.split('@')[0] if '@' in phone_number else phone_number
    clean_number = ''.join(filter(str.isdigit, clean_number))
    
    for authorized in AUTHORIZED_WHATSAPP_NUMBERS:
        clean_authorized = ''.join(filter(str.isdigit, authorized))
        if clean_number == clean_authorized or clean_number.endswith(clean_authorized) or clean_authorized in clean_number:
            return True
    
    return False


def format_chat_id(phone_number: str) -> str:
    """
    Formata um número de telefone para o formato de chat_id do WhatsApp
    
    Args:
        phone_number: Número de telefone
        
    Returns:
        Chat ID formatado (número@c.us)
    """
    # Remove caracteres especiais
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # Adiciona sufixo @c.us se não estiver presente
    if '@' not in clean_number:
        return f"{clean_number}@c.us"
    
    return clean_number


def process_whatsapp_webhook(data: Dict[str, Any], sess=None, add_magnet_func=None, qb_url: str = None, jellyfin_manager=None) -> Dict[str, str]:
    """
    Processa um webhook recebido do WhatsApp
    
    Args:
        data: Dados do webhook
        sess: Sessão de autenticação do qBittorrent
        add_magnet_func: Função para adicionar magnet
        qb_url: URL do qBittorrent
        jellyfin_manager: Instância do JellyfinManager
        
    Returns:
        Dicionário com resposta
    """
    try:
        event = data.get('event')
        payload = data.get('payload', {})
        
        logger.info(f"Webhook WhatsApp recebido - Evento: {event}")
        
        # Ignora eventos que não são mensagens
        if event != 'message':
            return {"status": "ignored", "reason": "not a message event"}
        
        # Extrai informações da mensagem
        message = payload
        from_number = message.get('from', '')
        chat_id = message.get('chatId', from_number)
        text = message.get('body', '')
        message_type = message.get('type', 'text')
        
        logger.info(f"Mensagem de {from_number}: {text}")
        logger.info(f"Tipo da mensagem: {message_type}")
        logger.info(f"Chat ID: {chat_id}")
        
        # Verifica autorização
        if not is_authorized_whatsapp(from_number):
            logger.warning(f"Número não autorizado: {from_number}")
            send_whatsapp("❌ Você não tem permissão para usar este bot.", chat_id)
            return {"status": "unauthorized"}
        
        logger.info(f"Número autorizado: {from_number}")
        
        # Processa apenas mensagens de texto (tipo 'text' ou 'chat')
        if message_type not in ['text', 'chat']:
            logger.warning(f"Mensagem ignorada - tipo '{message_type}' não é texto")
            return {"status": "ignored", "reason": "not a text message"}
        
        logger.info(f"Processando mensagem de texto: {text}")
        
        # Processar comandos usando whatsapp_commands
        from whatsapp_commands import process_whatsapp_message
        
        success = process_whatsapp_message(
            message_data=message,
            sess=sess,
            add_magnet_func=add_magnet_func,
            qb_url=qb_url,
            jellyfin_manager=jellyfin_manager
        )
        
        if success:
            return {"status": "processed"}
        else:
            return {"status": "error", "message": "Failed to process message"}
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook WhatsApp: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


def create_webhook_app(sess=None, add_magnet_func=None, qb_url: str = None, jellyfin_manager=None) -> Flask:
    """
    Cria uma aplicação Flask para receber webhooks do WhatsApp
    
    Args:
        sess: Sessão de autenticação do qBittorrent
        add_magnet_func: Função para adicionar magnet
        qb_url: URL do qBittorrent
        jellyfin_manager: Instância do JellyfinManager
    
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    
    @app.route('/whatsapp/webhook', methods=['POST'])
    def whatsapp_webhook():
        """Endpoint para receber webhooks do WhatsApp"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            result = process_whatsapp_webhook(
                data=data,
                sess=sess,
                add_magnet_func=add_magnet_func,
                qb_url=qb_url,
                jellyfin_manager=jellyfin_manager
            )
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Erro no webhook WhatsApp: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/whatsapp/health', methods=['GET'])
    def health_check():
        """Endpoint de health check"""
        global waha_client
        
        if waha_client and waha_client.check_health():
            return jsonify({"status": "healthy"}), 200
        else:
            return jsonify({"status": "unhealthy"}), 503
    
    return app


def get_whatsapp_qr() -> Optional[str]:
    """
    Obtém o QR code para autenticação WhatsApp
    
    Returns:
        URL do QR code ou None
    """
    global waha_client
    
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return None
    
    return waha_client.get_qr_code()


def start_whatsapp_session() -> bool:
    """
    Inicia uma nova sessão WhatsApp
    
    Returns:
        True se a sessão foi iniciada com sucesso
    """
    global waha_client
    
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return False
    
    return waha_client.start_session()


def get_whatsapp_status() -> Optional[Dict]:
    """
    Obtém o status da sessão WhatsApp
    
    Returns:
        Dicionário com informações da sessão
    """
    global waha_client
    
    if not waha_client:
        logger.error("Cliente WAHA não inicializado")
        return None
    
    return waha_client.get_session_status()
