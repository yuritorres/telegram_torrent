# Problema de Áudio EAC3 no Jellyfin Web Player

## 🔴 Problema Identificado

**Causa Raiz**: Todos os vídeos no servidor Jellyfin usam codec de áudio **EAC3 (Dolby Digital Plus)**, que **NÃO é suportado nativamente** pelos navegadores web.

### Navegadores Suportam Apenas:
- ✅ AAC
- ✅ MP3
- ✅ Opus
- ✅ Vorbis
- ❌ **EAC3** (Dolby Digital Plus)
- ❌ AC3 (Dolby Digital)
- ❌ DTS

### Status Atual:
- ✅ **Vídeo**: Reproduz perfeitamente
- ❌ **Áudio**: Não reproduz (codec incompatível)
- ✅ **Autenticação**: Funcionando
- ✅ **Streaming**: Funcionando

---

## 💡 Soluções Disponíveis

### Opção 1: Habilitar Transcodificação no Jellyfin Server (Recomendado)

**Passos:**

1. Acesse o Jellyfin Dashboard: `http://192.168.1.30:8097` ou `http://192.168.1.25:8096`
2. Vá em **Dashboard** → **Playback** → **Transcoding**
3. Verifique se **FFmpeg** está instalado e configurado
4. Habilite as seguintes opções:
   - ✅ "Allow audio playback that requires transcoding"
   - ✅ "Allow video playback that requires transcoding"
5. Configure o **Hardware Acceleration** (se disponível):
   - Intel QuickSync
   - NVIDIA NVENC
   - AMD AMF
   - VAAPI (Linux)
6. Salve as configurações
7. Reinicie o servidor Jellyfin

**Vantagens:**
- ✅ Funciona automaticamente para todos os vídeos
- ✅ Não precisa reconverter arquivos
- ✅ Transcodificação em tempo real

**Desvantagens:**
- ⚠️ Requer CPU/GPU para transcodificar
- ⚠️ Pode aumentar latência inicial

---

### Opção 2: Reconverter Arquivos de Mídia

Use **FFmpeg** para reconverter os arquivos com áudio AAC:

```bash
# Reconverter um arquivo (mantém vídeo, converte áudio)
ffmpeg -i input.mkv -c:v copy -c:a aac -b:a 192k output.mkv

# Reconverter em lote (todos os MKV em uma pasta)
for file in *.mkv; do
  ffmpeg -i "$file" -c:v copy -c:a aac -b:a 192k "converted_${file}"
done
```

**Vantagens:**
- ✅ Não requer transcodificação em tempo real
- ✅ Menor uso de CPU/GPU no servidor
- ✅ Reprodução instantânea

**Desvantagens:**
- ❌ Precisa reconverter todos os arquivos
- ❌ Ocupa espaço em disco durante conversão
- ❌ Processo demorado para bibliotecas grandes

---

### Opção 3: Usar Aplicativo Nativo Jellyfin

Os aplicativos nativos do Jellyfin suportam EAC3 diretamente:

- **Windows**: Jellyfin Media Player
- **Android**: Jellyfin for Android
- **iOS**: Jellyfin Mobile
- **Android TV**: Jellyfin for Android TV
- **Apple TV**: Swiftfin

**Vantagens:**
- ✅ Suporte nativo a EAC3
- ✅ Melhor performance
- ✅ Mais recursos

**Desvantagens:**
- ❌ Precisa instalar aplicativo
- ❌ Não funciona no navegador web

---

## 🔧 Verificação de Codec de Áudio

Para verificar o codec de áudio de um arquivo:

```bash
# Usando FFprobe
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 video.mkv

# Usando MediaInfo
mediainfo video.mkv | grep "Audio"
```

---

## 📊 Comparação de Soluções

| Solução | Facilidade | Custo CPU | Qualidade | Tempo |
|---------|-----------|-----------|-----------|-------|
| Transcodificação Server | ⭐⭐⭐⭐⭐ | Alto | Boa | Imediato |
| Reconverter Arquivos | ⭐⭐⭐ | Médio | Excelente | Horas/Dias |
| App Nativo | ⭐⭐⭐⭐⭐ | Nenhum | Perfeita | Imediato |

---

## 🎯 Recomendação Final

**Para uso imediato no navegador:**
1. Habilite transcodificação no Jellyfin Server (Opção 1)
2. Configure hardware acceleration se disponível
3. Teste a reprodução no navegador

**Para melhor qualidade a longo prazo:**
1. Reconverta gradualmente os arquivos para AAC (Opção 2)
2. Use scripts automatizados para processar em lote
3. Mantenha backups dos originais

**Para melhor experiência:**
1. Use o aplicativo nativo Jellyfin (Opção 3)
2. Suporte completo a todos os codecs
3. Melhor performance e recursos

---

## 📝 Notas Técnicas

- O código da aplicação web está **funcionando corretamente**
- A limitação é do **codec de áudio dos arquivos**, não do código
- Navegadores web têm suporte limitado a codecs por questões de licenciamento
- EAC3 requer licença Dolby, por isso não é suportado nativamente
