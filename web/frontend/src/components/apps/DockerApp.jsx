import React, { useMemo, useState } from 'react'
import { useSystem } from '../../context/SystemContext'
import { Play, Square, RefreshCw, Circle, ChevronDown, ChevronRight, Globe, Database, Film, Download, Server, Box } from 'lucide-react'

const DockerApp = () => {
  const { dockerContainers, startContainer, stopContainer, fetchDockerContainers } = useSystem()
  const [expandedGroups, setExpandedGroups] = useState({})

  const getStatusColor = (status) => {
    if (status?.toLowerCase().includes('running')) return 'text-green-400'
    if (status?.toLowerCase().includes('exited')) return 'text-red-400'
    return 'text-yellow-400'
  }

  const getStackIcon = (stackName) => {
    const name = (stackName || '').toLowerCase()
    
    if (name.includes('web') || name.includes('resolutahubos')) {
      return { icon: Globe, color: 'text-blue-400' }
    }
    if (name.includes('jellyfin') || name.includes('plex')) {
      return { icon: Film, color: 'text-pink-400' }
    }
    if (name.includes('telegram') || name.includes('torrent')) {
      return { icon: Download, color: 'text-green-400' }
    }
    if (name.includes('db') || name.includes('postgres')) {
      return { icon: Database, color: 'text-purple-400' }
    }
    return { icon: Server, color: 'text-cyan-400' }
  }

  const groupedContainers = useMemo(() => {
    const stackGroups = {}

    dockerContainers.forEach(container => {
      const stackName = container.stack || 'sem-stack'
      
      if (!stackGroups[stackName]) {
        stackGroups[stackName] = {
          name: stackName,
          containers: []
        }
      }
      
      stackGroups[stackName].containers.push(container)
    })

    return Object.entries(stackGroups)
      .map(([key, group]) => ({ key, ...group }))
      .sort((a, b) => {
        if (a.name === 'sem-stack') return 1
        if (b.name === 'sem-stack') return -1
        return a.name.localeCompare(b.name)
      })
  }, [dockerContainers])

  const toggleGroup = (groupKey) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupKey]: !prev[groupKey]
    }))
  }

  const isGroupExpanded = (groupKey) => {
    return expandedGroups[groupKey] !== false
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Containers Docker</h2>
        <button
          onClick={fetchDockerContainers}
          className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
        >
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      <div className="space-y-3">
        {dockerContainers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Nenhum container encontrado
          </div>
        ) : (
          groupedContainers.map((group) => {
            const { icon: GroupIcon, color: groupColor } = getStackIcon(group.name)
            const expanded = isGroupExpanded(group.key)
            const runningCount = group.containers.filter(c => c.status === 'running').length
            const totalCount = group.containers.length

            return (
              <div key={group.key} className="bg-secondary/50 rounded-lg overflow-hidden">
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group.key)}
                  className="w-full flex items-center justify-between p-4 hover:bg-secondary/80 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                    <GroupIcon size={20} className={groupColor} />
                    <h3 className="font-semibold text-lg">{group.name}</h3>
                    <span className="text-sm text-muted-foreground">
                      ({runningCount}/{totalCount} rodando)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {group.containers.map(c => (
                      <Circle
                        key={c.id}
                        size={8}
                        className={`${getStatusColor(c.status)} fill-current`}
                      />
                    ))}
                  </div>
                </button>

                {/* Group Containers */}
                {expanded && (
                  <div className="border-t border-border/50">
                    {group.containers.map((container) => (
                      <div
                        key={container.id}
                        className="bg-secondary p-4 border-b border-border/30 last:border-b-0 hover:bg-secondary/80 transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Circle size={12} className={`${getStatusColor(container.status)} fill-current`} />
                              <h4 className="font-semibold">{container.name || 'Unnamed'}</h4>
                            </div>
                            <div className="text-sm text-muted-foreground mt-1 space-y-0.5">
                              <div className="flex items-center gap-2">
                                <span className="text-xs bg-background/50 px-2 py-0.5 rounded">
                                  {container.image}
                                </span>
                              </div>
                              <div className="text-xs">{container.status}</div>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {container.status === 'running' ? (
                              <button
                                onClick={() => stopContainer(container.name)}
                                className="p-2 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                                title="Parar"
                              >
                                <Square size={16} />
                              </button>
                            ) : (
                              <button
                                onClick={() => startContainer(container.name)}
                                className="p-2 hover:bg-green-500/20 text-green-400 rounded transition-colors"
                                title="Iniciar"
                              >
                                <Play size={16} />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default DockerApp
