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

load_dotenv()

QB_URL = os.getenv('QB_URL')
QB_USER = os.getenv('QB_USER')
QB_PASS = os.getenv('QB_PASS')
INTERVALO = int(os.getenv('INTERVALO', 60))

def main():
    sess = login_qb(QB_URL, QB_USER, QB_PASS)
    last_update_id = 0
    while True:
        last_update_id = process_messages(sess, last_update_id, add_magnet, QB_URL)
        # O monitoramento dos torrents roda em paralelo, se desejado, pode ser thread/processo
        monitor_torrents(sess, QB_URL, fetch_torrents, resumo_torrents, INTERVALO)

if __name__ == "__main__":
    main()