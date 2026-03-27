import React, { useState } from 'react'
import Window from './Window'
import Dock from './Dock'
import TorrentsApp from './apps/TorrentsApp'
import JellyfinApp from './apps/JellyfinApp'
import DockerApp from './apps/DockerApp'
import SystemMonitor from './apps/SystemMonitor'
import AppStoreApp from './apps/AppStoreApp'
import FileManagerApp from './apps/FileManagerApp'
import { Download, Film, Container, Activity, Store, FolderOpen } from 'lucide-react'

const Desktop = () => {
  const [openWindows, setOpenWindows] = useState([])

  const apps = [
    {
      id: 'appstore',
      name: 'App Store',
      icon: Store,
      component: AppStoreApp,
      color: 'bg-gradient-to-br from-purple-500 to-pink-500'
    },
    {
      id: 'files',
      name: 'Gerenciador de Arquivos',
      icon: FolderOpen,
      component: FileManagerApp,
      color: 'bg-orange-500'
    },
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
      
      <Dock 
        apps={apps}
        openWindows={openWindows}
        onOpenApp={openApp}
      />
    </>
  )
}

export default Desktop
