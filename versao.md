# Changelog

## v0.1.5.5 - 2025-05-19

### feat

- Adiciona a variável de ambiente AUTHORIZED_USERS: permite configurar IDs de usuários autorizados a executar comandos críticos no bot, aumentando a segurança e o controle de acesso.
- Documentação atualizada no README.md para orientar sobre o uso da nova variável.

## v0.1.5.4 - 2025-05-19

### style

- Padroniza nomes das variáveis de ambiente do Telegram: substitui TG_TOKEN por TELEGRAM_BOT_TOKEN e TG_CHAT_ID por TELEGRAM_CHAT_ID em todo o projeto, garantindo consistência e rastreabilidade.

## v0.1.5.3 - 2025-05-19

### feat

- Cria o comando /qtorrents: Exibe  torrents parados, ativos, pausados e finalizados. A listagem está mais completa e informativa, proporcionando melhor acompanhamento do status dos torrents.

## v0.1.5.2 - 2025-05-19

### fix

- Melhora a tolerância a falhas na conexão com o qBittorrent: caso não seja possível conectar, o bot permanece funcional e informa o usuário, sem interromper outras funcionalidades.

## v0.1.5.1 - 2025-05-19

### fix

- Corrige concorrência e garante resposta imediata ao comando /start.
- Agora o processamento de mensagens e o monitoramento de torrents ocorrem em threads separadas, evitando bloqueios e melhorando a experiência do usuário.

## v0.1.5.0 - 2025-05-18

### feat

- Modulariza o projeto, separando funcionalidades em arquivos distintos para melhor organização e manutenção.
- Cria os módulos `telegram_utils.py` (utilitários para Telegram) e `torrent_monitor.py` (monitoramento e notificações de torrents).
- Simplifica o `main.py`, tornando-o responsável apenas pela orquestração dos módulos.

## v0.1.4.2 - 2025-05-18

### fix

- Corrige problema de notificação de download concluído não sendo exibida.

## v0.1.4.1 - 2025-05-18

### fix

- Corrige notificação duplicada de download concluído.

## v0.1.4.0 - 2025-05-18

### feat

- Adiciona notificação no Telegram quando um download de torrent é concluído.

## v0.1.3.1 - 2025-05-18

### fix

- Corrige erro de sintaxe em f-string na mensagem de confirmação de magnet.

## v0.1.3 - 2025-05-18

### feat

- Exibe o nome do torrent na mensagem de confirmação ao adicionar um link magnet.

## v0.1.2 - 2025-05-18

### feat

- Melhora extração e validação de links magnet.

## v0.1.0 - 2025-05-18

### feat

- Melhora extração e validação de links magnet.