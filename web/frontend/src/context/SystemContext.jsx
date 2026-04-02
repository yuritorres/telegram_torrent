import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from '../utils/axios'
import { systemEvents, SYSTEM_EVENTS } from '../utils/eventEmitter'

const SystemContext = createContext()

export const useSystem = () => {
  const context = useContext(SystemContext)
  if (!context) {
    throw new Error('useSystem must be used within SystemProvider')
  }
  return context
}

export const SystemProvider = ({ children }) => {
  const [systemStatus, setSystemStatus] = useState(null)
  const [torrents, setTorrents] = useState([])
  const [jellyfinItems, setJellyfinItems] = useState([])
  const [dockerContainers, setDockerContainers] = useState([])
  const [ws, setWs] = useState(null)
  const [clipboard, setClipboard] = useState(null)
  const [sharedData, setSharedData] = useState({})
  const [wallpaper, setWallpaper] = useState(() => {
    return localStorage.getItem('wallpaper') || 'gradient-1'
  })

  useEffect(() => {
    fetchSystemStatus()
    fetchTorrents()
    fetchJellyfinRecent()
    fetchDockerContainers()

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    const websocket = new WebSocket(wsUrl)
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'torrents_update') {
        setTorrents(data.data)
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    setWs(websocket)
    
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get('/api/system/status')
      setSystemStatus(response.data)
    } catch (error) {
      console.error('Error fetching system status:', error)
    }
  }

  const fetchTorrents = async () => {
    try {
      const response = await axios.get('/api/torrents')
      setTorrents(response.data.torrents || [])
    } catch (error) {
      console.error('Error fetching torrents:', error)
    }
  }

  const fetchJellyfinRecent = async () => {
    try {
      const response = await axios.get('/api/jellyfin/recent')
      setJellyfinItems(response.data.items || [])
    } catch (error) {
      console.error('Error fetching Jellyfin items:', error)
    }
  }

  const fetchDockerContainers = async () => {
    try {
      const response = await axios.get('/api/docker/containers')
      setDockerContainers(response.data.containers || [])
    } catch (error) {
      console.error('Error fetching Docker containers:', error)
    }
  }

  const addTorrent = async (magnetLink) => {
    try {
      await axios.post('/api/torrents/add', null, {
        params: { magnet_link: magnetLink }
      })
      fetchTorrents()
      systemEvents.emit(SYSTEM_EVENTS.TORRENT_ADDED, { magnetLink })
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Torrent adicionado com sucesso',
      })
    } catch (error) {
      console.error('Error adding torrent:', error)
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Erro ao adicionar torrent',
      })
      throw error
    }
  }

  const pauseTorrent = async (hash) => {
    try {
      await axios.post(`/api/torrents/${hash}/pause`)
      fetchTorrents()
    } catch (error) {
      console.error('Error pausing torrent:', error)
    }
  }

  const resumeTorrent = async (hash) => {
    try {
      await axios.post(`/api/torrents/${hash}/resume`)
      fetchTorrents()
    } catch (error) {
      console.error('Error resuming torrent:', error)
    }
  }

  const deleteTorrent = async (hash, deleteFiles = false) => {
    try {
      await axios.delete(`/api/torrents/${hash}`, {
        params: { delete_files: deleteFiles }
      })
      fetchTorrents()
      systemEvents.emit(SYSTEM_EVENTS.TORRENT_DELETED, { hash, deleteFiles })
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Torrent removido com sucesso',
      })
    } catch (error) {
      console.error('Error deleting torrent:', error)
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Erro ao remover torrent',
      })
    }
  }

  const startContainer = async (name) => {
    try {
      await axios.post(`/api/docker/containers/${name}/start`)
      fetchDockerContainers()
      systemEvents.emit(SYSTEM_EVENTS.DOCKER_CONTAINER_STARTED, { name })
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: `Container ${name} iniciado`,
      })
    } catch (error) {
      console.error('Error starting container:', error)
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: `Erro ao iniciar container ${name}`,
      })
    }
  }

  const stopContainer = async (name) => {
    try {
      await axios.post(`/api/docker/containers/${name}/stop`)
      fetchDockerContainers()
      systemEvents.emit(SYSTEM_EVENTS.DOCKER_CONTAINER_STOPPED, { name })
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: `Container ${name} parado`,
      })
    } catch (error) {
      console.error('Error stopping container:', error)
      systemEvents.emit(SYSTEM_EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: `Erro ao parar container ${name}`,
      })
    }
  }

  const copyToClipboard = useCallback((data, type = 'text') => {
    setClipboard({ data, type, timestamp: Date.now() })
    systemEvents.emit('clipboard:copy', { data, type })
  }, [])

  const pasteFromClipboard = useCallback(() => {
    return clipboard
  }, [clipboard])

  const clearClipboard = useCallback(() => {
    setClipboard(null)
    systemEvents.emit('clipboard:clear')
  }, [])

  const setSharedValue = useCallback((key, value) => {
    setSharedData(prev => ({ ...prev, [key]: value }))
    systemEvents.emit('shared:update', { key, value })
  }, [])

  const getSharedValue = useCallback((key) => {
    return sharedData[key]
  }, [sharedData])

  const emitEvent = useCallback((event, data) => {
    systemEvents.emit(event, data)
  }, [])

  const onEvent = useCallback((event, handler) => {
    return systemEvents.on(event, handler)
  }, [])

  const changeWallpaper = useCallback((wallpaperId) => {
    setWallpaper(wallpaperId)
    localStorage.setItem('wallpaper', wallpaperId)
    systemEvents.emit('wallpaper:changed', { wallpaperId })
  }, [])

  const value = {
    systemStatus,
    torrents,
    jellyfinItems,
    dockerContainers,
    fetchSystemStatus,
    fetchTorrents,
    fetchJellyfinRecent,
    fetchDockerContainers,
    addTorrent,
    pauseTorrent,
    resumeTorrent,
    deleteTorrent,
    startContainer,
    stopContainer,
    clipboard,
    copyToClipboard,
    pasteFromClipboard,
    clearClipboard,
    sharedData,
    setSharedValue,
    getSharedValue,
    emitEvent,
    onEvent,
    events: SYSTEM_EVENTS,
    wallpaper,
    changeWallpaper,
  }

  return <SystemContext.Provider value={value}>{children}</SystemContext.Provider>
}
