# Telegram Torrent Bot

Um bot para Telegram que interage com o qBittorrent para adicionar torrents via links magnet e fornecer atualizações de status.

## Estrutura Modular

O projeto foi modularizado para facilitar a manutenção e a extensão:
- `main.py`: ponto de entrada do bot, responsável por orquestrar as chamadas entre os módulos.
- `qbittorrent_api.py`: funções para autenticação e interação com o qBittorrent.
- `telegram_utils.py`: utilitários para envio e processamento de mensagens no Telegram.
- `torrent_monitor.py`: monitoramento de torrents e notificações automáticas de status/conclusão.
- `jellyfin_api.py`: integração com o Jellyfin para gerenciamento de mídia.
- `jellyfin_telegram.py`: comandos e notificações do Jellyfin via Telegram.

## Configuração

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

## Uso

Execute o script principal:

```bash
python main.py
```

O bot irá iniciar, conectar-se ao qBittorrent e começar a processar mensagens do Telegram e enviar atualizações de status.

## Comandos Disponíveis

### Comandos Gerais

- `/start`: Inicia a interação com o bot e exibe mensagem de boas-vindas.
- `/help`: Exibe a lista completa de comandos disponíveis e suas descrições.

### Comandos do qBittorrent

#### Gerenciamento de Torrents
- `/qtorrents`: Lista todos os torrents ativos, pausados, finalizados e parados (requer autorização).
  - Exibe nome, progresso, velocidade e status de cada torrent.
  - Permite visualizar detalhes específicos de cada download.
- **Links Magnet**: Envie qualquer link magnet válido para iniciar o download (requer autorização).
  - Formato: `magnet:?xt=urn:btih:...`
  - O bot confirmará o recebimento e iniciará o download automaticamente.

#### Monitoramento do Sistema
- `/qespaco`: Mostra o espaço em disco disponível no servidor do qBittorrent.
  - Em versões recentes: Exibe Total, Usado e Livre (via API `/api/v2/app/drive_info`).
  - Em versões antigas: Fallback para `/api/v2/sync/maindata` mostrando espaço livre.

### Comandos do Jellyfin

O bot oferece integração completa com o Jellyfin para gerenciamento de mídia através do módulo `jellyfin_telegram.py`.

#### Gerenciamento de Mídia
- `/jflib`: Lista todas as bibliotecas disponíveis no servidor Jellyfin.
  - Exibe nome e tipo de cada biblioteca
  - Mostra o número total de itens em cada biblioteca
  - Indica o status de sincronização de cada biblioteca

- `/jfsearch <termo>`: Pesquisa por conteúdo específico nas bibliotecas.
  - Busca por títulos, atores, diretores e gêneros
  - Suporta pesquisa parcial de termos
  - Exibe resultados com detalhes básicos

- `/jfrecent`: Mostra as adições mais recentes ao servidor.
  - Lista os últimos conteúdos adicionados
  - Inclui data de adição e detalhes do conteúdo
  - Organiza por data de adição

- `/jfinfo`: Exibe informações detalhadas sobre o servidor.
  - Versão do servidor
  - Status de operação
  - Estatísticas de uso
  - Informações de sistema

- `/jfitem <id>`: Mostra detalhes completos de um item específico.
  - Título e ano
  - Duração e qualidade
  - Elenco e equipe técnica
  - Sinopse e classificação
  - Informações técnicas do arquivo

- `/jfsessions`: Lista todas as sessões ativas no servidor (requer privilégios de administrador).
  - Usuários conectados
  - Conteúdo em reprodução
  - Dispositivo e qualidade de reprodução
  - Tempo de conexão

- `/jfhelp`: Exibe a lista completa de comandos disponíveis com suas descrições detalhadas.

#### Notificações e Status
- `/jstatus`: Verifica o status atual do servidor Jellyfin.
- `/jnotif [on/off]`: Ativa ou desativa notificações de novos conteúdos.

### Notificações Automáticas

O bot enviará automaticamente notificações para:
- Conclusão de downloads de torrents
- Erros durante o download
- Novos conteúdos adicionados ao Jellyfin
- Alertas de espaço em disco baixo
- Atualizações de status do servidor Jellyfin
- Sessões iniciadas ou finalizadas no Jellyfin

## Versionamento

Este projeto segue o Versionamento Semântico (SemVer) e utiliza commits padronizados em Português do Brasil. O changelog é mantido no arquivo `versao.md`.

## Changelog

Consulte o arquivo `versao.md` para o histórico de mudanças.