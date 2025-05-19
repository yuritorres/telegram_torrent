# Changelog

## v1.5.2 - 2025-05-19

### fix

- Melhora a tolerância a falhas na conexão com o qBittorrent: caso não seja possível conectar, o bot permanece funcional e informa o usuário, sem interromper outras funcionalidades.

## v1.5.1 - 2025-05-19

### fix

- Corrige concorrência e garante resposta imediata ao comando /start.
- Agora o processamento de mensagens e o monitoramento de torrents ocorrem em threads separadas, evitando bloqueios e melhorando a experiência do usuário.

## v1.5.0 - 2025-05-18

### feat

- Modulariza o projeto, separando funcionalidades em arquivos distintos para melhor organização e manutenção.
- Cria os módulos `telegram_utils.py` (utilitários para Telegram) e `torrent_monitor.py` (monitoramento e notificações de torrents).
- Simplifica o `main.py`, tornando-o responsável apenas pela orquestração dos módulos.

## v1.4.2 - 2025-05-18

### fix

- Corrige problema de notificação de download concluído não sendo exibida.

## v1.4.1 - 2025-05-18

### fix

- Corrige notificação duplicada de download concluído.

## v1.4.0 - 2025-05-18

### feat

- Adiciona notificação no Telegram quando um download de torrent é concluído.

## v1.3.1 - 2025-05-18

### fix

- Corrige erro de sintaxe em f-string na mensagem de confirmação de magnet.

## v1.3.0 - 2025-05-18

### feat

- Exibe o nome do torrent na mensagem de confirmação ao adicionar um link magnet.

## v1.2.0 - 2025-05-18

### feat

- Melhora extração e validação de links magnet.

## v1.1.0 - 2025-05-18

### feat

- Melhora extração e validação de links magnet.