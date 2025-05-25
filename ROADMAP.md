# Roadmap e Planejamento de Versões

> **⚠️ Aviso Importante**  
> Este documento representa o planejamento atual do projeto, mas está sujeito a alterações. O ciclo de desenvolvimento pode ser ajustado conforme prioridades, feedback dos usuários e mudanças tecnológicas. As datas são estimativas e podem ser alteradas para garantir a qualidade do software.

---

## Versão Atual
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

### v0.0.1.3-alpha (Próxima)
- [x] ~~Reintegração básica com Jellyfin~~
- [x] ~~Comandos básicos do Jellyfin (/recent, /libraries, /status)~~
- [x] ~~Suporte a botões inline nos itens recentes~~
- [ ] Busca avançada na biblioteca do Jellyfin
- [ ] Controle de permissões para comandos do Jellyfin
- [ ] Notificações de novos conteúdos adicionados

### v0.0.1.4-alpha (Em breve)
- [ ] Sincronização de status entre qBittorrent e Jellyfin
- [ ] Busca integrada nos conteúdos do Jellyfin
- [ ] Suporte a múltiplos servidores Jellyfin
- [ ] Documentação da API de integração

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

### v0.2.0 - Melhorias na Experiência (Previsto: Out/2025)
**Objetivo**: Melhorar a usabilidade e recursos Jellyfin

#### Recursos Planejados:
- [ ] Interface mais amigável com botões de ação rápida
- [ ] Busca integrada nos conteúdos do Jellyfin
- [ ] Suporte a categorias e pastas de destino
- [ ] Estatísticas detalhadas de uso e biblioteca
- [ ] Notificações de novos conteúdos adicionados
- [ ] Gerenciamento de bibliotecas do Jellyfin

### v0.3.0 - Suporte a YouTube (Previsto: Nov/2025)
**Objetivo**: Download e gerenciamento de vídeos

#### Novas Funcionalidades:
- [ ] Download de vídeos do YouTube via link
- [ ] Escolha de qualidade/formato do vídeo
- [ ] Extração apenas de áudio (formato MP3)
- [ ] Envio direto para o Jellyfin após download
- [ ] Fila de downloads do YouTube
- [ ] Histórico de downloads

### v0.4.0 - Recursos Avançados (Previsto: Dez/2025)
**Objetivo**: Automação e recursos avançados

#### Novas Funcionalidades:
- [ ] Sincronização entre qBittorrent e Jellyfin
- [ ] Suporte a múltiplos servidores Jellyfin
- [ ] Suporte a playlists do YouTube
- [ ] Agendamento de downloads e sincronização
- [ ] Painel web com visualização da biblioteca
- [ ] Suporte a webhooks para notificações

### v0.5.0 - Automação Avançada (Previsto: Jan/2026)
**Objetivo**: Automação completa do fluxo de mídia

#### Novas Funcionalidades:
- [ ] Integração com Sonarr/Radarr para gerenciamento automático
- [ ] Suporte a listas de desejos do Trakt/IMDb
- [ ] Monitoramento automático de RSS para novos episódios
- [ ] Sistema de perfil de qualidade por tipo de mídia
- [ ] Balanceamento automático de carga entre trackers
- [ ] Suporte a múltiplos indexadores via Prowlarr

### v0.6.0 - Segurança e Privacidade (Previsto: Fev/2026)
**Objetivo**: Melhorar segurança e privacidade

#### Melhorias:
- [ ] Suporte nativo a VPN com Kill Switch
- [ ] Criptografia de dados em repouso
- [ ] Autenticação em dois fatores
- [ ] Logs detalhados de atividades
- [ ] Suporte a proxy SOCKS5/HTTP

### v0.7.0 - Beta Avançado (Previsto: Mar/2026)
**Objetivo**: Preparação para versão estável

#### Melhorias:
- [ ] Otimização de desempenho
- [ ] Suporte a contêineres de mídia (MKV, MP4, etc.)
- [ ] Extração e gerenciamento de metadados
- [ ] Suporte a legendas automáticas (OpenSubtitles, etc.)
- [ ] Integração com serviços de nuvem (Google Drive, Dropbox)

### v1.0.0 - Versão Estável (Previsto: Set/2025)
**Objetivo**: Primeira versão estável

#### Requisitos para Lançamento:
- [ ] Testes abrangentes
- [ ] Documentação completa
- [ ] Guia de migração de versões anteriores
- [ ] Suporte a atualizações automáticas
- [ ] Política de suporte definida

## Versões Futuras (Pós 1.0)

### v1.1.0 - Internacionalização
- [ ] Suporte a múltiplos idiomas
- [ ] Documentação traduzida
- [ ] Localização de comandos e respostas

### v1.2.0 - Plugins e Extensões
- [ ] Sistema de plugins
- [ ] API para desenvolvedores
- [ ] Marketplace de plugins

### v1.3.0 - Suporte a WhatsApp (Previsto: 2026)
**Objetivo**: Expansão para novas plataformas

#### Recursos Planejados:
- [ ] Integração básica com WhatsApp Business API
- [ ] Comandos similares à versão Telegram
- [ ] Suporte a mídia no WhatsApp
- [ ] Documentação específica para WhatsApp

### v2.0.0 - Nova Arquitetura e Multiplataforma
- [ ] Refatoração para microsserviços
- [ ] Suporte unificado a Telegram e WhatsApp
- [ ] API unificada para mensageria
- [ ] Alta disponibilidade e escalabilidade
- [ ] Painel de controle unificado

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
*Atualizado em: 24/05/2025*
