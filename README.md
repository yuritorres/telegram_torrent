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

Agora, o comando `/qespaco` utiliza a API do qBittorrent para fornecer informações precisas sobre o espaço em disco, incluindo total, usado e livre.

## Versionamento

Este projeto segue o Versionamento Semântico (SemVer) e utiliza commits padronizados em Português do Brasil. O changelog é mantido no arquivo `versao.md`.

## Changelog

Consulte o arquivo `versao.md` para o histórico de mudanças.

- Para consultar o espaço em disco disponível, envie o comando /qespaco no chat do Telegram.