# Melhorias da Aplicação Web - Inspiradas no Pulse

Este documento descreve as melhorias implementadas na aplicação web do Telegram Torrent Manager, baseadas nas melhores práticas do projeto Pulse.

## 📋 Visão Geral

As melhorias focam em **robustez, segurança, observabilidade e resiliência** da aplicação, sem alterar a funcionalidade existente.

## 🚀 Melhorias Implementadas

### 1. **Middleware de Error Handling com Panic Recovery**

**Arquivo:** `middleware.py` - `ErrorHandlerMiddleware`

**O que faz:**
- Captura todas as exceções não tratadas (panic recovery)
- Retorna respostas de erro estruturadas e consistentes
- Registra stack traces completos para debugging
- Adiciona request ID para rastreamento

**Benefícios:**
- Aplicação nunca trava por exceções não tratadas
- Respostas de erro padronizadas e informativas
- Facilita debugging com logs estruturados

**Exemplo de resposta de erro:**
```json
{
  "error": "An unexpected error occurred",
  "code": "internal_error",
  "status_code": 500,
  "timestamp": 1234567890,
  "request_id": "uuid-here"
}
```

### 2. **Rate Limiting por Endpoint e IP**

**Arquivo:** `middleware.py` - `RateLimitMiddleware`, `RateLimiter`

**O que faz:**
- Limita requisições por IP com janelas de tempo configuráveis
- Diferentes limites para diferentes categorias de endpoints:
  - **Autenticação:** 10 req/min (previne brute force)
  - **Configuração:** 30 req/min
  - **API Geral:** 500 req/min
  - **Endpoints Públicos:** 1000 req/min
- Exclui localhost de rate limiting
- Retorna headers informativos (Retry-After, X-RateLimit-*)

**Benefícios:**
- Proteção contra ataques de força bruta
- Previne abuso de recursos
- Protege contra DDoS básicos

**Resposta quando limite excedido:**
```json
{
  "error": "Rate limit exceeded. Please try again later.",
  "code": "rate_limit_exceeded",
  "status_code": 429,
  "timestamp": 1234567890
}
```

### 3. **Logging Estruturado com Request ID**

**Arquivo:** `middleware.py` - `RequestIDMiddleware`, `LoggingMiddleware`

**O que faz:**
- Adiciona ID único a cada requisição
- Propaga request ID através de toda a stack
- Logs estruturados com contexto completo
- Request ID retornado no header de resposta

**Benefícios:**
- Rastreamento end-to-end de requisições
- Facilita debugging em produção
- Correlação de logs entre serviços

**Exemplo de log:**
```
Request started: GET /api/torrents request_id=abc-123 client=192.168.1.100
Request completed: GET /api/torrents status=200 request_id=abc-123 elapsed=0.234s
```

### 4. **Health Check Robusto**

**Arquivo:** `health.py` - `HealthMonitor`, `HealthResponse`

**Endpoint:** `GET /api/health` e `HEAD /api/health`

**O que faz:**
- Retorna status de saúde da aplicação
- Monitora uptime desde o início
- Verifica disponibilidade de todos os serviços
- Opcionalmente inclui métricas do sistema (CPU, memória, disco)

**Benefícios:**
- Monitoramento externo facilitado
- Detecção rápida de problemas
- Informações para load balancers e orquestradores

**Exemplo de resposta:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "uptime": 3600.5,
  "version": "1.0.0",
  "services": {
    "qbittorrent": true,
    "jellyfin": true,
    "docker": false,
    "telegram_storage": true
  },
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 60.1
  }
}
```

### 5. **Graceful Shutdown**

**Arquivo:** `shutdown.py` - `GracefulShutdown`

**O que faz:**
- Captura sinais SIGTERM e SIGINT
- Executa handlers de cleanup registrados
- Cancela tarefas assíncronas de forma limpa
- Fecha conexões e sessões abertas

**Benefícios:**
- Sem perda de dados durante shutdown
- Fechamento limpo de conexões
- Compatível com containers e orquestradores

**Handlers registrados:**
- Cancelamento de broadcast task
- Fechamento de sessões qBittorrent
- Cleanup de recursos

### 6. **Melhorias no Lifespan**

**Arquivo:** `main.py` - função `lifespan`

**O que faz:**
- Logging detalhado de inicialização
- Registro de signal handlers
- Tracking de uptime desde o início
- Cleanup automático no shutdown
- Logs informativos de cada serviço inicializado

**Benefícios:**
- Visibilidade completa do processo de inicialização
- Debugging facilitado de problemas de startup
- Shutdown limpo e previsível

## 🔧 Arquitetura dos Middlewares

Os middlewares são executados na seguinte ordem (de fora para dentro):

```
Request → RequestID → Logging → RateLimit → ErrorHandler → CORS → Application
```

1. **RequestIDMiddleware**: Adiciona ID único
2. **LoggingMiddleware**: Registra início/fim da requisição
3. **RateLimitMiddleware**: Verifica limites de taxa
4. **ErrorHandlerMiddleware**: Captura exceções
5. **CORSMiddleware**: Gerencia CORS
6. **Application**: Processa a requisição

## 📊 Métricas e Observabilidade

### Logs Estruturados

Todos os logs incluem:
- Timestamp
- Request ID
- Método HTTP e path
- Status code
- Tempo de processamento
- IP do cliente

### Health Check

Pode ser usado por:
- Kubernetes liveness/readiness probes
- Load balancers
- Sistemas de monitoramento (Prometheus, Grafana)
- Scripts de healthcheck

### Rate Limiting

Headers retornados:
- `X-RateLimit-Limit`: Limite máximo
- `X-RateLimit-Remaining`: Requisições restantes
- `Retry-After`: Segundos até poder tentar novamente
- `X-Request-ID`: ID da requisição

## 🛡️ Segurança

### Proteções Implementadas

1. **Rate Limiting**: Previne brute force e abuso
2. **Panic Recovery**: Previne crashes por exceções
3. **Request ID**: Facilita auditoria e investigação
4. **Structured Errors**: Não vaza informações sensíveis

### Endpoints Protegidos

- `/api/auth/login`: 10 req/min (anti brute force)
- `/api/auth/generate-hash`: 10 req/min
- `/api/config/*`: 30 req/min (write operations)
- Demais endpoints: 500 req/min

### Endpoints Públicos (sem rate limit estrito)

- `/api/health`: 1000 req/min
- `/`: 1000 req/min
- Localhost: sem limite

## 🚦 Como Usar

### Health Check

```bash
# Check básico
curl http://localhost:8000/api/health

# Com informações do sistema
curl http://localhost:8000/api/health?include_system=true

# HEAD request (para load balancers)
curl -I http://localhost:8000/api/health
```

### Verificar Rate Limit

```bash
# Headers de rate limit são retornados em cada resposta
curl -v http://localhost:8000/api/torrents

# Quando limite excedido, retorna 429
# HTTP/1.1 429 Too Many Requests
# Retry-After: 60
# X-RateLimit-Limit: 500
# X-RateLimit-Remaining: 0
```

### Rastrear Requisição

```bash
# Enviar request ID customizado
curl -H "X-Request-ID: my-custom-id" http://localhost:8000/api/torrents

# Request ID é retornado no header de resposta
# X-Request-ID: my-custom-id
```

## 📝 Logs Exemplo

### Startup
```
INFO: Starting Web API Backend...
INFO: Application version: 1.0.0
INFO: qBittorrent connected: default (http://localhost:8080)
INFO: Jellyfin initialized with 1 account(s)
INFO: Docker client initialized
INFO: Telegram Storage initialized
INFO: User Manager initialized
INFO: Web API Backend started successfully
INFO: Uptime tracking started at 2026-04-05T14:30:00
```

### Request Normal
```
INFO: Request started: GET /api/torrents request_id=abc-123 client=192.168.1.100
INFO: Request completed: GET /api/torrents status=200 request_id=abc-123 elapsed=0.234s
```

### Request com Erro
```
INFO: Request started: POST /api/torrents/add request_id=def-456 client=192.168.1.100
WARNING: Request failed: POST /api/torrents/add status=500 request_id=def-456 elapsed=0.123s
ERROR: Panic recovered in API handler: POST /api/torrents/add error=Connection refused request_id=def-456 elapsed=0.123s
[stack trace]
```

### Shutdown
```
INFO: Received signal 15, initiating shutdown...
INFO: Shutting down Web API Backend...
INFO: Initiating graceful shutdown...
INFO: Cleaning up resources...
INFO: Cleanup completed
INFO: Graceful shutdown completed
```

## 🔄 Compatibilidade

- ✅ Totalmente compatível com código existente
- ✅ Não quebra APIs existentes
- ✅ Não requer mudanças no frontend
- ✅ Funciona com Docker/Docker Compose
- ✅ Compatível com Kubernetes
- ✅ Suporta proxy reverso (Nginx, Traefik)

## 🎯 Próximas Melhorias Sugeridas

1. **Métricas Prometheus**: Exportar métricas para Prometheus
2. **Distributed Tracing**: OpenTelemetry para tracing distribuído
3. **Circuit Breaker**: Proteção contra falhas em cascata
4. **Cache Layer**: Redis para cache de dados frequentes
5. **API Versioning**: Versionamento de API para evolução
6. **Request Validation**: Validação mais rigorosa de inputs
7. **HTTPS Support**: Suporte nativo a HTTPS
8. **JWT Refresh Tokens**: Tokens de refresh para melhor UX

## 📚 Referências

- **Pulse Project**: https://github.com/rcourtman/pulse-go-rewrite
- **FastAPI Best Practices**: https://fastapi.tiangolo.com/
- **12 Factor App**: https://12factor.net/
- **Production-Ready Microservices**: Building Standardized Systems Across an Engineering Organization
