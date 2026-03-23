# 🚀 TorrentOS - Guia Rápido de Instalação

Interface web moderna com aparência de sistema operacional para gerenciar torrents, Jellyfin e Docker.

## 📋 Pré-requisitos

- Python 3.9+
- Node.js 18+
- qBittorrent rodando
- (Opcional) Jellyfin
- (Opcional) Docker

## ⚡ Instalação Rápida

### Opção 1: Desenvolvimento Local

#### 1. Backend (Terminal 1)

```bash
cd web/backend
pip install -r requirements.txt
python main.py
```

Backend disponível em: `http://localhost:8000`

#### 2. Frontend (Terminal 2)

```bash
cd web/frontend
npm install
npm run dev
```

Frontend disponível em: `http://localhost:3001`

### Opção 2: Docker (Recomendado)

```bash
cd web
docker-compose -f docker-compose.web.yml up -d
```

Acesse: `http://localhost:3001`

## 🎯 Uso

1. Abra `http://localhost:3001` no navegador
2. Clique nos ícones da área de trabalho:
   - **Gerenciador de Torrents**: Adicionar e gerenciar downloads
   - **Biblioteca Jellyfin**: Visualizar mídia recente
   - **Containers Docker**: Controlar containers
   - **Monitor do Sistema**: Status geral

3. Arraste janelas, maximize/minimize como um OS real!

## 🔧 Configuração

O sistema usa o mesmo arquivo `.env` da aplicação principal. Certifique-se de que está configurado corretamente.

## 📱 Funcionalidades

### ✅ Gerenciador de Torrents
- Adicionar torrents via magnet link
- Pausar/retomar downloads
- Remover torrents
- Visualizar progresso em tempo real
- Suporte multi-instância qBittorrent

### ✅ Biblioteca Jellyfin
- Itens recentes adicionados
- Informações detalhadas (ano, gênero, sinopse)
- Ícones por tipo de mídia

### ✅ Containers Docker
- Listar todos os containers
- Iniciar/parar containers
- Visualizar status e portas

### ✅ Monitor do Sistema
- Status de conexão (qBittorrent, Jellyfin, Docker)
- Estatísticas de armazenamento
- Informações de instâncias

## 🐛 Solução de Problemas

### Backend não conecta ao qBittorrent
- Verifique se o qBittorrent está rodando
- Confirme as credenciais no `.env`
- Teste: `curl http://localhost:8080`

### Frontend não carrega
- Limpe cache: `cd web/frontend && rm -rf node_modules && npm install`
- Verifique se a porta 3001 está livre

### WebSocket não conecta
- Verifique se o backend está rodando
- Confirme que não há firewall bloqueando

## 🎨 Personalização

### Mudar Porta do Backend
Edite `web/backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=SUAPORTA)
```

### Mudar Porta do Frontend
Edite `web/frontend/vite.config.js`:
```javascript
server: {
  port: SUAPORTA
}
```

## 📚 Estrutura do Projeto

```
web/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── requirements.txt     # Dependências Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── context/         # Context API
│   │   └── App.jsx          # App principal
│   ├── package.json
│   └── Dockerfile
└── docker-compose.web.yml   # Orquestração Docker
```

## 🔮 Próximas Funcionalidades

- [ ] Busca integrada de torrents (YTS, Rede)
- [ ] Gráficos de velocidade
- [ ] Notificações push
- [ ] Temas personalizáveis
- [ ] Autenticação
- [ ] PWA (Progressive Web App)

## 💡 Dicas

- Use `Ctrl+R` para atualizar dados
- Arraste janelas pela barra de título
- Maximize janelas para melhor visualização
- WebSocket atualiza torrents automaticamente a cada 5s

## 🆘 Suporte

Problemas? Abra uma issue no GitHub ou consulte a documentação completa em `web/README.md`
