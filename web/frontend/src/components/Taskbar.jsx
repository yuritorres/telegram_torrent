import React, { useState, useEffect } from 'react'
import { useSystem } from '../context/SystemContext'
import { Wifi, WifiOff, Clock } from 'lucide-react'

const Taskbar = () => {
  const { systemStatus } = useSystem()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const isConnected = systemStatus?.qbittorrent?.connected || systemStatus?.jellyfin?.connected

  return (
    <div className="taskbar">
      <div className="flex items-center gap-2">
        <div className="bg-primary px-3 py-1 rounded font-bold text-sm">
          TorrentOS
        </div>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Wifi size={16} className="text-green-400" />
          ) : (
            <WifiOff size={16} className="text-red-400" />
          )}
          <span className="text-xs">
            {systemStatus?.qbittorrent?.connected ? 'qBittorrent' : ''}
            {systemStatus?.qbittorrent?.connected && systemStatus?.jellyfin?.connected ? ' • ' : ''}
            {systemStatus?.jellyfin?.connected ? 'Jellyfin' : ''}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Clock size={16} />
          <span>{time.toLocaleTimeString('pt-BR')}</span>
        </div>
      </div>
    </div>
  )
}

export default Taskbar
