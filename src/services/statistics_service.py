import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class StatisticsManager:
    """Gerenciador de estatísticas de downloads e uso de banda"""

    def __init__(self, qb_session=None, qb_url: str = None, data_file: str = "stats_data.json", multi_instance_manager=None):
        # Sessão/URL de instância única (modo legado)
        self.qb_session = qb_session
        self.qb_url = qb_url
        # Gerenciador multi-instância (quando habilitado)
        self.multi_instance_manager = multi_instance_manager
        self.data_file = data_file

        self.bandwidth_history: List[Dict] = []
        self.download_history: List[Dict] = []
        self.session_stats: Dict = {}

        self._load_data()
        logger.info("StatisticsManager inicializado")

    def _load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bandwidth_history = data.get('bandwidth_history', [])
                    self.download_history = data.get('download_history', [])
                    logger.info(f"Dados carregados: {len(self.bandwidth_history)} registros de banda, {len(self.download_history)} downloads")
        except Exception as e:
            logger.error(f"Erro ao carregar dados históricos: {e}")

    def _save_data(self):
        try:
            data = {
                'bandwidth_history': self.bandwidth_history,
                'download_history': self.download_history,
                'last_updated': datetime.now().isoformat(),
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar dados históricos: {e}")

    def _get_instances(self):
        """Retorna lista de tuplas (session, url, name) para coleta de stats."""
        if self.multi_instance_manager:
            # Considera apenas instâncias ativas e com sessão
            return [
                (inst.session, inst.url, inst.name)
                for inst in self.multi_instance_manager.instances.values()
                if inst.session and inst.is_active
            ]
        if self.qb_session and self.qb_url:
            return [(self.qb_session, self.qb_url, "default")]
        return []

    def record_bandwidth(self):
        from src.integrations.qbittorrent.client import get_transfer_info
        try:
            instances = self._get_instances()
            if not instances:
                return

            total_dl_speed = 0
            total_up_speed = 0
            total_dl_data = 0
            total_up_data = 0
            collected = 0

            for session, url, name in instances:
                transfer_info = get_transfer_info(session, url)
                if not transfer_info:
                    continue
                total_dl_speed += transfer_info.get('dl_info_speed', 0)
                total_up_speed += transfer_info.get('up_info_speed', 0)
                total_dl_data += transfer_info.get('dl_info_data', 0)
                total_up_data += transfer_info.get('up_info_data', 0)
                collected += 1

            if collected == 0:
                return

            record = {
                'timestamp': datetime.now().isoformat(),
                'dl_speed': total_dl_speed,
                'up_speed': total_up_speed,
                'dl_data': total_dl_data,
                'up_data': total_up_data,
            }
            self.bandwidth_history.append(record)
            max_records = 10000
            if len(self.bandwidth_history) > max_records:
                self.bandwidth_history = self.bandwidth_history[-max_records:]
            self._save_data()
        except Exception as e:
            logger.error(f"Erro ao registrar uso de banda: {e}")

    def record_download(self, torrent_hash: str, name: str, size: int, category: str = None):
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'hash': torrent_hash,
                'name': name,
                'size': size,
                'category': category,
            }
            self.download_history.append(record)
            self._save_data()
            logger.info(f"Download registrado: {name}")
        except Exception as e:
            logger.error(f"Erro ao registrar download: {e}")

    def get_bandwidth_stats(self, hours: int = 24) -> Dict:
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_records = [r for r in self.bandwidth_history if datetime.fromisoformat(r['timestamp']) > cutoff_time]
            if not recent_records:
                return {'period_hours': hours, 'total_downloaded': 0, 'total_uploaded': 0,
                        'avg_dl_speed': 0, 'avg_up_speed': 0, 'peak_dl_speed': 0, 'peak_up_speed': 0, 'records_count': 0}
            return {
                'period_hours': hours,
                'total_downloaded': sum(r['dl_data'] for r in recent_records),
                'total_uploaded': sum(r['up_data'] for r in recent_records),
                'avg_dl_speed': sum(r['dl_speed'] for r in recent_records) / len(recent_records),
                'avg_up_speed': sum(r['up_speed'] for r in recent_records) / len(recent_records),
                'peak_dl_speed': max(r['dl_speed'] for r in recent_records),
                'peak_up_speed': max(r['up_speed'] for r in recent_records),
                'records_count': len(recent_records),
            }
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de banda: {e}")
            return {}

    def get_download_history(self, days: int = 7) -> List[Dict]:
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_downloads = [d for d in self.download_history if datetime.fromisoformat(d['timestamp']) > cutoff_time]
            return sorted(recent_downloads, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"Erro ao obter histórico de downloads: {e}")
            return []

    def get_activity_summary(self) -> Dict:
        try:
            from src.integrations.qbittorrent.client import get_transfer_info
            instances = self._get_instances()

            current_dl = 0
            current_up = 0
            for session, url, _ in instances:
                transfer_info = get_transfer_info(session, url)
                if not transfer_info:
                    continue
                current_dl += transfer_info.get('dl_info_speed', 0)
                current_up += transfer_info.get('up_info_speed', 0)

            stats_24h = self.get_bandwidth_stats(24)
            stats_7d = self.get_bandwidth_stats(24 * 7)
            recent_downloads = self.get_download_history(7)
            return {
                'current': {
                    'dl_speed': current_dl,
                    'up_speed': current_up,
                },
                'last_24h': stats_24h,
                'last_7d': stats_7d,
                'recent_downloads': len(recent_downloads),
                'total_downloads': len(self.download_history),
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de atividade: {e}")
            return {}

    def format_bandwidth_stats(self, hours: int = 24) -> str:
        from src.integrations.qbittorrent.client import format_bytes
        stats = self.get_bandwidth_stats(hours)
        if not stats:
            return "❌ Erro ao obter estatísticas"
        if stats['records_count'] == 0:
            return f"📊 Sem dados de banda para as últimas {hours} horas"
        text = f"📊 <b>Estatísticas de Banda ({hours}h)</b>\n\n"
        text += f"📥 <b>Download:</b>\n"
        text += f"  • Total: {format_bytes(stats['total_downloaded'])}\n"
        text += f"  • Média: {format_bytes(stats['avg_dl_speed'])}/s\n"
        text += f"  • Pico: {format_bytes(stats['peak_dl_speed'])}/s\n\n"
        text += f"📤 <b>Upload:</b>\n"
        text += f"  • Total: {format_bytes(stats['total_uploaded'])}\n"
        text += f"  • Média: {format_bytes(stats['avg_up_speed'])}/s\n"
        text += f"  • Pico: {format_bytes(stats['peak_up_speed'])}/s\n\n"
        text += f"📈 Registros: {stats['records_count']}"
        return text

    def format_download_history(self, days: int = 7) -> str:
        from src.integrations.qbittorrent.client import format_bytes
        downloads = self.get_download_history(days)
        if not downloads:
            return f"📜 Nenhum download nos últimos {days} dias"
        text = f"📜 <b>Histórico de Downloads ({days} dias)</b>\n\n"
        for i, dl in enumerate(downloads[:10], 1):
            timestamp = datetime.fromisoformat(dl['timestamp'])
            date_str = timestamp.strftime('%d/%m %H:%M')
            name = dl['name'][:40]
            size = format_bytes(dl['size'])
            text += f"{i}. <b>{name}</b>\n"
            text += f"   📅 {date_str} | 💾 {size}\n\n"
        if len(downloads) > 10:
            text += f"... e mais {len(downloads) - 10} downloads"
        return text

    def format_activity_graph(self, hours: int = 24) -> str:
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_records = [r for r in self.bandwidth_history if datetime.fromisoformat(r['timestamp']) > cutoff_time]
            if not recent_records:
                return "📈 Sem dados para gráfico"

            intervals = min(hours, 24)
            interval_duration = hours / intervals
            buckets = defaultdict(lambda: {'dl': 0, 'up': 0, 'count': 0})

            for record in recent_records:
                timestamp = datetime.fromisoformat(record['timestamp'])
                hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
                bucket_idx = int(hours_ago / interval_duration)
                if 0 <= bucket_idx < intervals:
                    buckets[bucket_idx]['dl'] += record['dl_speed']
                    buckets[bucket_idx]['up'] += record['up_speed']
                    buckets[bucket_idx]['count'] += 1

            avg_speeds = [buckets[i]['dl'] / buckets[i]['count'] if buckets[i]['count'] > 0 else 0 for i in range(intervals)]
            max_speed = max(avg_speeds) if avg_speeds else 1
            bar_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

            text = f"📈 <b>Gráfico de Atividade ({hours}h)</b>\n\n"
            for i, speed in enumerate(reversed(avg_speeds)):
                bar_level = int((speed / max_speed) * (len(bar_chars) - 1)) if max_speed > 0 else 0
                bar = bar_chars[bar_level]
                hours_label = f"-{(i+1)*interval_duration:.0f}h"
                text += f"{hours_label:>5} {bar}\n"

            from src.integrations.qbittorrent.client import format_bytes
            text += f"\nMáx: {format_bytes(max_speed)}/s"
            return text
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de atividade: {e}")
            return "❌ Erro ao gerar gráfico"
