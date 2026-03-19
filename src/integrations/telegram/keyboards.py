def get_main_keyboard() -> dict:
    keyboard = {
        'keyboard': [
            [{'text': '📊 Status do Servidor'}],
            [{'text': '📦 Listar Torrents'}, {'text': '💾 Espaço em Disco'}],
            [{'text': '🎬 Itens Recentes'}, {'text': '🎭 Recentes Detalhado'}],
            [{'text': '📚 Bibliotecas'}, {'text': '🎥 YouTube'}],
            [{'text': '❓ Ajuda'}],
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False,
    }
    return keyboard
