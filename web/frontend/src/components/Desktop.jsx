import React, { useState } from 'react'
import Window from './Window'
import Dock from './Dock'
import TorrentsApp from './apps/TorrentsApp'
import JellyfinApp from './apps/JellyfinApp'
import DockerApp from './apps/DockerApp'
import SystemMonitor from './apps/SystemMonitor'
import AppStoreApp from './apps/AppStoreApp'
import FileManagerApp from './apps/FileManagerApp'
import FileEditor from './FileEditor'
import SettingsApp from './apps/SettingsApp'
import { Download, Film, Container, Activity, Store, FolderOpen, FileText, Settings } from 'lucide-react'
import { useSystem } from '../context/SystemContext'

const Desktop = () => {
  const { wallpaper } = useSystem()
  const [openWindows, setOpenWindows] = useState([])

  const wallpaperClasses = {
    'gradient-1': 'from-slate-900 via-blue-900 to-slate-900',
    'gradient-2': 'from-purple-900 via-pink-900 to-purple-900',
    'gradient-3': 'from-emerald-900 via-teal-900 to-emerald-900',
    'gradient-4': 'from-orange-900 via-red-900 to-orange-900',
    'gradient-5': 'from-cyan-900 via-blue-900 to-cyan-900',
    'gradient-6': 'from-gray-900 via-slate-900 to-black',
    'gradient-7': 'from-indigo-900 via-purple-900 to-pink-900',
    'gradient-8': 'from-yellow-900 via-orange-900 to-red-900'
  }

  const apps = [
    {
      id: 'appstore',
      name: 'App Store',
      icon: Store,
      component: AppStoreApp,
      color: 'bg-gradient-to-br from-purple-500 to-pink-500'
    },
    {
      id: 'editor',
      name: 'Editor de Arquivos',
      icon: FileText,
      component: FileEditor,
      color: 'bg-gradient-to-br from-yellow-500 to-orange-500'
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
    },
    {
      id: 'settings',
      name: 'Configurações',
      icon: Settings,
      component: SettingsApp,
      color: 'bg-gray-500'
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
    <div className={`min-h-screen bg-gradient-to-br ${wallpaperClasses[wallpaper] || wallpaperClasses['gradient-1']} p-4 transition-all duration-500`}>
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
    </div>
  )
}

export default Desktop
