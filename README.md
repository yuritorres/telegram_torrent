# Telegram Torrent Bot

Um bot para Telegram que interage com o qBittorrent para adicionar torrents via links magnet e fornecer atualizações de status.

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
   TG_TOKEN=seu_token_do_bot_telegram
   TG_CHAT_ID=seu_chat_id_do_telegram # O ID do chat onde o bot enviará mensagens
   INTERVALO=60 # Intervalo em segundos entre as verificações de status (opcional, padrão é 60)
   ```
4. Obtenha seu `TG_CHAT_ID` enviando uma mensagem para o seu bot e acessando `https://api.telegram.org/botSEU_TOKEN/getUpdates`.

## Uso

Execute o script principal:

```bash
python main.py
```

O bot irá iniciar, conectar-se ao qBittorrent e começar a processar mensagens do Telegram e enviar atualizações de status.

## Versionamento

Este projeto segue o Versionamento Semântico (SemVer) e utiliza commits padronizados em Português do Brasil. O changelog é mantido no arquivo `versao.md`.

## Changelog

Consulte o arquivo `versao.md` para o histórico de mudanças.