import logging
from src.services.ytsbr_service import YTSBRApi
from src.integrations.telegram.client import send_telegram

logger = logging.getLogger(__name__)

_user_search_cache = {}


def format_ytsbr_result(item: dict, index: int) -> str:
    title = item.get('title', 'Título desconhecido')
    rating = item.get('rating', 'N/A')
    item_type = item.get('type', 'unknown')
    url = item.get('url', '')
    type_emoji = {'movie': '🎬', 'series': '📺', 'anime': '🎌'}.get(item_type, '📦')
    return f"{index}. {type_emoji} *{title}*\n   ⭐ {rating}\n   🔗 {url}\n"


def format_quality_info(quality_list: list) -> str:
    if not quality_list:
        return ""
    quality_sections = []
    cinema_quality, low_quality, other_quality = [], [], []
    for q in quality_list:
        q_type = q.get('type', '').upper()
        if 'CINEMA' in q_type:
            cinema_quality.append(q)
        elif 'BAIXA' in q_type or 'CAM' in q_type:
            low_quality.append(q)
        else:
            other_quality.append(q)

    def fmt_details(q):
        details = [q[k] for k in ('video_audio', 'resolution', 'language', 'format', 'codec') if q.get(k)]
        return "   • " + " | ".join(details) if details else ""

    if cinema_quality:
        quality_sections.append("\n🎬 *IMAGEM DE CINEMA*")
        for q in cinema_quality:
            d = fmt_details(q)
            if d:
                quality_sections.append(d)
    if low_quality:
        quality_sections.append("\n⚠️ *QUALIDADE BAIXA*")
        for q in low_quality:
            d = fmt_details(q)
            if d:
                quality_sections.append(d)
    for q in other_quality:
        q_type = q.get('type', 'HD')
        quality_sections.append(f"\n📀 *{q_type}*")
        d = fmt_details(q)
        if d:
            quality_sections.append(d)
    return "\n".join(quality_sections) if quality_sections else ""


def handle_ytsbr_search(query: str, media_type: str, chat_id: str, user_id: str = None):
    try:
        send_telegram(f"🔍 Buscando {media_type} por '{query}'...", chat_id, use_keyboard=True)
        api = YTSBRApi()
        results = api.search(query, media_type, limit=10)
        if not results:
            send_telegram(f"❌ Nenhum resultado encontrado para '{query}'", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"📋 *Resultados para '{query}':*\n\n"
        for i, item in enumerate(results, 1):
            message += format_ytsbr_result(item, i)
        message += "\n💡 *Para baixar:* `/ytsbr_baixar [número]`\n"
        message += "*Exemplo:* `/ytsbr_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao buscar no YTS Brasil: {e}")
        send_telegram(f"❌ Erro ao buscar: {str(e)}", chat_id, use_keyboard=True)


def handle_ytsbr_details(url: str, chat_id: str, add_magnet_func, sess, qb_url: str):
    try:
        send_telegram("🔍 Obtendo informações...", chat_id, use_keyboard=True)
        api = YTSBRApi()
        details = api.get_details(url)
        if not details:
            send_telegram("❌ Não foi possível obter detalhes do item", chat_id, use_keyboard=True)
            return

        title = details.get('title', 'Título desconhecido')
        rating = details.get('rating', 'N/A')
        year = details.get('year', 'N/A')
        duration = details.get('duration', 'N/A')
        genres = details.get('genres', 'N/A')
        synopsis = details.get('synopsis', 'Sem sinopse disponível')
        quality_list = details.get('quality', [])

        if len(synopsis) > 200:
            synopsis = synopsis[:200] + "..."

        quality_info = format_quality_info(quality_list)

        info_message = f"""
📺 *{title}*

⭐ *Avaliação:* {rating}
📅 *Ano:* {year}
⏱ *Duração:* {duration}
🎭 *Gêneros:* {genres}

📝 *Sinopse:*
{synopsis}
{quality_info}

🔍 Buscando link magnet..."""
        send_telegram(info_message, chat_id, parse_mode="Markdown", use_keyboard=True)

        magnet = api.get_magnet_link(url)
        if not magnet:
            send_telegram("❌ Link magnet não encontrado. O conteúdo pode não estar disponível.", chat_id, use_keyboard=True)
            return

        send_telegram("⏳ Adicionando torrent ao qBittorrent...", chat_id, use_keyboard=True)
        result = add_magnet_func(sess, qb_url, magnet)
        if result:
            send_telegram(f"✅ *{title}* adicionado com sucesso ao qBittorrent!", chat_id, parse_mode="Markdown", use_keyboard=True)
        else:
            send_telegram(f"❌ Falha ao adicionar torrent.\n\n🔗 Link magnet:\n`{magnet}`", chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar item do YTS Brasil: {e}")
        send_telegram(f"❌ Erro ao processar: {str(e)}", chat_id, use_keyboard=True)


def handle_ytsbr_popular(media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'anime': 'Animes'}
        type_name = type_names.get(media_type, 'Itens')
        send_telegram(f"🔥 Buscando {type_name} populares...", chat_id, use_keyboard=True)
        api = YTSBRApi()
        results = api.get_popular(media_type, limit=10)
        if not results:
            send_telegram(f"❌ Não foi possível obter {type_name.lower()} populares", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"🔥 *{type_name} Populares:*\n\n"
        for i, item in enumerate(results, 1):
            message += format_ytsbr_result(item, i)
        message += "\n💡 *Para baixar:* `/ytsbr_baixar [número]`\n"
        message += "*Exemplo:* `/ytsbr_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao obter populares do YTS Brasil: {e}")
        send_telegram(f"❌ Erro ao obter populares: {str(e)}", chat_id, use_keyboard=True)


def handle_ytsbr_genres(media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'anime': 'Animes'}
        type_name = type_names.get(media_type, 'Itens')
        api = YTSBRApi()
        genres = api.get_available_genres(media_type)
        if not genres:
            send_telegram(f"❌ Não foi possível obter gêneros para {type_name.lower()}", chat_id, use_keyboard=True)
            return
        message = f"🎭 *Gêneros Disponíveis - {type_name}:*\n\n"
        cols = 3
        rows = (len(genres) + cols - 1) // cols
        for row in range(rows):
            line_genres = []
            for col in range(cols):
                idx = row + col * rows
                if idx < len(genres):
                    line_genres.append(f"• {genres[idx].capitalize()}")
            message += "  ".join(line_genres) + "\n"
        message += f"\n💡 *Como usar:*\n"
        message += f"Para filmes: `/ytsbr_genero [gênero]`\n"
        message += f"Para séries: `/ytsbr_series_genero [gênero]`\n"
        message += f"Para animes: `/ytsbr_anime_genero [gênero]`\n\n"
        message += f"*Exemplo:* `/ytsbr_genero acao`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao listar gêneros: {e}")
        send_telegram(f"❌ Erro ao listar gêneros: {str(e)}", chat_id, use_keyboard=True)


def handle_ytsbr_by_genre(genre: str, media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'anime': 'Animes'}
        type_name = type_names.get(media_type, 'Itens')
        genre_display = genre.capitalize()
        send_telegram(f"🎭 Buscando {type_name} de {genre_display}...", chat_id, use_keyboard=True)
        api = YTSBRApi()
        results = api.search_by_genre(genre, media_type, limit=10)
        if not results:
            send_telegram(f"❌ Nenhum resultado encontrado para o gênero '{genre_display}' em {type_name.lower()}", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"🎭 *{type_name} - {genre_display}:*\n\n"
        for i, item in enumerate(results, 1):
            message += format_ytsbr_result(item, i)
        message += "\n💡 *Para baixar:* `/ytsbr_baixar [número]`\n"
        message += "*Exemplo:* `/ytsbr_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao buscar por gênero '{genre}': {e}")
        send_telegram(f"❌ Erro ao buscar por gênero: {str(e)}", chat_id, use_keyboard=True)


def handle_ytsbr_download_by_number(number: int, user_id: str, chat_id: str, add_magnet_func, sess, qb_url: str):
    try:
        if user_id not in _user_search_cache:
            send_telegram(
                "❌ Nenhuma busca recente encontrada.\n\nFaça uma busca primeiro usando `/ytsbr`, `/ytsbr_series`, `/ytsbr_anime` ou `/ytsbr_genero`",
                chat_id, parse_mode="Markdown", use_keyboard=True,
            )
            return
        results = _user_search_cache[user_id]
        if number < 1 or number > len(results):
            send_telegram(f"❌ Número inválido. Escolha entre 1 e {len(results)}", chat_id, use_keyboard=True)
            return
        selected_item = results[number - 1]
        url = selected_item.get('url')
        if not url:
            send_telegram("❌ URL não encontrada para este item", chat_id, use_keyboard=True)
            return
        handle_ytsbr_details(url, chat_id, add_magnet_func, sess, qb_url)
    except ValueError:
        send_telegram("❌ Número inválido. Use apenas números.\n\n*Exemplo:* `/ytsbr_baixar 1`", chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao baixar item por número: {e}")
        send_telegram(f"❌ Erro ao processar: {str(e)}", chat_id, use_keyboard=True)
