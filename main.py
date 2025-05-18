#!/usr/bin/env python3
#!/usr/bin/env python3
import time
import requests
import re
from dotenv import load_dotenv
import os
from qbittorrent_api import login_qb, fetch_torrents, resumo_torrents, add_magnet

load_dotenv()

QB_URL = os.getenv('QB_URL')
QB_USER = os.getenv('QB_USER')
QB_PASS = os.getenv('QB_PASS')
TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')
INTERVALO = int(os.getenv('INTERVALO', 60))

def send_telegram(msg, chat_id=None):
    if chat_id is None:
        chat_id = TG_CHAT_ID
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    resp = requests.post(url, data=data)
    resp.raise_for_status()

def process_messages(sess, last_update_id):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    params = {'offset': last_update_id + 1, 'timeout': 0}
    
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get('ok', False):
            return last_update_id
            
        updates = data.get('result', [])
        new_last_id = last_update_id
        
        for update in updates:
            update_id = update['update_id']
            message = update.get('message', {})
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id')
            
            if text and chat_id:
                magnet_regex = r'magnet:\?xt=urn:btih:[0-9a-f]{40}.*' # Regex mais robusta para links magnet
                magnets = re.findall(magnet_regex, text, re.IGNORECASE)
                # Adiciona validação básica para garantir que os links encontrados são válidos
                valid_magnets = [m for m in magnets if m.startswith("magnet:")]
                for magnet in valid_magnets:
                    try:
                        add_magnet(sess, QB_URL, magnet)
                        # Extrai o nome do torrent do link magnet
                        from urllib.parse import urlparse, parse_qs
                        parsed_magnet = urlparse(magnet)
                        query_params = parse_qs(parsed_magnet.query)
                        torrent_name = query_params.get('dn', [magnet])[0] # Usa o link completo como fallback
                        send_telegram(f"✅ <b>Magnet adicionado:</b>\n{torrent_name}", chat_id)
                    except requests.exceptions.HTTPError as e:
                        error_msg = f"Erro no qBittorrent: {e.response.text}"
                        send_telegram(f"❌ {error_msg}", chat_id)
                    except Exception as e:
                        send_telegram(f"❌ Erro ao processar magnet: {str(e)}", chat_id)
            
            new_last_id = max(new_last_id, update_id)
        
        return new_last_id
        
    except Exception as e:
        send_telegram(f"⚠️ Erro no processamento de mensagens: {str(e)}")
        return last_update_id

def main():
    sess = login_qb(QB_URL, QB_USER, QB_PASS)
    last_update_id = 0
    last_status_time = 0 # Tempo da última atualização de status
    
    # Dicionário para rastrear torrents concluídos e evitar notificações duplicadas
    completed_torrents = {}
    previous_torrents_state = {}

    while True:
        try:
            # Processa mensagens do Telegram
            last_update_id = process_messages(sess, last_update_id)
            
            # Verifica o status dos torrents
            current_torrents = fetch_torrents(sess, QB_URL)
            
            # Verifica se algum torrent foi concluído desde a última verificação
            for torrent in current_torrents:
                infohash = torrent['hash']
                current_state = torrent['state']
                name = torrent['name']

                # Verifica se o torrent estava baixando e agora está semeando/concluído
                if infohash in previous_torrents_state and previous_torrents_state[infohash]['state'] == 'downloading' and current_state in ['seeding', 'finished']:
                    if infohash not in completed_torrents:
                        send_telegram(f"🎉 <b>Download Concluído:</b>\n{name}")
                        completed_torrents[infohash] = True # Marca como notificado
                
                # Atualiza o estado anterior do torrent
                previous_torrents_state[infohash] = {'state': current_state, 'name': name}

            # Envia status periódico baseado no tempo
            current_time = time.time()
            if current_time - last_status_time >= INTERVALO:
                resumo = resumo_torrents(current_torrents)
                send_telegram(f"📊 <b>Status do qBittorrent</b>\n\n{resumo}")
                last_status_time = current_time # Atualiza o tempo da última atualização
                
        except Exception as e:
            send_telegram(f"❗️ Erro crítico: {str(e)}")
        
        # Pequena pausa para evitar uso excessivo de CPU
        time.sleep(1)

if __name__ == "__main__":
    main()