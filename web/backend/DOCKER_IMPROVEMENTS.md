# 🐳 Melhorias no Gerenciamento Docker

## Resumo Executivo

O sistema de gerenciamento Docker foi completamente reformulado baseado nas melhores práticas do projeto **Pulse**, transformando uma implementação básica em um sistema robusto de monitoramento e controle de containers.

## 📦 Arquivos Criados/Modificados

### Novos Arquivos

1. **`docker_manager.py`** (650+ linhas)
   - `DockerStats`: Classe para cálculo de métricas avançadas
   - `DockerManager`: Sistema completo de gerenciamento Docker
   - Suporte a Docker Compose stacks
   - Cache de estatísticas com TTL

2. **`docker_routes.py`** (280+ linhas)
   - Endpoints RESTful para gerenciamento Docker
   - Rotas para containers, stacks e sistema
   - Documentação automática via OpenAPI

### Arquivos Modificados

1. **`main.py`**
   - Substituição do `DockerHelper` básico pelo `DockerManager`
   - Integração das rotas avançadas
   - Logging melhorado na inicialização

## 🚀 Funcionalidades Implementadas

### 1. **Coleta de Métricas Avançadas**

Inspirado no algoritmo de cálculo do Pulse, implementamos:

#### CPU Usage
```python
# Cálculo preciso de CPU baseado em deltas
cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
```

**Métricas incluídas:**
- Uso de CPU por container (%)
- Uso de memória (ativa, cache, total)
- I/O de rede (RX/TX bytes)
- I/O de disco (Read/Write bytes)
- Número de processos (PIDs)

#### Memory Stats
```python
{
  "usage": 524288000,      # Uso total
  "limit": 8589934592,     # Limite
  "cache": 104857600,      # Cache
  "active": 419430400,     # Memória ativa (sem cache)
  "percent": 4.88          # Percentual de uso
}
```

#### Network Stats
```python
{
  "rx_bytes": 1048576,     # Bytes recebidos
  "tx_bytes": 524288,      # Bytes transmitidos
  "total_bytes": 1572864   # Total
}
```

### 2. **Informações Enriquecidas de Containers**

Cada container retorna metadados completos:

```json
{
  "id": "abc123...",
  "short_id": "abc123",
  "name": "my-container",
  "status": "running",
  "state": "running",
  "image": "nginx:latest",
  "created": "2026-04-05T14:30:00Z",
  "restart_count": 0,
  "labels": {...},
  "networks": [
    {
      "name": "bridge",
      "ip_address": "172.17.0.2",
      "gateway": "172.17.0.1",
      "mac_address": "02:42:ac:11:00:02"
    }
  ],
  "ports": [
    {
      "container_port": "80/tcp",
      "host_ip": "0.0.0.0",
      "host_port": "8080"
    }
  ],
  "mounts": [
    {
      "type": "bind",
      "source": "/host/path",
      "destination": "/container/path",
      "mode": "rw",
      "rw": true
    }
  ],
  "compose": {
    "project": "myapp",
    "service": "web",
    "number": "1",
    "is_compose": true
  }
}
```

### 3. **Suporte a Docker Compose Stacks**

Agrupamento automático de containers por projeto Compose:

```json
{
  "stacks": [
    {
      "name": "telegram_torrent",
      "containers": [...],
      "services": ["web", "backend", "db"],
      "running": 2,
      "stopped": 1,
      "total": 3
    }
  ]
}
```

**Operações em stack:**
- Iniciar todos os containers de uma stack
- Parar todos os containers de uma stack
- Reiniciar todos os containers de uma stack

### 4. **Cache de Estatísticas**

Sistema de cache com TTL para otimizar performance:

```python
stats_cache_ttl = 5  # segundos
```

**Benefícios:**
- Reduz carga no Docker daemon
- Melhora tempo de resposta da API
- Evita requisições duplicadas

### 5. **Gerenciamento Completo de Containers**

Todas as operações essenciais implementadas:

- ✅ **Start**: Iniciar container
- ✅ **Stop**: Parar container (com timeout)
- ✅ **Restart**: Reiniciar container
- ✅ **Pause**: Pausar container
- ✅ **Unpause**: Despausar container
- ✅ **Remove**: Remover container (com opções force/volumes)

## 🌐 Novos Endpoints API

### Sistema Docker

```bash
GET /api/docker-advanced/system/info
```

**Resposta:**
```json
{
  "containers": 10,
  "containers_running": 7,
  "containers_paused": 0,
  "containers_stopped": 3,
  "images": 25,
  "driver": "overlay2",
  "docker_version": "24.0.7",
  "operating_system": "Ubuntu 22.04",
  "architecture": "x86_64",
  "cpus": 8,
  "memory_total": 17179869184,
  "name": "docker-host"
}
```

### Listagem de Containers

```bash
GET /api/docker-advanced/containers?all=true&status=running
```

**Parâmetros:**
- `all`: Incluir containers parados (default: true)
- `status`: Filtrar por status (running, exited, etc)

### Inspeção Detalhada

```bash
GET /api/docker-advanced/containers/{container_id}/inspect
```

Retorna dados completos de inspeção do Docker (equivalente a `docker inspect`).

### Estatísticas em Tempo Real

```bash
GET /api/docker-advanced/containers/{container_id}/stats
```

**Resposta:**
```json
{
  "container_id": "abc123",
  "container_name": "my-app",
  "timestamp": "2026-04-05T14:30:00",
  "cpu": 12.5,
  "memory": {
    "usage": 524288000,
    "limit": 8589934592,
    "cache": 104857600,
    "active": 419430400,
    "percent": 4.88
  },
  "network": {
    "rx_bytes": 1048576,
    "tx_bytes": 524288,
    "total_bytes": 1572864
  },
  "block_io": {
    "read_bytes": 2097152,
    "write_bytes": 1048576,
    "total_bytes": 3145728
  },
  "pids": 15
}
```

### Logs de Container

```bash
GET /api/docker-advanced/containers/{container_id}/logs?tail=100&timestamps=true
```

**Parâmetros:**
- `tail`: Número de linhas (default: 100)
- `since`: Logs desde timestamp ou tempo relativo (e.g., '1h')
- `timestamps`: Incluir timestamps (default: true)

### Ações de Container

```bash
POST /api/docker-advanced/containers/{container_id}/start
POST /api/docker-advanced/containers/{container_id}/stop?timeout=10
POST /api/docker-advanced/containers/{container_id}/restart?timeout=10
POST /api/docker-advanced/containers/{container_id}/pause
POST /api/docker-advanced/containers/{container_id}/unpause
DELETE /api/docker-advanced/containers/{container_id}?force=false&volumes=false
```

### Docker Compose Stacks

```bash
# Listar stacks
GET /api/docker-advanced/stacks

# Gerenciar stack
POST /api/docker-advanced/stacks/{stack_name}/start
POST /api/docker-advanced/stacks/{stack_name}/stop?timeout=10
POST /api/docker-advanced/stacks/{stack_name}/restart?timeout=10
```

## 📊 Comparação Antes/Depois

| Funcionalidade | Antes (DockerHelper) | Depois (DockerManager) |
|----------------|---------------------|------------------------|
| **Listagem de Containers** | Básica (id, nome, status) | Completa (redes, portas, volumes, compose) |
| **Métricas** | ❌ Nenhuma | ✅ CPU, memória, rede, disco |
| **Logs** | ❌ Não disponível | ✅ Com filtros e timestamps |
| **Inspeção** | ❌ Não disponível | ✅ Dados completos |
| **Docker Compose** | ⚠️ Apenas detecção | ✅ Gerenciamento completo |
| **Cache** | ❌ Nenhum | ✅ Cache com TTL |
| **Ações** | ⚠️ Start/Stop básico | ✅ Start/Stop/Restart/Pause/Unpause/Remove |
| **Operações em Lote** | ❌ Não disponível | ✅ Stacks completas |
| **Informações do Sistema** | ❌ Não disponível | ✅ Info completo |

## 🎯 Casos de Uso

### 1. Monitoramento de Recursos

```bash
# Ver uso de recursos de um container específico
curl http://localhost:8000/api/docker-advanced/containers/my-app/stats

# Monitorar todos os containers
curl http://localhost:8000/api/docker-advanced/containers
```

### 2. Debugging

```bash
# Ver logs recentes
curl "http://localhost:8000/api/docker-advanced/containers/my-app/logs?tail=50"

# Ver logs da última hora
curl "http://localhost:8000/api/docker-advanced/containers/my-app/logs?since=1h"

# Inspeção completa
curl http://localhost:8000/api/docker-advanced/containers/my-app/inspect
```

### 3. Gerenciamento de Stacks

```bash
# Listar todas as stacks Compose
curl http://localhost:8000/api/docker-advanced/stacks

# Reiniciar stack completa
curl -X POST http://localhost:8000/api/docker-advanced/stacks/myapp/restart
```

### 4. Operações em Containers

```bash
# Reiniciar container com timeout customizado
curl -X POST "http://localhost:8000/api/docker-advanced/containers/my-app/restart?timeout=30"

# Remover container forçadamente com volumes
curl -X DELETE "http://localhost:8000/api/docker-advanced/containers/my-app?force=true&volumes=true"
```

## 🔧 Arquitetura Técnica

### DockerStats (Classe Utilitária)

Métodos estáticos para cálculo de métricas:

```python
DockerStats.calculate_cpu_percent(stats)      # CPU %
DockerStats.calculate_memory_stats(stats)     # Memória
DockerStats.calculate_network_stats(stats)    # Rede
DockerStats.calculate_block_io_stats(stats)   # Disco
```

### DockerManager (Classe Principal)

**Inicialização:**
```python
docker_client = docker.from_env()
manager = DockerManager(docker_client)
```

**Métodos principais:**
- `list_containers(all, filters)`: Listar containers
- `get_container_stats(container_id)`: Obter estatísticas
- `get_container_logs(container_id, tail, since, timestamps)`: Obter logs
- `inspect_container(container_id)`: Inspeção completa
- `get_compose_stacks()`: Listar stacks Compose
- `get_system_info()`: Informações do sistema Docker

**Operações:**
- `start_container(container_id)`
- `stop_container(container_id, timeout)`
- `restart_container(container_id, timeout)`
- `pause_container(container_id)`
- `unpause_container(container_id)`
- `remove_container(container_id, force, volumes)`

### Cache System

```python
stats_cache = {
    'container_id': (stats_data, timestamp)
}
```

**Lógica:**
1. Verificar se existe no cache
2. Verificar se TTL ainda é válido
3. Retornar do cache ou buscar novo
4. Atualizar cache com novo resultado

## 🚦 Como Testar

### 1. Verificar Sistema Docker

```bash
curl http://localhost:8000/api/docker-advanced/system/info
```

### 2. Listar Containers

```bash
# Todos os containers
curl http://localhost:8000/api/docker-advanced/containers

# Apenas running
curl "http://localhost:8000/api/docker-advanced/containers?status=running"
```

### 3. Monitorar Recursos

```bash
# Stats de um container
curl http://localhost:8000/api/docker-advanced/containers/my-container/stats

# Logs
curl "http://localhost:8000/api/docker-advanced/containers/my-container/logs?tail=20"
```

### 4. Gerenciar Stacks

```bash
# Listar stacks
curl http://localhost:8000/api/docker-advanced/stacks

# Parar stack
curl -X POST http://localhost:8000/api/docker-advanced/stacks/mystack/stop
```

## 📈 Performance

### Otimizações Implementadas

1. **Cache de Stats**: TTL de 5 segundos reduz chamadas ao Docker daemon
2. **Filtros Eficientes**: Filtros aplicados no Docker API, não em memória
3. **Lazy Loading**: Dados detalhados apenas quando solicitados
4. **Batch Operations**: Operações em stack processadas em lote

### Benchmarks Estimados

| Operação | Tempo Médio | Cache Hit |
|----------|-------------|-----------|
| List Containers | ~50ms | N/A |
| Get Stats (cached) | ~5ms | 95% |
| Get Stats (uncached) | ~100ms | 5% |
| Get Logs | ~80ms | N/A |
| Inspect | ~60ms | N/A |
| Start/Stop | ~200ms | N/A |

## 🔐 Segurança

### Proteções Implementadas

1. **Autenticação**: Todos os endpoints requerem autenticação
2. **Rate Limiting**: Proteção contra abuso (via middleware global)
3. **Error Handling**: Erros tratados sem vazamento de informações
4. **Validação**: Parâmetros validados via Pydantic/FastAPI

### Recomendações

- ✅ Usar HTTPS em produção
- ✅ Limitar acesso ao Docker socket
- ✅ Implementar RBAC para operações destrutivas
- ✅ Auditar operações de remoção de containers

## 🎓 Aprendizados do Pulse

Práticas adaptadas do Pulse:

1. **Cálculo Preciso de CPU**: Algoritmo baseado em deltas de uso
2. **Estrutura de Dados Rica**: Metadados completos de containers
3. **Suporte a Compose**: Agrupamento por projeto
4. **Cache Inteligente**: TTL para otimizar performance
5. **API RESTful Completa**: Endpoints para todas as operações
6. **Logging Estruturado**: Logs detalhados de todas as operações

## 📚 Próximos Passos Sugeridos

1. **WebSocket para Stats**: Stream de métricas em tempo real
2. **Histórico de Métricas**: Armazenar histórico para gráficos
3. **Alertas**: Notificações quando recursos excedem limites
4. **Docker Events**: Monitorar eventos do Docker daemon
5. **Image Management**: Gerenciamento de imagens Docker
6. **Volume Management**: Gerenciamento de volumes
7. **Network Management**: Gerenciamento de redes
8. **Container Exec**: Executar comandos em containers
9. **Container Attach**: Attach a containers em execução
10. **Swarm Support**: Suporte a Docker Swarm (se aplicável)

## 🤝 Integração com Frontend

### Exemplo de Uso no Frontend

```javascript
// Listar containers
const response = await fetch('/api/docker-advanced/containers');
const data = await response.json();
console.log(`Total containers: ${data.total}`);

// Obter stats
const stats = await fetch('/api/docker-advanced/containers/my-app/stats');
const statsData = await stats.json();
console.log(`CPU: ${statsData.cpu}%`);
console.log(`Memory: ${statsData.memory.percent}%`);

// Reiniciar container
await fetch('/api/docker-advanced/containers/my-app/restart', {
  method: 'POST'
});

// Gerenciar stack
await fetch('/api/docker-advanced/stacks/mystack/restart', {
  method: 'POST'
});
```

### Componentes Sugeridos

1. **Container List**: Tabela com todos os containers e status
2. **Container Details**: Painel com informações detalhadas
3. **Stats Dashboard**: Gráficos de CPU, memória, rede
4. **Logs Viewer**: Visualizador de logs com filtros
5. **Stack Manager**: Gerenciamento de stacks Compose
6. **Quick Actions**: Botões para start/stop/restart

---

**Versão:** 2.0.0  
**Data:** Abril 2026  
**Inspirado por:** [Pulse Project](https://github.com/rcourtman/pulse-go-rewrite)  
**Compatibilidade:** Docker API v1.41+
