# 📝 Editor de Arquivos com Armazenamento no Telegram

## Visão Geral

O **Editor de Arquivos** é uma funcionalidade completa que permite criar, editar e gerenciar arquivos de texto diretamente através da interface web, com armazenamento automático no Telegram. Todos os arquivos são salvos como documentos no seu chat do Telegram, proporcionando backup automático e acesso de qualquer lugar.

## ✨ Funcionalidades

### 📄 Gerenciamento de Arquivos
- **Criar novos arquivos** com diferentes tipos (texto, código, markdown, JSON, YAML)
- **Editar arquivos** com syntax highlighting automático
- **Salvar arquivos** diretamente no Telegram
- **Excluir arquivos** do Telegram
- **Buscar arquivos** por nome
- **Visualizar metadados** (tamanho, data de criação/modificação)

### 🎨 Editor de Código
- **Monaco Editor** (mesmo editor do VS Code)
- **Syntax highlighting** para múltiplas linguagens
- **Autocompletar** e sugestões inteligentes
- **Minimap** para navegação rápida
- **Word wrap** automático
- **Temas escuros** otimizados

### 💾 Armazenamento no Telegram
- Arquivos salvos como **documentos no Telegram**
- **Backup automático** em nuvem
- **Versionamento** através de atualizações
- **Acesso de qualquer lugar** através do Telegram
- **Metadados persistentes** em arquivo local

## 🚀 Como Usar

### 1. Acessar o Editor

1. Faça login na interface web
2. Clique no ícone **"Editor de Arquivos"** no dock (ícone de documento amarelo/laranja)
3. A janela do editor será aberta

### 2. Criar um Novo Arquivo

1. Clique no botão **"+"** no canto superior direito da barra lateral
2. Digite o **nome do arquivo** (ex: `meu-script.py`, `notas.txt`)
3. Selecione o **tipo de arquivo**:
   - **Texto**: Arquivos de texto simples
   - **Código**: Scripts e código-fonte
   - **Markdown**: Documentação em Markdown
   - **JSON**: Arquivos de configuração JSON
   - **YAML**: Arquivos de configuração YAML
4. Clique em **"Criar"**
5. O arquivo será criado e salvo automaticamente no Telegram

### 3. Editar um Arquivo

1. Na **barra lateral esquerda**, clique no arquivo que deseja editar
2. O conteúdo será carregado no editor
3. Faça suas alterações no editor
4. Clique em **"Salvar no Telegram"** para salvar as mudanças
5. Uma notificação confirmará que o arquivo foi salvo

### 4. Buscar Arquivos

1. Use a **barra de busca** no topo da barra lateral
2. Digite parte do nome do arquivo
3. Pressione **Enter** para buscar
4. Os resultados serão exibidos na lista

### 5. Excluir um Arquivo

1. Passe o mouse sobre o arquivo na lista
2. Clique no ícone de **lixeira** (🗑️)
3. Confirme a exclusão
4. O arquivo será removido do Telegram

## 🎯 Linguagens Suportadas

O editor detecta automaticamente a linguagem baseada na extensão do arquivo:

| Extensão | Linguagem |
|----------|-----------|
| `.js`, `.jsx` | JavaScript |
| `.ts`, `.tsx` | TypeScript |
| `.py` | Python |
| `.json` | JSON |
| `.html` | HTML |
| `.css` | CSS |
| `.md` | Markdown |
| `.yml`, `.yaml` | YAML |
| `.xml` | XML |
| `.sql` | SQL |
| `.sh` | Shell Script |
| `.txt` | Texto Simples |

## 🔧 Configuração Técnica

### Backend

O backend utiliza o serviço `TelegramStorageService` que:

1. **Salva arquivos** usando a API do Telegram Bot (`sendDocument`)
2. **Armazena metadados** localmente em `appstore_data/telegram_files_metadata.json`
3. **Recupera arquivos** usando `getFile` e download direto
4. **Gerencia versões** deletando a mensagem antiga e criando uma nova

### API Endpoints

```
GET    /api/editor/files              # Listar todos os arquivos
POST   /api/editor/files              # Criar novo arquivo
GET    /api/editor/files/{file_id}    # Obter conteúdo de um arquivo
PUT    /api/editor/files/{file_id}    # Atualizar arquivo
DELETE /api/editor/files/{file_id}    # Excluir arquivo
GET    /api/editor/files/search/{query} # Buscar arquivos
```

### Frontend

Componente React com:
- **Monaco Editor** para edição de código
- **Interface responsiva** com sidebar e área de edição
- **Notificações** em tempo real
- **Gerenciamento de estado** local

## 📦 Estrutura de Dados

### Metadata do Arquivo

```json
{
  "file_id": "AgACAgEAAxkBAAIC...",
  "filename": "exemplo.py",
  "file_type": "code",
  "file_size": 1024,
  "created_at": "2024-03-27T12:00:00",
  "updated_at": "2024-03-27T12:30:00",
  "message_id": 12345
}
```

## 🔐 Segurança

- **Autenticação JWT** obrigatória para todos os endpoints
- **Validação de tokens** em cada requisição
- **Armazenamento seguro** no Telegram (privado do bot)
- **Metadados locais** protegidos no servidor

## 💡 Casos de Uso

### 1. Notas e Documentação
Crie e edite notas em Markdown, mantendo tudo sincronizado no Telegram.

### 2. Scripts e Automações
Desenvolva scripts Python, Shell ou JavaScript diretamente na interface web.

### 3. Configurações
Edite arquivos JSON e YAML de configuração com syntax highlighting.

### 4. Logs e Registros
Mantenha logs e registros em arquivos de texto organizados.

### 5. Snippets de Código
Salve trechos de código úteis para referência futura.

## 🎨 Interface

### Barra Lateral
- **Lista de arquivos** com nome, tamanho e data
- **Busca rápida** por nome
- **Botão de criar** arquivo
- **Indicador** de armazenamento no Telegram

### Área do Editor
- **Cabeçalho** com nome do arquivo e última atualização
- **Editor Monaco** com syntax highlighting
- **Botão salvar** destacado
- **Minimap** lateral para navegação

### Notificações
- **Sucesso**: Verde com ícone de check
- **Erro**: Vermelho com ícone de alerta
- **Auto-dismiss**: Desaparecem após 3 segundos

## 🚨 Limitações

1. **Tamanho máximo**: Telegram limita documentos a 50MB
2. **Tipos de arquivo**: Otimizado para arquivos de texto
3. **Versionamento**: Não mantém histórico de versões (apenas versão atual)
4. **Concorrência**: Não há lock de edição simultânea

## 🔄 Fluxo de Trabalho Recomendado

1. **Criar** arquivo com nome descritivo
2. **Editar** conteúdo no Monaco Editor
3. **Salvar** frequentemente (Ctrl+S ou botão)
4. **Verificar** no Telegram que o arquivo foi salvo
5. **Buscar** arquivos quando necessário
6. **Excluir** arquivos obsoletos

## 📱 Acesso via Telegram

Todos os arquivos salvos aparecem como documentos no seu chat do Telegram. Você pode:

- **Baixar** arquivos diretamente do Telegram
- **Compartilhar** com outros usuários
- **Fazer backup** manual se necessário
- **Visualizar** metadados no Telegram

## 🛠️ Instalação

### Dependências do Backend

Já incluídas no `requirements.txt`:
```
requests
python-dotenv
fastapi
```

### Dependências do Frontend

Adicione ao `package.json`:
```json
"@monaco-editor/react": "^4.6.0"
```

Instale com:
```bash
cd web/frontend
npm install
```

### Variáveis de Ambiente

Certifique-se de que estão configuradas no `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

## 🎓 Dicas e Truques

1. **Atalhos do Editor**:
   - `Ctrl+S`: Salvar arquivo
   - `Ctrl+F`: Buscar no arquivo
   - `Ctrl+H`: Buscar e substituir
   - `Ctrl+/`: Comentar/descomentar linha

2. **Organização**:
   - Use nomes descritivos para arquivos
   - Adicione extensões corretas para syntax highlighting
   - Crie pastas virtuais usando prefixos (ex: `config/app.json`)

3. **Performance**:
   - Arquivos grandes podem demorar para carregar
   - Salve com frequência para evitar perda de dados
   - Use a busca para encontrar arquivos rapidamente

## 🐛 Solução de Problemas

### Arquivo não salva
- Verifique se o token do Telegram está configurado
- Confirme que o chat_id está correto
- Veja os logs do backend para erros

### Editor não carrega
- Limpe o cache do navegador
- Verifique se o Monaco Editor foi instalado (`npm install`)
- Veja o console do navegador para erros

### Arquivo não aparece na lista
- Aguarde alguns segundos e recarregue
- Verifique se o arquivo foi realmente salvo no Telegram
- Confira o arquivo de metadados em `appstore_data/`

## 📊 Monitoramento

Os logs do backend mostrarão:
- Arquivos salvos no Telegram
- Erros de upload/download
- Operações de CRUD nos arquivos

Exemplo de log:
```
INFO: File saved to Telegram: exemplo.py (file_id: AgACAgEAAxkBAAIC...)
INFO: File deleted from Telegram: AgACAgEAAxkBAAIC...
```

## 🎉 Conclusão

O Editor de Arquivos com armazenamento no Telegram oferece uma solução única e conveniente para gerenciar arquivos de texto, combinando a facilidade de um editor web moderno com o backup automático e a acessibilidade do Telegram.

**Principais Vantagens**:
- ✅ Backup automático em nuvem
- ✅ Interface moderna e intuitiva
- ✅ Syntax highlighting profissional
- ✅ Acesso de qualquer lugar
- ✅ Integração perfeita com o Telegram
