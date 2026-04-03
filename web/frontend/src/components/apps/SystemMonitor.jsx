import React from 'react'
import { useSystem } from '../../context/SystemContext'
import { Activity, HardDrive, Cpu, Database } from 'lucide-react'

const SystemMonitor = () => {
  const { systemStatus } = useSystem()

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Monitor do Sistema</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-secondary p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-blue-400">
            <Database size={20} />
            <span className="font-semibold">qBittorrent</span>
          </div>
          <div className="text-sm space-y-1">
            <div>Status: {systemStatus?.qbittorrent?.connected ? '✅ Conectado' : '❌ Desconectado'}</div>
            <div>Instâncias: {systemStatus?.qbittorrent?.instances || 0}</div>
            <div>Multi-instância: {systemStatus?.qbittorrent?.multi_instance ? 'Sim' : 'Não'}</div>
          </div>
        </div>

        <div className="bg-secondary p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-purple-400">
            <Activity size={20} />
            <span className="font-semibold">Jellyfin</span>
          </div>
          <div className="text-sm space-y-1">
            <div>Status: {systemStatus?.jellyfin?.connected ? '✅ Conectado' : '❌ Desconectado'}</div>
            {systemStatus?.jellyfin?.url && <div className="truncate">URL: {systemStatus.jellyfin.url}</div>}
          </div>
        </div>

        <div className="bg-secondary p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-cyan-400">
            <HardDrive size={20} />
            <span className="font-semibold">Armazenamento</span>
          </div>
          <div className="text-sm space-y-1">
            <div>Total: {formatBytes(systemStatus?.storage?.total || 0)}</div>
            <div>Baixado: {formatBytes(systemStatus?.storage?.used || 0)}</div>
          </div>
        </div>

        <div className="bg-secondary p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-green-400">
            <Cpu size={20} />
            <span className="font-semibold">Docker</span>
          </div>
          <div className="text-sm space-y-1">
            <div>Status: {systemStatus?.docker?.available ? '✅ Disponível' : '❌ Indisponível'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemMonitor
