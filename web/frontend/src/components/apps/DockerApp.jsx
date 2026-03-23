import React from 'react'
import { useSystem } from '../../context/SystemContext'
import { Play, Square, RefreshCw, Circle } from 'lucide-react'

const DockerApp = () => {
  const { dockerContainers, startContainer, stopContainer, fetchDockerContainers } = useSystem()

  const getStatusColor = (status) => {
    if (status?.toLowerCase().includes('running')) return 'text-green-400'
    if (status?.toLowerCase().includes('exited')) return 'text-red-400'
    return 'text-yellow-400'
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

      <div className="space-y-2">
        {dockerContainers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Nenhum container encontrado
          </div>
        ) : (
          dockerContainers.map((container) => (
            <div key={container.id} className="bg-secondary p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Circle size={12} className={`${getStatusColor(container.status)} fill-current`} />
                    <h3 className="font-semibold">{container.name || 'Unnamed'}</h3>
                  </div>
                  <div className="text-sm text-muted-foreground mt-1 space-y-0.5">
                    <div>🏷️ {container.image}</div>
                    <div>📊 {container.status}</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  {container.status === 'running' ? (
                    <button
                      onClick={() => stopContainer(container.name)}
                      className="p-2 hover:bg-red-500 rounded transition-colors"
                      title="Parar"
                    >
                      <Square size={16} />
                    </button>
                  ) : (
                    <button
                      onClick={() => startContainer(container.name)}
                      className="p-2 hover:bg-green-500 rounded transition-colors"
                      title="Iniciar"
                    >
                      <Play size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default DockerApp
