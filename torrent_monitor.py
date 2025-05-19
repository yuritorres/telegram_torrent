import time
from telegram_utils import send_telegram

def monitor_torrents(sess, qb_url, fetch_torrents_func, resumo_torrents_func, intervalo):
    last_status_time = 0
    completed_torrents = {}
    initial_torrents = fetch_torrents_func(sess, qb_url)
    previous_torrents_state = {torrent['hash']: {'state': torrent['state'], 'name': torrent['name']} for torrent in initial_torrents}
    while True:
        try:
            current_torrents = fetch_torrents_func(sess, qb_url)
            for torrent in current_torrents:
                infohash = torrent['hash']
                current_state = torrent['state']
                name = torrent['name']
                download_states = ['downloading', 'stalledDL', 'checkingDL', 'pausedDL', 'queuedDL', 'forcedDL']
                completion_states = ['uploading', 'seeding', 'finished', 'stalledUP', 'checkingUP', 'forcedUP']
                if infohash in previous_torrents_state:
                    prev_state = previous_torrents_state[infohash]['state']
                    if prev_state in download_states and current_state in completion_states:
                        if infohash not in completed_torrents:
                            send_telegram(f"🎉 <b>Download Concluído:</b>\n{name}")
                            completed_torrents[infohash] = True
                previous_torrents_state[infohash] = {'state': current_state, 'name': name}
            current_time = time.time()
            if current_time - last_status_time >= intervalo:
                resumo = resumo_torrents_func(current_torrents)
                send_telegram(f"📊 <b>Status do qBittorrent</b>\n\n{resumo}")
                last_status_time = current_time
        except Exception as e:
            send_telegram(f"❗️ Erro crítico: {str(e)}")
        time.sleep(1)