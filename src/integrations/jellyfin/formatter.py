from typing import Dict, Any


class JellyfinFormatter:
    """Classe para formatação de dados do Jellyfin"""

    @staticmethod
    def format_item_info(item: Dict) -> Dict[str, Any]:
        return {
            'title': item.get('Name', 'Sem título'),
            'type': item.get('Type', 'Desconhecido'),
            'year': item.get('ProductionYear'),
            'rating': item.get('CommunityRating'),
            'genres': item.get('Genres', []),
            'overview': item.get('Overview', ''),
            'id': item.get('Id'),
        }

    @staticmethod
    def format_telegram_message(item: Dict, web_link: str = None) -> str:
        info = JellyfinFormatter.format_item_info(item)

        message = f"📺 **{info['title']}**\n"
        message += f"▶️ Tipo: {info['type']}\n"

        if info['rating']:
            message += f"⭐ Avaliação: {info['rating']}\n"
        if info['year']:
            message += f"📅 Ano: {info['year']}\n"
        if info['genres']:
            message += f"🎭 Gêneros: {', '.join(info['genres'][:3])}\n"
        if info['overview']:
            overview = info['overview']
            if len(overview) > 200:
                overview = overview[:200] + "..."
            message += f"\n{overview}"

        return message.strip()
