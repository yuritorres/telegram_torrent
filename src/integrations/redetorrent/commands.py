import logging
from src.integrations.redetorrent.client import RedeTorrentApi
from src.integrations.telegram.client import send_telegram

logger = logging.getLogger(__name__)

_user_search_cache = {}


def format_redetorrent_result(item: dict, index: int) -> str:
    title = item.get('title', 'Título desconhecido')
    rating = item.get('rating', 'N/A')
    item_type = item.get('type', 'unknown')
    quality = item.get('quality', '')
    audio_type = item.get('audio_type', '')
    url = item.get('url', '')
    type_emoji = {'movie': '🎬', 'series': '📺', 'desenho': '🎨'}.get(item_type, '📦')
    quality_str = f"   📀 {quality}\n" if quality else ""
    audio_str = f"   🔊 {audio_type}\n" if audio_type else ""
    return f"{index}. {type_emoji} *{title}*\n   ⭐ {rating}\n{quality_str}{audio_str}   🔗 {url}\n"


def format_detail_info(details: dict) -> str:
    title = details.get('title', 'Título desconhecido')
    original_title = details.get('original_title')
    imdb_rating = details.get('imdb_rating', 'N/A')
    year = details.get('year', 'N/A')
    duration = details.get('duration', 'N/A')
    genres = details.get('genres', 'N/A')
    language = details.get('language', 'N/A')
    quality = details.get('quality', 'N/A')
    fmt = details.get('format', 'N/A')
    video_audio = details.get('video_audio', 'N/A')
    size = details.get('size', 'N/A')
    synopsis = details.get('synopsis', 'Sem sinopse disponível')

    if synopsis and len(synopsis) > 300:
        synopsis = synopsis[:300] + "..."

    original_line = f"\n📌 *Título Original:* {original_title}" if original_title else ""

    return f"""📺 *{title}*{original_line}

⭐ *IMDB:* {imdb_rating}
📅 *Ano:* {year}
⏱ *Duração:* {duration}
🎭 *Gêneros:* {genres}
🔊 *Idioma:* {language}
📀 *Qualidade:* {quality}
📦 *Formato:* {fmt}
🎥 *{video_audio}*
💾 *Tamanho:* {size}

📝 *Sinopse:*
{synopsis}"""


def handle_redetorrent_search(query: str, media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'all': 'conteúdo', 'movie': 'filmes', 'series': 'séries', 'desenho': 'desenhos'}
        type_name = type_names.get(media_type, 'conteúdo')
        send_telegram(f"🔍 Buscando {type_name} por '{query}'...", chat_id, use_keyboard=True)
        api = RedeTorrentApi()
        results = api.search(query, media_type, limit=10)
        if not results:
            send_telegram(f"❌ Nenhum resultado encontrado para '{query}'", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"📋 *Resultados para '{query}':*\n\n"
        for i, item in enumerate(results, 1):
            message += format_redetorrent_result(item, i)
        message += "\n💡 *Para baixar:* `/rede_baixar [número]`\n"
        message += "*Exemplo:* `/rede_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao buscar no Rede Torrent: {e}")
        send_telegram(f"❌ Erro ao buscar: {str(e)}", chat_id, use_keyboard=True)


def handle_redetorrent_details(url: str, chat_id: str, add_magnet_func, sess, qb_url: str):
    try:
        send_telegram("🔍 Obtendo informações...", chat_id, use_keyboard=True)
        api = RedeTorrentApi()
        details = api.get_details(url)
        if not details:
            send_telegram("❌ Não foi possível obter detalhes do item", chat_id, use_keyboard=True)
            return

        info_message = format_detail_info(details)
        info_message += "\n\n🔍 Buscando link magnet..."
        send_telegram(info_message, chat_id, parse_mode="Markdown", use_keyboard=True)

        magnets = details.get('magnets', [])
        if not magnets:
            # Tenta buscar novamente
            magnets_list = api.get_all_magnets(url)
            if magnets_list:
                magnets = magnets_list

        if not magnets:
            send_telegram("❌ Link magnet não encontrado. O conteúdo pode não estar disponível.", chat_id, use_keyboard=True)
            return

        # Usa o primeiro magnet
        magnet = magnets[0]['url']
        title = details.get('title', 'Título desconhecido')

        # Se há múltiplos magnets, informa
        if len(magnets) > 1:
            versions_msg = "📋 *Versões disponíveis:*\n"
            for i, m in enumerate(magnets, 1):
                versions_msg += f"  {i}. {m.get('label', 'DOWNLOAD')}\n"
            versions_msg += f"\n⬇️ Baixando versão 1: *{magnets[0].get('label', 'DOWNLOAD')}*"
            send_telegram(versions_msg, chat_id, parse_mode="Markdown", use_keyboard=True)

        send_telegram("⏳ Adicionando torrent ao qBittorrent...", chat_id, use_keyboard=True)
        result = add_magnet_func(sess, qb_url, magnet)
        if result:
            send_telegram(f"✅ *{title}* adicionado com sucesso ao qBittorrent!", chat_id, parse_mode="Markdown", use_keyboard=True)
        else:
            send_telegram(f"❌ Falha ao adicionar torrent.\n\n🔗 Link magnet:\n`{magnet}`", chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao processar item do Rede Torrent: {e}")
        send_telegram(f"❌ Erro ao processar: {str(e)}", chat_id, use_keyboard=True)


def handle_redetorrent_popular(media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'desenho': 'Desenhos',
                      'dublado': 'Dublados', 'legendado': 'Legendados', 'lancamento': 'Lançamentos'}
        type_name = type_names.get(media_type, 'Itens')
        send_telegram(f"🔥 Buscando {type_name} populares...", chat_id, use_keyboard=True)
        api = RedeTorrentApi()
        results = api.get_popular(media_type, limit=10)
        if not results:
            send_telegram(f"❌ Não foi possível obter {type_name.lower()} populares", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"🔥 *{type_name} Populares - Rede Torrent:*\n\n"
        for i, item in enumerate(results, 1):
            message += format_redetorrent_result(item, i)
        message += "\n💡 *Para baixar:* `/rede_baixar [número]`\n"
        message += "*Exemplo:* `/rede_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao obter populares do Rede Torrent: {e}")
        send_telegram(f"❌ Erro ao obter populares: {str(e)}", chat_id, use_keyboard=True)


def handle_redetorrent_genres(media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'desenho': 'Desenhos'}
        type_name = type_names.get(media_type, 'Itens')
        api = RedeTorrentApi()
        genres = api.get_available_genres(media_type)
        if not genres:
            send_telegram(f"❌ Não foi possível obter gêneros para {type_name.lower()}", chat_id, use_keyboard=True)
            return
        message = f"🎭 *Gêneros Disponíveis - {type_name} (Rede Torrent):*\n\n"
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
        message += f"Para filmes: `/rede_genero [gênero]`\n"
        message += f"Para séries: `/rede_series_genero [gênero]`\n"
        message += f"Para desenhos: `/rede_desenhos_genero [gênero]`\n\n"
        message += f"*Exemplo:* `/rede_genero acao`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao listar gêneros: {e}")
        send_telegram(f"❌ Erro ao listar gêneros: {str(e)}", chat_id, use_keyboard=True)


def handle_redetorrent_by_genre(genre: str, media_type: str, chat_id: str, user_id: str = None):
    try:
        type_names = {'movie': 'Filmes', 'series': 'Séries', 'desenho': 'Desenhos'}
        type_name = type_names.get(media_type, 'Itens')
        genre_display = genre.capitalize()
        send_telegram(f"🎭 Buscando {type_name} de {genre_display}...", chat_id, use_keyboard=True)
        api = RedeTorrentApi()
        results = api.search_by_genre(genre, media_type, limit=10)
        if not results:
            send_telegram(f"❌ Nenhum resultado encontrado para o gênero '{genre_display}' em {type_name.lower()}", chat_id, use_keyboard=True)
            return
        if user_id:
            _user_search_cache[user_id] = results
        message = f"🎭 *{type_name} - {genre_display} (Rede Torrent):*\n\n"
        for i, item in enumerate(results, 1):
            message += format_redetorrent_result(item, i)
        message += "\n💡 *Para baixar:* `/rede_baixar [número]`\n"
        message += "*Exemplo:* `/rede_baixar 1`"
        send_telegram(message, chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao buscar por gênero '{genre}': {e}")
        send_telegram(f"❌ Erro ao buscar por gênero: {str(e)}", chat_id, use_keyboard=True)


def handle_redetorrent_download_by_number(number: int, user_id: str, chat_id: str, add_magnet_func, sess, qb_url: str):
    try:
        if user_id not in _user_search_cache:
            send_telegram(
                "❌ Nenhuma busca recente encontrada.\n\nFaça uma busca primeiro usando `/rede`, `/rede_series`, `/rede_desenhos` ou `/rede_genero`",
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
        handle_redetorrent_details(url, chat_id, add_magnet_func, sess, qb_url)
    except ValueError:
        send_telegram("❌ Número inválido. Use apenas números.\n\n*Exemplo:* `/rede_baixar 1`", chat_id, parse_mode="Markdown", use_keyboard=True)
    except Exception as e:
        logger.error(f"Erro ao baixar item por número: {e}")
        send_telegram(f"❌ Erro ao processar: {str(e)}", chat_id, use_keyboard=True)
