from jellyfin_api import JellyfinAPI
from telegram_utils import send_telegram
import re
import requests

# Comandos Jellyfin para o Telegram

def format_item_info(item):
    """Formata informações de um item para exibição no Telegram"""
    name = item.get('Name', 'Sem nome')
    item_type = item.get('Type', 'Desconhecido')
    overview = item.get('Overview', '')
    if overview and len(overview) > 100:
        overview = overview[:97] + '...'
    
    info = f"<b>{name}</b> ({item_type})\n"
    if overview:
        info += f"{overview}\n"
    
    # Adiciona informações específicas por tipo
    if item_type == 'Movie':
        year = item.get('ProductionYear', '')
        runtime = item.get('RunTimeTicks', 0) / 10000000 / 60  # Converte ticks para minutos
        if year:
            info += f"Ano: {year}\n"
        if runtime:
            info += f"Duração: {int(runtime)} min\n"
    elif item_type == 'Series':
        year = item.get('ProductionYear', '')
        status = item.get('Status', '')
        if year:
            info += f"Ano: {year}\n"
        if status:
            info += f"Status: {status}\n"
    
    return info

def process_jellyfin_command(text, chat_id):
    jf = JellyfinAPI()
    
    # Comando de ajuda
    if text == "/jfhelp":
        try:
            help_text = "<b>Comandos Jellyfin disponíveis:</b>\n\n"
            help_text += "/jflib - Lista todas as bibliotecas\n"
            help_text += "/jfsearch &lt;termo&gt; - Pesquisa por conteúdo\n"
            help_text += "/jfrecent - Mostra adições recentes\n"
            help_text += "/jfinfo - Informações do servidor\n"
            help_text += "/jfitem &lt;id&gt; - Detalhes de um item específico\n"
            help_text += "/jfsessions - Lista sessões ativas (admin)\n"
            send_telegram(help_text, chat_id)
            return True
        except Exception as e:
            print(f"❌ Erro ao processar comando /jfhelp: {str(e)}")
            # Tenta enviar uma mensagem simplificada sem formatação
            send_telegram("Comandos Jellyfin disponíveis: /jflib, /jfsearch, /jfrecent, /jfinfo, /jfitem, /jfsessions", chat_id, parse_mode=None)
            return True
    
    # Lista bibliotecas
    if text.startswith("/jflib"):
        try:
            libs = jf.get_libraries()
            msg = "<b>Bibliotecas Jellyfin:</b>\n"
            for item in libs.get('Items', []):
                msg += f"- {item.get('Name')} ({item.get('Type')}) [ID: {item.get('Id')}]\n"
            send_telegram(msg, chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao listar bibliotecas Jellyfin: {str(e)}", chat_id)
        return True
    
    # Pesquisa por conteúdo
    if text.startswith("/jfsearch "):
        query = text[len("/jfsearch "):].strip()
        if not query:
            send_telegram("❌ Use: /jfsearch <termo>", chat_id)
            return True
        try:
            results = jf.search_media(query)
            msg = f"<b>Resultados para '{query}':</b>\n"
            for hint in results.get('SearchHints', []):
                item_id = hint.get('Id')
                msg += f"- {hint.get('Name')} ({hint.get('Type')})\n"
                if item_id:
                    msg += f"  ID: {item_id}\n"
            send_telegram(msg if results.get('SearchHints') else "Nenhum resultado encontrado.", chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro na busca Jellyfin: {str(e)}", chat_id)
        return True
    
    # Mostra adições recentes
    if text.startswith("/jfrecent"):
        try:
            # Verifica se há um tipo específico solicitado
            match = re.search(r'/jfrecent\s+(\w+)', text)
            item_type = match.group(1) if match else None
            
            # Define o limite padrão
            limit = 10
            # Verifica se há um limite especificado
            limit_match = re.search(r'\blimit=(\d+)', text)
            if limit_match:
                limit = int(limit_match.group(1))
                limit = min(limit, 20)  # Limita a 20 itens no máximo
            
            recent_items = jf.get_recently_added(limit=limit, include_item_types=item_type)
            
            if not recent_items:
                send_telegram("Nenhum item recente encontrado.", chat_id)
                return True
                
            msg = f"<b>Adições recentes{' de ' + item_type if item_type else ''}:</b>\n\n"
            
            for item in recent_items:
                msg += format_item_info(item) + "\n"
                
            send_telegram(msg, chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao obter itens recentes: {str(e)}", chat_id)
        return True
    
    # Informações do servidor
    if text == "/jfinfo":
        try:
            # Verifica se a conexão com o servidor está funcionando
            try:
                # Tenta autenticar primeiro para garantir que a conexão está ativa
                jf.authenticate()
                info = jf.get_system_info()
                msg = "<b>Informações do Servidor:</b>\n"
                msg += f"Nome: {info.get('ServerName', 'N/A')}\n"
                msg += f"Versão: {info.get('Version', 'N/A')}\n"
                msg += f"Sistema Operacional: {info.get('OperatingSystem', 'N/A')}\n"
                msg += f"Arquitetura: {info.get('SystemArchitecture', 'N/A')}\n"
                
                # Tenta obter informações de usuários (requer admin)
                try:
                    users = jf.get_users()
                    msg += f"Usuários: {len(users)}\n"
                except Exception:
                    pass  # Ignora se não tiver permissão
                    
                send_telegram(msg, chat_id)
            except requests.exceptions.ConnectionError:
                send_telegram("❌ Não foi possível conectar ao servidor Jellyfin. Verifique se o servidor está online.", chat_id)
            except requests.exceptions.HTTPError as http_err:
                send_telegram(f"❌ Erro HTTP ao acessar o servidor: {http_err}", chat_id)
            except requests.exceptions.Timeout:
                send_telegram("❌ Tempo esgotado ao tentar conectar ao servidor Jellyfin.", chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao obter informações do servidor: {str(e)}", chat_id)
            # Evita que o erro seja repetido múltiplas vezes
            import traceback
            print(f"Erro detalhado no comando /jfinfo: {traceback.format_exc()}")
        return True
    
    # Detalhes de um item específico
    if text.startswith("/jfitem "):
        item_id = text[len("/jfitem "):].strip()
        if not item_id:
            send_telegram("❌ Use: /jfitem <id>", chat_id)
            return True
        try:
            item = jf.get_item_details(item_id)
            msg = "<b>Detalhes do Item:</b>\n\n"
            msg += format_item_info(item)
            
            # Adiciona informações extras
            if item.get('Genres'):
                msg += f"Gêneros: {', '.join(item.get('Genres'))}\n"
            if item.get('Studios'):
                studios = [studio.get('Name') for studio in item.get('Studios', [])]
                msg += f"Estúdios: {', '.join(studios)}\n"
            if item.get('CommunityRating'):
                msg += f"Avaliação: {item.get('CommunityRating')}/10\n"
                
            send_telegram(msg, chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao obter detalhes do item: {str(e)}", chat_id)
        return True
    
    # Lista sessões ativas (requer admin)
    if text == "/jfsessions":
        try:
            sessions = jf.get_sessions()
            if not sessions:
                send_telegram("Nenhuma sessão ativa no momento.", chat_id)
                return True
                
            msg = "<b>Sessões Ativas:</b>\n\n"
            
            for session in sessions:
                user_name = session.get('UserName', 'Desconhecido')
                device_name = session.get('DeviceName', 'Dispositivo desconhecido')
                client = session.get('Client', 'Cliente desconhecido')
                
                msg += f"Usuário: {user_name}\n"
                msg += f"Dispositivo: {device_name}\n"
                msg += f"Cliente: {client}\n"
                
                # Verifica se está reproduzindo algo
                now_playing = session.get('NowPlayingItem')
                if now_playing:
                    msg += f"Reproduzindo: {now_playing.get('Name')}\n"
                    
                msg += "\n"
                
            send_telegram(msg, chat_id)
        except Exception as e:
            send_telegram(f"❌ Erro ao listar sessões: {str(e)}", chat_id)
        return True
        
    return False
