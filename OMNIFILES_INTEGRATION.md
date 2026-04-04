# Integração Crom OmniFiles no Telegram Torrent

## ✅ Integração Completa

O **Crom OmniFiles** foi completamente integrado ao projeto Telegram Torrent, substituindo o gerenciador de arquivos anterior.

## 📁 Estrutura de Arquivos Copiados

Todos os arquivos do crom-omnifiles foram copiados para:
```
web/frontend/src/omnifiles/
├── providers/           # Provedores de armazenamento (IndexedDB, Google Drive, S3, Local FS)
├── hooks/              # Hooks customizados (useFileSystem, useSelection, useDragDrop, etc.)
├── context/            # Contextos React (FileSystem, Clipboard, Modal)
├── components/         # Componentes UI (core, layout, modals, settings)
├── db/                 # Configuração Dexie.js (IndexedDB)
├── locales/            # Traduções (pt-BR, en)
├── constants/          # Constantes e configurações
├── config/             # Configurações (Google OAuth)
├── utils/              # Utilitários
├── workers/            # Web Workers (fileProcessor.worker.js)
├── i18n.js            # Configuração i18next
└── OmniFilesApp.jsx   # Componente principal
```

## 🔧 Modificações Realizadas

### 1. **package.json**
Adicionadas as seguintes dependências:
- `@aws-sdk/client-s3` - Integração AWS S3
- `dexie` - IndexedDB wrapper
- `dompurify` - Sanitização HTML/Markdown
- `file-saver` - Download de arquivos
- `framer-motion` - Animações
- `i18next` + `react-i18next` - Internacionalização
- `i18next-browser-languagedetector` - Detecção de idioma
- `jszip` - Compressão ZIP
- `react-hot-toast` - Notificações toast
- `react-use-measure` - Medições de componentes
- `react-window` - Virtualização de listas

### 2. **FileManagerApp.jsx**
Completamente substituído para integrar o OmniFiles:
```javascript
import OmniFilesApp from '../../omnifiles/OmniFilesApp'
import { Toaster } from 'react-hot-toast'
import { ModalProvider } from '../../omnifiles/context/ModalContext'
```

## ✨ Funcionalidades Disponíveis

### Armazenamento Multi-Provider
- ✅ **Navegador Local** - IndexedDB (Dexie.js), funciona offline
- ✅ **Sistema de Ficheiros** - File System Access API
- ✅ **Google Drive** - OAuth 2.0 completo
- ✅ **AWS S3** - Integração cloud
- 🔜 **Dropbox** - Em desenvolvimento

### Gerenciamento de Arquivos
- ✅ Criar, renomear e excluir pastas/arquivos
- ✅ Upload de arquivos e pastas (recursivo)
- ✅ Download individual e em lote (ZIP)
- ✅ Copiar/Colar e Recortar/Colar (Ctrl+C, Ctrl+X, Ctrl+V)
- ✅ Mover e Copiar entre providers
- ✅ Lixeira com restauração
- ✅ Favoritos (estrelar arquivos)
- ✅ Arquivos recentes

### Visualização
- ✅ **Modo Grade** - Cards visuais
- ✅ **Modo Lista** - Tabela ordenável
- ✅ **Painel de Detalhes** - Informações detalhadas
- ✅ **Preview de Arquivos** - Texto, Markdown, imagens, PDFs, vídeos, áudio
- ✅ **Listas Virtualizadas** - Performance com milhares de arquivos

### Seleção Avançada
- ✅ Checkboxes para seleção rápida
- ✅ Seleção múltipla com Ctrl+Click
- ✅ Seleção em range com Shift+Click
- ✅ Drag Selection (arrastar para selecionar)
- ✅ Long Press para dispositivos touch

### Organização
- ✅ Sistema de Tags com cores customizáveis
- ✅ Workspaces com múltiplas conexões
- ✅ Busca por nome de arquivo
- ✅ Ordenação por nome, tipo, tamanho e data

### Interface
- ✅ Tema dark moderno com glassmorphism
- ✅ Internacionalização (Português BR e Inglês)
- ✅ Layout responsivo
- ✅ Atalhos de teclado (Ctrl+B sidebar, Ctrl+C/X/V clipboard)
- ✅ Sistema de Toasts para feedback
- ✅ Breadcrumb navigation com histórico
- ✅ Menu de contexto completo (botão direito)

### Segurança
- ✅ Sanitização de HTML/Markdown via DOMPurify
- ✅ Tokens OAuth gerenciados sem exposição
- ✅ Arquitetura Provider isolada

## 🚀 Como Usar

### Instalação de Dependências
```bash
cd web/frontend
npm install
```

### Desenvolvimento
```bash
npm run dev
```

### Build de Produção
```bash
npm run build
```

## 🔑 Configuração Google Drive (Opcional)

Para habilitar a integração com Google Drive:

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
2. Ative a Google Drive API
3. Configure OAuth 2.0 credentials
4. Crie um arquivo `.env` em `web/frontend/`:
```env
VITE_GOOGLE_CLIENT_ID=seu-google-client-id
```

## 📝 Atalhos de Teclado

- `Ctrl+B` - Toggle sidebar
- `Ctrl+C` - Copiar arquivos selecionados
- `Ctrl+X` - Recortar arquivos selecionados
- `Ctrl+V` - Colar arquivos
- `Shift+Click` - Seleção em range
- `Ctrl+Click` - Seleção múltipla

## 🎨 Personalização

O OmniFiles usa Tailwind CSS e pode ser personalizado através do `tailwind.config.js` existente no projeto.

## 📦 Estrutura de Dados

### IndexedDB (Dexie.js)
```javascript
workspaces: {
  id, name, type, color, connections
}

files: {
  id, parentId, workspaceId, name, type, size, date,
  isStarred, tags, deletedAt, content
}

tags: {
  id, name, color
}
```

## 🔄 Migração do Gerenciador Anterior

O gerenciador de arquivos anterior foi **completamente substituído**. Todas as funcionalidades antigas foram migradas para o OmniFiles com melhorias significativas:

- ❌ Gerenciador simples com backend API
- ✅ Gerenciador completo multi-provider com suporte offline

## 🐛 Troubleshooting

### Erro: "Module not found"
Execute `npm install` no diretório `web/frontend/`

### Erro: Google Drive não conecta
Verifique se o `VITE_GOOGLE_CLIENT_ID` está configurado corretamente no `.env`

### Performance lenta com muitos arquivos
O OmniFiles usa virtualização (react-window) automaticamente para listas grandes

## 📚 Documentação Adicional

- [Crom OmniFiles README](https://github.com/MrJc01/crom-omnifiles)
- [Dexie.js Documentation](https://dexie.org/)
- [Google Drive API](https://developers.google.com/drive)

## 👨‍💻 Créditos

**Crom OmniFiles** desenvolvido por **Juan Cândido / Crom.Run**
Integrado ao **Telegram Torrent** em 03/04/2026

## 📄 Licença

O código do OmniFiles é Source Available. Para uso comercial, entre em contato: mrj.crom@gmail.com
