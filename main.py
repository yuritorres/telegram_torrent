#!/usr/bin/env python3
import time
import os
import threading
import logging
from dotenv import load_dotenv
from src.integrations.telegram import send_telegram, process_messages, set_bot_commands
from src.integrations.jellyfin import JellyfinManager, JellyfinNotifier
from src.integrations.whatsapp import init_waha_client, create_webhook_app
from src.integrations.docker import DockerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do qBittorrent
QB_URL = os.getenv('QB_URL')
QB_USER = os.getenv('QB_USER')
QB_PASS = os.getenv('QB_PASS')
INTERVALO = int(os.getenv('INTERVALO', 60))

# Tenta importar os módulos necessários
try:
    from src.integrations.qbittorrent import login_qb, fetch_torrents, add_magnet, monitor_torrents
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
            logger.info("Conexão com qBittorrent estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"❌ Não foi possível conectar ao qBittorrent: {e}")
            send_telegram("❌ Não foi possível se conectar ao qBittorrent. O bot continuará funcional, mas sem integração com o qBittorrent.")
    else:
        logger.warning("Módulos do qBittorrent não disponíveis. O bot será executado sem integração com o qBittorrent.")
    
    last_update_id = 0
    
    # Inicializa o gerenciador do Jellyfin
    jellyfin_notifier = None
    try:
        jellyfin_manager = JellyfinManager()
        if jellyfin_manager.is_available():
            logger.info("Jellyfin configurado e disponível.")
            
            # Inicializa o notificador do Jellyfin se habilitado
            notifications_enabled = os.getenv('JELLYFIN_NOTIFICATIONS_ENABLED', 'True').lower() in ('true', '1', 't')
            if notifications_enabled:
                notification_interval = int(os.getenv('JELLYFIN_NOTIFICATION_INTERVAL', 1800))
                jellyfin_notifier = JellyfinNotifier(jellyfin_manager, interval=notification_interval)
                logger.info(f"Notificações do Jellyfin habilitadas (intervalo: {notification_interval}s)")
            else:
                logger.info("Notificações do Jellyfin desabilitadas")
        else:
            logger.warning("Jellyfin não configurado ou indisponível.")
    except Exception as e:
        logger.error(f"Erro ao inicializar o gerenciador do Jellyfin: {e}")
        jellyfin_manager = None
    
    # Inicializa o gerenciador de sincronização (v0.0.1.7-alpha)
    sync_manager = None
    if sess and jellyfin_manager and jellyfin_manager.is_available():
        try:
            from src.services import SyncManager
            sync_manager = SyncManager(sess, QB_URL, jellyfin_manager, send_telegram)
            logger.info("SyncManager inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar SyncManager: {e}")
    
    # Inicializa o gerenciador de estatísticas (v0.0.1.7-alpha)
    stats_manager = None
    if sess:
        try:
            from src.services import StatisticsManager
            stats_manager = StatisticsManager(sess, QB_URL)
            logger.info("StatisticsManager inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar StatisticsManager: {e}")
    
    # Inicializa o gerenciador Docker
    docker_manager = None
    try:
        docker_manager = DockerManager()
        if docker_manager.is_available():
            logger.info("Docker configurado e disponível.")
        else:
            logger.warning("Docker não disponível.")
    except Exception as e:
        logger.error(f"Erro ao inicializar o gerenciador Docker: {e}")
        docker_manager = None
    
    # Inicializa o cliente WhatsApp WAHA
    waha_enabled = os.getenv('WAHA_URL') and os.getenv('WAHA_API_KEY')
    flask_app = None
    if waha_enabled:
        try:
            logger.info("Inicializando cliente WhatsApp WAHA...")
            
            # Aguarda alguns segundos para o WAHA estar pronto
            logger.info("Aguardando WAHA inicializar...")
            time.sleep(10)
            
            waha_client = init_waha_client()
            if waha_client:
                logger.info("Cliente WhatsApp WAHA inicializado com sucesso")
            else:
                logger.warning("Cliente WAHA não respondeu, mas o servidor Flask será iniciado")
            
            # Cria aplicação Flask para webhooks (independente do status do WAHA)
            flask_app = create_webhook_app(
                sess=sess,
                add_magnet_func=add_magnet if QBITTORRENT_AVAILABLE else None,
                qb_url=QB_URL,
                jellyfin_manager=jellyfin_manager
            )
            logger.info("Servidor Flask para webhooks WhatsApp configurado")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar WhatsApp WAHA: {e}")
            # Mesmo com erro, tenta criar o Flask app
            try:
                flask_app = create_webhook_app(
                    sess=sess,
                    add_magnet_func=add_magnet if QBITTORRENT_AVAILABLE else None,
                    qb_url=QB_URL,
                    jellyfin_manager=jellyfin_manager
                )
                logger.info("Servidor Flask criado apesar do erro na inicialização do WAHA")
            except Exception as flask_error:
                logger.error(f"Erro ao criar Flask app: {flask_error}")
                waha_enabled = False
    else:
        logger.info("WhatsApp WAHA não configurado (WAHA_URL ou WAHA_API_KEY ausentes)")
    
    def mensagens_thread():
        nonlocal last_update_id, sess
        while True:
            try:
                last_update_id = process_messages(sess, last_update_id, add_magnet, QB_URL, jellyfin_manager, sync_manager, stats_manager, docker_manager)
                time.sleep(1)
            except Exception as e:
                print(f"Erro no processamento de mensagens: {e}")
                time.sleep(5)  # Espera 5 segundos antes de tentar novamente
    
    def monitor_thread():
        if sess is not None and QBITTORRENT_AVAILABLE:
            try:
                monitor_torrents(sess, QB_URL, send_telegram, INTERVALO)
            except Exception as e:
                print(f"Erro no monitoramento de torrents: {e}")
    
    def jellyfin_notifier_thread():
        if jellyfin_notifier is not None:
            try:
                jellyfin_notifier.start_monitoring()
            except Exception as e:
                logger.error(f"Erro no monitoramento do Jellyfin: {e}")
    
    def sync_manager_thread():
        if sync_manager is not None:
            try:
                sync_manager.start()
                while True:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Erro no SyncManager: {e}")
    
    def stats_recorder_thread():
        if stats_manager is not None:
            try:
                while True:
                    stats_manager.record_bandwidth()
                    time.sleep(60)
            except Exception as e:
                logger.error(f"Erro no StatisticsManager: {e}")
    
    def flask_webhook_thread():
        if flask_app is not None:
            try:
                logger.info("Iniciando servidor Flask para webhooks WhatsApp na porta 5000")
                flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Erro no servidor Flask: {e}")
    
    # Inicia as threads
    threads = []
    
    # Thread de processamento de mensagens Telegram
    t1 = threading.Thread(target=mensagens_thread, daemon=True)
    threads.append(t1)
    t1.start()
    
    # Thread de monitoramento de torrents (apenas se qBittorrent estiver disponível)
    if QBITTORRENT_AVAILABLE and sess is not None:
        t2 = threading.Thread(target=monitor_thread, daemon=True)
        threads.append(t2)
        t2.start()
    
    # Thread de notificações do Jellyfin (apenas se habilitado)
    if jellyfin_notifier is not None:
        t3 = threading.Thread(target=jellyfin_notifier_thread, daemon=True)
        threads.append(t3)
        t3.start()
        logger.info("Thread de notificações do Jellyfin iniciada")
    
    # Thread do servidor Flask para webhooks WhatsApp (apenas se WAHA estiver configurado)
    if flask_app is not None:
        t4 = threading.Thread(target=flask_webhook_thread, daemon=True)
        threads.append(t4)
        t4.start()
        logger.info("Thread do servidor Flask para WhatsApp iniciada")
    
    # Thread do SyncManager (v0.0.1.7-alpha)
    if sync_manager is not None:
        t5 = threading.Thread(target=sync_manager_thread, daemon=True)
        threads.append(t5)
        t5.start()
        logger.info("Thread do SyncManager iniciada")
    
    # Thread do StatisticsManager (v0.0.1.7-alpha)
    if stats_manager is not None:
        t6 = threading.Thread(target=stats_recorder_thread, daemon=True)
        threads.append(t6)
        t6.start()
        logger.info("Thread do StatisticsManager iniciada")
    
    # Mantém o programa em execução
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando o bot...")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
    finally:
        logger.info("Bot encerrado.")

if __name__ == "__main__":
    logger.info("Iniciando o bot de gerenciamento de torrents...")
    main()