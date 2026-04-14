# GoStream Python - BitTorrent Streaming Engine

Implementação em Python da tecnologia **GoStream** para streaming direto de torrents via filesystem virtual FUSE, baseada no projeto [MrRobotoGit/gostream](https://github.com/MrRobotoGit/gostream).

## Visão Geral

GoStream Python permite **streamar conteúdo de torrents sem precisar baixar o arquivo completo**, similar ao que o Popcorn Time faz. Os arquivos são apresentados como arquivos MKV locais via FUSE, podendo ser reproduzidos diretamente no Jellyfin, Plex ou qualquer player de vídeo.

### Características Principais

- **Zero-Storage Streaming**: Arquivos são lidos diretamente da rede P2P
- **FUSE Virtual Filesystem**: Apresenta torrents como arquivos locais em `/mnt/gostream`
- **Native Bridge**: Streaming zero-copy via pipes em memória (sem overhead HTTP)
- **Read-Ahead Cache**: Cache sharded em RAM para pré-busca inteligente
- **Priority Mode**: Acelera download quando playback começa (via webhooks Jellyfin)
- **Adaptive Shield**: Proteção contra peers corrompidos
- **API REST**: Controle completo via HTTP (porta 8090)

## Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Jellyfin/Plex │────▶│  FUSE Layer     │────▶│  Native Bridge  │
│   Media Server  │     │  (Virtual MKV)  │     │  (Zero-Copy)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Read-Ahead     │
                    │  Cache (RAM)    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  BitTorrent     │
                    │  Engine         │
                    │  (libtorrent)   │
                    └─────────────────┘
```

## Instalação

### Pré-requisitos

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install libfuse3-dev

# macOS
brew install macfuse

# Windows
# FUSE não é suportado nativamente, mas a API REST funciona
```

### Instalação das Dependências

```bash
# Instalar libtorrent e fusepy
pip install libtorrent fusepy>=3.0.1
```

## Configuração

Adicione ao seu `.env`:

```env
# Habilitar GoStream
GOSTREAM_ENABLED=true

# Caminho de montagem FUSE
GOSTREAM_MOUNT_PATH=/mnt/gostream

# Portas BitTorrent
GOSTREAM_PORT_START=6881
GOSTREAM_PORT_END=6889

# Cache em RAM (MB)
GOSTREAM_READ_AHEAD_MB=512
GOSTREAM_CACHE_SHARDS=32

# API REST
GOSTREAM_API_PORT=8090
```

## Uso

### Via Bot Telegram

O GoStream é integrado automaticamente ao bot. Comandos disponíveis:

```
/gostream_add <magnet>  - Adiciona torrent para streaming
/gostream_list         - Lista torrents ativos
/gostream_remove <hash> - Remove torrent
/gostream_status       - Status do GoStream
```

### Via API REST

```bash
# Adicionar torrent
curl -X POST http://localhost:8090/api/torrents/add \
  -H "Content-Type: application/json" \
  -d '{"magnet": "magnet:?xt=urn:btih:..."}'

# Listar torrents
curl http://localhost:8090/api/torrents

# Ativar Priority Mode
curl -X POST http://localhost:8090/api/torrents/<hash>/priority \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Estatísticas do cache
curl http://localhost:8090/api/cache/stats
```

### Uso Standalone (sem o bot)

```python
from src.integrations.gostream import create_gostream, GoStreamConfig

# Cria instância
config = GoStreamConfig(
    fuse_mount_path='/mnt/gostream',
    read_ahead_budget_mb=512
)

manager = create_gostream(config)

# Inicializa
if manager.initialize() and manager.start():
    # Adiciona torrent
    info_hash = manager.add_torrent(
        'magnet:?xt=urn:btih:...',
        save_path='./downloads'
    )
    
    # Arquivo disponível em /mnt/gostream/<nome>/<arquivo>.mkv
    print(f"Streaming disponível em: /mnt/gostream/{info_hash[:8]}/")
    
    # Aguarda
    try:
        manager.wait()
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
```

## Integração com Jellyfin

### 1. Configurar Webhook no Jellyfin

1. Instale o plugin **Webhook** no Jellyfin
2. Configure webhook para `http://<bot>:5001/webhook/media`
3. Eventos: `media.play`, `media.stop`

### 2. Adicionar Biblioteca

1. No Jellyfin, adicione uma biblioteca do tipo **Filmes** ou **Séries**
2. Caminho: `/mnt/gostream` (ou seu `GOSTREAM_MOUNT_PATH`)
3. Ative monitoramento de pastas

### 3. Usar

1. Adicione torrents via bot: `/gostream_add magnet:?xt=...`
2. Aguarde metadata ser obtida (~5-30s)
3. No Jellyfin, atualize a biblioteca
4. Clique no filme - o Jellyfin começará a reproduzir imediatamente!

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/torrents` | Lista torrents |
| POST | `/api/torrents/add` | Adiciona magnet |
| POST | `/api/torrents/<hash>/remove` | Remove torrent |
| POST | `/api/torrents/<hash>/priority` | Priority mode |
| GET | `/api/cache/stats` | Stats do cache |
| POST | `/api/cache/clear` | Limpa cache |
| GET | `/api/session/stats` | Stats da sessão BT |
| POST | `/webhook/media` | Webhook Jellyfin/Plex |

## Componentes

### 1. BTEngine (`bt_engine.py`)
Engine BitTorrent usando `libtorrent-rasterbar`. Gerencia torrents, sessão P2P e streaming de peças.

### 2. ReadAheadCache (`read_ahead_cache.py`)
Cache em RAM com 32 shards para paralelismo. Pré-busca peças sequenciais para streaming fluido.

### 3. NativeBridge (`native_bridge.py`)
Conecta FUSE ao BTEngine via pipes em memória. Elimina overhead de HTTP.

### 4. FUSEFilesystem (`fuse_filesystem.py`)
Camada FUSE que apresenta torrents como arquivos `.mkv` locais.

### 5. StreamingAPI (`streaming_api.py`)
API REST Flask para controle e monitoramento.

## Troubleshooting

### "Transport endpoint not connected"
```bash
# Desmontar e remontar
fusermount -u /mnt/gostream
# Ou reinicie o bot
```

### Lentidão no streaming
- Aumente `GOSTREAM_READ_AHEAD_MB` (padrão: 512MB)
- Ative `GOSTREAM_RESPONSIVE_MODE=true`
- Verifique portas de firewall para P2P

### Erro ao montar FUSE
```bash
# Verifique permissões
sudo usermod -a -G fuse $USER
# Reinicie login
```

## Diferenças do GoStream Original (Go)

| Feature | GoStream (Go) | GoStream Python |
|---------|---------------|-----------------|
| Linguagem | Go | Python |
| BitTorrent | anacrolix/torrent fork | libtorrent-rasterbar |
| FUSE | go-fuse | fusepy |
| Performance | Nativo | ~90% do original |
| Facilidade | Complexa | Simples |
| Integração | Standalone | Bot Telegram |

## Créditos

- Baseado em [MrRobotoGit/gostream](https://github.com/MrRobotoGit/gostream)
- Engine BitTorrent: [libtorrent](https://www.libtorrent.org/)
- FUSE Python: [fusepy](https://github.com/fusepy/fusepy)

## Licença

MIT License - Mesma do projeto original.
