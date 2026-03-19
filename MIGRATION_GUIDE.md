# Guia de Migração - Feature-based Package Structure

## Visão Geral

Este documento descreve a refatoração do projeto de uma estrutura plana (todos os arquivos no root) para uma **Feature-based Package Structure** organizada em `src/`.

## Data da Migração
**19 de Março de 2026** - Versão v0.0.1.8-alpha

## Estrutura Anterior vs Nova

### Antes (Estrutura Plana)
```
telegram_torrent/
├── main.py
├── qbittorrent_api.py
├── torrent_monitor.py
├── telegram_utils.py
├── jellyfin_consolidated.py
├── jellyfin_notifier.py
├── waha_api.py
├── waha_utils.py
├── youtube_downloader.py
├── sync_manager.py
├── statistics_manager.py
├── ytsbr_api.py
├── ytsbr_commands.py
├── whatsapp_commands.py
└── advanced_commands.py
```

### Depois (Feature-based)
```
telegram_torrent/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações centralizadas
│   │   ├── logging_config.py      # Setup de logging
│   │   └── exceptions.py          # Exceções customizadas
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── qbittorrent/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # API do qBittorrent
│   │   │   └── monitor.py         # Monitor de torrents
│   │   ├── jellyfin/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Cliente Jellyfin
│   │   │   ├── formatter.py       # Formatação de dados
│   │   │   ├── manager.py         # Gerenciador Jellyfin
│   │   │   └── notifier.py        # Notificações
│   │   ├── telegram/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Cliente Telegram
│   │   │   ├── keyboards.py       # Teclados customizados
│   │   │   ├── utils.py           # Utilitários Telegram
│   │   │   └── handlers.py        # Processamento de mensagens
│   │   ├── whatsapp/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Cliente WAHA
│   │   │   ├── utils.py           # Utilitários WhatsApp
│   │   │   └── webhook.py         # Webhook Flask
│   │   └── youtube/
│   │       ├── __init__.py
│   │       ├── downloader.py      # Downloader YouTube
│   │       └── utils.py           # Utilitários YouTube
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sync_service.py        # SyncManager
│   │   ├── statistics_service.py  # StatisticsManager
│   │   └── ytsbr_service.py       # YTSBRApi
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── telegram_commands.py   # Comandos avançados
│   │   ├── ytsbr_commands.py      # Comandos YTSBR
│   │   └── whatsapp_commands.py   # Comandos WhatsApp
│   └── utils/
│       ├── __init__.py
│       └── formatters.py          # Formatadores compartilhados
├── main.py                        # Ponto de entrada (atualizado)
└── [arquivos legados].py          # Shims de compatibilidade
```

## Mapeamento de Arquivos

| Arquivo Antigo | Novo Localização | Tipo |
|----------------|------------------|------|
| `qbittorrent_api.py` | `src/integrations/qbittorrent/client.py` + `monitor.py` | Migrado |
| `torrent_monitor.py` | `src/integrations/qbittorrent/monitor.py` | Migrado |
| `telegram_utils.py` | `src/integrations/telegram/client.py` + `utils.py` + `handlers.py` + `keyboards.py` | Dividido |
| `jellyfin_consolidated.py` | `src/integrations/jellyfin/client.py` + `formatter.py` + `manager.py` | Dividido |
| `jellyfin_notifier.py` | `src/integrations/jellyfin/notifier.py` | Migrado |
| `waha_api.py` | `src/integrations/whatsapp/client.py` | Migrado |
| `waha_utils.py` | `src/integrations/whatsapp/utils.py` + `webhook.py` | Dividido |
| `youtube_downloader.py` | `src/integrations/youtube/downloader.py` + `utils.py` | Dividido |
| `sync_manager.py` | `src/services/sync_service.py` | Migrado |
| `statistics_manager.py` | `src/services/statistics_service.py` | Migrado |
| `ytsbr_api.py` | `src/services/ytsbr_service.py` | Migrado |
| `ytsbr_commands.py` | `src/commands/ytsbr_commands.py` | Migrado |
| `whatsapp_commands.py` | `src/commands/whatsapp_commands.py` | Migrado |
| `advanced_commands.py` | `src/commands/telegram_commands.py` | Migrado |

## Mudanças de Importação

### Antes
```python
from qbittorrent_api import login_qb, fetch_torrents
from telegram_utils import send_telegram, process_messages
from jellyfin_consolidated import JellyfinManager
from sync_manager import SyncManager
```

### Depois
```python
from src.integrations.qbittorrent import login_qb, fetch_torrents
from src.integrations.telegram import send_telegram, process_messages
from src.integrations.jellyfin import JellyfinManager
from src.services import SyncManager
```

## Backward Compatibility

Todos os arquivos legados no root foram mantidos como **shims de compatibilidade**:
- Re-exportam funcionalidades de `src/`
- Código antigo continua funcionando sem modificações
- Permite migração gradual de código dependente

### Exemplo de Shim
```python
# qbittorrent_api.py (arquivo legado)
"""Backward-compatibility shim – use src.integrations.qbittorrent directly."""
from src.integrations.qbittorrent.client import (
    login_qb, fetch_torrents, add_magnet, # ...
)
from src.integrations.qbittorrent.monitor import monitor_torrents

__all__ = ["login_qb", "fetch_torrents", "add_magnet", "monitor_torrents"]
```

## Configuração Centralizada

### Antes
Múltiplos arquivos carregavam `.env`:
```python
# Em cada arquivo
from dotenv import load_dotenv
load_dotenv()
QB_URL = os.getenv('QB_URL')
```

### Depois
Carregamento único em `src/core/config.py`:
```python
# src/core/config.py
from dotenv import load_dotenv
load_dotenv()

QB_URL = os.getenv('QB_URL', 'http://localhost:8080')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# ... todas as variáveis centralizadas
```

Uso em outros módulos:
```python
from src.core.config import QB_URL, TELEGRAM_BOT_TOKEN
```

## Novas Variáveis de Ambiente

Adicionadas ao `src/core/config.py`:
- `QBITTORRENT_STORAGE_PATH`
- `WAHA_DASHBOARD_USERNAME`
- `WAHA_DASHBOARD_PASSWORD`
- `WAHA_SWAGGER_USERNAME`
- `WAHA_SWAGGER_PASSWORD`

## Benefícios da Nova Estrutura

1. **Organização Clara**: Código agrupado por feature/domínio
2. **Escalabilidade**: Fácil adicionar novas integrações
3. **Manutenibilidade**: Responsabilidades bem definidas
4. **Testabilidade**: Módulos isolados e testáveis
5. **Configuração Centralizada**: Único ponto de carregamento de variáveis
6. **Imports Explícitos**: `__all__` em todos os `__init__.py`
7. **Backward Compatibility**: Código legado continua funcionando

## Verificação da Migração

### Testes Realizados
```bash
# Imports do src/
python -c "from src.core.config import TELEGRAM_BOT_TOKEN; print('OK')"
python -c "from src.integrations.qbittorrent import login_qb; print('OK')"
python -c "from src.integrations.telegram import send_telegram; print('OK')"
python -c "from src.services import SyncManager; print('OK')"

# Imports legados (shims)
python -c "from qbittorrent_api import login_qb; print('OK')"
python -c "from telegram_utils import send_telegram; print('OK')"
python -c "from sync_manager import SyncManager; print('OK')"

# Build Docker
docker compose up -d --build  # ✓ Sucesso
```

## Próximos Passos (Opcional)

1. **Fase 2**: Remover shims após migração completa de código dependente
2. **Fase 3**: Adicionar testes unitários para cada módulo
3. **Fase 4**: Implementar type hints completos
4. **Fase 5**: Adicionar documentação inline (docstrings)

## Rollback (Se Necessário)

Para reverter a migração:
1. Os arquivos legados ainda existem como shims
2. `main.py` pode ser revertido para imports antigos
3. Pasta `src/` pode ser removida sem quebrar funcionalidade

## Suporte

Para dúvidas sobre a nova estrutura:
- Consulte `README.md` para visão geral
- Veja `versao.md` para changelog completo
- Examine `src/*/__init__.py` para exports disponíveis
