import React, { useState } from 'react'
import { useSystem } from '../../context/SystemContext'
import { Download, Pause, Play, Trash2, Plus, RefreshCw } from 'lucide-react'

const TorrentsApp = () => {
  const { torrents, addTorrent, pauseTorrent, resumeTorrent, deleteTorrent, fetchTorrents } = useSystem()
  const [magnetLink, setMagnetLink] = useState('')
  const [showAddDialog, setShowAddDialog] = useState(false)

  const handleAddTorrent = async () => {
    if (!magnetLink.trim()) return
    try {
      await addTorrent(magnetLink)
      setMagnetLink('')
      setShowAddDialog(false)
    } catch (error) {
      alert('Erro ao adicionar torrent: ' + error.message)
    }
  }

  const getProgressColor = (progress) => {
    if (progress >= 100) return 'bg-green-500'
    if (progress >= 50) return 'bg-blue-500'
    return 'bg-yellow-500'
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatSpeed = (bytes) => {
    return formatBytes(bytes) + '/s'
  }

  const activeTorrents = torrents.filter(t => t.state === 'downloading' || t.state === 'uploading')
  const pausedTorrents = torrents.filter(t => t.state === 'pausedDL')
  const completedTorrents = torrents.filter(t => t.progress >= 1)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Gerenciador de Torrents</h2>
        <div className="flex gap-2">
          <button
            onClick={fetchTorrents}
            className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
          >
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button
            onClick={() => setShowAddDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/80 rounded-lg transition-colors"
          >
            <Plus size={16} />
            Adicionar Torrent
          </button>
        </div>
      </div>

      {showAddDialog && (
        <div className="bg-secondary p-4 rounded-lg space-y-3">
          <h3 className="font-semibold">Adicionar Novo Torrent</h3>
          <input
            type="text"
            value={magnetLink}
            onChange={(e) => setMagnetLink(e.target.value)}
            placeholder="Cole o link magnet aqui..."
            className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAddTorrent}
              className="px-4 py-2 bg-primary hover:bg-primary/80 rounded-lg transition-colors"
            >
              Adicionar
            </button>
            <button
              onClick={() => {
                setShowAddDialog(false)
                setMagnetLink('')
              }}
              className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-secondary p-4 rounded-lg">
          <div className="text-sm text-muted-foreground">Ativos</div>
          <div className="text-2xl font-bold text-green-400">{activeTorrents.length}</div>
        </div>
        <div className="bg-secondary p-4 rounded-lg">
          <div className="text-sm text-muted-foreground">Pausados</div>
          <div className="text-2xl font-bold text-yellow-400">{pausedTorrents.length}</div>
        </div>
        <div className="bg-secondary p-4 rounded-lg">
          <div className="text-sm text-muted-foreground">Completos</div>
          <div className="text-2xl font-bold text-blue-400">{completedTorrents.length}</div>
        </div>
      </div>

      <div className="space-y-2">
        {torrents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Nenhum torrent encontrado
          </div>
        ) : (
          torrents.map((torrent) => (
            <div key={torrent.hash} className="bg-secondary p-4 rounded-lg space-y-2">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold truncate">{torrent.name}</h3>
                  <div className="text-sm text-muted-foreground flex gap-4 mt-1">
                    <span>{formatBytes(torrent.size)}</span>
                    {torrent.state === 'downloading' && (
                      <>
                        <span>↓ {formatSpeed(torrent.dlspeed)}</span>
                        <span>↑ {formatSpeed(torrent.upspeed)}</span>
                      </>
                    )}
                    {torrent.instance && <span className="text-primary">📍 {torrent.instance}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  {torrent.state === 'pausedDL' ? (
                    <button
                      onClick={() => resumeTorrent(torrent.hash)}
                      className="p-2 hover:bg-background rounded transition-colors"
                      title="Retomar"
                    >
                      <Play size={16} />
                    </button>
                  ) : (
                    <button
                      onClick={() => pauseTorrent(torrent.hash)}
                      className="p-2 hover:bg-background rounded transition-colors"
                      title="Pausar"
                    >
                      <Pause size={16} />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm('Deseja remover este torrent?')) {
                        deleteTorrent(torrent.hash, false)
                      }
                    }}
                    className="p-2 hover:bg-red-500 rounded transition-colors"
                    title="Remover"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{(torrent.progress * 100).toFixed(1)}%</span>
                  <span>{torrent.state}</span>
                </div>
                <div className="w-full bg-background rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full ${getProgressColor(torrent.progress * 100)} transition-all duration-300`}
                    style={{ width: `${torrent.progress * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default TorrentsApp
