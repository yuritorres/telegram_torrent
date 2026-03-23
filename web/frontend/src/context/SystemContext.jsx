import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

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

  useEffect(() => {
    fetchSystemStatus()
    fetchTorrents()
    fetchJellyfinRecent()
    fetchDockerContainers()

    const websocket = new WebSocket('ws://localhost:8000/ws')
    
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
    } catch (error) {
      console.error('Error adding torrent:', error)
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
    } catch (error) {
      console.error('Error deleting torrent:', error)
    }
  }

  const startContainer = async (name) => {
    try {
      await axios.post(`/api/docker/containers/${name}/start`)
      fetchDockerContainers()
    } catch (error) {
      console.error('Error starting container:', error)
    }
  }

  const stopContainer = async (name) => {
    try {
      await axios.post(`/api/docker/containers/${name}/stop`)
      fetchDockerContainers()
    } catch (error) {
      console.error('Error stopping container:', error)
    }
  }

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
  }

  return <SystemContext.Provider value={value}>{children}</SystemContext.Provider>
}
