import React, { useState } from 'react'
import Window from './Window'
import TorrentsApp from './apps/TorrentsApp'
import JellyfinApp from './apps/JellyfinApp'
import DockerApp from './apps/DockerApp'
import SystemMonitor from './apps/SystemMonitor'
import { Download, Film, Container, Activity } from 'lucide-react'

const Desktop = () => {
  const [openWindows, setOpenWindows] = useState([])

  const apps = [
    {
      id: 'torrents',
      name: 'Gerenciador de Torrents',
      icon: Download,
      component: TorrentsApp,
      color: 'bg-blue-500'
    },
    {
      id: 'jellyfin',
      name: 'Biblioteca Jellyfin',
      icon: Film,
      component: JellyfinApp,
      color: 'bg-purple-500'
    },
    {
      id: 'docker',
      name: 'Containers Docker',
      icon: Container,
      component: DockerApp,
      color: 'bg-cyan-500'
    },
    {
      id: 'monitor',
      name: 'Monitor do Sistema',
      icon: Activity,
      component: SystemMonitor,
      color: 'bg-green-500'
    }
  ]

  const openApp = (app) => {
    if (!openWindows.find(w => w.id === app.id)) {
      setOpenWindows([...openWindows, { ...app, zIndex: openWindows.length }])
    }
  }

  const closeWindow = (id) => {
    setOpenWindows(openWindows.filter(w => w.id !== id))
  }

  const focusWindow = (id) => {
    const maxZ = Math.max(...openWindows.map(w => w.zIndex), 0)
    setOpenWindows(openWindows.map(w => 
      w.id === id ? { ...w, zIndex: maxZ + 1 } : w
    ))
  }

  return (
    <>
      <div className="grid grid-cols-4 gap-4 p-4">
        {apps.map(app => (
          <button
            key={app.id}
            onClick={() => openApp(app)}
            className="flex flex-col items-center gap-2 p-4 rounded-lg hover:bg-white/10 transition-colors group"
          >
            <div className={`${app.color} p-4 rounded-xl shadow-lg group-hover:scale-110 transition-transform`}>
              <app.icon className="w-8 h-8 text-white" />
            </div>
            <span className="text-sm font-medium text-white">{app.name}</span>
          </button>
        ))}
      </div>

      {openWindows.map(window => (
        <Window
          key={window.id}
          title={window.name}
          onClose={() => closeWindow(window.id)}
          onFocus={() => focusWindow(window.id)}
          zIndex={window.zIndex}
        >
          <window.component />
        </Window>
      ))}
    </>
  )
}

export default Desktop
