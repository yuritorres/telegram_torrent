# Changelog - Telegram Torrent Bot

## v0.0.1.4-alpha - 2025-01-15

### feat
- Implementado comando `/youtube` para download de vídeos do YouTube
- Adicionado botão "🎥 YouTube" no teclado personalizado
- Detecção automática de URLs do YouTube em mensagens
- Download assíncrono com monitoramento de progresso
- Envio automático de vídeos para o Telegram após download
- Suporte a informações detalhadas do vídeo (título, canal, duração, visualizações)
- Limite de 50MB para compatibilidade com Telegram
- Sistema de timeout de 10 minutos por download
- Remoção automática de arquivos após envio (configurável)

### docs
- Criado README_YOUTUBE.md com documentação completa
- Adicionado requirements_youtube.txt com dependências necessárias
- Atualizada mensagem de boas-vindas com comando `/youtube`

### refactor
- Criado módulo youtube_downloader.py baseado em up_youtube_downloader.py
- Integração completa com sistema de comandos existente
- Adicionadas funções process_youtube_download e send_video_to_telegram
- Melhorado tratamento de erros para downloads do YouTube

## v0.0.1.3-alpha - 2024-12-30

### docs
- Atualizado README.md com informações precisas sobre o comando `/recentes`
- Corrigida duplicação na seção de comandos rápidos
- Atualizada estrutura modular para refletir o arquivo `jellyfin_consolidated.py`
- Melhorada documentação dos comandos do Jellyfin com detalhes específicos
- Diferenciação clara entre `/recent` e `/recentes`

## v0.0.1.2.fix3-alpha - 2025-05-25

### Melhorias
- Corrigido o comando `/recentes` para exibir itens recentes do Jellyfin
- Melhor tratamento de erros ao buscar itens recentes
- Adicionada verificação de inicialização do bot Jellyfin

### Corrigido
- Comando `/recentes` não estava sendo processado corretamente
- Falha na inicialização do polling do Telegram para comandos do Jellyfin

## v0.0.1.2.fix2-alpha - 2025-05-25

### Melhorias
- Refatoração completa do sistema de processamento de mensagens
- Centralização do mapeamento de comandos do teclado
- Melhor tratamento de erros e validações
- Remoção de código duplicado e otimizações gerais

### Corrigido
- Dupla verificação de autorização removida
- Mensagens de erro mais claras e informativas
- Melhor tratamento de exceções em operações assíncronas

### Segurança
- Melhor validação de entradas de usuário
- Proteção contra injeção de comandos
- Verificação de permissões mais robusta

## v0.0.1.2.fix1-alpha - 2025-05-25

### feat
- Adicionado teclado personalizado com botões de acesso rápido
- Novos atalhos para comandos frequentes
- Melhorias na experiência do usuário
- Integração do teclado com todos os comandos existentes

### refactor
- Otimização do código para melhor desempenho
- Melhor tratamento de erros para comandos do teclado
- Ajustes na formatação das mensagens

## v0.0.1.2-alpha - 2025-05-25

### feat
- Reintegração completa com Jellyfin
- Novos comandos: `/recent`, `/libraries`, `/status`
- Exibição de itens recentes em mensagens individuais com botões inline
- Suporte a Markdown nas mensagens do Jellyfin
- Botões de ação rápida nos itens recentes (Assistir/Não Assistir/Detalhes)
- Sistema de expiração automática para mensagens de status
- Comandos de status do qBittorrent com mensagens auto-expiráveis

### refactor
- Melhorada a estrutura do código para suportar múltiplos serviços
- Sistema de autenticação unificado
- Tratamento de erros aprimorado
- Melhor gerenciamento de mensagens e callbacks do Telegram

## v0.0.1.1-alpha - 2025-05-24

## Sobre a Numeração de Versões

A partir da versão v0.0.1.0-alpha de 24/05/2025, adotamos o versionamento semântico (SemVer) para melhor controle das alterações.

### Legado (Histórico de Desenvolvimento)

As versões anteriores (v0.1.x até v0.3.x) representam o histórico de desenvolvimento interno. A numeração foi reiniciada para refletir melhor o ciclo de lançamentos oficiais.

---

## Próximas Versões (a partir de v0.0.1-alpha)

*Nota: A versão alpha está em desenvolvimento ativo. Consulte as notas de versão para mudanças recentes.*

## v0.0.1.1-alpha - 2025-05-24

### feat
- O menu do bot Telegram agora exibe apenas comandos reais da aplicação: `/start`, `/qespaco`, `/qtorrents`.
- Adicionada função utilitária `set_bot_commands()` para registro automático dos comandos do menu.
- O menu é atualizado automaticamente ao iniciar o bot.

## v0.0.1.0-alpha - 2025-05-24

### refactor

- Removida a integração com Jellyfin e o código relacionado foi movido para um diretório de arquivo
- Melhorada a estrutura do código para focar exclusivamente na funcionalidade do qBittorrent
- Adicionadas anotações de tipo e documentação detalhada das funções
- Melhorado o tratamento de erros e mensagens de log

### feat

- Adicionada formatação aprimorada para listas de torrents, mostrando o progresso de downloads ativos
- Melhorada a mensagem de boas-vindas com comandos disponíveis
- Adicionado suporte a Markdown além de HTML nas mensagens
- Implementado timeout em todas as requisições HTTP

## v0.2.0.4 - 2025-05-19

### docs
- Atualizada a documentação dos comandos do Jellyfin no README.md
- Adicionada descrição detalhada para cada comando (/jflib, /jfsearch, /jfrecent, /jfinfo, /jfitem, /jfsessions)
- Incluídas informações sobre funcionalidades e requisitos de cada comando
- Reorganizada a seção de comandos do Jellyfin para melhor legibilidade

## v0.2.0.3 - 2025-05-19
### docs
- Documentação completa dos comandos do Jellyfin no README.md
- Adicionada descrição detalhada de cada comando com exemplos de uso
- Incluídas informações sobre permissões e limitações do sistema

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
