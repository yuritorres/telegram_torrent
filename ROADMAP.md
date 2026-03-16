# Roadmap e Planejamento de Versões

> **⚠️ Aviso Importante**  
> Este documento representa o planejamento atual do projeto, mas está sujeito a alterações. O ciclo de desenvolvimento pode ser ajustado conforme prioridades, feedback dos usuários e mudanças tecnológicas. As datas são estimativas e podem ser alteradas para garantir a qualidade do software.

---

## Versão Atual
- **v0.0.1.5-alpha** (16/03/2026)
  - **Integração WhatsApp WAHA completa**
    - Cliente API WAHA para comunicação com WhatsApp
    - Servidor Flask para recebimento de webhooks
    - Processamento de comandos WhatsApp (todos os comandos do Telegram adaptados)
    - Sistema de autorização por número de telefone
    - Suporte a mensagens de texto e formatação Markdown
    - Documentação completa da integração WhatsApp
  - API YTS Brasil para busca de filmes, séries e animes
  - Sistema de cache e seleção interativa de torrents
  - Notificações de novos conteúdos do Jellyfin

- **v0.0.1.4-alpha** (01/06/2025)
  - Implementação completa do comando `/youtube` para download de vídeos
  - Detecção automática de URLs do YouTube em mensagens
  - Download assíncrono com monitoramento de progresso
  - Envio automático de vídeos para o Telegram
  - Sistema de timeout e limite de tamanho (50MB)
  - Documentação completa da funcionalidade YouTube

- **v0.0.1.2.fix2-alpha** (25/05/2025)
  - Refatoração completa do processamento de mensagens
  - Centralização do mapeamento de comandos do teclado
  - Melhor tratamento de erros e validações
  - Remoção de código duplicado
  - Mensagens de erro mais claras e informativas
  - Verificação de permissões mais robusta

- **v0.0.1.2.fix1-alpha** (25/05/2025)
  - Teclado personalizado com botões de acesso rápido
  - Melhorias na experiência do usuário
  - Otimizações de desempenho

- **v0.0.1.2-alpha** (25/05/2025)
  - Reintegração com Jellyfin
  - Novos comandos: `/recent`, `/libraries`, `/status`
  - Exibição de itens recentes com botões inline
  - Botões de ação rápida (Assistir/Não Assistir/Detalhes)
  - Mensagens de status auto-expiráveis
  - Suporte a Markdown nas mensagens

## Próximas Versões Alpha (Desenvolvimento Ativo)

### v0.0.1.5-alpha (Atual)
- [x] ~~Reintegração básica com Jellyfin~~
- [x] ~~Comandos básicos do Jellyfin (/recent, /recentes, /libraries, /status)~~
- [x] ~~Suporte a botões inline nos itens recentes~~
- [x] ~~Correção do comando /recentes~~
- [x] ~~Implementação do comando `/youtube` para download de vídeos~~
- [x] ~~Detecção automática de URLs do YouTube~~
- [x] ~~Sistema de download assíncrono com progresso~~
- [x] ~~Documentação completa da funcionalidade YouTube~~
- [x] ~~Notificações de novos conteúdos adicionados~~
- [x] ~~**Integração WhatsApp WAHA completa**~~
  - [x] ~~Cliente API WAHA (waha_api.py)~~
  - [x] ~~Servidor Flask para webhooks (waha_utils.py)~~
  - [x] ~~Processamento de comandos WhatsApp (whatsapp_commands.py)~~
  - [x] ~~Sistema de autorização por número~~
  - [x] ~~Todos os comandos do Telegram adaptados para WhatsApp~~
  - [x] ~~Documentação completa (README_WHATSAPP.md, QUICKSTART_WHATSAPP.md)~~
- [ ] Busca avançada na biblioteca do Jellyfin
- [ ] Controle de permissões para comandos do Jellyfin

### v0.0.1.6-alpha (Previsto: Abr/2026)
**Objetivo**: Busca e permissões avançadas

#### Funcionalidades:
- [ ] Busca avançada na biblioteca do Jellyfin
  - [ ] Busca por título, gênero, ano
  - [ ] Filtros por tipo de mídia (filme, série, música)
  - [ ] Resultados paginados com botões inline
- [ ] Controle de permissões para comandos do Jellyfin
  - [ ] Níveis de acesso (admin, usuário, convidado)
  - [ ] Restrição de comandos por nível
  - [ ] Logs de acesso e auditoria
- [ ] Melhorias na interface de listagem de torrents
  - [ ] Formatação aprimorada com contadores
  - [ ] Limitação de caracteres em nomes longos
  - [ ] Separadores visuais entre categorias

### v0.0.1.6-alpha (Previsto: Mai/2026)
**Objetivo**: Sincronização e automação básica

#### Funcionalidades:
- [ ] Sincronização de status entre qBittorrent e Jellyfin
  - [ ] Detecção automática de downloads concluídos
  - [ ] Atualização automática da biblioteca do Jellyfin
  - [ ] Notificação quando conteúdo estiver disponível
- [ ] Gerenciamento avançado de torrents
  - [ ] Pausar/retomar torrents via comando
  - [ ] Remover torrents com opção de manter/deletar arquivos
  - [ ] Priorização de downloads
- [ ] Estatísticas detalhadas
  - [ ] Uso de banda por período
  - [ ] Histórico de downloads
  - [ ] Gráficos de atividade

### v0.0.1.7-alpha (Previsto: Jun/2026)
**Objetivo**: Múltiplos servidores e configurações avançadas

#### Funcionalidades:
- [ ] Suporte a múltiplos servidores Jellyfin
  - [ ] Configuração de múltiplas instâncias
  - [ ] Seleção de servidor via comando
  - [ ] Sincronização entre servidores
- [ ] Configurações por usuário
  - [ ] Preferências de notificação
  - [ ] Idioma e formato de data/hora
  - [ ] Temas de mensagens
- [ ] Backup e restauração
  - [ ] Backup automático de configurações
  - [ ] Exportação/importação de dados
  - [ ] Histórico de versões

### v0.0.1.8-alpha (Previsto: Jul/2026)
**Objetivo**: Melhorias de YouTube e mídia

#### Funcionalidades:
- [ ] YouTube avançado
  - [ ] Escolha de qualidade (360p, 720p, 1080p, 4K)
  - [ ] Extração apenas de áudio (MP3, AAC)
  - [ ] Download de playlists completas
  - [ ] Agendamento de downloads
- [ ] Processamento de mídia
  - [ ] Conversão automática de formatos
  - [ ] Compressão de vídeos grandes
  - [ ] Extração de legendas embutidas
- [ ] Integração com armazenamento
  - [ ] Upload direto para Jellyfin após download
  - [ ] Organização automática por tipo/gênero
  - [ ] Limpeza automática de arquivos antigos

## Próximas Versões Estáveis Planejadas

### v0.1.0 - Primeira Versão Beta (Previsto: Set/2025)
**Objetivo**: Estabilização e integração Jellyfin

#### Melhorias Planejadas:
- [ ] Suporte a múltiplos usuários com níveis de permissão
- [ ] Integração estável com Jellyfin
- [ ] Documentação básica de instalação e uso
- [ ] Testes automatizados básicos
- [x] ~~Suporte a comandos via botões inline~~
- [ ] Controle de permissões para comandos do Jellyfin

### v0.2.0 - Melhorias na Experiência (Previsto: Out/2026)
**Objetivo**: Melhorar a usabilidade e recursos Jellyfin

#### Recursos Planejados:
- [ ] Interface mais amigável com botões de ação rápida
- [ ] Busca integrada nos conteúdos do Jellyfin
- [ ] Suporte a categorias e pastas de destino
- [ ] Estatísticas detalhadas de uso e biblioteca
- [ ] Gerenciamento de bibliotecas do Jellyfin
- [ ] Dashboard web para visualização
  - [ ] Estatísticas em tempo real
  - [ ] Gráficos de uso de banda
  - [ ] Histórico de atividades
  - [ ] Gerenciamento de usuários
- [ ] Melhorias de performance
  - [ ] Cache de consultas frequentes
  - [ ] Otimização de queries ao banco
  - [ ] Compressão de respostas

### v0.3.0 - Suporte Avançado a YouTube (Previsto: Dez/2026)
**Objetivo**: Expansão das funcionalidades de download de vídeos

#### Funcionalidades Básicas (Já Implementadas em v0.0.1.4-alpha):
- [x] ~~Download de vídeos do YouTube via link~~
- [x] ~~Detecção automática de URLs do YouTube~~
- [x] ~~Envio direto para o Telegram após download~~
- [x] ~~Sistema de progresso e timeout~~

#### Novas Funcionalidades Avançadas:
- [ ] Escolha de qualidade/formato do vídeo
  - [ ] Seleção via botões inline (360p, 720p, 1080p, 4K)
  - [ ] Formatos: MP4, MKV, WEBM
  - [ ] Prévia de tamanho estimado
- [ ] Extração apenas de áudio
  - [ ] Formatos: MP3, AAC, FLAC, OGG
  - [ ] Qualidade configurável (128k, 192k, 320k)
  - [ ] Metadados automáticos (título, artista, capa)
- [ ] Envio direto para o Jellyfin após download
  - [ ] Organização automática por tipo
  - [ ] Atualização automática da biblioteca
  - [ ] Notificação quando disponível
- [ ] Fila de downloads do YouTube
  - [ ] Múltiplos downloads simultâneos
  - [ ] Priorização de downloads
  - [ ] Pausar/retomar downloads
- [ ] Histórico de downloads
  - [ ] Registro completo de downloads
  - [ ] Estatísticas de uso
  - [ ] Exportação de histórico
- [ ] Suporte a playlists do YouTube
  - [ ] Download completo de playlists
  - [ ] Seleção de vídeos específicos
  - [ ] Atualização automática de playlists

### v0.4.0 - Automação e Integração (Previsto: Jan/2027)
**Objetivo**: Automação e recursos avançados

#### Novas Funcionalidades:
- [ ] Integração com Sonarr/Radarr
  - [ ] Monitoramento automático de séries/filmes
  - [ ] Busca automática de torrents
  - [ ] Download automático de novos episódios
  - [ ] Sincronização de bibliotecas
- [ ] Agendamento avançado
  - [ ] Agendamento de downloads por horário
  - [ ] Limite de banda por período
  - [ ] Priorização automática
  - [ ] Pausar/retomar automático
- [ ] Painel web completo
  - [ ] Interface responsiva
  - [ ] Gerenciamento completo de torrents
  - [ ] Visualização de biblioteca Jellyfin
  - [ ] Configurações avançadas
  - [ ] Logs em tempo real
- [ ] Webhooks e notificações
  - [ ] Suporte a Discord, Slack, Pushover
  - [ ] Notificações personalizáveis
  - [ ] Triggers configuráveis
  - [ ] Templates de mensagens

### v0.5.0 - Listas e Monitoramento (Previsto: Fev/2027)
**Objetivo**: Automação completa do fluxo de mídia

#### Novas Funcionalidades:
- [ ] Integração com listas externas
  - [ ] Trakt.tv (watchlist, coleções)
  - [ ] IMDb (listas personalizadas)
  - [ ] Letterboxd (listas de filmes)
  - [ ] MyAnimeList (anime/manga)
  - [ ] Sincronização automática
- [ ] Monitoramento de RSS
  - [ ] Múltiplos feeds RSS
  - [ ] Filtros personalizados
  - [ ] Download automático
  - [ ] Notificações de novos itens
- [ ] Perfis de qualidade
  - [ ] Perfis por tipo de mídia
  - [ ] Qualidade mínima/máxima
  - [ ] Preferência de codec (H.264, H.265, AV1)
  - [ ] Tamanho de arquivo preferencial
- [ ] Integração com Prowlarr
  - [ ] Múltiplos indexadores
  - [ ] Busca unificada
  - [ ] Estatísticas de indexadores
  - [ ] Fallback automático

### v0.6.0 - Segurança e Privacidade (Previsto: Mar/2027)
**Objetivo**: Melhorar segurança e privacidade

#### Melhorias:
- [ ] Segurança de rede
  - [ ] Suporte nativo a VPN com Kill Switch
  - [ ] Detecção automática de vazamento de IP
  - [ ] Suporte a proxy SOCKS5/HTTP
  - [ ] Túnel split para aplicações específicas
- [ ] Criptografia e autenticação
  - [ ] Criptografia de dados em repouso (AES-256)
  - [ ] Autenticação em dois fatores (2FA)
  - [ ] Tokens de sessão seguros
  - [ ] Rotação automática de credenciais
- [ ] Auditoria e logs
  - [ ] Logs detalhados de atividades
  - [ ] Registro de acessos e comandos
  - [ ] Exportação de logs para SIEM
  - [ ] Alertas de atividades suspeitas
- [ ] Privacidade
  - [ ] Modo anônimo para downloads
  - [ ] Limpeza automática de metadados
  - [ ] Ofuscação de tráfego
  - [ ] Suporte a Tor (opcional)

### v0.7.0 - Processamento de Mídia (Previsto: Abr/2027)
**Objetivo**: Processamento avançado de mídia

#### Melhorias:
- [ ] Suporte a contêineres e codecs
  - [ ] MKV, MP4, AVI, WEBM
  - [ ] H.264, H.265/HEVC, AV1, VP9
  - [ ] Conversão automática entre formatos
  - [ ] Otimização de tamanho
- [ ] Metadados e informações
  - [ ] Extração automática de metadados
  - [ ] Integração com TMDb, TVDb, OMDb
  - [ ] Download automático de posters/fanart
  - [ ] Organização por metadados
- [ ] Legendas
  - [ ] Integração com OpenSubtitles
  - [ ] Download automático de legendas
  - [ ] Múltiplos idiomas
  - [ ] Sincronização automática
  - [ ] Conversão de formatos (SRT, ASS, VTT)
- [ ] Integração com nuvem
  - [ ] Google Drive
  - [ ] Dropbox
  - [ ] OneDrive
  - [ ] Amazon S3
  - [ ] Backup automático
  - [ ] Sincronização bidirecional

### v0.8.0 - Otimização e Performance (Previsto: Mai/2027)
**Objetivo**: Melhorias de performance e escalabilidade

#### Melhorias:
- [ ] Performance
  - [ ] Cache distribuído (Redis)
  - [ ] Otimização de queries
  - [ ] Compressão de dados
  - [ ] Lazy loading de recursos
  - [ ] Pool de conexões
- [ ] Escalabilidade
  - [ ] Suporte a múltiplas instâncias
  - [ ] Load balancing
  - [ ] Filas de processamento (RabbitMQ/Kafka)
  - [ ] Processamento assíncrono
- [ ] Monitoramento
  - [ ] Métricas detalhadas (Prometheus)
  - [ ] Dashboards (Grafana)
  - [ ] Alertas automáticos
  - [ ] Health checks
  - [ ] Tracing distribuído
- [ ] Banco de dados
  - [ ] Migração para PostgreSQL (opcional)
  - [ ] Índices otimizados
  - [ ] Particionamento de tabelas
  - [ ] Backup automático

### v0.9.0 - Release Candidate (Previsto: Jun/2027)
**Objetivo**: Preparação final para versão 1.0

#### Melhorias:
- [ ] Testes extensivos
  - [ ] Testes unitários (>80% cobertura)
  - [ ] Testes de integração
  - [ ] Testes de carga
  - [ ] Testes de segurança
- [ ] Documentação completa
  - [ ] Guia de instalação detalhado
  - [ ] Documentação de API
  - [ ] Tutoriais e exemplos
  - [ ] FAQ e troubleshooting
- [ ] Estabilização
  - [ ] Correção de bugs críticos
  - [ ] Otimizações finais
  - [ ] Validação de segurança
  - [ ] Testes de usuário beta

### v1.0.0 - Primeira Versão Estável (Previsto: Ago/2027)
**Objetivo**: Primeira versão estável para produção

#### Requisitos para Lançamento:
- [ ] Todos os recursos principais implementados e testados
- [ ] Documentação completa e atualizada
- [ ] Guia de migração de versões anteriores
- [ ] Suporte a atualizações automáticas
- [ ] Política de suporte definida (LTS)
- [ ] Zero bugs críticos conhecidos
- [ ] Performance otimizada
- [ ] Segurança validada

#### Recursos Garantidos:
- [x] ~~Gerenciamento completo de torrents via qBittorrent~~
- [x] ~~Integração completa com Jellyfin~~
- [x] ~~Download de vídeos do YouTube~~
- [x] ~~Notificações automáticas~~
- [ ] Interface web completa
- [ ] Suporte a múltiplos usuários
- [ ] Sistema de permissões robusto
- [ ] Backup e restauração
- [ ] Monitoramento e logs

## Versões Futuras (Pós 1.0)

### v1.1.0 - Internacionalização (Previsto: Set/2027)
**Objetivo**: Suporte a múltiplos idiomas

#### Recursos:
- [ ] Sistema de tradução
  - [ ] Framework i18n completo
  - [ ] Suporte a 10+ idiomas
  - [ ] Detecção automática de idioma
  - [ ] Fallback para inglês
- [ ] Idiomas suportados
  - [ ] Português (BR/PT)
  - [ ] Inglês (US/UK)
  - [ ] Espanhol (ES/LATAM)
  - [ ] Francês
  - [ ] Alemão
  - [ ] Italiano
  - [ ] Russo
  - [ ] Japonês
  - [ ] Chinês (Simplificado/Tradicional)
  - [ ] Coreano
- [ ] Documentação traduzida
  - [ ] Guias em múltiplos idiomas
  - [ ] Interface web localizada
  - [ ] Mensagens de erro traduzidas
- [ ] Localização completa
  - [ ] Formatos de data/hora por região
  - [ ] Moedas e números
  - [ ] Fusos horários

### v1.2.0 - Sistema de Plugins (Previsto: Out/2027)
**Objetivo**: Extensibilidade via plugins

#### Recursos:
- [ ] Arquitetura de plugins
  - [ ] Sistema de hooks
  - [ ] API de plugins documentada
  - [ ] Sandboxing de plugins
  - [ ] Gerenciamento de dependências
- [ ] Tipos de plugins
  - [ ] Plugins de notificação
  - [ ] Plugins de download
  - [ ] Plugins de processamento
  - [ ] Plugins de interface
- [ ] Marketplace
  - [ ] Repositório oficial de plugins
  - [ ] Sistema de avaliações
  - [ ] Verificação de segurança
  - [ ] Instalação com um clique
- [ ] Ferramentas para desenvolvedores
  - [ ] SDK de desenvolvimento
  - [ ] Templates de plugins
  - [ ] Documentação de API
  - [ ] Ambiente de testes

### v1.3.0 - Suporte a Discord (Previsto: Nov/2027)
**Objetivo**: Expansão para Discord

#### Recursos:
- [ ] Bot do Discord
  - [ ] Comandos slash nativos
  - [ ] Botões e menus interativos
  - [ ] Embeds ricos
  - [ ] Threads para conversas
- [ ] Funcionalidades
  - [ ] Todos os comandos do Telegram
  - [ ] Notificações em canais
  - [ ] Permissões por role
  - [ ] Múltiplos servidores
- [ ] Integração
  - [ ] Sincronização com Telegram
  - [ ] Configuração unificada
  - [ ] Logs compartilhados

### v1.4.0 - Suporte a WhatsApp ✅ (Implementado antecipadamente em v0.0.1.5-alpha)
**Objetivo**: Expansão para WhatsApp

#### Recursos Implementados:
- [x] ~~Integração com WhatsApp via WAHA~~
  - [x] ~~Autenticação via QR Code~~
  - [x] ~~Mensagens de texto~~
  - [x] ~~Servidor Flask para webhooks~~
  - [x] ~~Cliente API WAHA completo~~
- [x] ~~Funcionalidades~~
  - [x] ~~Todos os comandos do Telegram adaptados~~
  - [x] ~~Sistema de autorização por número~~
  - [x] ~~Formatação Markdown~~
  - [x] ~~Processamento de comandos WhatsApp~~

#### Recursos Futuros (Melhorias):
- [ ] Suporte a mídia (imagens, vídeos, áudio)
- [ ] Botões de resposta rápida
- [ ] Listas interativas
- [ ] Notificações automáticas via WhatsApp
- [ ] Suporte a grupos do WhatsApp
- [ ] Status de leitura e confirmação

### v1.5.0 - Machine Learning (Previsto: Jan/2028)
**Objetivo**: Recursos inteligentes

#### Recursos:
- [ ] Recomendações inteligentes
  - [ ] Sugestões baseadas em histórico
  - [ ] Análise de preferências
  - [ ] Descoberta de conteúdo
- [ ] Automação inteligente
  - [ ] Detecção automática de qualidade
  - [ ] Otimização de downloads
  - [ ] Previsão de espaço em disco
- [ ] Análise de conteúdo
  - [ ] Classificação automática
  - [ ] Detecção de duplicatas
  - [ ] Análise de qualidade de vídeo

### v2.0.0 - Nova Arquitetura (Previsto: Jun/2028)
**Objetivo**: Refatoração completa para microsserviços

#### Mudanças Arquiteturais:
- [ ] Microsserviços
  - [ ] Serviço de autenticação
  - [ ] Serviço de downloads
  - [ ] Serviço de notificações
  - [ ] Serviço de mídia
  - [ ] API Gateway
- [ ] Multiplataforma unificada
  - [ ] Suporte a Telegram, Discord, WhatsApp
  - [ ] API unificada para mensageria
  - [ ] Configuração centralizada
  - [ ] Sincronização entre plataformas
- [ ] Alta disponibilidade
  - [ ] Replicação de serviços
  - [ ] Failover automático
  - [ ] Load balancing avançado
  - [ ] Disaster recovery
- [ ] Escalabilidade horizontal
  - [ ] Kubernetes nativo
  - [ ] Auto-scaling
  - [ ] Service mesh (Istio)
  - [ ] Distributed tracing
- [ ] Painel de controle unificado
  - [ ] Interface web moderna (React/Vue)
  - [ ] Mobile-first design
  - [ ] Real-time updates (WebSockets)
  - [ ] Dashboards personalizáveis
- [ ] Cloud-native
  - [ ] Suporte a AWS, GCP, Azure
  - [ ] Terraform/IaC
  - [ ] CI/CD completo
  - [ ] Monitoramento cloud-native

## Política de Versionamento

### Números de Versão (SemVer)
- **MAJOR**: Mudanças incompatíveis
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis
- **SUFFIX**: -alpha, -beta, -rc para versões de desenvolvimento

### Ciclo de Lançamento
- **Versões alpha**: Testes internos
- **Versões beta**: Testes com usuários selecionados
- **Versões rc**: Candidatas a lançamento
- **Versões estáveis**: Para produção

## Como Contribuir
1. Verifique as issues abertas
2. Siga o guia de contribuição
3. Envie seus PRs para a branch `develop`

---
*Atualizado em: 16/03/2026*
