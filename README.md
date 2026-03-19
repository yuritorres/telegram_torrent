# Telegram Torrent Bot

Um bot para Telegram que interage com o qBittorrent para adicionar torrents via links magnet, fornecer atualizações de status, sincronizar automaticamente com Jellyfin e oferecer estatísticas detalhadas de uso.

## Estrutura Modular (Feature-based Package Structure)

O projeto foi refatorado para uma estrutura de pacotes baseada em features, facilitando manutenção, escalabilidade e organização:

```
src/
├── core/              # Configurações e utilitários centrais
│   ├── config.py      # Carregamento centralizado de variáveis de ambiente
│   ├── logging_config.py  # Configuração de logging
│   └── exceptions.py  # Exceções customizadas
├── integrations/      # Integrações com serviços externos
│   ├── qbittorrent/   # Cliente e monitor do qBittorrent
│   ├── jellyfin/      # Cliente, formatador, manager e notifier do Jellyfin
│   ├── telegram/      # Cliente, teclados, utils e handlers do Telegram
│   ├── whatsapp/      # Cliente WAHA, utils e webhook
│   └── youtube/       # Downloader e utils do YouTube
├── services/          # Serviços de negócio
│   ├── sync_service.py        # Sincronização qBittorrent ↔ Jellyfin
│   ├── statistics_service.py  # Estatísticas e histórico
│   └── ytsbr_service.py       # Integração YTS Brasil
├── commands/          # Handlers de comandos
│   ├── telegram_commands.py   # Comandos avançados do Telegram
│   ├── ytsbr_commands.py      # Comandos YTSBR
│   └── whatsapp_commands.py   # Comandos WhatsApp
└── utils/             # Utilitários compartilhados
    └── formatters.py  # Formatação de bytes, duração, etc.
```

**Arquivos legados** (root): Mantidos como shims de compatibilidade, re-exportando de `src/` para garantir backward compatibility.

**Ponto de entrada**: `main.py` - orquestra a inicialização de todos os serviços e integrações.

## Configuração

### Instalação Direta

1. Clone este repositório.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com as variáveis de ambiente necessárias:
   ```env
   # qBittorrent
   QB_URL=http://localhost:8080
   QB_USER=admin
   QB_PASS=sua_senha
   INTERVALO=30
   QBITTORRENT_STORAGE_PATH=/

   # Telegram
   TELEGRAM_BOT_TOKEN=seu_token_do_bot
   TELEGRAM_CHAT_ID=seu_chat_id
   AUTHORIZED_USERS=123456789,987654321
   EXPIRAR_MSG=30

   # Jellyfin
   JELLYFIN_URL=http://localhost:8096
   JELLYFIN_USERNAME=seu_usuario
   JELLYFIN_PASSWORD=sua_senha
   JELLYFIN_API_KEY=sua_api_key
   JELLYFIN_NOTIFICATIONS_ENABLED=True
   JELLYFIN_NOTIFICATION_INTERVAL=1800

   # WhatsApp (WAHA)
   WAHA_URL=http://localhost:3000
   WAHA_API_KEY=local-dev-key-123
   WAHA_SESSION=default
   AUTHORIZED_WHATSAPP_NUMBERS=5511999999999
   WAHA_DASHBOARD_USERNAME=admin
   WAHA_DASHBOARD_PASSWORD=admin123
   WAHA_SWAGGER_USERNAME=admin
   WAHA_SWAGGER_PASSWORD=swagger123

   # YouTube
   YOUTUBE_DOWNLOAD_DIR=downloads
   REMOVE_AFTER_SEND=False

   # Sincronização
   SYNC_INTERVAL=30
   AUTO_SCAN_JELLYFIN=True
   ```
4. Obtenha seu `TG_CHAT_ID` enviando uma mensagem para o seu bot e acessando `https://api.telegram.org/botSEU_TOKEN/getUpdates`.

### Instalação com Docker

O projeto também pode ser executado em contêineres Docker, facilitando a implantação e isolando as dependências.

#### Criando o Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto com o seguinte conteúdo:

```dockerfile
# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo de requisitos e instale as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação para o contêiner
COPY . .

# O arquivo .env não deve ser copiado diretamente para a imagem por questões de segurança.
# Considere montar o arquivo .env como um volume ou passá-lo como variáveis de ambiente ao executar o contêiner.

# Comando para executar o script principal quando o contêiner iniciar
CMD ["python", "main.py"]
```

---

## Instalação e Execução sem Docker (Ambiente Virtual Python)

Se você está em um sistema Linux (Armbian, Debian, Ubuntu, Orange Pi, Raspberry Pi, etc) e não quer ou não pode usar Docker, siga estes passos para rodar o bot em um ambiente isolado:

### 1. Instale Python 3, venv e pip (se necessário)
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```

### 2. Crie um ambiente virtual na pasta do projeto
```bash
cd /caminho/para/telegram_torrent
python3 -m venv venv
```

### 3. Ative o ambiente virtual
```bash
source venv/bin/activate
```

### 4. Instale as dependências do projeto
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_youtube.txt
```

### 5. Configure o arquivo `.env`
Crie ou edite o arquivo `.env` com seus dados do Telegram e qBittorrent.

### 6. Execute o bot
```bash
python main.py
```

### 7. (Opcional) Execute em background
```bash
nohup python main.py &
```

Caso desejar verificar o log de todos os nohup utilizados (em execução e finalizados), utilize o comando:

ps aux | grep "nome_do_arquivo.py"

Se você quiser parar ou matar o processo em execução, use o killcomando seguido do ID do processo:

kill 2565

### Observações
- Sempre que quiser rodar o bot, ative o ambiente virtual:
  ```bash
  cd /caminho/para/telegram_torrent
  source venv/bin/activate
  python main.py
  ```
- Para sair do ambiente virtual, use `deactivate`.
- O ambiente virtual mantém as dependências isoladas do sistema.

---

#### Criando o docker-compose.yml

Copie o arquivo `docker-compose.yml` na raiz do projeto:

```

#### Utilizando Docker

Depois de criar os arquivos, execute os seguintes comandos para construir e iniciar os contêineres:

1. Construir e iniciar os contêineres em segundo plano:
   ```bash
   docker compose up -d
   ```

2. Verificar os logs da aplicação:
   ```bash
   docker compose logs -f telegram-torrent
   ```

3. Parar os contêineres:
   ```bash
   docker compose down
   ```

4. Para reconstruir a imagem após alterações no código:
   ```bash
   docker compose build telegram-torrent
   ou
   docker compose build --no-cache telegram-torrent
   docker compose up -d
   
   ```

> **Nota**: Certifique-se de que o arquivo `.env` esteja configurado corretamente antes de iniciar os contêineres.

## Uso

Execute o script principal:

```bash
python main.py
```

O bot irá iniciar, conectar-se ao qBittorrent e começar a processar mensagens do Telegram e enviar atualizações de status.

## Interface do Usuário

### Teclado Personalizado

O bot inclui um teclado personalizado que aparece na parte inferior do chat, fornecendo acesso rápido aos comandos mais usados. O teclado é ativado automaticamente após o comando `/start`.

#### Comandos Rápidos:
- 📊 **Status do Servidor**: Verifica o status do servidor Jellyfin
- 📦 **Listar Torrents**: Mostra a lista de torrents ativos
- 💾 **Espaço em Disco**: Exibe o espaço em disco disponível
- 🎬 **Itens Recentes**: Lista os itens adicionados recentemente ao Jellyfin (comando: `/recent`)
- 🎭 **Recentes Detalhado**: Exibe informações detalhadas dos itens recentes (comando: `/recentes`)
- 📚 **Bibliotecas**: Mostra as bibliotecas disponíveis no Jellyfin
- ❓ **Ajuda**: Exibe a mensagem de ajuda com todos os comandos

## Comandos Disponíveis

### Comandos Gerais

- `/start`: Inicia a interação com o bot e exibe mensagem de boas-vindas com o teclado personalizado
- `/help` ou clique em **Ajuda**: Exibe a lista completa de comandos disponíveis e suas descrições

### Comandos do qBittorrent

#### Gerenciamento de Torrents
- `/qtorrents`: Lista todos os torrents ativos, pausados, finalizados e parados (requer autorização).
  - **Interface Aprimorada**: Formatação moderna com contadores e separadores visuais
  - **Informações Detalhadas**: Exibe nome (limitado a 50 caracteres), progresso, tamanho, velocidade de download/upload
  - **Categorização Inteligente**: 
    - **Downloads Ativos** (até 5 exibidos)
    - **Pausados** (até 3 exibidos)
    - **Finalizados/Seeding** (até 3 exibidos)
    - **Com Erro** (todos exibidos)
  - **Botões Interativos**:
    - **Atualizar Lista**: Atualiza a lista de torrents em tempo real
    - **Pausar Todos**: Pausa todos os torrents ativos de uma vez
    - **Retomar Todos**: Retoma todos os torrents pausados simultaneamente
    - **Detalhes**: Exibe ajuda contextual sobre o gerenciador
  - **Feedback Instantâneo**: Confirmação imediata de ações executadas
  
- **Links Magnet**: Envie qualquer link magnet válido para iniciar o download (requer autorização).
  - Formato: `magnet:?xt=urn:btih:...`
  - O bot confirmará o recebimento e iniciará o download automaticamente.

#### Monitoramento do Sistema
- `/qespaco`: Mostra o espaço em disco disponível no servidor do qBittorrent.
  - Em versões recentes: Exibe Total, Usado e Livre (via API `/api/v2/app/drive_info`).
  - Em versões antigas: Fallback para `/api/v2/sync/maindata` mostrando espaço livre.

### Comandos do Jellyfin

#### Gerenciamento de Conteúdo
- `/recentes`: Lista os itens recentemente adicionados ao Jellyfin com informações detalhadas
  - Exibe até 8 itens recentes com informações completas
  - Mostra título, ano, tipo de mídia, gêneros e avaliação
  - Inclui sinopse resumida (até 150 caracteres)
  - Data de adição ao servidor
  - Link direto para visualização no Jellyfin
  - Formatação em Markdown para melhor legibilidade

- `/recent`: Lista os itens mais recentes adicionados ao Jellyfin (versão simplificada)
  - Exibe informações básicas dos itens recentes
  - Formato mais compacto e rápido
  
- `/libraries`: Lista todas as bibliotecas disponíveis no servidor Jellyfin
  - Mostra o nome e tipo de cada biblioteca
  - Útil para verificar acessos e organizações de mídia
  
- `/status`: Exibe o status atual do servidor Jellyfin
  - Mostra informações de conexão
  - Exibe contagem de bibliotecas
  - Último item adicionado
  - Status da conexão

#### Recursos em Desenvolvimento
- `Em breve`: Busca avançada na biblioteca
- `Planejado`: Controle de permissões
- `Futuro`: Notificações automáticas de novos conteúdos

> ℹ️ **Acompanhe nosso [ROADMAP.md](ROADMAP.md) para atualizações sobre o cronograma de lançamento e recursos planejados.**

### Comandos v0.0.1.7-alpha - Sincronização e Estatísticas

#### Sincronização qBittorrent ↔ Jellyfin
- `/sync`: Sincronização manual entre qBittorrent e Jellyfin
  - Dispara verificação imediata de torrents concluídos
  - Atualiza biblioteca Jellyfin automaticamente
  - Envia notificação quando conteúdo está disponível
  - **Exemplo**: `/sync`

- `/sync_status`: Exibe status atual da sincronização
  - Estado do sincronizador (Ativo/Inativo)
  - Contador de torrents concluídos processados
  - Tamanho da fila de processamento
  - Configurações de auto-scan e intervalo
  - **Exemplo**: `/sync_status`

#### Estatísticas e Monitoramento
- `/stats [horas]`: Exibe estatísticas de uso de banda
  - Uso de banda por período (padrão: 24 horas)
  - Download e upload totais no período
  - Média de velocidade
  - **Exemplos**: 
    - `/stats` (últimas 24 horas)
    - `/stats 48` (últimas 48 horas)
    - `/stats 12` (últimas 12 horas)

- `/history [dias]`: Exibe histórico de downloads
  - Lista de torrents concluídos recentemente
  - Informações: nome, tamanho, data de conclusão
  - Período configurável (padrão: 7 dias)
  - **Exemplos**:
    - `/history` (últimos 7 dias)
    - `/history 14` (últimos 14 dias)
    - `/history 3` (últimos 3 dias)

#### Gerenciamento Avançado de Torrents
- `/priority [hash] [prioridade]`: Altera prioridade de downloads
  - **Prioridades disponíveis**:
    - `top` - Move para o topo da fila
    - `bottom` - Move para o final da fila
    - `increase` - Aumenta a prioridade
    - `decrease` - Diminui a prioridade
  - **Exemplos**:
    - `/priority abc123def456 top`
    - `/priority abc123def456 increase`
  - **Dica**: Use `/qtorrents` para ver os hashes dos torrents

- `/remove [hash] [delete]`: Remove torrents com opção de deletar arquivos
  - Remove apenas o torrent (mantém arquivos)
  - Remove torrent e arquivos (com `delete`)
  - **Exemplos**:
    - `/remove abc123def456` (remove apenas torrent)
    - `/remove abc123def456 delete` (remove torrent e arquivos)
  - **⚠️ Atenção**: A remoção de arquivos é permanente!
  - **Dica**: Use `/qtorrents` para ver os hashes dos torrents

#### Funcionalidades Automáticas (v0.0.1.7-alpha)
- **Detecção Automática**: Verifica periodicamente torrents concluídos
- **Atualização Jellyfin**: Scan automático da biblioteca quando downloads terminam
- **Notificações**: Avisa quando conteúdo está disponível no Jellyfin
- **Registro de Estatísticas**: Coleta dados de banda a cada minuto
- **Persistência**: Histórico mantido em arquivo JSON

#### Configurações Adicionais
Adicione ao seu arquivo `.env` as novas configurações:

```env
# CONFIGURAÇÕES DE SINCRONIZAÇÃO (v0.0.1.7-alpha)
# Intervalo em segundos para verificar torrents concluídos (padrão: 30)
SYNC_INTERVAL=30
# Habilita/desabilita atualização automática da biblioteca Jellyfin (True/False)
AUTO_SCAN_JELLYFIN=True
```

### Comandos do YouTube

- `/youtube`: Baixar vídeos do YouTube e enviar para o Telegram
  - **Detecção Automática**: Envie qualquer URL do YouTube diretamente no chat
  - **Formatos Suportados**:
    - `youtube.com/watch?v=...`
    - `youtu.be/...`
    - `youtube.com/shorts/...`
  - **Informações do Vídeo**: Exibe título, canal, duração, visualizações e data de publicação
  - **Download Assíncrono**: Monitoramento de progresso em tempo real
  - **Envio Automático**: Vídeo enviado automaticamente após conclusão do download
  - **Limitações**:
    - Tamanho máximo: 50MB (limite do Telegram)
    - Apenas vídeos públicos
    - Timeout de 10 minutos por download
  - **Exemplo**: `/youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ`

### Comandos do YTS Brasil

#### Busca de Filmes
- `/ytsbr [termo]`: Busca filmes no YTS Brasil
  - Sem termo: Exibe filmes populares
  - Com termo: Busca por título específico
  - **Exemplo**: `/ytsbr Matrix`

- `/ytsbr_generos`: Lista todos os gêneros de filmes disponíveis
- `/ytsbr_genero [gênero]`: Busca filmes por gênero específico
  - **Exemplo**: `/ytsbr_genero acao`

#### Busca de Séries
- `/ytsbr_series [termo]`: Busca séries no YTS Brasil
  - Sem termo: Exibe séries populares
  - Com termo: Busca por título específico
  - **Exemplo**: `/ytsbr_series Breaking Bad`

- `/ytsbr_series_generos`: Lista todos os gêneros de séries disponíveis
- `/ytsbr_series_genero [gênero]`: Busca séries por gênero específico
  - **Exemplo**: `/ytsbr_series_genero drama`

#### Busca de Animes
- `/ytsbr_anime [termo]`: Busca animes no YTS Brasil
  - Sem termo: Exibe animes populares
  - Com termo: Busca por título específico
  - **Exemplo**: `/ytsbr_anime Naruto`

- `/ytsbr_anime_generos`: Lista todos os gêneros de animes disponíveis
- `/ytsbr_anime_genero [gênero]`: Busca animes por gênero específico
  - **Exemplo**: `/ytsbr_anime_genero acao`

#### Download de Torrents
- `/ytsbr_baixar [número]`: Baixa o torrent selecionado da última busca
  - **Exemplo**: `/ytsbr_baixar 1`
  - O número corresponde à posição do item na lista de resultados
  - Sistema de cache mantém os últimos resultados de busca por usuário

#### Funcionalidades YTS Brasil
- **Seleção Interativa**: Resultados numerados para fácil seleção
- **Informações Detalhadas**: Título, ano, qualidade, tamanho, gêneros
- **Cache Inteligente**: Mantém resultados de busca para download rápido
- **Integração com qBittorrent**: Download automático após seleção

### Notificações Automáticas

O bot enviará automaticamente notificações para:
- Conclusão de downloads de torrents
- Erros durante o download
- Novos conteúdos adicionados ao Jellyfin
- Alertas de espaço em disco baixo
- Atualizações de status do servidor Jellyfin
- Sessões iniciadas ou finalizadas no Jellyfin

## Configuração do Jellyfin

Para habilitar os comandos do Jellyfin, adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# Configurações do Jellyfin
JELLYFIN_URL=http://seu-servidor-jellyfin:8096
JELLYFIN_USERNAME=seu_usuario
JELLYFIN_PASSWORD=sua_senha
```

Certifique-se de que o usuário tenha permissões adequadas no servidor Jellyfin para acessar as bibliotecas e informações do sistema.

## Versionamento

Este projeto segue o Versionamento Semântico (SemVer) e utiliza commits padronizados em Português do Brasil. O changelog é mantido no arquivo `versao.md`.

## Changelog

Consulte o arquivo `versao.md` para o histórico de mudanças.

## Links
https://www.digitalocean.com/community/tutorials/nohup-command-in-linux

## Disclaimer

Este projeto é desenvolvido apenas para fins educacionais e de uso pessoal. Não incentivamos ou apoiamos qualquer forma de pirataria ou uso ilegal. Os usuários são responsáveis por garantir que suas ações estejam em conformidade com todas as leis de direitos autorais e propriedade intelectual aplicáveis.