# 🔐 Documentação de Segurança - Docker API Routes

## Resumo

Todas as rotas Docker avançadas (`/api/docker-advanced/*`) foram protegidas com autenticação JWT obrigatória. Nenhuma operação Docker pode ser executada sem um token válido.

---

## 🛡️ Proteção Implementada

### Autenticação JWT

Todas as 16 rotas Docker requerem autenticação via token JWT:

```python
from auth import get_current_user

@router.get("/containers")
async def list_containers(
    current_user: Dict = Depends(get_current_user),  # ✅ Autenticação obrigatória
    docker_manager=Depends(get_docker_manager)
):
    """List all Docker containers (requires authentication)"""
    # ...
```

### Rotas Protegidas

#### Informações do Sistema
- `GET /api/docker-advanced/system/info` ✅ Protegida

#### Gerenciamento de Containers
- `GET /api/docker-advanced/containers` ✅ Protegida
- `GET /api/docker-advanced/containers/{id}/inspect` ✅ Protegida
- `GET /api/docker-advanced/containers/{id}/stats` ✅ Protegida
- `GET /api/docker-advanced/containers/{id}/logs` ✅ Protegida

#### Ações de Containers
- `POST /api/docker-advanced/containers/{id}/start` ✅ Protegida
- `POST /api/docker-advanced/containers/{id}/stop` ✅ Protegida
- `POST /api/docker-advanced/containers/{id}/restart` ✅ Protegida
- `POST /api/docker-advanced/containers/{id}/pause` ✅ Protegida
- `POST /api/docker-advanced/containers/{id}/unpause` ✅ Protegida
- `DELETE /api/docker-advanced/containers/{id}` ✅ Protegida

#### Gerenciamento de Stacks
- `GET /api/docker-advanced/stacks` ✅ Protegida
- `POST /api/docker-advanced/stacks/{name}/start` ✅ Protegida
- `POST /api/docker-advanced/stacks/{name}/stop` ✅ Protegida
- `POST /api/docker-advanced/stacks/{name}/restart` ✅ Protegida

**Total: 16 rotas protegidas** 🔒

---

## 🔑 Como Funciona a Autenticação

### 1. Login

```bash
# Obter token JWT
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}'

# Resposta:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Usar Token nas Requisições

```bash
# Exemplo: Listar containers
curl http://localhost:8000/api/docker-advanced/containers \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Respostas de Erro

#### Sem Token (401 Unauthorized)
```bash
curl http://localhost:8000/api/docker-advanced/containers

# Resposta:
{
  "detail": "Not authenticated"
}
```

#### Token Inválido (401 Unauthorized)
```bash
curl http://localhost:8000/api/docker-advanced/containers \
  -H "Authorization: Bearer token_invalido"

# Resposta:
{
  "detail": "Could not validate credentials"
}
```

#### Token Expirado (401 Unauthorized)
```bash
# Resposta:
{
  "detail": "Token has expired"
}
```

---

## 🔒 Camadas de Segurança

### 1. Autenticação JWT
- **Obrigatória** em todas as rotas Docker
- Token deve ser válido e não expirado
- Usuário deve existir no sistema

### 2. Rate Limiting
- Proteção contra abuso via middleware
- Limites configurados por categoria de endpoint
- Bloqueio automático após exceder limite

### 3. Error Handling
- Middleware de panic recovery
- Erros não vazam informações sensíveis
- Logs estruturados para auditoria

### 4. Docker Manager Validation
- Verifica se Docker está disponível
- Valida IDs de containers/stacks
- Retorna erros apropriados (404, 400, 503)

---

## 📊 Matriz de Permissões

| Rota | Método | Autenticação | Rate Limit | Ação |
|------|--------|--------------|------------|------|
| `/system/info` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/containers` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/containers/{id}/inspect` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/containers/{id}/stats` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/containers/{id}/logs` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/containers/{id}/start` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/containers/{id}/stop` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/containers/{id}/restart` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/containers/{id}/pause` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/containers/{id}/unpause` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/containers/{id}` | DELETE | ✅ JWT | ✅ 10/min | Destrutiva |
| `/stacks` | GET | ✅ JWT | ✅ 500/min | Leitura |
| `/stacks/{name}/start` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/stacks/{name}/stop` | POST | ✅ JWT | ✅ 30/min | Escrita |
| `/stacks/{name}/restart` | POST | ✅ JWT | ✅ 30/min | Escrita |

---

## 🧪 Testes de Segurança

### Teste 1: Acesso sem Autenticação

```bash
# Deve retornar 401
curl -i http://localhost:8000/api/docker-advanced/containers

# Esperado:
HTTP/1.1 401 Unauthorized
{"detail": "Not authenticated"}
```

### Teste 2: Token Inválido

```bash
# Deve retornar 401
curl -i http://localhost:8000/api/docker-advanced/containers \
  -H "Authorization: Bearer invalid_token"

# Esperado:
HTTP/1.1 401 Unauthorized
{"detail": "Could not validate credentials"}
```

### Teste 3: Token Válido

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}' \
  | jq -r '.access_token')

# 2. Usar token
curl http://localhost:8000/api/docker-advanced/containers \
  -H "Authorization: Bearer $TOKEN"

# Esperado:
HTTP/1.1 200 OK
{"containers": [...], "total": 10}
```

### Teste 4: Operação Destrutiva

```bash
# DELETE deve estar protegido
curl -X DELETE http://localhost:8000/api/docker-advanced/containers/abc123

# Esperado:
HTTP/1.1 401 Unauthorized
{"detail": "Not authenticated"}
```

---

## 🚨 Auditoria e Logging

### Logs de Acesso

Todas as requisições são logadas com:

```python
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-05T15:30:00Z",
  "method": "POST",
  "path": "/api/docker-advanced/containers/abc123/start",
  "user": "admin",
  "ip": "192.168.1.100",
  "status_code": 200,
  "elapsed_ms": 150
}
```

### Logs de Erro

Erros de autenticação são logados:

```python
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-05T15:30:00Z",
  "level": "WARNING",
  "message": "Authentication failed",
  "path": "/api/docker-advanced/containers",
  "ip": "192.168.1.100",
  "reason": "Invalid token"
}
```

---

## 🔐 Boas Práticas de Segurança

### Para Desenvolvedores

1. **Nunca** remova `Depends(get_current_user)` das rotas
2. **Sempre** valide entrada do usuário
3. **Use** HTTPS em produção
4. **Rotacione** secrets regularmente
5. **Audite** logs de acesso periodicamente

### Para Administradores

1. **Configure** senhas fortes
2. **Monitore** tentativas de acesso falhas
3. **Revise** logs de operações destrutivas
4. **Limite** acesso ao Docker socket
5. **Implemente** backup regular

### Para Usuários

1. **Proteja** seu token JWT
2. **Não compartilhe** credenciais
3. **Use** senhas únicas
4. **Faça logout** após uso
5. **Reporte** atividades suspeitas

---

## 🛠️ Configuração de Segurança

### Variáveis de Ambiente

```bash
# JWT Secret (OBRIGATÓRIO - mude em produção)
SECRET_KEY=your-secret-key-here-change-in-production

# Token expiration (padrão: 30 minutos)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate limiting (requisições por minuto)
RATE_LIMIT_GENERAL=500
RATE_LIMIT_CONFIG=30
RATE_LIMIT_AUTH=10
```

### Hardening Adicional

#### 1. HTTPS Obrigatório

```python
# main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

#### 2. CORS Restritivo

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dominio.com"],  # Específico
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

#### 3. Headers de Segurança

```python
# middleware.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## 📋 Checklist de Segurança

### Implementado ✅

- [x] Autenticação JWT em todas as rotas Docker
- [x] Rate limiting global
- [x] Error handling com panic recovery
- [x] Request ID para rastreamento
- [x] Logging estruturado
- [x] Validação de entrada
- [x] Proteção contra CORS

### Recomendado para Produção 🔶

- [ ] HTTPS obrigatório
- [ ] Rotação automática de secrets
- [ ] 2FA (Two-Factor Authentication)
- [ ] IP whitelisting
- [ ] Auditoria externa
- [ ] Penetration testing
- [ ] WAF (Web Application Firewall)

---

## 🚀 Exemplo de Uso Seguro

### Frontend (React)

```javascript
// Armazenar token após login
const login = async (username, password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  
  const data = await response.json()
  localStorage.setItem('token', data.access_token)
}

// Usar token em requisições
const getContainers = async () => {
  const token = localStorage.getItem('token')
  
  const response = await fetch('/api/docker-advanced/containers', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  
  if (response.status === 401) {
    // Token expirado - redirecionar para login
    window.location.href = '/login'
    return
  }
  
  return await response.json()
}

// Logout
const logout = () => {
  localStorage.removeItem('token')
  window.location.href = '/login'
}
```

---

## 📞 Suporte e Incidentes

### Reportar Vulnerabilidade

Se encontrar uma vulnerabilidade de segurança:

1. **NÃO** abra issue pública
2. **Envie** email para security@example.com
3. **Inclua** detalhes técnicos
4. **Aguarde** resposta em 48h

### Incidentes de Segurança

Em caso de incidente:

1. **Revogue** todos os tokens
2. **Analise** logs de acesso
3. **Identifique** escopo do incidente
4. **Corrija** vulnerabilidade
5. **Notifique** usuários afetados

---

## 📚 Referências

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security](https://docs.docker.com/engine/security/)

---

**Versão:** 1.0.0  
**Data:** Abril 2026  
**Status:** ✅ Todas as rotas protegidas  
**Nível de Segurança:** 🔒 Alto
