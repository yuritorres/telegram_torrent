# Funcionalidade YouTube Downloader

Este documento descreve como configurar e usar a funcionalidade de download de vídeos do YouTube no bot do Telegram.

## 📋 Pré-requisitos

### Instalação das Dependências

Instale as dependências necessárias executando:

```bash
pip install -r requirements_youtube.txt
```

Ou instale manualmente:

```bash
pip install yt-dlp>=2023.12.30 pytube>=15.0.0 requests>=2.31.0 aiofiles>=23.2.1
```

### Configuração do Diretório de Downloads

Certifique-se de que o diretório `downloads` existe no diretório raiz do projeto:

```bash
mkdir downloads
```

## 🚀 Como Usar

### Comando /youtube

1. **Via comando direto:**
   ```
   /youtube
   ```
   O bot responderá com instruções sobre como usar.

2. **Via botão do teclado:**
   - Clique no botão "🎥 YouTube" no teclado principal

3. **Enviando URL diretamente:**
   - Envie qualquer URL do YouTube diretamente no chat
   - O bot detectará automaticamente e iniciará o download

### URLs Suportadas

O bot suporta os seguintes formatos de URL do YouTube:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`

## ⚙️ Configurações

### Variáveis de Ambiente (Opcionais)

Adicione ao seu arquivo `.env`:

```env
# Remove arquivos após enviar para o Telegram (padrão: True)
REMOVE_AFTER_SEND=True
```

### Limitações

- **Tamanho máximo:** 50MB (limitação do Telegram)
- **Timeout:** 10 minutos por download
- **Formatos:** MP4 (vídeo) com melhor qualidade disponível

## 🔧 Funcionalidades

### Informações do Vídeo
Antes do download, o bot exibe:
- 📺 Título do vídeo
- 👤 Nome do canal
- ⏱ Duração
- 📊 Número de visualizações
- 📅 Data de publicação

### Progresso do Download
- 🔍 Obtenção de informações
- 📥 Progresso do download (atualizado a cada 10 segundos)
- ✅ Confirmação de conclusão
- ❌ Tratamento de erros

### Tratamento de Erros
- URLs inválidas
- Vídeos muito grandes (>50MB)
- Falhas de rede
- Timeouts
- Vídeos privados ou indisponíveis

## 🐛 Solução de Problemas

### Erro: "Módulo não encontrado"
```bash
pip install yt-dlp pytube
```

### Erro: "Não foi possível obter informações do vídeo"
- Verifique se a URL está correta
- Teste se o vídeo está disponível publicamente
- Verifique sua conexão com a internet

### Erro: "Vídeo muito grande"
- O Telegram limita arquivos a 50MB
- Considere usar um serviço externo para vídeos maiores

### Erro de Timeout
- Downloads são limitados a 10 minutos
- Vídeos muito longos podem exceder este limite

## 📝 Logs

Os logs do sistema incluem:
- Início e fim de downloads
- Erros de processamento
- Informações de arquivos enviados/removidos

Verifique os logs para diagnosticar problemas.

## 🔄 Atualizações

Para manter o yt-dlp atualizado (recomendado):

```bash
pip install --upgrade yt-dlp
```

## ⚠️ Avisos Legais

- Respeite os direitos autorais
- Use apenas para conteúdo que você tem permissão para baixar
- Verifique os termos de serviço do YouTube
- Este bot é apenas para uso pessoal/educacional