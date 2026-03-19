# Telegram Torrent Bot

Um bot para Telegram que interage com o qBittorrent para adicionar torrents via links magnet e fornecer atualizações de status.

## Estrutura Modular

O projeto foi modularizado para facilitar a manutenção e a extensão:
- `main.py`: ponto de entrada do bot, responsável por orquestrar as chamadas entre os módulos.
- `qbittorrent_api.py`: funções para autenticação e interação com o qBittorrent.
- `telegram_utils.py`: utilitários para envio e processamento de mensagens no Telegram.
- `torrent_monitor.py`: monitoramento de torrents e notificações automáticas de status/conclusão.
- `jellyfin_consolidated.py`: integração consolidada com o Jellyfin para gerenciamento de mídia e comandos via Telegram.

## Configuração

### Instalação Direta

1. Clone este repositório.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```env
   QB_URL=http://localhost:8080 # URL do seu qBittorrent WebUI
   QB_USER=seu_usuario
   QB_PASS=sua_senha
   TELEGRAM_BOT_TOKEN=seu_token_do_bot_telegram
   TELEGRAM_CHAT_ID=seu_chat_id_do_telegram # O ID do chat onde o bot enviará mensagens
   INTERVALO=60 # Intervalo em segundos entre as verificações de status (opcional, padrão é 60)
   AUTHORIZED_USERS=123456789,987654321 # (Opcional) IDs dos usuários autorizados a executar comandos críticos, separados por vírgula. Se não definido, qualquer usuário pode executar comandos.
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