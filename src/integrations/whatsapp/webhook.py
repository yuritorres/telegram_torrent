"""
Webhook Flask para receber mensagens do WhatsApp via WAHA
"""
import logging
from typing import Dict, Any
from flask import Flask, request, jsonify
from src.integrations.whatsapp.utils import is_authorized_whatsapp, send_whatsapp, waha_client

logger = logging.getLogger(__name__)


def process_whatsapp_webhook(data: Dict[str, Any], sess=None, add_magnet_func=None, qb_url: str = None, jellyfin_manager=None) -> Dict[str, str]:
    try:
        event = data.get('event')
        payload = data.get('payload', {})
        logger.info(f"Webhook WhatsApp recebido - Evento: {event}")

        if event != 'message':
            return {"status": "ignored", "reason": "not a message event"}

        message = payload
        from_number = message.get('from', '')
        chat_id = message.get('chatId', from_number)
        text = message.get('body', '')
        message_type = message.get('type', 'text')

        logger.info(f"Mensagem de {from_number}: {text}")

        if not is_authorized_whatsapp(from_number):
            logger.warning(f"Número não autorizado: {from_number}")
            send_whatsapp("❌ Você não tem permissão para usar este bot.", chat_id)
            return {"status": "unauthorized"}

        if message_type not in ['text', 'chat']:
            return {"status": "ignored", "reason": "not a text message"}

        from src.commands.whatsapp_commands import process_whatsapp_message
        success = process_whatsapp_message(
            message_data=message,
            sess=sess,
            add_magnet_func=add_magnet_func,
            qb_url=qb_url,
            jellyfin_manager=jellyfin_manager,
        )
        return {"status": "processed"} if success else {"status": "error", "message": "Failed to process message"}

    except Exception as e:
        logger.error(f"Erro ao processar webhook WhatsApp: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


def create_webhook_app(sess=None, add_magnet_func=None, qb_url: str = None, jellyfin_manager=None) -> Flask:
    app = Flask(__name__)

    @app.route('/whatsapp/webhook', methods=['POST'])
    def whatsapp_webhook():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            result = process_whatsapp_webhook(
                data=data, sess=sess, add_magnet_func=add_magnet_func,
                qb_url=qb_url, jellyfin_manager=jellyfin_manager,
            )
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Erro no webhook WhatsApp: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/whatsapp/health', methods=['GET'])
    def health_check():
        if waha_client and waha_client.check_health():
            return jsonify({"status": "healthy"}), 200
        return jsonify({"status": "unhealthy"}), 503

    return app
