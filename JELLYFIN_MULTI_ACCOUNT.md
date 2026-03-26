# Suporte a Múltiplas Contas Jellyfin

## Visão Geral

A aplicação agora suporta múltiplas contas Jellyfin simultaneamente, permitindo que você monitore e gerencie conteúdo de vários servidores Jellyfin a partir de uma única instância da aplicação.

## Configuração

### Formato das Variáveis de Ambiente

As variáveis de ambiente do Jellyfin agora aceitam múltiplos valores separados por vírgula:

```env
# Conta única (formato antigo - ainda suportado)
JELLYFIN_URL=http://192.168.1.30:8097
JELLYFIN_USERNAME=usuario
JELLYFIN_PASSWORD=senha
JELLYFIN_API_KEY=api_key

# Múltiplas contas (novo formato)
JELLYFIN_URL=http://192.168.1.30:8097,http://192.168.1.31:8096,http://jellyfin.example.com
JELLYFIN_USERNAME=usuario1,usuario2,usuario3
JELLYFIN_PASSWORD=senha1,senha2,senha3
JELLYFIN_API_KEY=api_key1,api_key2,api_key3
```

### Regras de Configuração

1. **Ordem dos valores**: Os valores devem estar na mesma ordem em todas as variáveis
2. **Valores opcionais**: Se uma conta não tiver username/password, deixe vazio mas mantenha a vírgula
3. **Autenticação**: Cada conta pode usar username/password OU api_key
4. **Compatibilidade**: Configurações de conta única continuam funcionando normalmente

### Exemplos de Configuração

#### Exemplo 1: Duas contas com username/password
```env
JELLYFIN_URL=http://servidor1:8096,http://servidor2:8096
JELLYFIN_USERNAME=admin,user
JELLYFIN_PASSWORD=senha123,senha456
JELLYFIN_API_KEY=,
```

#### Exemplo 2: Duas contas com API keys
```env
JELLYFIN_URL=http://servidor1:8096,http://servidor2:8096
JELLYFIN_USERNAME=,
JELLYFIN_PASSWORD=,
JELLYFIN_API_KEY=abc123def456,xyz789ghi012
```

#### Exemplo 3: Conta mista (username/password + API key)
```env
JELLYFIN_URL=http://servidor1:8096,http://servidor2:8096
JELLYFIN_USERNAME=admin,
JELLYFIN_PASSWORD=senha123,
JELLYFIN_API_KEY=,xyz789ghi012
```

## Funcionalidades

### Notificações
- O sistema monitora todos os servidores configurados
- Notificações incluem informação do servidor de origem quando há múltiplas contas
- Estado de itens conhecidos é mantido separadamente por servidor

### Comandos do Telegram
Todos os comandos existentes funcionam com múltiplas contas:

- `/recent` - Lista itens recentes de todos os servidores
- `/recentes` - Mostra detalhes de itens recentes (inclui servidor de origem)
- `/libraries` - Lista bibliotecas de todos os servidores
- `/status` - Mostra status de todos os servidores configurados

### Web Interface
A interface web também suporta múltiplas contas:
- Itens recentes agregados de todos os servidores
- Bibliotecas de todos os servidores
- Identificação do servidor de origem em cada item
- Imagens, streams e legendas buscadas do servidor correto automaticamente
- Player de vídeo funciona corretamente com conteúdo de qualquer servidor

## Mudanças Técnicas

### Arquivos Modificados

1. **`.env.example`** - Documentação e exemplos de múltiplas contas
2. **`src/core/config.py`** - Parser de múltiplas contas Jellyfin
3. **`src/integrations/jellyfin/manager.py`** - Gerenciamento de múltiplos clientes
4. **`src/integrations/jellyfin/notifier.py`** - Notificações multi-servidor
5. **`src/integrations/telegram/utils.py`** - Compatibilidade com múltiplas contas
6. **`web/backend/main.py`** - API web com suporte multi-conta

### Compatibilidade com Código Existente

O código foi projetado para manter compatibilidade total:

- `jellyfin_manager.client` - Retorna o primeiro cliente (compatibilidade)
- `jellyfin_manager.clients` - Lista de todos os clientes (novo)
- `jellyfin_manager.is_available()` - Verifica se há pelo menos uma conta
- `jellyfin_manager.multi_account_enabled` - Flag indicando múltiplas contas

### Migração de Estado

O sistema detecta automaticamente o formato antigo do arquivo de estado (`jellyfin_notifier_state.json`) e migra para o novo formato que suporta múltiplos servidores.

## Benefícios

1. **Centralização**: Gerencie múltiplos servidores Jellyfin de um único bot
2. **Redundância**: Continue recebendo notificações mesmo se um servidor estiver offline
3. **Organização**: Mantenha conteúdo separado em diferentes servidores
4. **Flexibilidade**: Adicione ou remova servidores sem reconfigurar tudo

## Troubleshooting

### Problema: Notificações duplicadas
**Solução**: Verifique se não há URLs duplicadas na configuração

### Problema: Servidor não aparece
**Solução**: 
- Verifique se a URL está acessível
- Confirme que as credenciais estão corretas
- Verifique os logs para mensagens de erro de autenticação

### Problema: Estado de itens conhecidos perdido após atualização
**Solução**: O sistema migra automaticamente. Se houver problemas, delete o arquivo `jellyfin_notifier_state.json` e reinicie (todos os itens atuais serão marcados como conhecidos)

## Notas de Versão

- **Versão**: v0.0.1.8-alpha
- **Data**: Março 2026
- **Compatibilidade**: Totalmente compatível com configurações existentes
- **Breaking Changes**: Nenhum
