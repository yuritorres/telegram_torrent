#!/usr/bin/env python3
import time
import os
import threading
import asyncio
import requests
from dotenv import load_dotenv
from telegram_utils import send_telegram, process_messages, set_bot_commands
from jellyfin_telegram import JellyfinTelegramBot

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do qBittorrent
QB_URL = os.getenv('QB_URL')
QB_USER = os.getenv('QB_USER')
QB_PASS = os.getenv('QB_PASS')
INTERVALO = int(os.getenv('INTERVALO', 60))

# Tenta importar os módulos necessários
try:
    from qbittorrent_api import login_qb, fetch_torrents, resumo_torrents, add_magnet
    from telegram_utils import send_telegram, process_messages
    from torrent_monitor import monitor_torrents
    QBITTORRENT_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Módulos do qBittorrent não encontrados. {e}")
    QBITTORRENT_AVAILABLE = False

def main():
    # Atualiza o menu de comandos do bot no Telegram
    set_bot_commands()
    # Inicializa a sessão do qBittorrent se disponível
    sess = None
    if QBITTORRENT_AVAILABLE:
        try:
            sess = login_qb(QB_URL, QB_USER, QB_PASS)
            print("Conexão com qBittorrent estabelecida com sucesso.")
        except Exception as e:
            print(f"❌ Não foi possível conectar ao qBittorrent: {e}")
            send_telegram("❌ Não foi possível se conectar ao qBittorrent. O bot continuará funcional, mas sem integração com o qBittorrent.")
    else:
        print("Módulos do qBittorrent não disponíveis. O bot será executado sem integração com o qBittorrent.")
    
    last_update_id = 0
    
    # Inicializa o bot do Jellyfin
    try:
        jellyfin_bot = JellyfinTelegramBot()
        print("Bot do Jellyfin inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o bot do Jellyfin: {e}")
        jellyfin_bot = None
    
    def mensagens_thread():
        nonlocal last_update_id, sess
        while True:
            try:
                last_update_id = process_messages(sess, last_update_id, add_magnet, QB_URL, jellyfin_bot)
                time.sleep(1)
            except Exception as e:
                print(f"Erro no processamento de mensagens: {e}")
                time.sleep(5)  # Espera 5 segundos antes de tentar novamente
    
    def monitor_thread():
        if sess is not None and QBITTORRENT_AVAILABLE:
            try:
                monitor_torrents(sess, QB_URL, fetch_torrents, resumo_torrents, INTERVALO)
            except Exception as e:
                print(f"Erro no monitoramento de torrents: {e}")
    
    # Inicia as threads
    threads = []
    
    # Thread de processamento de mensagens
    t1 = threading.Thread(target=mensagens_thread, daemon=True)
    threads.append(t1)
    t1.start()
    
    # Thread de monitoramento de torrents (apenas se qBittorrent estiver disponível)
    if QBITTORRENT_AVAILABLE and sess is not None:
        t2 = threading.Thread(target=monitor_thread, daemon=True)
        threads.append(t2)
        t2.start()
    
    # Mantém o programa em execução
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando o bot...")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        print("Bot encerrado.")

if __name__ == "__main__":
    print("Iniciando o bot de gerenciamento de torrents...")
    main()