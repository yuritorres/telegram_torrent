# Changelog

## v0.2.0.2 - 2025-05-19

### fix

- Corrigido erro 400 Bad Request no comando /jfhelp, melhorando o tratamento de caracteres especiais em mensagens HTML
- Implementado sistema de fallback para envio de mensagens sem formatação quando ocorrem erros de formatação HTML
- Adicionada validação de tags HTML para evitar erros de formatação nas mensagens do Telegram
- Limitado o tamanho das mensagens para evitar erros de requisição

## v0.2.0.1 - 2025-05-19

### fix

- Melhorado o tratamento de erros nos comandos Jellyfin para evitar mensagens de erro repetidas
- Adicionado timeout nas requisições para o servidor Jellyfin
- Implementado tratamento de exceções mais robusto na API do Jellyfin
- Corrigido o problema específico com o comando /jfinfo

## v0.2.0.0 - 2025-05-19

### feat

- Melhoria significativa na integração com Jellyfin/Emby: expansão da API com novos métodos para obter informações do sistema, detalhes de itens, sessões ativas e conteúdo recentemente adicionado.
- Novos comandos Telegram para Jellyfin: `/jfhelp`, `/jfrecent`, `/jfinfo`, `/jfitem`, `/jfsessions`.
- Melhor formatação das respostas do Jellyfin no Telegram, incluindo detalhes como ano, duração, gêneros e avaliações.
- Tratamento automático de URLs do Jellyfin/Emby, garantindo compatibilidade com ambos os sistemas.

## v0.1.6.3 - 2025-05-19

### feat

- O comando `/qespaco` agora é compatível com todas as versões do qBittorrent: tenta obter o espaço total, usado e livre usando a API `/api/v2/app/drive_info` (quando disponível) e, caso não exista, faz fallback para `/api/v2/sync/maindata`, mostrando ao menos o espaço livre e, se possível, também o total/usado. Isso garante que o comando sempre informe o espaço disponível no servidor do qBittorrent, independentemente da versão.

## v0.1.6.2 - 2025-05-19

### fix

- Corrige a exibição do espaço em disco no comando `/qespaco`. Agora, o bot obtém o caminho de salvamento diretamente do qBittorrent e utiliza `shutil.disk_usage` para mostrar os valores corretos de espaço total, usado e livre, resolvendo a inconsistência anterior onde o espaço usado podia aparecer maior que o total.

## v0.1.6.1 - 2025-05-19

### feat

- Atualização do comando `/qespaco` para utilizar a API do qBittorrent, fornecendo informações detalhadas sobre o espaço em disco, incluindo total, usado e livre.

## v0.1.6.0 - 2025-05-19

### feat

- Integração com o Jellyfin: adiciona os módulos jellyfin_api.py e jellyfin_telegram.py para gerenciamento de mídia e notificações via Telegram.

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