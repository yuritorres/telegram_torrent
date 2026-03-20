import logging
from typing import Optional
from src.integrations.telegram.client import send_telegram
from src.integrations.docker import DockerManager
from datetime import datetime

logger = logging.getLogger(__name__)


def format_containers_list(containers: list) -> str:
    if not containers:
        return "📦 <b>Nenhum container encontrado</b>"
    
    running = [c for c in containers if c['status'] == 'running']
    stopped = [c for c in containers if c['status'] != 'running']
    
    text = f"🐳 <b>Containers Docker</b>\n\n"
    
    if running:
        text += "▶️ <b>Em execução:</b>\n"
        for c in running:
            text += f"  • <code>{c['name']}</code>\n"
            text += f"    ID: <code>{c['id']}</code>\n"
            text += f"    Imagem: {c['image']}\n\n"
    
    if stopped:
        text += "⏸️ <b>Parados:</b>\n"
        for c in stopped:
            status_emoji = "⏹️" if c['status'] == 'exited' else "⚠️"
            text += f"  {status_emoji} <code>{c['name']}</code>\n"
            text += f"    ID: <code>{c['id']}</code>\n"
            text += f"    Status: {c['status']}\n"
            text += f"    Imagem: {c['image']}\n\n"
    
    text += f"\n📊 <b>Total:</b> {len(containers)} containers"
    text += f"\n✅ <b>Ativos:</b> {len(running)}"
    text += f"\n⏸️ <b>Parados:</b> {len(stopped)}"
    
    return text


def handle_docker_list_command(docker_manager: Optional[DockerManager], chat_id: int):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        containers = docker_manager.list_containers(all_containers=True)
        message = format_containers_list(containers)
        send_telegram(message, chat_id, parse_mode="HTML", use_keyboard=True)
        
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_list: {e}")
        send_telegram(f"❌ Erro ao listar containers: {str(e)}", chat_id, use_keyboard=True)


def handle_docker_start_command(docker_manager: Optional[DockerManager], chat_id: int, container_name: str = None):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        if not container_name:
            help_text = """🚀 <b>Iniciar Container Docker</b>

<b>Como usar:</b>
<code>/docker_start [nome ou ID]</code>

<b>Exemplo:</b>
<code>/docker_start qbittorrent</code>
<code>/docker_start abc123</code>

💡 <b>Dica:</b> Use /docker_list para ver os containers disponíveis"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        send_telegram(f"⏳ Iniciando container <code>{container_name}</code>...", chat_id, parse_mode="HTML", use_keyboard=True)
        success, message = docker_manager.start_container(container_name)
        
        if success:
            send_telegram(f"✅ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
        else:
            send_telegram(f"❌ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
            
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_start: {e}")
        send_telegram(f"❌ Erro ao iniciar container: {str(e)}", chat_id, use_keyboard=True)


def handle_docker_stop_command(docker_manager: Optional[DockerManager], chat_id: int, container_name: str = None):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        if not container_name:
            help_text = """🛑 <b>Parar Container Docker</b>

<b>Como usar:</b>
<code>/docker_stop [nome ou ID]</code>

<b>Exemplo:</b>
<code>/docker_stop qbittorrent</code>
<code>/docker_stop abc123</code>

⚠️ <b>Atenção:</b> O container será parado graciosamente (timeout de 10s)

💡 <b>Dica:</b> Use /docker_list para ver os containers em execução"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        send_telegram(f"⏳ Parando container <code>{container_name}</code>...", chat_id, parse_mode="HTML", use_keyboard=True)
        success, message = docker_manager.stop_container(container_name)
        
        if success:
            send_telegram(f"✅ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
        else:
            send_telegram(f"❌ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
            
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_stop: {e}")
        send_telegram(f"❌ Erro ao parar container: {str(e)}", chat_id, use_keyboard=True)


def handle_docker_restart_command(docker_manager: Optional[DockerManager], chat_id: int, container_name: str = None):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        if not container_name:
            help_text = """🔄 <b>Reiniciar Container Docker</b>

<b>Como usar:</b>
<code>/docker_restart [nome ou ID]</code>

<b>Exemplo:</b>
<code>/docker_restart qbittorrent</code>
<code>/docker_restart abc123</code>

💡 <b>Dica:</b> Use /docker_list para ver os containers disponíveis"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        send_telegram(f"⏳ Reiniciando container <code>{container_name}</code>...", chat_id, parse_mode="HTML", use_keyboard=True)
        success, message = docker_manager.restart_container(container_name)
        
        if success:
            send_telegram(f"✅ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
        else:
            send_telegram(f"❌ {message}", chat_id, parse_mode="HTML", use_keyboard=True)
            
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_restart: {e}")
        send_telegram(f"❌ Erro ao reiniciar container: {str(e)}", chat_id, use_keyboard=True)


def handle_docker_stats_command(docker_manager: Optional[DockerManager], chat_id: int, container_name: str = None):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        if not container_name:
            help_text = """📊 <b>Estatísticas de Container Docker</b>

<b>Como usar:</b>
<code>/docker_stats [nome ou ID]</code>

<b>Exemplo:</b>
<code>/docker_stats qbittorrent</code>

💡 <b>Dica:</b> Use /docker_list para ver os containers disponíveis"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        stats = docker_manager.get_container_stats(container_name)
        
        if not stats:
            send_telegram(f"❌ Não foi possível obter estatísticas do container <code>{container_name}</code>", chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        mem_usage_mb = stats['memory_usage'] / (1024 * 1024)
        mem_limit_mb = stats['memory_limit'] / (1024 * 1024)
        
        stats_text = f"""📊 <b>Estatísticas - {stats['name']}</b>

💻 <b>CPU:</b> {stats['cpu_percent']}%
🧠 <b>Memória:</b> {mem_usage_mb:.2f}MB / {mem_limit_mb:.2f}MB ({stats['memory_percent']:.1f}%)"""
        
        send_telegram(stats_text, chat_id, parse_mode="HTML", use_keyboard=True)
        
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_stats: {e}")
        send_telegram(f"❌ Erro ao obter estatísticas: {str(e)}", chat_id, use_keyboard=True)


def handle_docker_logs_command(docker_manager: Optional[DockerManager], chat_id: int, container_name: str = None, tail: int = 30):
    try:
        if not docker_manager or not docker_manager.is_available():
            send_telegram("❌ Docker não disponível ou não configurado.", chat_id, use_keyboard=True)
            return
        
        if not container_name:
            help_text = """📜 <b>Logs de Container Docker</b>

<b>Como usar:</b>
<code>/docker_logs [nome ou ID] [linhas]</code>

<b>Exemplo:</b>
<code>/docker_logs qbittorrent</code>
<code>/docker_logs qbittorrent 50</code>

💡 <b>Dica:</b> Por padrão mostra as últimas 30 linhas"""
            send_telegram(help_text, chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        logs = docker_manager.get_container_logs(container_name, tail=tail)
        
        if not logs:
            send_telegram(f"❌ Não foi possível obter logs do container <code>{container_name}</code>", chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        if len(logs) > 4000:
            logs = logs[-4000:]
            logs = "...\n" + logs
        
        logs_text = f"📜 <b>Logs - {container_name}</b> (últimas {tail} linhas)\n\n<pre>{logs}</pre>"
        send_telegram(logs_text, chat_id, parse_mode="HTML", use_keyboard=True)
        
    except Exception as e:
        logger.error(f"Erro ao processar comando /docker_logs: {e}")
        send_telegram(f"❌ Erro ao obter logs: {str(e)}", chat_id, use_keyboard=True)
