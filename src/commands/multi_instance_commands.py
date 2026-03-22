import logging
from typing import Optional
from src.integrations.telegram.client import send_telegram
from src.integrations.qbittorrent import get_manager
from src.core.config import QB_MULTI_INSTANCE_ENABLED, QB_INSTANCES_LIST

logger = logging.getLogger(__name__)


def initialize_multi_instance_manager():
    if not QB_MULTI_INSTANCE_ENABLED:
        logger.info("Multi-instância desabilitada.")
        return None
    
    manager = get_manager()
    
    for instance_config in QB_INSTANCES_LIST:
        manager.add_instance(
            name=instance_config['name'],
            url=instance_config['url'],
            username=instance_config['username'],
            password=instance_config['password'],
            storage_path=instance_config['storage_path'],
            priority=instance_config['priority']
        )
    
    logger.info(f"Multi-instância inicializada com {len(QB_INSTANCES_LIST)} instâncias.")
    return manager


def handle_instances_command(chat_id: int):
    try:
        if not QB_MULTI_INSTANCE_ENABLED:
            send_telegram(
                "❌ Multi-instância não está habilitada.\n\n"
                "Para habilitar, configure QB_MULTI_INSTANCE_ENABLED=True no .env",
                chat_id,
                use_keyboard=True
            )
            return
        
        manager = get_manager()
        summary = manager.get_instances_summary()
        send_telegram(summary, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /instances: {e}")
        send_telegram(f"❌ Erro ao listar instâncias: {str(e)}", chat_id, use_keyboard=True)


def handle_add_magnet_multi(magnet: str, chat_id: int, instance_name: Optional[str] = None):
    try:
        if not QB_MULTI_INSTANCE_ENABLED:
            send_telegram(
                "❌ Multi-instância não está habilitada. Use o comando /addmagnet padrão.",
                chat_id,
                use_keyboard=True
            )
            return False
        
        manager = get_manager()
        
        success, message = manager.add_magnet_smart(
            magnet=magnet,
            estimated_size=0,
            preferred_instance=instance_name
        )
        
        if success:
            send_telegram(
                f"✅ <b>Download adicionado!</b>\n\n{message}",
                chat_id,
                parse_mode="HTML",
                use_keyboard=True
            )
        else:
            send_telegram(
                f"❌ <b>Falha ao adicionar download</b>\n\n{message}",
                chat_id,
                parse_mode="HTML",
                use_keyboard=True
            )
        
        return success
    except Exception as e:
        logger.error(f"Erro ao adicionar magnet via multi-instância: {e}")
        send_telegram(
            f"❌ Erro ao adicionar download: {str(e)}",
            chat_id,
            use_keyboard=True
        )
        return False


def handle_torrents_multi_command(chat_id: int):
    try:
        if not QB_MULTI_INSTANCE_ENABLED:
            send_telegram(
                "❌ Multi-instância não está habilitada.",
                chat_id,
                use_keyboard=True
            )
            return
        
        manager = get_manager()
        all_instances = manager.get_all_instances()
        
        # Verificar instâncias inativas
        inactive_instances = [inst for inst in all_instances if not inst.is_active]
        active_instances = [inst for inst in all_instances if inst.is_active]
        
        response_lines = ["📊 <b>Torrents por Instância:</b>\n"]
        
        # Avisar sobre instâncias indisponíveis
        if inactive_instances:
            response_lines.append("⚠️ <b>Atenção:</b> Instâncias indisponíveis:\n")
            for inst in inactive_instances:
                response_lines.append(f"   ❌ <b>{inst.name}</b> - {inst.url}")
            response_lines.append("")
        
        # Verificar se há instâncias ativas
        if not active_instances:
            send_telegram("📭 Nenhuma instância ativa encontrada.", chat_id, use_keyboard=True)
            return
        
        all_torrents = manager.get_all_torrents()
        
        if not all_torrents:
            response_lines.append("� Nenhum torrent encontrado nas instâncias ativas.")
            send_telegram("\n".join(response_lines), chat_id, parse_mode="HTML", use_keyboard=True)
            return
        
        for instance_name, torrents in all_torrents.items():
            response_lines.append(f"\n🖥️ <b>{instance_name}</b>")
            
            if not torrents:
                response_lines.append("   └─ Nenhum torrent ativo\n")
                continue
            
            for t in torrents[:5]:
                name = t.get("name", "Sem nome")[:40]
                progress = t.get("progress", 0) * 100
                state = t.get("state", "unknown")
                
                state_emoji = {
                    "downloading": "⬇️",
                    "uploading": "⬆️",
                    "pausedDL": "⏸️",
                    "pausedUP": "⏸️",
                    "queuedDL": "⏳",
                    "queuedUP": "⏳",
                    "stalledDL": "🔄",
                    "stalledUP": "🔄",
                    "checkingDL": "🔍",
                    "checkingUP": "🔍",
                    "error": "❌",
                }.get(state, "📦")
                
                response_lines.append(
                    f"   {state_emoji} {name}\n"
                    f"      └─ {progress:.1f}% | {state}"
                )
            
            if len(torrents) > 5:
                response_lines.append(f"   └─ ... e mais {len(torrents) - 5} torrents")
            
            response_lines.append("")
        
        send_telegram("\n".join(response_lines), chat_id, parse_mode="HTML", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar comando /torrents_multi: {e}")
        send_telegram(f"❌ Erro ao listar torrents: {str(e)}", chat_id, use_keyboard=True)


def handle_refresh_storage_command(chat_id: int):
    try:
        if not QB_MULTI_INSTANCE_ENABLED:
            send_telegram(
                "❌ Multi-instância não está habilitada.",
                chat_id,
                use_keyboard=True
            )
            return
        
        manager = get_manager()
        send_telegram("🔄 Atualizando informações de armazenamento...", chat_id, use_keyboard=True)
        
        manager.update_all_storage_info()
        
        summary = manager.get_instances_summary()
        send_telegram(
            f"✅ <b>Armazenamento atualizado!</b>\n\n{summary}",
            chat_id,
            parse_mode="Markdown",
            use_keyboard=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar comando /refresh_storage: {e}")
        send_telegram(f"❌ Erro ao atualizar armazenamento: {str(e)}", chat_id, use_keyboard=True)


def handle_reconnect_instances_command(chat_id: int):
    try:
        if not QB_MULTI_INSTANCE_ENABLED:
            send_telegram(
                "❌ Multi-instância não está habilitada.",
                chat_id,
                use_keyboard=True
            )
            return
        
        manager = get_manager()
        send_telegram("🔄 Reconectando todas as instâncias...", chat_id, use_keyboard=True)
        
        results = manager.reconnect_all()
        
        response_lines = ["🔌 <b>Resultado da Reconexão:</b>\n"]
        for instance_name, success in results.items():
            status = "✅ Conectado" if success else "❌ Falha"
            response_lines.append(f"• <b>{instance_name}</b>: {status}")
        
        send_telegram(
            "\n".join(response_lines),
            chat_id,
            parse_mode="HTML",
            use_keyboard=True
        )
    except Exception as e:
        logger.error(f"Erro ao processar comando /reconnect_instances: {e}")
        send_telegram(f"❌ Erro ao reconectar instâncias: {str(e)}", chat_id, use_keyboard=True)
