# 📝 Editor de Arquivos - Quick Start

## O que é?

Um editor de código completo integrado à interface web que **salva todos os arquivos diretamente no Telegram** como documentos. Você pode criar, editar e gerenciar arquivos de texto com syntax highlighting profissional, e tudo fica automaticamente armazenado no seu chat do Telegram.

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
# Frontend
cd web/frontend
npm install

# O backend já tem todas as dependências necessárias
```

### 2. Configurar Variáveis de Ambiente

Certifique-se de que seu `.env` tem:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

### 3. Usar o Editor

1. Acesse a interface web
2. Clique no ícone **"Editor de Arquivos"** (documento amarelo/laranja)
3. Clique no **"+"** para criar um novo arquivo
4. Digite o nome (ex: `script.py`) e escolha o tipo
5. Edite o conteúdo no editor Monaco
6. Clique em **"Salvar no Telegram"**
7. Pronto! O arquivo está salvo no Telegram

## ✨ Recursos Principais

- **Monaco Editor** (mesmo do VS Code)
- **Syntax highlighting** para 15+ linguagens
- **Salvar direto no Telegram** como documento
- **Busca de arquivos** por nome
- **Exclusão** de arquivos do Telegram
- **Metadados** (tamanho, data de modificação)

## 📁 Linguagens Suportadas

JavaScript, TypeScript, Python, JSON, HTML, CSS, Markdown, YAML, XML, SQL, Shell Script, e mais!

## 🎯 Casos de Uso

- ✍️ Notas e documentação em Markdown
- 💻 Scripts Python/JavaScript
- ⚙️ Arquivos de configuração JSON/YAML
- 📋 Logs e registros
- 🔧 Snippets de código

## 🔧 Arquitetura

### Backend
- `telegram_storage.py`: Serviço de armazenamento no Telegram
- API REST com FastAPI
- Metadados em `appstore_data/telegram_files_metadata.json`

### Frontend
- `FileEditor.jsx`: Componente React principal
- Monaco Editor para edição
- Interface moderna com TailwindCSS

### API Endpoints
```
GET    /api/editor/files              # Listar arquivos
POST   /api/editor/files              # Criar arquivo
GET    /api/editor/files/{file_id}    # Obter arquivo
PUT    /api/editor/files/{file_id}    # Atualizar arquivo
DELETE /api/editor/files/{file_id}    # Excluir arquivo
GET    /api/editor/files/search/{q}   # Buscar arquivos
```

## 💡 Como Funciona

1. **Criar/Editar**: Você cria ou edita um arquivo no editor web
2. **Salvar**: Ao clicar em "Salvar", o arquivo é enviado para o backend
3. **Upload**: Backend usa a API do Telegram para enviar como documento
4. **Metadados**: Informações são salvas localmente para acesso rápido
5. **Telegram**: Arquivo aparece como documento no seu chat

## 📱 Acesso aos Arquivos

Todos os arquivos salvos aparecem como **documentos no Telegram**. Você pode:
- Baixar do Telegram a qualquer momento
- Compartilhar com outros usuários
- Acessar de qualquer dispositivo
- Fazer backup manual se desejar

## 🔐 Segurança

- Autenticação JWT obrigatória
- Arquivos salvos no chat privado do bot
- Metadados protegidos no servidor
- Validação em todas as operações

## 🎨 Interface

```
┌─────────────────────────────────────────────────────┐
│  Editor de Arquivos                            [+]  │
├─────────────┬───────────────────────────────────────┤
│             │  📄 script.py                    [💾] │
│  📄 Files   │  ┌─────────────────────────────────┐ │
│  ─────────  │  │                                 │ │
│  script.py  │  │  def hello():                   │ │
│  config.yml │  │      print("Hello World!")      │ │
│  notes.md   │  │                                 │ │
│             │  │  hello()                        │ │
│  [Search]   │  │                                 │ │
│             │  └─────────────────────────────────┘ │
│             │                                       │
└─────────────┴───────────────────────────────────────┘
```

## 🚨 Limitações

- Tamanho máximo: 50MB (limite do Telegram)
- Otimizado para arquivos de texto
- Sem histórico de versões (apenas versão atual)
- Sem edição colaborativa em tempo real

## 📚 Documentação Completa

Veja `FILE_EDITOR_GUIDE.md` para documentação detalhada com exemplos, troubleshooting e dicas avançadas.

## 🎉 Pronto!

Agora você tem um editor de código completo com backup automático no Telegram! 🚀
