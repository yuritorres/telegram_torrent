import React, { useState, useEffect } from 'react'
import { useSystem } from '../context/SystemContext'
import { useAuth } from '../context/AuthContext'
import { Wifi, WifiOff, Clock, User, LogOut } from 'lucide-react'

const Taskbar = () => {
  const { systemStatus } = useSystem()
  const { user, logout } = useAuth()
  const [time, setTime] = useState(new Date())
  const [showUserMenu, setShowUserMenu] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const isConnected = systemStatus?.qbittorrent?.connected || systemStatus?.jellyfin?.connected

  const handleLogout = () => {
    if (confirm('Tem certeza que deseja sair?')) {
      logout()
    }
  }

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

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-2 py-1 rounded hover:bg-white/10 transition-colors"
          >
            <User size={16} />
            <span className="text-xs">{user?.username}</span>
          </button>

          {showUserMenu && (
            <>
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => setShowUserMenu(false)}
              />
              <div className="absolute right-0 bottom-full mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 min-w-[150px]">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-red-600/20 text-red-400 transition-colors rounded-lg"
                >
                  <LogOut size={16} />
                  <span>Sair</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Taskbar
