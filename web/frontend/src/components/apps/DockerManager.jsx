import React, { useState, useEffect } from 'react'
import { 
  Container, Play, Square, RotateCw, Pause, Trash2, 
  Activity, HardDrive, Network, Cpu, MemoryStick,
  ChevronDown, ChevronRight, Terminal, Eye, RefreshCw,
  Layers, Box, Server, AlertCircle
} from 'lucide-react'
import axios from 'axios'
import { useNotification } from '../../context/NotificationContext'

const API_BASE = 'http://localhost:8000'

export default function DockerManager() {
  const [containers, setContainers] = useState([])
  const [stacks, setStacks] = useState([])
  const [systemInfo, setSystemInfo] = useState(null)
  const [selectedContainer, setSelectedContainer] = useState(null)
  const [containerStats, setContainerStats] = useState({})
  const [containerLogs, setContainerLogs] = useState('')
  const [view, setView] = useState('containers') // containers, stacks, logs, stats
  const [loading, setLoading] = useState(true)
  const [expandedStacks, setExpandedStacks] = useState(new Set())
  const { addNotification } = useNotification()

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (selectedContainer && view === 'stats') {
      loadContainerStats(selectedContainer.id)
      const interval = setInterval(() => loadContainerStats(selectedContainer.id), 3000)
      return () => clearInterval(interval)
    }
  }, [selectedContainer, view])

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const [containersRes, stacksRes, systemRes] = await Promise.all([
        axios.get(`${API_BASE}/api/docker-advanced/containers`, { headers }),
        axios.get(`${API_BASE}/api/docker-advanced/stacks`, { headers }),
        axios.get(`${API_BASE}/api/docker-advanced/system/info`, { headers })
      ])

      setContainers(containersRes.data.containers || [])
      setStacks(stacksRes.data.stacks || [])
      setSystemInfo(systemRes.data)
      setLoading(false)
    } catch (error) {
      console.error('Error loading Docker data:', error)
      addNotification('Erro ao carregar dados do Docker', 'error')
      setLoading(false)
    }
  }

  const loadContainerStats = async (containerId) => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      const res = await axios.get(`${API_BASE}/api/docker-advanced/containers/${containerId}/stats`, { headers })
      setContainerStats(prev => ({ ...prev, [containerId]: res.data }))
    } catch (error) {
      console.error('Error loading container stats:', error)
    }
  }

  const loadContainerLogs = async (containerId) => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      const res = await axios.get(`${API_BASE}/api/docker-advanced/containers/${containerId}/logs?tail=100`, { headers })
      setContainerLogs(res.data.logs || '')
    } catch (error) {
      console.error('Error loading container logs:', error)
      addNotification('Erro ao carregar logs', 'error')
    }
  }

  const executeContainerAction = async (containerId, action) => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      
      await axios.post(`${API_BASE}/api/docker-advanced/containers/${containerId}/${action}`, {}, { headers })
      
      addNotification(`Container ${action} executado com sucesso`, 'success')
      loadData()
    } catch (error) {
      console.error(`Error executing ${action}:`, error)
      addNotification(`Erro ao executar ${action}`, 'error')
    }
  }

  const executeStackAction = async (stackName, action) => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      
      await axios.post(`${API_BASE}/api/docker-advanced/stacks/${stackName}/${action}`, {}, { headers })
      
      addNotification(`Stack ${action} executado com sucesso`, 'success')
      loadData()
    } catch (error) {
      console.error(`Error executing stack ${action}:`, error)
      addNotification(`Erro ao executar ${action} na stack`, 'error')
    }
  }

  const toggleStack = (stackName) => {
    setExpandedStacks(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stackName)) {
        newSet.delete(stackName)
      } else {
        newSet.add(stackName)
      }
      return newSet
    })
  }

  const getStatusColor = (state) => {
    switch (state) {
      case 'running': return 'text-green-500'
      case 'exited': return 'text-red-500'
      case 'paused': return 'text-yellow-500'
      default: return 'text-gray-500'
    }
  }

  const getStatusBg = (state) => {
    switch (state) {
      case 'running': return 'bg-green-500/10 border-green-500/30'
      case 'exited': return 'bg-red-500/10 border-red-500/30'
      case 'paused': return 'bg-yellow-500/10 border-yellow-500/30'
      default: return 'bg-gray-500/10 border-gray-500/30'
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">Carregando dados do Docker...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Container className="w-6 h-6 text-blue-400" />
            <h1 className="text-xl font-bold">Docker Manager</h1>
          </div>
          <button
            onClick={loadData}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar
          </button>
        </div>

        {/* System Info */}
        {systemInfo && (
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <Box className="w-4 h-4" />
                <span>Containers</span>
              </div>
              <div className="text-2xl font-bold">{systemInfo.containers}</div>
              <div className="text-xs text-gray-400 mt-1">
                {systemInfo.containers_running} rodando
              </div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <Layers className="w-4 h-4" />
                <span>Imagens</span>
              </div>
              <div className="text-2xl font-bold">{systemInfo.images}</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <Cpu className="w-4 h-4" />
                <span>CPUs</span>
              </div>
              <div className="text-2xl font-bold">{systemInfo.cpus}</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-400 mb-1">
                <MemoryStick className="w-4 h-4" />
                <span>Memória</span>
              </div>
              <div className="text-2xl font-bold">{formatBytes(systemInfo.memory_total)}</div>
            </div>
          </div>
        )}

        {/* View Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setView('containers')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === 'containers' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <Container className="w-4 h-4 inline mr-2" />
            Containers
          </button>
          <button
            onClick={() => setView('stacks')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === 'stacks' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <Layers className="w-4 h-4 inline mr-2" />
            Stacks
          </button>
          {selectedContainer && (
            <>
              <button
                onClick={() => setView('stats')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'stats' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <Activity className="w-4 h-4 inline mr-2" />
                Estatísticas
              </button>
              <button
                onClick={() => {
                  setView('logs')
                  loadContainerLogs(selectedContainer.id)
                }}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  view === 'logs' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <Terminal className="w-4 h-4 inline mr-2" />
                Logs
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {view === 'containers' && (
          <div className="space-y-2">
            {containers.map(container => (
              <div
                key={container.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedContainer?.id === container.id
                    ? 'bg-blue-900/20 border-blue-500'
                    : `${getStatusBg(container.state)} border hover:border-gray-500`
                }`}
                onClick={() => setSelectedContainer(container)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Container className={`w-5 h-5 ${getStatusColor(container.state)}`} />
                      <span className="font-semibold text-lg">{container.name}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(container.state)}`}>
                        {container.state}
                      </span>
                      {container.compose && (
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                          {container.compose.project}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-400 space-y-1">
                      <div>Imagem: {container.image}</div>
                      {container.ports && container.ports.length > 0 && (
                        <div className="flex items-center gap-2">
                          <Network className="w-4 h-4" />
                          {container.ports.map((p, i) => (
                            <span key={i} className="bg-gray-700 px-2 py-0.5 rounded text-xs">
                              {p.host_port}→{p.container_port}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    {container.state === 'running' && (
                      <>
                        <button
                          onClick={(e) => { e.stopPropagation(); executeContainerAction(container.id, 'pause') }}
                          className="p-2 bg-yellow-600 hover:bg-yellow-700 rounded transition-colors"
                          title="Pausar"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); executeContainerAction(container.id, 'restart') }}
                          className="p-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                          title="Reiniciar"
                        >
                          <RotateCw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); executeContainerAction(container.id, 'stop') }}
                          className="p-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
                          title="Parar"
                        >
                          <Square className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {container.state === 'paused' && (
                      <button
                        onClick={(e) => { e.stopPropagation(); executeContainerAction(container.id, 'unpause') }}
                        className="p-2 bg-green-600 hover:bg-green-700 rounded transition-colors"
                        title="Despausar"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    {container.state === 'exited' && (
                      <button
                        onClick={(e) => { e.stopPropagation(); executeContainerAction(container.id, 'start') }}
                        className="p-2 bg-green-600 hover:bg-green-700 rounded transition-colors"
                        title="Iniciar"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {view === 'stacks' && (
          <div className="space-y-2">
            {stacks.map(stack => (
              <div key={stack.name} className="border border-gray-700 rounded-lg overflow-hidden">
                <div
                  className="bg-gray-800 p-4 cursor-pointer hover:bg-gray-750 transition-colors"
                  onClick={() => toggleStack(stack.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {expandedStacks.has(stack.name) ? (
                        <ChevronDown className="w-5 h-5" />
                      ) : (
                        <ChevronRight className="w-5 h-5" />
                      )}
                      <Layers className="w-5 h-5 text-purple-400" />
                      <span className="font-semibold text-lg">{stack.name}</span>
                      <span className="text-sm text-gray-400">
                        {stack.running}/{stack.total} rodando
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); executeStackAction(stack.name, 'start') }}
                        className="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm"
                      >
                        <Play className="w-4 h-4 inline mr-1" />
                        Iniciar
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); executeStackAction(stack.name, 'restart') }}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
                      >
                        <RotateCw className="w-4 h-4 inline mr-1" />
                        Reiniciar
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); executeStackAction(stack.name, 'stop') }}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded transition-colors text-sm"
                      >
                        <Square className="w-4 h-4 inline mr-1" />
                        Parar
                      </button>
                    </div>
                  </div>
                </div>
                
                {expandedStacks.has(stack.name) && (
                  <div className="p-4 bg-gray-900 space-y-2">
                    {stack.containers.map(container => (
                      <div
                        key={container.id}
                        className={`border rounded p-3 ${getStatusBg(container.state)} border`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Container className={`w-4 h-4 ${getStatusColor(container.state)}`} />
                            <span className="font-medium">{container.name}</span>
                            <span className={`text-xs ${getStatusColor(container.state)}`}>
                              {container.state}
                            </span>
                          </div>
                          <button
                            onClick={() => {
                              setSelectedContainer(container)
                              setView('containers')
                            }}
                            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                          >
                            <Eye className="w-3 h-3 inline mr-1" />
                            Ver detalhes
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {view === 'stats' && selectedContainer && containerStats[selectedContainer.id] && (
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4">
                Estatísticas: {selectedContainer.name}
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                {/* CPU */}
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Cpu className="w-5 h-5 text-blue-400" />
                    <span className="font-medium">CPU</span>
                  </div>
                  <div className="text-3xl font-bold text-blue-400">
                    {containerStats[selectedContainer.id].cpu.toFixed(2)}%
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(containerStats[selectedContainer.id].cpu, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Memory */}
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <MemoryStick className="w-5 h-5 text-green-400" />
                    <span className="font-medium">Memória</span>
                  </div>
                  <div className="text-3xl font-bold text-green-400">
                    {containerStats[selectedContainer.id].memory.percent.toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {formatBytes(containerStats[selectedContainer.id].memory.active)} / {formatBytes(containerStats[selectedContainer.id].memory.limit)}
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{ width: `${containerStats[selectedContainer.id].memory.percent}%` }}
                    />
                  </div>
                </div>

                {/* Network */}
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Network className="w-5 h-5 text-purple-400" />
                    <span className="font-medium">Rede</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">RX:</span>
                      <span className="text-purple-400">{formatBytes(containerStats[selectedContainer.id].network.rx_bytes)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">TX:</span>
                      <span className="text-purple-400">{formatBytes(containerStats[selectedContainer.id].network.tx_bytes)}</span>
                    </div>
                  </div>
                </div>

                {/* Disk I/O */}
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <HardDrive className="w-5 h-5 text-yellow-400" />
                    <span className="font-medium">Disco I/O</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Read:</span>
                      <span className="text-yellow-400">{formatBytes(containerStats[selectedContainer.id].block_io.read_bytes)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Write:</span>
                      <span className="text-yellow-400">{formatBytes(containerStats[selectedContainer.id].block_io.write_bytes)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'logs' && selectedContainer && (
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                Logs: {selectedContainer.name}
              </h3>
              <button
                onClick={() => loadContainerLogs(selectedContainer.id)}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
              >
                <RefreshCw className="w-4 h-4 inline mr-1" />
                Atualizar
              </button>
            </div>
            <div className="bg-black rounded p-4 font-mono text-sm overflow-auto max-h-[600px]">
              <pre className="text-green-400 whitespace-pre-wrap">{containerLogs || 'Nenhum log disponível'}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
