# API YTS Brasil - Documentação

## Visão Geral

A API YTS Brasil permite buscar e baixar filmes, séries e animes do site [ytsbr.com](https://ytsbr.com/) diretamente através do bot do Telegram. O sistema extrai links magnet e adiciona automaticamente ao qBittorrent.

## Arquitetura

### Módulos Criados

1. **`ytsbr_api.py`** - Cliente principal da API
   - Classe `YTSBRApi` com métodos de busca e extração
   - Funções auxiliares para uso direto

2. **`ytsbr_commands.py`** - Comandos do Telegram
   - Handlers para processar comandos do bot
   - Formatação de mensagens

## Funcionalidades

### 1. Busca de Conteúdo

#### Buscar Filmes
```
/ytsbr [termo de busca]
/ytsbr peaky blinders
```
- Sem termo: mostra filmes populares
- Com termo: busca filmes específicos

#### Buscar Séries
```
/ytsbr_series [termo de busca]
/ytsbr_series breaking bad
```
- Sem termo: mostra séries populares
- Com termo: busca séries específicas

#### Buscar Animes
```
/ytsbr_anime [termo de busca]
/ytsbr_anime dragon ball
```
- Sem termo: mostra animes populares
- Com termo: busca animes específicos

### 2. Download Automático

Ao enviar um link do ytsbr.com, o bot:
1. Extrai informações detalhadas (título, rating, sinopse)
2. Busca o link magnet
3. Adiciona automaticamente ao qBittorrent
4. Notifica o status

**Exemplo:**
```
https://ytsbr.com/filme/peaky-blinders-o-homem-imortal/
```

## Uso da API

### Exemplo Básico

```python
from ytsbr_api import YTSBRApi

# Inicializa a API
api = YTSBRApi()

# Busca por filmes
results = api.search("matrix", media_type="movie", limit=5)
for item in results:
    print(f"{item['title']} - {item['rating']}")

# Obtém detalhes
details = api.get_details(results[0]['url'])
print(f"Sinopse: {details['synopsis']}")

# Obtém link magnet
magnet = api.get_magnet_link(results[0]['url'])
print(f"Magnet: {magnet}")
```

### Métodos Disponíveis

#### `search(query, media_type, limit)`
Busca por conteúdo no YTS Brasil.

**Parâmetros:**
- `query` (str): Termo de busca
- `media_type` (str): Tipo de mídia - "movie", "series", "anime", "all"
- `limit` (int): Número máximo de resultados (padrão: 10)

**Retorna:** Lista de dicionários com:
- `title`: Título do item
- `url`: URL da página
- `type`: Tipo de mídia
- `rating`: Avaliação (ex: "89 %")
- `image`: URL da imagem

#### `get_details(url)`
Obtém informações detalhadas de um item.

**Parâmetros:**
- `url` (str): URL da página do item

**Retorna:** Dicionário com:
- `title`: Título completo
- `rating`: Avaliação (ex: "★ 8.9")
- `year`: Ano de lançamento
- `duration`: Duração (ex: "1h 52min")
- `genres`: Gêneros (ex: "Crime • Drama • Guerra")
- `synopsis`: Sinopse completa
- `image`: URL da imagem

#### `get_magnet_link(url)`
Extrai o link magnet de um item.

**Parâmetros:**
- `url` (str): URL da página do item

**Retorna:** String com o link magnet ou None

#### `get_popular(media_type, limit)`
Obtém lista de itens populares.

**Parâmetros:**
- `media_type` (str): "movie", "series" ou "anime"
- `limit` (int): Número máximo de resultados

**Retorna:** Lista de dicionários (mesmo formato do `search`)

## Comandos do Bot

### Botões do Teclado

- **🎬 Buscar Filmes** - Mostra filmes populares
- **📺 Buscar Séries** - Mostra séries populares
- **🎌 Buscar Animes** - Mostra animes populares

### Comandos de Texto

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/ytsbr` | Busca filmes ou mostra populares | `/ytsbr matrix` |
| `/ytsbr_series` | Busca séries ou mostra populares | `/ytsbr_series breaking bad` |
| `/ytsbr_anime` | Busca animes ou mostra populares | `/ytsbr_anime naruto` |

### Detecção Automática de URLs

O bot detecta automaticamente URLs do ytsbr.com e processa:
```
https://ytsbr.com/filme/avatar-fogo-e-cinzas/
https://ytsbr.com/serie/o-cavaleiro-dos-sete-reinos/
https://ytsbr.com/anime/dragon-ball-z/
```

## Fluxo de Trabalho

### 1. Busca
```
Usuário → /ytsbr matrix
Bot → Busca no ytsbr.com
Bot → Retorna lista de resultados com links
```

### 2. Download
```
Usuário → Envia URL do ytsbr.com
Bot → Extrai informações detalhadas
Bot → Busca link magnet
Bot → Adiciona ao qBittorrent
Bot → Confirma adição
```

## Estrutura de Dados

### Resultado de Busca
```json
{
  "title": "Matrix",
  "url": "https://ytsbr.com/filme/matrix/",
  "type": "movie",
  "rating": "87 %",
  "image": "https://assets.ytsbr.com/filmes/ptbr/matrix-w200-poster.webp"
}
```

### Detalhes do Item
```json
{
  "title": "Matrix Torrent 1999",
  "url": "https://ytsbr.com/filme/matrix/",
  "type": "movie",
  "rating": "★ 8.7",
  "year": "1999",
  "duration": "2h 16min",
  "genres": "Ação • Ficção científica",
  "synopsis": "Um hacker descobre a verdade sobre sua realidade...",
  "image": "https://assets.ytsbr.com/filmes/ptbr/matrix-w154-poster.webp"
}
```

## Tratamento de Erros

### Erros Comuns

1. **Link magnet não encontrado**
   - Causa: Conteúdo pode não estar disponível
   - Solução: Bot notifica o usuário

2. **Falha na busca**
   - Causa: Site fora do ar ou bloqueado
   - Solução: Bot retorna mensagem de erro

3. **Sem resultados**
   - Causa: Termo de busca não encontrado
   - Solução: Bot sugere refinar a busca

## Requisitos

### Dependências Python
```bash
pip install requests beautifulsoup4
```

### Variáveis de Ambiente
Nenhuma variável adicional necessária. Usa as configurações existentes do bot.

## Limitações

1. **Dependência do Site**
   - A API depende da estrutura HTML do ytsbr.com
   - Mudanças no site podem quebrar a funcionalidade

2. **Rate Limiting**
   - Não há controle de taxa de requisições
   - Uso excessivo pode resultar em bloqueio temporário

3. **Conteúdo Disponível**
   - Nem todos os itens têm links magnet disponíveis
   - Qualidade e disponibilidade variam

## Segurança

### Boas Práticas

1. **Autorização**
   - Apenas usuários autorizados podem usar os comandos
   - Verificação via `AUTHORIZED_USERS`

2. **Validação de URLs**
   - URLs são validadas antes do processamento
   - Regex para extrair URLs válidas

3. **Tratamento de Exceções**
   - Todos os erros são capturados e logados
   - Mensagens de erro amigáveis para o usuário

## Exemplos de Uso

### Buscar e Baixar um Filme

```
1. Usuário: /ytsbr matrix
2. Bot: [Lista de resultados]
3. Usuário: https://ytsbr.com/filme/matrix/
4. Bot: 
   📺 Matrix Torrent 1999
   ⭐ Avaliação: ★ 8.7
   📅 Ano: 1999
   ⏱ Duração: 2h 16min
   🎭 Gêneros: Ação • Ficção científica
   
   🔍 Buscando link magnet...
   ⏳ Adicionando torrent ao qBittorrent...
   ✅ Matrix adicionado com sucesso ao qBittorrent!
```

### Explorar Séries Populares

```
1. Usuário: /ytsbr_series
2. Bot: [Lista de séries populares]
3. Usuário: [Seleciona uma série]
4. Bot: [Processa download]
```

## Manutenção

### Atualizações Necessárias

Se o site ytsbr.com mudar sua estrutura:

1. Atualizar seletores CSS/HTML em `ytsbr_api.py`
2. Testar métodos `search()`, `get_details()` e `get_magnet_link()`
3. Verificar formatação de mensagens em `ytsbr_commands.py`

### Logs

Todos os erros são registrados via `logging`:
```python
logger.error(f"Erro ao buscar em ytsbr.com: {e}")
```

## Roadmap

### Funcionalidades Futuras

- [ ] Cache de resultados de busca
- [ ] Filtros avançados (ano, gênero, qualidade)
- [ ] Suporte a múltiplas qualidades
- [ ] Histórico de downloads
- [ ] Favoritos/Watchlist
- [ ] Notificações de novos lançamentos

## Contribuindo

Para adicionar novas funcionalidades:

1. Edite `ytsbr_api.py` para novos métodos de API
2. Adicione handlers em `ytsbr_commands.py`
3. Integre comandos em `telegram_utils.py`
4. Atualize esta documentação

## Licença

Este módulo faz parte do projeto Telegram Torrent Bot e segue a mesma licença.

---

**Última atualização:** 15/03/2026
**Versão:** 1.0.0
