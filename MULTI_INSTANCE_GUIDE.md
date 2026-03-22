# Guia de Multi-Instância qBittorrent

## Visão Geral

O sistema de multi-instância permite conectar e gerenciar múltiplas instalações do qBittorrent simultaneamente, com distribuição inteligente de downloads baseada no espaço disponível em cada instância.

## Características Principais

### 1. **Gerenciamento de Múltiplas Instâncias**
- Conecte até N instâncias do qBittorrent simultaneamente
- Cada instância pode estar em servidores diferentes
- Monitoramento automático de status de conexão

### 2. **Distribuição Inteligente de Downloads**
- Algoritmo que seleciona automaticamente a melhor instância baseado em:
  - Espaço livre disponível
  - Prioridade configurada da instância
  - Status de conexão ativa
- Balanceamento automático de carga

### 3. **Monitoramento de Armazenamento**
- Verificação automática de espaço disponível
- Cache de informações com atualização periódica
- Visualização em tempo real do espaço em cada instância

## Configuração

### Configuração Unificada (Uma ou Múltiplas Instâncias)

O sistema usa uma **configuração única** que funciona tanto para uma quanto para múltiplas instâncias do qBittorrent.

#### Para Uma Instância (modo tradicional):

```env
QB_NAMES=default
QB_URLS=http://localhost:8080
QB_USERS=admin
QB_PASSWORDS=sua_senha
QB_STORAGE_PATHS=/
QB_PRIORITIES=0
INTERVALO=120
```

#### Para Múltiplas Instâncias:

Basta adicionar mais valores separados por vírgula:

```env
QB_NAMES=servidor-principal,servidor-backup,servidor-local
QB_URLS=http://192.168.1.10:8080,http://192.168.1.20:8080,http://localhost:8080
QB_USERS=admin,admin,admin
QB_PASSWORDS=senha123,senha456,adminpass
QB_STORAGE_PATHS=/downloads,/data,/torrents
QB_PRIORITIES=10,5,0
INTERVALO=120
```

### Variáveis de Configuração

1. **QB_NAMES**: Identificadores únicos das instâncias
2. **QB_URLS**: URLs completas do qBittorrent
3. **QB_USERS**: Usuários para login (opcional, padrão: `admin`)
4. **QB_PASSWORDS**: Senhas de acesso (opcional, padrão: `adminadmin`)
5. **QB_STORAGE_PATHS**: Caminhos de armazenamento (opcional, padrão: `/`)
6. **QB_PRIORITIES**: Prioridades numéricas (opcional, padrão: `0`, maior = mais prioritário)
7. **INTERVALO**: Intervalo de verificação em segundos

**Importante:** 
- Todas as listas devem ter valores na mesma ordem
- Multi-instância é **automaticamente habilitada** quando há mais de uma URL
- Para uma única instância, use apenas um valor em cada campo

## Comandos do Telegram

### `/instances`
Exibe informações sobre todas as instâncias configuradas:
- Status de conexão (ativa/inativa)
- Espaço disponível e total
- Prioridade configurada
- URL de acesso

**Exemplo de resposta:**
```
📊 **Instâncias qBittorrent:**

• **servidor-principal** (✅ Ativa)
   🔗 http://192.168.1.10:8080
   💾 Espaço: 500.00 GB livres / 1.00 TB total
   ⭐ Prioridade: 10

• **servidor-backup** (✅ Ativa)
   🔗 http://192.168.1.20:8080
   💾 Espaço: 200.00 GB livres / 500.00 GB total
   ⭐ Prioridade: 5
```

### `/torrents_multi`
Lista todos os torrents de todas as instâncias ativas, organizados por servidor.

**Exemplo de resposta:**
```
📊 **Torrents por Instância:**

🖥️ **servidor-principal**
   ⬇️ Ubuntu 22.04 LTS
      └─ 45.2% | downloading
   ⬆️ Debian 11
      └─ 100.0% | uploading

🖥️ **servidor-backup**
   ⬇️ CentOS Stream 9
      └─ 12.8% | downloading
```

### `/refresh_storage`
Força a atualização das informações de armazenamento de todas as instâncias.

### `/reconnect_instances`
Reconecta todas as instâncias (útil após mudanças de configuração ou problemas de rede).

**Exemplo de resposta:**
```
🔌 **Resultado da Reconexão:**
• **servidor-principal**: ✅ Conectado
• **servidor-backup**: ✅ Conectado
• **servidor-local**: ❌ Falha
```

## Funcionamento do Algoritmo de Distribuição

### Critérios de Seleção

Quando um novo download é adicionado, o sistema:

1. **Filtra instâncias ativas** com espaço suficiente
2. **Ordena por prioridade** (maior primeiro)
3. **Em caso de empate**, seleciona a com mais espaço livre
4. **Adiciona o torrent** na instância selecionada

### Exemplo Prático

Configuração:
- **Servidor A**: 1TB livre, prioridade 10
- **Servidor B**: 2TB livre, prioridade 5
- **Servidor C**: 500GB livre, prioridade 10

Resultado: **Servidor C** será escolhido (mesma prioridade que A, mas mais espaço)

Se C estiver offline, **Servidor A** será escolhido (maior prioridade que B).

## Uso Automático

Quando a multi-instância está habilitada, **todos os magnet links** enviados ao bot são automaticamente distribuídos para a melhor instância disponível.

**Exemplo:**
```
Usuário: magnet:?xt=urn:btih:abc123...

Bot: ✅ Download adicionado!
     Download adicionado à instância 'servidor-principal' (500.00 GB disponíveis)
```

## Monitoramento e Manutenção

### Verificação Automática de Espaço

O sistema verifica o espaço disponível:
- Automaticamente a cada 60 segundos (configurável)
- Antes de adicionar cada novo download
- Quando solicitado via `/refresh_storage`

### Reconexão Automática

Se uma instância perder conexão:
- O sistema a marca como inativa
- Downloads futuros são direcionados para outras instâncias
- Use `/reconnect_instances` para tentar reconectar

## Arquitetura Técnica

### Componentes Principais

1. **`MultiInstanceManager`** (`multi_instance_manager.py`)
   - Gerencia pool de conexões
   - Implementa algoritmo de distribuição
   - Monitora espaço em disco

2. **`QBInstance`** (dataclass)
   - Representa uma instância individual
   - Armazena sessão HTTP, espaço disponível, status

3. **Comandos Telegram** (`multi_instance_commands.py`)
   - Interface de usuário via Telegram
   - Handlers para todos os comandos

### Fluxo de Adição de Torrent

```
Magnet Link Recebido
    ↓
Multi-instância habilitada?
    ↓ Sim
Atualizar info de armazenamento (se necessário)
    ↓
Filtrar instâncias ativas com espaço suficiente
    ↓
Ordenar por (prioridade, espaço livre)
    ↓
Selecionar primeira da lista
    ↓
Adicionar torrent via API qBittorrent
    ↓
Retornar confirmação ao usuário
```

## Solução de Problemas

### Instância aparece como inativa

**Causas possíveis:**
- Servidor qBittorrent offline
- Credenciais incorretas
- Firewall bloqueando conexão
- URL incorreta

**Solução:**
1. Verifique se o qBittorrent está rodando
2. Teste as credenciais manualmente
3. Use `/reconnect_instances`

### Downloads não são distribuídos

**Verificar:**
- `QB_MULTI_INSTANCE_ENABLED=True` no `.env`
- Formato correto em `QB_INSTANCES`
- Pelo menos uma instância ativa (`/instances`)

### Espaço não atualiza

**Solução:**
- Use `/refresh_storage` para forçar atualização
- Verifique logs para erros de API

## Migração e Compatibilidade

### Configuração Antiga (ainda funciona):

```env
QB_URL=http://localhost:8080
QB_USER=admin
QB_PASS=senha
QBITTORRENT_STORAGE_PATH=/
INTERVALO=120
```

### Nova Configuração Unificada (recomendada):

```env
QB_NAMES=default
QB_URLS=http://localhost:8080
QB_USERS=admin
QB_PASSWORDS=senha
QB_STORAGE_PATHS=/
QB_PRIORITIES=0
INTERVALO=120
```

**Compatibilidade:** O sistema detecta automaticamente qual formato você está usando. As variáveis antigas (`QB_URL`, `QB_USER`, `QB_PASS`, `QBITTORRENT_STORAGE_PATH`) ainda funcionam perfeitamente.

### Para Adicionar Mais Instâncias:

Basta adicionar mais valores separados por vírgula nas novas variáveis:

```env
QB_NAMES=principal,backup
QB_URLS=http://localhost:8080,http://192.168.1.20:8080
QB_USERS=admin,admin
QB_PASSWORDS=senha1,senha2
QB_STORAGE_PATHS=/,/backup
QB_PRIORITIES=10,5
INTERVALO=120
```

O multi-instância é **ativado automaticamente** quando detecta mais de uma URL.

## Limitações Conhecidas

- Máximo recomendado: 10 instâncias (performance)
- Atualização de espaço: intervalo mínimo de 60s
- Não suporta balanceamento de torrents existentes entre instâncias

## Exemplos de Uso

### Cenário 1: Servidor Principal + Backup

```env
QB_NAMES=principal,backup
QB_URLS=http://192.168.1.10:8080,http://192.168.1.20:8080
QB_USERS=admin,admin
QB_PASSWORDS=pass1,pass2
QB_STORAGE_PATHS=/data,/backup
QB_PRIORITIES=100,1
INTERVALO=120
```

Downloads vão para `principal` (prioridade 100). Se ficar sem espaço ou offline, vão para `backup`.

### Cenário 2: Múltiplos Discos no Mesmo Servidor

```env
QB_NAMES=disco1,disco2,disco3
QB_URLS=http://localhost:8080,http://localhost:8081,http://localhost:8082
QB_USERS=admin,admin,admin
QB_PASSWORDS=pass,pass,pass
QB_STORAGE_PATHS=/mnt/disk1,/mnt/disk2,/mnt/disk3
QB_PRIORITIES=0,0,0
INTERVALO=120
```

Downloads distribuídos igualmente pelo disco com mais espaço livre.

### Cenário 3: Servidores Especializados

```env
QB_NAMES=rapido,lento
QB_URLS=http://ssd-server:8080,http://hdd-server:8080
QB_USERS=admin,admin
QB_PASSWORDS=pass,pass
QB_STORAGE_PATHS=/ssd,/hdd
QB_PRIORITIES=50,10
INTERVALO=120
```

Prioriza `rapido` (SSD) para downloads, usa `lento` (HDD) quando necessário.

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs do bot
2. Use `/instances` para diagnóstico
3. Teste `/reconnect_instances`
4. Consulte a documentação da API do qBittorrent
