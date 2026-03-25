import React, { useState, useRef, useEffect } from 'react'
import { useSystem } from '../context/SystemContext'
import { Download, Film, Container, Activity, Store, Wifi, WifiOff, Clock } from 'lucide-react'

const DockIcon = ({ app, onOpen, isOpen, index, mouseX, setMouseX }) => {
  const iconRef = useRef(null)
  const [isHovered, setIsHovered] = useState(false)

  const calculateScale = () => {
    if (!iconRef.current || mouseX === null) return 1
    
    const rect = iconRef.current.getBoundingClientRect()
    const iconCenter = rect.left + rect.width / 2
    const distance = Math.abs(mouseX - iconCenter)
    const maxDistance = 150
    
    if (distance > maxDistance) return 1
    
    const scale = 1 + (1 - distance / maxDistance) * 0.5
    return scale
  }

  const scale = calculateScale()

  return (
    <div
      ref={iconRef}
      className="relative flex flex-col items-center transition-all duration-200 ease-out"
      style={{
        transform: `scale(${scale}) translateY(${-10 * (scale - 1)}px)`,
        transformOrigin: 'bottom center',
        zIndex: scale > 1 ? 10 : 1,
        margin: '0 4px'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <button
        onClick={() => onOpen(app)}
        className={`relative group ${app.color} p-3 rounded-2xl shadow-lg transition-all duration-200 hover:shadow-2xl`}
        style={{ width: '56px', height: '56px' }}
      >
        <app.icon className="w-full h-full text-white" />
        
        {isOpen && (
          <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-white rounded-full" />
        )}
      </button>
      
      {isHovered && (
        <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-gray-900/90 text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap backdrop-blur-sm border border-white/10">
          {app.name}
        </div>
      )}
    </div>
  )
}

const Dock = ({ apps, openWindows, onOpenApp }) => {
  const { systemStatus } = useSystem()
  const [mouseX, setMouseX] = useState(null)
  const [time, setTime] = useState(new Date())
  const dockRef = useRef(null)

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const handleMouseMove = (e) => {
    if (dockRef.current) {
      setMouseX(e.clientX)
    }
  }

  const handleMouseLeave = () => {
    setMouseX(null)
  }

  const isConnected = systemStatus?.qbittorrent?.connected || systemStatus?.jellyfin?.connected

  return (
    <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
      <div
        ref={dockRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl px-3 py-2 shadow-2xl"
        style={{
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        }}
      >
        <div className="flex items-end gap-2 px-2">
          {apps.map((app, index) => (
            <DockIcon
              key={app.id}
              app={app}
              onOpen={onOpenApp}
              isOpen={openWindows.some(w => w.id === app.id)}
              index={index}
              mouseX={mouseX}
              setMouseX={setMouseX}
            />
          ))}
          
          <div className="w-px h-12 bg-white/20 mx-1" />
          
          <div className="relative group">
            <div className="bg-gray-800/80 p-3 rounded-2xl shadow-lg flex items-center justify-center" style={{ width: '56px', height: '56px' }}>
              <div className="text-white text-xs font-medium text-center leading-tight">
                <div>{time.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</div>
                <div className="text-[10px] opacity-70">{time.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</div>
              </div>
            </div>
            
            <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-gray-900/90 text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap backdrop-blur-sm border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity">
              {time.toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
          </div>
          
          <div className="relative group">
            <div className="bg-gray-800/80 p-3 rounded-2xl shadow-lg" style={{ width: '56px', height: '56px' }}>
              {isConnected ? (
                <Wifi className="w-full h-full text-green-400" />
              ) : (
                <WifiOff className="w-full h-full text-red-400" />
              )}
            </div>
            
            <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-gray-900/90 text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap backdrop-blur-sm border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity">
              {systemStatus?.qbittorrent?.connected ? 'qBittorrent' : ''}
              {systemStatus?.qbittorrent?.connected && systemStatus?.jellyfin?.connected ? ' • ' : ''}
              {systemStatus?.jellyfin?.connected ? 'Jellyfin' : ''}
              {!isConnected ? 'Desconectado' : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dock
