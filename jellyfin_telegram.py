from jellyfin_api import JellyfinAPI
from telegram_utils import send_telegram

# Comandos Jellyfin para o Telegram

def process_jellyfin_command(text, chat_id):
    jf = JellyfinAPI()
    if text.startswith("/jflib"):  # Lista bibliotecas
        try:
            libs = jf.get_libraries()
            msg = "<b>Bibliotecas Jellyfin:</b>\n"
            for item in libs.get('Items', []):
                msg += f"- {item.get('Name')} ({item.get('Type')})\n"
            send_telegram(msg, chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao listar bibliotecas Jellyfin: {str(e)}", chat_id)
        return True
    if text.startswith("/jfsearch "):
        query = text[len("/jfsearch "):].strip()
        if not query:
            send_telegram("❌ Use: /jfsearch <termo>", chat_id)
            return True
        try:
            results = jf.search_media(query)
            msg = f"<b>Resultados para '{query}':</b>\n"
            for hint in results.get('SearchHints', []):
                msg += f"- {hint.get('Name')} ({hint.get('Type')})\n"
            send_telegram(msg if results.get('SearchHints') else "Nenhum resultado encontrado.", chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro na busca Jellyfin: {str(e)}", chat_id)
        return True
    return False
