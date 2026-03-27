# Guia de Autenticação da Interface Web

## Visão Geral

A interface web do Telegram Torrent Manager agora possui um sistema completo de autenticação baseado em JWT (JSON Web Tokens) para proteger todas as rotas da API.

## Características

- **Autenticação JWT**: Tokens seguros com expiração configurável
- **Proteção de Rotas**: Todas as rotas da API (exceto login) requerem autenticação
- **Hash de Senhas**: Senhas armazenadas usando bcrypt para máxima segurança
- **Configuração Flexível**: Fácil configuração via variáveis de ambiente

## Configuração Inicial

### 1. Gerar Hash da Senha

Você tem três opções para gerar o hash da senha:

#### Opção A: Usando o endpoint da API
```bash
# Inicie o servidor primeiro
cd web/backend
python main.py

# Em outro terminal, gere o hash
curl -X POST http://localhost:8000/api/auth/generate-hash \
  -H "Content-Type: application/json" \
  -d '{"password":"sua_senha_segura"}'
```

#### Opção B: Usando Python diretamente
```bash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('sua_senha_segura'))"
```

#### Opção C: Usando o módulo auth
```bash
cd web/backend
python -c "from auth import generate_password_hash; print(generate_password_hash('sua_senha_segura'))"
```

### 2. Configurar Variáveis de Ambiente

Edite seu arquivo `.env` e adicione:

```bash
# Nome de usuário (padrão: admin)
WEB_USERNAME=admin

# Hash da senha gerado no passo anterior
WEB_PASSWORD_HASH=$2b$12$exemplo_de_hash_bcrypt_aqui

# Chave secreta para JWT (IMPORTANTE: mude em produção!)
JWT_SECRET_KEY=sua-chave-secreta-super-segura-aqui

# Tempo de expiração do token em minutos (padrão: 1440 = 24 horas)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. Gerar Chave Secreta JWT

Para produção, gere uma chave secreta forte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Uso da API

### Login

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "sua_senha"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Usando o Token

Inclua o token no header `Authorization` de todas as requisições:

```bash
curl -H "Authorization: Bearer seu_token_aqui" \
  http://localhost:8000/api/torrents
```

### Verificar Autenticação

**Endpoint:** `GET /api/auth/verify`

```bash
curl -H "Authorization: Bearer seu_token_aqui" \
  http://localhost:8000/api/auth/verify
```

**Response:**
```json
{
  "authenticated": true,
  "username": "admin"
}
```

## Rotas Protegidas

Todas as seguintes rotas agora requerem autenticação:

### Sistema
- `GET /api/system/status`

### Torrents
- `GET /api/torrents`
- `POST /api/torrents/add`
- `POST /api/torrents/{hash}/pause`
- `POST /api/torrents/{hash}/resume`
- `DELETE /api/torrents/{hash}`

### Jellyfin
- `GET /api/jellyfin/libraries`
- `GET /api/jellyfin/recent`
- `GET /api/jellyfin/items/{item_id}`
- `GET /api/jellyfin/shows/{series_id}/seasons`
- `GET /api/jellyfin/shows/{series_id}/episodes`
- `GET /api/jellyfin/image/{item_id}`
- `GET /api/jellyfin/playback-info/{item_id}`
- `GET /api/jellyfin/subtitles/{item_id}/{media_source_id}/{index}`
- `GET /api/jellyfin/stream/{item_id}`

### Docker
- `GET /api/docker/containers`
- `POST /api/docker/containers/{name}/start`
- `POST /api/docker/containers/{name}/stop`

### AppStore
- `GET /api/appstore/categories`
- `GET /api/appstore/apps`
- `GET /api/appstore/apps/{app_id}`
- `POST /api/appstore/apps/{app_id}/install`
- `POST /api/appstore/apps/{app_id}/uninstall`

## Rotas Públicas

As seguintes rotas **não** requerem autenticação:

- `GET /` - Status da API
- `POST /api/auth/login` - Login
- `POST /api/auth/generate-hash` - Gerar hash de senha (utilitário)

## Exemplo de Integração com Frontend

### JavaScript/Fetch

```javascript
// Login
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Salvar token
    localStorage.setItem('token', data.access_token);
    return data;
  } else {
    throw new Error('Login falhou');
  }
}

// Fazer requisição autenticada
async function getTorrents() {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/torrents', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    // Token expirado, fazer login novamente
    throw new Error('Não autenticado');
  }
  
  return await response.json();
}
```

### Axios

```javascript
import axios from 'axios';

// Configurar interceptor
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Login
async function login(username, password) {
  const response = await axios.post('/api/auth/login', {
    username,
    password,
  });
  
  localStorage.setItem('token', response.data.access_token);
  return response.data;
}

// Usar API normalmente
const torrents = await axios.get('/api/torrents');
```

## Segurança

### Recomendações de Produção

1. **Sempre use HTTPS** em produção
2. **Mude a chave JWT_SECRET_KEY** para um valor único e seguro
3. **Use senhas fortes** e gere o hash corretamente
4. **Configure CORS** adequadamente para seu domínio
5. **Monitore tokens expirados** e implemente refresh tokens se necessário
6. **Considere rate limiting** para prevenir ataques de força bruta

### Primeira Execução (Desenvolvimento)

Se você não configurar `WEB_PASSWORD_HASH`, o sistema usará a senha padrão `admin` automaticamente. **Isso é apenas para desenvolvimento e NUNCA deve ser usado em produção!**

## Troubleshooting

### Erro 401 Unauthorized

- Verifique se o token está sendo enviado corretamente no header
- Verifique se o token não expirou
- Tente fazer login novamente

### Erro ao gerar hash

- Certifique-se de que as dependências estão instaladas: `pip install -r requirements.txt`
- Verifique se o bcrypt está instalado corretamente

### Token não funciona após reiniciar servidor

- Se você mudou a `JWT_SECRET_KEY`, todos os tokens antigos ficam inválidos
- Faça login novamente para obter um novo token

## Instalação de Dependências

```bash
cd web/backend
pip install -r requirements.txt
```

As novas dependências incluem:
- `passlib[bcrypt]` - Para hash de senhas
- `python-jose[cryptography]` - Para JWT
- `bcrypt` - Algoritmo de hash

## Migração de Versões Anteriores

Se você está atualizando de uma versão sem autenticação:

1. Instale as novas dependências
2. Configure as variáveis de ambiente de autenticação
3. Atualize seu frontend para incluir o fluxo de login
4. Teste em ambiente de desenvolvimento antes de produção

## Suporte

Para problemas ou dúvidas, abra uma issue no repositório do projeto.
