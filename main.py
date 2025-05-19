#!/usr/bin/env python3
#!/usr/bin/env python3
import time
import requests
import re
from dotenv import load_dotenv
import os
from qbittorrent_api import login_qb, fetch_torrents, resumo_torrents, add_magnet
from telegram_utils import send_telegram, process_messages
from torrent_monitor import monitor_torrents
import threading

load_dotenv()

QB_URL = os.getenv('QB_URL')
QB_USER = os.getenv('QB_USER')
QB_PASS = os.getenv('QB_PASS')
INTERVALO = int(os.getenv('INTERVALO', 60))

def main():
    try:
        sess = login_qb(QB_URL, QB_USER, QB_PASS)
    except Exception as e:
        send_telegram("❌ Não foi possível se conectar ao qBittorrent. O bot continuará funcional, mas sem integração com o qBittorrent.")
        sess = None
    last_update_id = 0
    def mensagens_thread():
        nonlocal last_update_id, sess
        while True:
            last_update_id = process_messages(sess, last_update_id, add_magnet, QB_URL)
            time.sleep(1)
    def monitor_thread():
        if sess is not None:
            monitor_torrents(sess, QB_URL, fetch_torrents, resumo_torrents, INTERVALO)
    t1 = threading.Thread(target=mensagens_thread, daemon=True)
    t2 = threading.Thread(target=monitor_thread, daemon=True)
    t1.start()
    t2.start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()