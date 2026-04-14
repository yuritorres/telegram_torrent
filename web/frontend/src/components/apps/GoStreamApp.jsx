import React, { useState, useEffect, useCallback } from 'react'
import { 
  Play, 
  Pause, 
  Trash2, 
  Plus, 
  Film, 
  HardDrive, 
  Zap,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
  Search,
  Clock,
  FileVideo,
  ExternalLink,
  Download
} from 'lucide-react'
import { useNotification } from '../../context/NotificationContext'
import axios from '../../utils/axios'

// API base path for GoStream endpoints
const API_BASE = '/api'

const GoStreamApp = () => {
  const { showNotification } = useNotification()
  
  // State
  const [torrents, setTorrents] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isAvailable, setIsAvailable] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [magnetLink, setMagnetLink] = useState('')
  const [selectedTorrent, setSelectedTorrent] = useState(null)
  const [streamableFiles, setStreamableFiles] = useState([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentStream, setCurrentStream] = useState(null)
  const [cacheStats, setCacheStats] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Check GoStream status
  const checkStatus = useCallback(async () => {
    try {
      const resp = await axios.get(`${API_BASE}/gostream/status`)
      const data = resp.data
      setIsAvailable(data.available && data.enabled)
    } catch (e) {
      setIsAvailable(false)
    }
  }, [])

  // Load torrents
  const loadTorrents = useCallback(async () => {
    if (!isAvailable) return
    
    setIsLoading(true)
    try {
      const resp = await axios.get(`${API_BASE}/gostream/torrents`)
      const data = resp.data
      if (data.success) {
        setTorrents(data.torrents || [])
      }
    } catch (e) {
      showNotification('Erro ao carregar torrents', 'error')
    } finally {
      setIsLoading(false)
    }
  }, [isAvailable])

  // Load cache stats
  const loadCacheStats = useCallback(async () => {
    if (!isAvailable) return
    
    try {
      const resp = await axios.get(`${API_BASE}/gostream/cache/stats`)
      const data = resp.data
      if (data.success) {
        setCacheStats(data.stats)
      }
    } catch (e) {
      // Silently fail
    }
  }, [isAvailable])

  // Initial load
  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Check every 30s
    return () => clearInterval(interval)
  }, [checkStatus])

  useEffect(() => {
    if (isAvailable) {
      loadTorrents()
      loadCacheStats()
      
      // Auto-refresh every 5 seconds
      const interval = setInterval(() => {
        loadTorrents()
        loadCacheStats()
      }, 5000)
      
      return () => clearInterval(interval)
    }
  }, [isAvailable, loadTorrents, loadCacheStats])

  // Add torrent
  const handleAddTorrent = async (e) => {
    e.preventDefault()
    if (!magnetLink.trim()) return

    setIsLoading(true)
    try {
      const resp = await axios.post(`${API_BASE}/gostream/torrents/add?magnet_link=${encodeURIComponent(magnetLink)}`)
      const data = resp.data
      
      if (data.success) {
        showNotification('Torrent adicionado com sucesso!', 'success')
        setMagnetLink('')
        setShowAddModal(false)
        loadTorrents()
      } else {
        showNotification('Erro ao adicionar torrent', 'error')
      }
    } catch (e) {
      showNotification('Erro ao adicionar torrent', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  // Remove torrent
  const handleRemoveTorrent = async (infoHash) => {
    if (!confirm('Tem certeza que deseja remover este torrent?')) return

    try {
      const resp = await axios.delete(`${API_BASE}/gostream/torrents/${infoHash}?delete_files=false`)
      const data = resp.data
      
      if (data.success) {
        showNotification('Torrent removido', 'success')
        loadTorrents()
        if (selectedTorrent?.info_hash === infoHash) {
          setSelectedTorrent(null)
          setStreamableFiles([])
        }
      }
    } catch (e) {
      showNotification('Erro ao remover torrent', 'error')
    }
  }

  // Set priority mode
  const handleSetPriority = async (infoHash, enabled) => {
    try {
      const resp = await axios.post(`${API_BASE}/gostream/torrents/${infoHash}/priority?enabled=${enabled}`)
      const data = resp.data
      
      if (data.success) {
        showNotification(`Priority mode ${enabled ? 'ativado' : 'desativado'}`, 'success')
        loadTorrents()
      }
    } catch (e) {
      showNotification('Erro ao configurar priority mode', 'error')
    }
  }

  // Load streamable files
  const loadStreamableFiles = async (infoHash) => {
    try {
      const resp = await axios.get(`${API_BASE}/gostream/torrents/${infoHash}`)
      const data = resp.data
      
      if (data.success) {
        setStreamableFiles(data.streamable_files || [])
      }
    } catch (e) {
      console.error('Error loading streamable files:', e)
    }
  }

  // Select torrent
  const handleSelectTorrent = (torrent) => {
    setSelectedTorrent(torrent)
    loadStreamableFiles(torrent.info_hash)
    
    // Enable priority mode when selecting
    if (!torrent.is_priority) {
      handleSetPriority(torrent.info_hash, true)
    }
  }

  // Play stream
  const handlePlay = (file) => {
    setCurrentStream(file)
    setIsPlaying(true)
  }

  // Stop stream
  const handleStop = () => {
    setIsPlaying(false)
    setCurrentStream(null)
  }

  // Format size
  const formatSize = (bytes) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  // Format speed
  const formatSpeed = (bytesPerSec) => {
    if (!bytesPerSec) return '0 KB/s'
    if (bytesPerSec < 1024) return `${bytesPerSec} B/s`
    return `${(bytesPerSec / 1024).toFixed(1)} KB/s`
  }

  // Filter torrents
  const filteredTorrents = torrents.filter(t => 
    t.name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Not available state
  if (!isAvailable) {
    return (
      <div className="h-full flex flex-col p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Film className="w-8 h-8 text-cyan-400" />
            GoStream - Streaming de Torrents
          </h1>
        </div>
        
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center bg-white/5 rounded-2xl p-8 border border-white/10">
            <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">GoStream não disponível</h2>
            <p className="text-gray-400 mb-4 max-w-md">
              O GoStream BitTorrent Streaming Engine não está rodando ou não está habilitado.
            </p>
            <div className="text-sm text-gray-500">
              <p>Para habilitar:</p>
              <ol className="text-left mt-2 space-y-1">
                <li>1. Configure GOSTREAM_ENABLED=true no .env</li>
                <li>2. Reinicie o bot principal (main.py)</li>
                <li>3. Aguarde a inicialização do GoStream</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col p-6 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Film className="w-8 h-8 text-cyan-400" />
          GoStream - Streaming de Torrents
        </h1>
        
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar torrents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400"
            />
          </div>
          
          {/* Add button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white font-medium transition-colors"
          >
            <Plus className="w-5 h-5" />
            Adicionar Magnet
          </button>
          
          {/* Refresh */}
          <button
            onClick={loadTorrents}
            disabled={isLoading}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats */}
      {cacheStats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 mb-1">
              <HardDrive className="w-4 h-4" />
              <span className="text-sm">Cache RAM</span>
            </div>
            <p className="text-xl font-semibold text-white">
              {((cacheStats.current_size || 0) / 1024 / 1024).toFixed(1)} MB
            </p>
            <p className="text-xs text-gray-500">
              de {((cacheStats.total_budget || 0) / 1024 / 1024).toFixed(0)} MB
            </p>
          </div>
          
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 mb-1">
              <Zap className="w-4 h-4" />
              <span className="text-sm">Hit Rate</span>
            </div>
            <p className="text-xl font-semibold text-white">
              {((cacheStats.hit_rate || 0) * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500">
              eficiência do cache
            </p>
          </div>
          
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 mb-1">
              <FileVideo className="w-4 h-4" />
              <span className="text-sm">Torrents</span>
            </div>
            <p className="text-xl font-semibold text-white">{torrents.length}</p>
            <p className="text-xs text-gray-500">
              ativos no GoStream
            </p>
          </div>
          
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-sm">Status</span>
            </div>
            <p className="text-xl font-semibold text-green-400">Online</p>
            <p className="text-xs text-gray-500">
              API: 8090
            </p>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Torrent list */}
        <div className="flex-1 bg-white/5 rounded-xl border border-white/10 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-lg font-semibold text-white">Torrents</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {filteredTorrents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Film className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Nenhum torrent encontrado</p>
                <p className="text-sm mt-1">Adicione um magnet link para começar</p>
              </div>
            ) : (
              filteredTorrents.map((torrent) => (
                <div
                  key={torrent.info_hash}
                  onClick={() => handleSelectTorrent(torrent)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedTorrent?.info_hash === torrent.info_hash
                      ? 'bg-cyan-500/20 border-cyan-500/50'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-white truncate">
                        {torrent.name || torrent.info_hash}
                      </h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                        <span className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          {(torrent.progress * 100).toFixed(1)}%
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Download className="w-3 h-3" />
                          {formatSpeed(torrent.download_rate)}
                        </span>
                        <span>•</span>
                        <span>{torrent.num_peers || 0} peers</span>
                        {torrent.is_priority && (
                          <>
                            <span>•</span>
                            <span className="text-cyan-400 flex items-center gap-1">
                              <Zap className="w-3 h-3" />
                              Priority
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRemoveTorrent(torrent.info_hash)
                      }}
                      className="p-2 hover:bg-red-500/20 rounded-lg text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="mt-3 h-1 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyan-500 rounded-full transition-all"
                      style={{ width: `${torrent.progress * 100}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Streamable files */}
        {selectedTorrent && (
          <div className="w-80 bg-white/5 rounded-xl border border-white/10 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white truncate">
                {selectedTorrent.name}
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {formatSize(selectedTorrent.total_size)}
              </p>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {streamableFiles.length === 0 ? (
                <div className="text-center py-4 text-gray-400 text-sm">
                  <p>Nenhum arquivo de vídeo encontrado</p>
                  <p className="mt-1">Aguardando metadata...</p>
                </div>
              ) : (
                streamableFiles.map((file) => (
                  <div
                    key={file.index}
                    className="p-3 bg-white/5 rounded-lg border border-white/10"
                  >
                    <p className="text-sm text-white font-medium truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {file.size_formatted}
                    </p>
                    <button
                      onClick={() => handlePlay(file)}
                      className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white text-sm font-medium transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Reproduzir
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Video Player Modal */}
      {isPlaying && currentStream && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-8">
          <div className="w-full max-w-6xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold truncate">
                {currentStream.name}
              </h3>
              <button
                onClick={handleStop}
                className="p-2 hover:bg-white/20 rounded-lg text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
              <video
                src={currentStream.stream_url}
                controls
                autoPlay
                className="w-full h-full"
              />
            </div>
            
            <div className="mt-4 flex items-center justify-between text-gray-400 text-sm">
              <div className="flex items-center gap-4">
                <span>Size: {currentStream.size_formatted}</span>
                <span>•</span>
                <span>Streaming via GoStream</span>
              </div>
              <a
                href={currentStream.stream_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
              >
                <ExternalLink className="w-4 h-4" />
                Abrir em nova aba
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-lg border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">
              Adicionar Magnet Link
            </h2>
            
            <form onSubmit={handleAddTorrent}>
              <textarea
                value={magnetLink}
                onChange={(e) => setMagnetLink(e.target.value)}
                placeholder="magnet:?xt=urn:btih:..."
                className="w-full h-24 p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 resize-none"
              />
              
              <div className="flex justify-end gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={!magnetLink.trim() || isLoading}
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-cyan-500/50 rounded-lg text-white font-medium transition-colors"
                >
                  {isLoading ? 'Adicionando...' : 'Adicionar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default GoStreamApp
