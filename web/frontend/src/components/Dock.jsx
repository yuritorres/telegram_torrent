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
    const maxDistance = 120
    
    if (distance > maxDistance) return 1
    
    const scale = 1 + (1 - distance / maxDistance) * 0.4
    return scale
  }

  const scale = calculateScale()

  return (
    <div
      className="flex flex-col items-center justify-end relative"
      style={{
        width: '70px',
        height: '85px',
        flexShrink: 0
      }}
    >
      <div
        ref={iconRef}
        className="relative flex flex-col items-center transition-all duration-300 ease-out"
        style={{
          transform: `scale(${scale}) translateY(${-8 * (scale - 1)}px)`,
          transformOrigin: 'bottom center',
          zIndex: scale > 1 ? 10 : 1
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <button
          onClick={() => onOpen(app)}
          className={`relative group ${app.color} p-3.5 rounded-[20px] shadow-xl transition-all duration-300 hover:shadow-2xl border border-white/10`}
          style={{ 
            width: '60px', 
            height: '60px',
            boxShadow: isOpen ? '0 0 20px rgba(59, 130, 246, 0.5)' : undefined
          }}
        >
          <app.icon className="w-full h-full text-white drop-shadow-lg" />
        </button>
        
        {isOpen && (
          <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-1.5 h-1.5 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50" />
        )}
      
        {isHovered && (
          <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 bg-gradient-to-b from-gray-800 to-gray-900 text-white text-xs px-4 py-2 rounded-xl whitespace-nowrap backdrop-blur-md border border-white/20 shadow-2xl">
            <div className="font-medium">{app.name}</div>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900 border-r border-b border-white/20"></div>
          </div>
        )}
      </div>
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
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
      <div
        ref={dockRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative backdrop-blur-2xl bg-gradient-to-b from-gray-900/40 to-gray-900/60 border border-white/10 rounded-3xl px-4 py-3 shadow-2xl"
        style={{
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        }}
      >
        <div className="flex items-end gap-2 px-1">
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
          
          <div className="w-px h-14 bg-gradient-to-b from-transparent via-white/30 to-transparent mx-2" />
          
          <div className="relative group flex flex-col items-center justify-end" style={{ width: '70px', height: '85px', flexShrink: 0 }}>
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 backdrop-blur-sm rounded-[20px] shadow-xl overflow-hidden border border-white/10" style={{ width: '60px', height: '60px' }}>
              <div className="h-full flex flex-col items-center justify-center px-1">
                <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider mb-0.5">
                  {time.toLocaleDateString('pt-BR', { month: 'short' })}
                </div>
                <div className="text-2xl font-bold text-white leading-none">
                  {time.getDate()}
                </div>
                <div className="text-[9px] text-gray-400 mt-0.5">
                  {time.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
            
            <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 bg-gradient-to-b from-gray-800 to-gray-900 text-white text-xs px-4 py-2 rounded-xl whitespace-nowrap backdrop-blur-md border border-white/20 shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="font-medium">{time.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</div>
              <div className="text-[10px] text-gray-400 mt-0.5">{time.toLocaleTimeString('pt-BR')}</div>
              <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900 border-r border-b border-white/20"></div>
            </div>
          </div>
          
          <div className="relative group flex flex-col items-center justify-end" style={{ width: '70px', height: '85px', flexShrink: 0 }}>
            <div className={`backdrop-blur-sm rounded-[20px] shadow-xl border border-white/10 p-3.5 transition-all duration-300 ${
              isConnected 
                ? 'bg-gradient-to-br from-emerald-600 to-emerald-700' 
                : 'bg-gradient-to-br from-red-600 to-red-700'
            }`} style={{ width: '60px', height: '60px' }}>
              {isConnected ? (
                <Wifi className="w-full h-full text-white drop-shadow-lg" />
              ) : (
                <WifiOff className="w-full h-full text-white drop-shadow-lg" />
              )}
            </div>
            
            <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 bg-gradient-to-b from-gray-800 to-gray-900 text-white text-xs px-4 py-2 rounded-xl whitespace-nowrap backdrop-blur-md border border-white/20 shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="font-medium">
                {isConnected ? 'Conectado' : 'Desconectado'}
              </div>
              {isConnected && (
                <div className="text-[10px] text-gray-400 mt-0.5">
                  {systemStatus?.qbittorrent?.connected ? 'qBittorrent' : ''}
                  {systemStatus?.qbittorrent?.connected && systemStatus?.jellyfin?.connected ? ' • ' : ''}
                  {systemStatus?.jellyfin?.connected ? 'Jellyfin' : ''}
                </div>
              )}
              <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900 border-r border-b border-white/20"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dock
