# ResolutaHubOs - Interface Web

Interface web moderna com aparência de sistema operacional para gerenciar sua aplicação Telegram Torrent.

## 🎨 Características

- **Interface estilo OS**: Design inspirado em sistemas operacionais modernos
- **Gerenciamento de Torrents**: Adicionar, pausar, retomar e remover torrents
- **GoStream Streaming**: Streamar torrents sem baixar via BitTorrent
- **Biblioteca Jellyfin**: Visualizar itens recentes do servidor de mídia
- **Controle Docker**: Gerenciar containers Docker
- **Monitor do Sistema**: Acompanhar status de todos os serviços
- **Atualizações em Tempo Real**: WebSocket para updates automáticos
- **Design Responsivo**: Interface adaptável com TailwindCSS

## 🚀 Instalação

### Backend (FastAPI)

```bash
cd web/backend
pip install -r requirements.txt
python main.py
```

O backend estará disponível em `http://localhost:8000`

### Frontend (React + Vite)

```bash
cd web/frontend
npm install
npm run dev
```

O frontend estará disponível em `http://localhost:3001`

## 🐳 Docker

Arquivo docker-compose será adicionado para facilitar o deploy completo.

## 📱 Uso

1. Inicie o backend FastAPI
2. Inicie o frontend React
3. Acesse `http://localhost:3001` no navegador
4. Clique nos ícones da área de trabalho para abrir aplicativos
5. Arraste janelas, maximize/minimize conforme necessário

## 🔧 Configuração

O backend utiliza as mesmas variáveis de ambiente do arquivo `.env` principal da aplicação.

### GoStream (Streaming de Torrents)

Para habilitar o GoStream na interface web, configure no `.env`:

```env
# Habilitar GoStream
GOSTREAM_ENABLED=true

# Configuração da API GoStream
GOSTREAM_API_HOST=localhost
GOSTREAM_API_PORT=8090
GOSTREAM_MOUNT_PATH=/mnt/gostream
```

O GoStream permite streamar conteúdo de torrents **sem precisar baixar o arquivo completo**. Os vídeos são reproduzidos diretamente via BitTorrent streaming.

**Como usar:**
1. Clique no ícone "GoStream" na área de trabalho
2. Adicione um magnet link
3. Aguarde carregar a metadata (5-30 segundos)
4. Clique no torrent para ver os arquivos disponíveis
5. Clique em "Reproduzir" no arquivo de vídeo desejado

## 📚 Tecnologias

**Backend:**
- FastAPI
- WebSockets
- Uvicorn

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Lucide Icons
- Axios

## 🎯 Funcionalidades

### Gerenciador de Torrents
- ✅ Listar todos os torrents
- ✅ Adicionar novos torrents via magnet link
- ✅ Pausar/retomar torrents
- ✅ Remover torrents
- ✅ Visualizar progresso em tempo real
- ✅ Suporte multi-instância

### GoStream - Streaming de Torrents
- ✅ Adicionar torrents via magnet link
- ✅ Visualizar arquivos de vídeo disponíveis
- ✅ Reproduzir vídeos diretamente (streaming)
- ✅ Ativar Priority Mode para streaming otimizado
- ✅ Estatísticas de cache em tempo real
- ✅ Suporte a múltiplos formatos (MKV, MP4, AVI, MOV)

### Biblioteca Jellyfin
- ✅ Visualizar itens recentes
- ✅ Informações detalhadas de mídia
- ✅ Filtros por tipo

### Containers Docker
- ✅ Listar containers
- ✅ Iniciar/parar containers
- ✅ Visualizar status e portas

### Monitor do Sistema
- ✅ Status de conexão dos serviços
- ✅ Estatísticas de armazenamento
- ✅ Informações de instâncias

## 🔮 Próximas Funcionalidades

- [ ] Busca de torrents integrada (YTS, Rede Torrent)
- [ ] Gráficos de velocidade e uso
- [ ] Notificações push
- [ ] Temas personalizáveis
- [ ] Autenticação de usuários
- [ ] Mobile app (PWA)
