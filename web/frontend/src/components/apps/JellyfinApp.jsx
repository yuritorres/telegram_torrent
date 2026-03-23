import React from 'react'
import { useSystem } from '../../context/SystemContext'
import { Film, Tv, Music, RefreshCw } from 'lucide-react'

const JellyfinApp = () => {
  const { jellyfinItems, fetchJellyfinRecent } = useSystem()

  const getMediaIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'movie':
        return <Film size={20} className="text-blue-400" />
      case 'series':
      case 'episode':
        return <Tv size={20} className="text-purple-400" />
      case 'audio':
        return <Music size={20} className="text-green-400" />
      default:
        return <Film size={20} className="text-gray-400" />
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Biblioteca Jellyfin</h2>
        <button
          onClick={fetchJellyfinRecent}
          className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
        >
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {jellyfinItems.length === 0 ? (
          <div className="col-span-2 text-center py-8 text-muted-foreground">
            Nenhum item recente encontrado
          </div>
        ) : (
          jellyfinItems.map((item, index) => (
            <div key={index} className="bg-secondary p-4 rounded-lg space-y-2 hover:bg-secondary/80 transition-colors">
              <div className="flex items-start gap-3">
                {getMediaIcon(item.Type)}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold truncate">{item.Name}</h3>
                  <div className="text-sm text-muted-foreground space-y-1">
                    {item.ProductionYear && <div>📅 {item.ProductionYear}</div>}
                    {item.Type && <div>🎬 {item.Type}</div>}
                    {item.Genres && item.Genres.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {item.Genres.slice(0, 3).map((genre, i) => (
                          <span key={i} className="px-2 py-0.5 bg-background rounded text-xs">
                            {genre}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              {item.Overview && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {item.Overview}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default JellyfinApp
