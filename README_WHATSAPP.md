# 📱 Integração WhatsApp (WAHA)

## 📋 Visão Geral

Este projeto integra a API WhatsApp WAHA (WhatsApp HTTP API) para permitir o gerenciamento de torrents e mídia através do WhatsApp, além do Telegram já existente.

WAHA é uma solução self-hosted que permite enviar e receber mensagens do WhatsApp através de uma API HTTP REST.

## 🚀 Recursos

- ✅ Envio de mensagens de texto
- ✅ Envio de imagens com legenda
- ✅ Envio de arquivos
- ✅ Recebimento de mensagens via webhook
- ✅ Autenticação via QR Code
- ✅ Dashboard web para gerenciamento
- ✅ Documentação Swagger integrada
- ✅ Persistência de sessões com PostgreSQL
- ✅ Fila de mensagens com Redis

## 🏗️ Arquitetura

```
┌─────────────────┐
│   WhatsApp      │
│   (Seu celular) │
└────────┬────────┘
         │ QR Code
         ▼
┌─────────────────┐      ┌──────────────┐
│   WAHA API      │◄────►│ PostgreSQL   │
│   (Container)   │      │ (Sessões)    │
└────────┬────────┘      └──────────────┘
         │                      
         │               ┌──────────────┐
         ├──────────────►│    Redis     │
         │               │   (Filas)    │
         │               └──────────────┘
         ▼
┌─────────────────┐
│  Telegram Bot   │
│  (Python App)   │
└─────────────────┘
```

## 📦 Componentes

### 1. **WAHA (WhatsApp HTTP API)**
- Container Docker: `devlikeapro/waha:latest`
- Porta: `3000`
- Dashboard: `http://localhost:3000/dashboard`
- Swagger: `http://localhost:3000/`

### 2. **PostgreSQL**
- Container: `postgres:17`
- Porta: `5432`
- Database: `wahadb`
- Armazena sessões do WhatsApp

### 3. **Redis**
- Container: `redis:latest`
- Porta: `6379`
- Gerencia filas de mensagens

### 4. **Módulos Python**
- `waha_api.py`: Cliente para comunicação com WAHA
- `waha_utils.py`: Utilitários e processamento de webhooks

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Edite o arquivo `.env`:

```bash
# CONFIGURAÇÕES DO WHATSAPP (WAHA)
WAHA_URL=http://waha:3000
WAHA_API_KEY=local-dev-key-123
WAHA_SESSION=default
AUTHORIZED_WHATSAPP_NUMBERS=5511999999999,5511888888888

# Dashboard
WAHA_DASHBOARD_USERNAME=admin
WAHA_DASHBOARD_PASSWORD=admin123

# Swagger
WAHA_SWAGGER_USERNAME=admin
WAHA_SWAGGER_PASSWORD=swagger123
```

### 2. Iniciar Serviços

```bash
# Subir todos os containers
docker-compose up -d

# Verificar logs
docker-compose logs -f waha
```

### 3. Autenticar WhatsApp

#### Opção 1: Via Dashboard (Recomendado)

1. Acesse: `http://localhost:3000/dashboard`
2. Login: `admin` / `admin123`
3. Clique em "Start Session"
4. Escaneie o QR Code com seu WhatsApp

#### Opção 2: Via Swagger

1. Acesse: `http://localhost:3000/`
2. Login: `admin` / `swagger123`
3. Execute `POST /api/sessions` com:
   ```json
   {
     "name": "default"
   }
   ```
4. Execute `GET /api/screenshot` para ver o QR Code
5. Escaneie com seu WhatsApp

#### Opção 3: Via Python

```python
from waha_utils import init_waha_client, start_whatsapp_session, get_whatsapp_qr

# Inicializar cliente
client = init_waha_client()

# Iniciar sessão
start_whatsapp_session()

# Obter QR Code
qr_url = get_whatsapp_qr()
print(f"QR Code: {qr_url}")
```

## 💻 Uso da API

### Enviar Mensagem de Texto

```python
from waha_utils import send_whatsapp

# Enviar mensagem
send_whatsapp(
    text="Olá! Seu torrent foi concluído.",
    chat_id="5511999999999@c.us"
)
```

### Enviar Imagem

```python
from waha_api import WAHAApi

client = WAHAApi("http://localhost:3000", "local-dev-key-123")

client.send_image(
    chat_id="5511999999999@c.us",
    image_url="https://example.com/image.jpg",
    caption="Poster do filme"
)
```

### Enviar Arquivo

```python
client.send_file(
    chat_id="5511999999999@c.us",
    file_url="https://example.com/video.mp4",
    filename="video.mp4",
    caption="Download concluído!"
)
```

### Verificar Status da Sessão

```python
from waha_utils import get_whatsapp_status

status = get_whatsapp_status()
print(status)
```

## 🔔 Webhooks

### Configurar Webhook

O webhook já está configurado no `docker-compose.yml`:

```yaml
environment:
  - WHATSAPP_HOOK_URL=http://telegram-torrent:5000/whatsapp/webhook
  - WHATSAPP_HOOK_EVENTS=*
```

### Processar Mensagens Recebidas

O arquivo `waha_utils.py` já possui um handler de webhooks:

```python
def process_whatsapp_webhook(data: Dict[str, Any]) -> Dict[str, str]:
    """Processa mensagens recebidas do WhatsApp"""
    event = data.get('event')
    payload = data.get('payload', {})
    
    if event == 'message':
        from_number = payload.get('from', '')
        text = payload.get('body', '')
        
        # Processar comando
        # ...
```

## 🎯 Comandos Disponíveis

Os mesmos comandos do Telegram podem ser adaptados para WhatsApp:

- `/status` - Status do servidor
- `/qtorrents` - Listar torrents
- `/ytsbr [termo]` - Buscar filmes
- `/ytsbr_baixar [número]` - Baixar item da lista
- E todos os outros comandos existentes

## 🔒 Segurança

### Autenticação

1. **API Key**: Todas as requisições requerem `X-Api-Key` header
2. **Números Autorizados**: Configure `AUTHORIZED_WHATSAPP_NUMBERS` no `.env`
3. **Dashboard/Swagger**: Protegidos por senha

### Boas Práticas

- ✅ Altere as senhas padrão em produção
- ✅ Use HTTPS em produção (configure reverse proxy)
- ✅ Mantenha a API Key segura
- ✅ Limite os números autorizados
- ✅ Faça backup regular do PostgreSQL

## 📊 Monitoramento

### Verificar Saúde dos Serviços

```bash
# WAHA
curl http://localhost:3000/api/health

# PostgreSQL
docker exec postgreswaha pg_isready -U postgres

# Redis
docker exec redis redis-cli ping
```

### Logs

```bash
# WAHA
docker-compose logs -f waha

# PostgreSQL
docker-compose logs -f postgreswaha

# Redis
docker-compose logs -f redis
```

## 🐛 Troubleshooting

### QR Code não aparece

```bash
# Reiniciar sessão
docker-compose restart waha

# Verificar logs
docker-compose logs waha
```

### Mensagens não são enviadas

1. Verifique se a sessão está ativa:
   ```bash
   curl -H "X-Api-Key: local-dev-key-123" \
        http://localhost:3000/api/sessions/default
   ```

2. Verifique o formato do chat_id:
   - Contatos: `5511999999999@c.us`
   - Grupos: `5511999999999@g.us`

### PostgreSQL não conecta

```bash
# Verificar se está rodando
docker ps | grep postgreswaha

# Testar conexão
docker exec postgreswaha psql -U postgres -d wahadb -c "SELECT 1"
```

## 📚 Recursos Adicionais

- [Documentação WAHA](https://waha.devlike.pro/)
- [GitHub WAHA](https://github.com/devlikeapro/waha)
- [Exemplos Python](https://github.com/devlikeapro/waha/tree/core/examples/python)
- [API Reference](https://waha.devlike.pro/docs/how-to/swagger/)

## 🔄 Atualização

```bash
# Parar serviços
docker-compose down

# Atualizar imagem
docker pull devlikeapro/waha:latest

# Reiniciar
docker-compose up -d
```

## 💾 Backup

### Backup do PostgreSQL

```bash
# Criar backup
docker exec postgreswaha pg_dump -U postgres wahadb > backup_waha.sql

# Restaurar backup
docker exec -i postgreswaha psql -U postgres wahadb < backup_waha.sql
```

### Backup das Sessões

```bash
# Backup dos volumes
docker run --rm -v telegram_torrent_waha_sessions:/data \
           -v $(pwd):/backup alpine \
           tar czf /backup/waha_sessions_backup.tar.gz /data
```

## 🎓 Exemplos de Integração

### Notificar Download Concluído

```python
from waha_utils import send_whatsapp

def notify_download_complete(torrent_name, chat_id):
    message = f"""
✅ *Download Concluído!*

📁 {torrent_name}

Use /qtorrents para ver todos os torrents.
    """
    
    send_whatsapp(message, chat_id)
```

### Enviar Poster do Filme

```python
from waha_api import WAHAApi

def send_movie_poster(movie_title, poster_url, chat_id):
    client = WAHAApi("http://localhost:3000", "local-dev-key-123")
    
    client.send_image(
        chat_id=chat_id,
        image_url=poster_url,
        caption=f"🎬 {movie_title}"
    )
```

## ⚠️ Limitações

- WhatsApp não permite bots oficiais
- Risco de bloqueio se usado comercialmente
- Limite de mensagens por segundo (evite spam)
- Não suporta chamadas de voz/vídeo
- Grupos têm limitações específicas

## 📝 Notas

- WAHA Core é gratuito e open-source
- WAHA Plus oferece recursos adicionais (pago)
- Use por sua conta e risco
- Respeite os Termos de Serviço do WhatsApp
