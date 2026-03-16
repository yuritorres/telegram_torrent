# 🚀 Guia Rápido - WhatsApp WAHA

## ⚡ Início Rápido (5 minutos)

### 1️⃣ Configurar Variáveis de Ambiente

Edite o arquivo `.env` e adicione seus números autorizados:

```bash
# Números autorizados (com código do país)
AUTHORIZED_WHATSAPP_NUMBERS=5511999999999,5511888888888
```

### 2️⃣ Iniciar Serviços

```bash
# Subir todos os containers
docker-compose up -d

# Aguardar inicialização (30-60 segundos)
docker-compose logs -f waha
```

### 3️⃣ Autenticar WhatsApp

**Opção A: Dashboard (Mais Fácil)**

1. Abra: http://localhost:3000/dashboard
2. Login: `admin` / `admin123`
3. Clique em "Start Session"
4. Escaneie o QR Code com WhatsApp

**Opção B: Swagger API**

1. Abra: http://localhost:3000/
2. Login: `admin` / `swagger123`
3. Execute `POST /api/sessions`:
   ```json
   {"name": "default"}
   ```
4. Execute `GET /api/screenshot` para ver QR Code
5. Escaneie com WhatsApp

### 4️⃣ Testar Envio

```python
# Executar exemplo
python whatsapp_example.py
```

Ou via curl:

```bash
curl -X POST http://localhost:3000/api/sendText \
  -H "X-Api-Key: local-dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "5511999999999@c.us",
    "text": "Olá do bot!"
  }'
```

## 📱 Formato de Números

- **Contatos**: `5511999999999@c.us`
- **Grupos**: `5511999999999@g.us`
- Sempre use código do país (55 para Brasil)

## 🔍 Verificar Status

```bash
# Status da API
curl http://localhost:3000/api/health

# Status da sessão
curl -H "X-Api-Key: local-dev-key-123" \
     http://localhost:3000/api/sessions/default
```

## 🎯 Próximos Passos

1. ✅ Configure números autorizados em `.env`
2. ✅ Altere senhas padrão para produção
3. ✅ Teste envio de mensagens
4. ✅ Configure webhooks (opcional)
5. ✅ Integre com seus comandos existentes

## 📚 Documentação Completa

Veja `README_WHATSAPP.md` para documentação detalhada.

## ⚠️ Importante

- Mantenha a API Key segura
- Use HTTPS em produção
- Respeite limites do WhatsApp
- Faça backup regular do PostgreSQL

## 🆘 Problemas Comuns

**QR Code não aparece:**
```bash
docker-compose restart waha
```

**Sessão desconectada:**
```bash
# Deletar e recriar sessão
curl -X DELETE -H "X-Api-Key: local-dev-key-123" \
     http://localhost:3000/api/sessions/default

# Iniciar nova sessão
curl -X POST -H "X-Api-Key: local-dev-key-123" \
     http://localhost:3000/api/sessions \
     -d '{"name":"default"}'
```

**Mensagens não enviam:**
- Verifique se a sessão está ativa
- Confirme formato do chat_id (número@c.us)
- Verifique logs: `docker-compose logs waha`

## 📞 Suporte

- [Documentação WAHA](https://waha.devlike.pro/)
- [GitHub Issues](https://github.com/devlikeapro/waha/issues)
- [Exemplos](https://github.com/devlikeapro/waha/tree/core/examples)
