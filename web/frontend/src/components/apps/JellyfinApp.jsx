import React, { useState, useEffect } from 'react'
import { useSystem } from '../../context/SystemContext'
import { Film, Tv, Music, RefreshCw, Play, ArrowLeft, ChevronRight } from 'lucide-react'
import axios from 'axios'
import MediaPlayer from './MediaPlayer'

const JellyfinApp = () => {
  const { jellyfinItems, fetchJellyfinRecent } = useSystem()
  const [view, setView] = useState('browse')
  const [selectedItem, setSelectedItem] = useState(null)
  const [seasons, setSeasons] = useState([])
  const [episodes, setEpisodes] = useState([])
  const [selectedSeason, setSelectedSeason] = useState(null)
  const [playingItem, setPlayingItem] = useState(null)
  const [playingTitle, setPlayingTitle] = useState('')
  const [episodeList, setEpisodeList] = useState([])
  const [playingIndex, setPlayingIndex] = useState(-1)
  const [loading, setLoading] = useState(false)

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

  const handleItemClick = async (item) => {
    if (item.Type === 'Movie') {
      setPlayingItem(item.Id)
      setPlayingTitle(item.Name)
      setEpisodeList([])
      setPlayingIndex(-1)
      setView('player')
    } else if (item.Type === 'Series') {
      setSelectedItem(item)
      setLoading(true)
      try {
        const resp = await axios.get(`/api/jellyfin/shows/${item.Id}/seasons`)
        setSeasons(resp.data.items || [])
        setEpisodes([])
        setSelectedSeason(null)
        setView('series')
      } catch (err) {
        console.error('Error fetching seasons:', err)
      } finally {
        setLoading(false)
      }
    } else if (item.Type === 'Episode') {
      setPlayingItem(item.Id)
      setPlayingTitle(`${item.SeriesName ? item.SeriesName + ' - ' : ''}${item.Name}`)
      setEpisodeList([])
      setPlayingIndex(-1)
      setView('player')
    }
  }

  const handleSeasonClick = async (season) => {
    setSelectedSeason(season)
    setLoading(true)
    try {
      const resp = await axios.get(`/api/jellyfin/shows/${selectedItem.Id}/episodes`, {
        params: { season_id: season.Id }
      })
      setEpisodes(resp.data.items || [])
    } catch (err) {
      console.error('Error fetching episodes:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEpisodePlay = (episode, index) => {
    setPlayingItem(episode.Id)
    setPlayingTitle(`${selectedItem?.Name || ''} - S${episode.ParentIndexNumber || '?'}E${episode.IndexNumber || '?'} - ${episode.Name}`)
    setEpisodeList(episodes)
    setPlayingIndex(index)
    setView('player')
  }

  const handleNext = () => {
    if (episodeList.length > 0 && playingIndex < episodeList.length - 1) {
      const nextIdx = playingIndex + 1
      const ep = episodeList[nextIdx]
      setPlayingItem(ep.Id)
      setPlayingTitle(`${selectedItem?.Name || ''} - S${ep.ParentIndexNumber || '?'}E${ep.IndexNumber || '?'} - ${ep.Name}`)
      setPlayingIndex(nextIdx)
    }
  }

  const handlePrevious = () => {
    if (episodeList.length > 0 && playingIndex > 0) {
      const prevIdx = playingIndex - 1
      const ep = episodeList[prevIdx]
      setPlayingItem(ep.Id)
      setPlayingTitle(`${selectedItem?.Name || ''} - S${ep.ParentIndexNumber || '?'}E${ep.IndexNumber || '?'} - ${ep.Name}`)
      setPlayingIndex(prevIdx)
    }
  }

  const goBack = () => {
    if (view === 'player' && episodeList.length > 0) {
      setView('series')
    } else if (view === 'player') {
      setView('browse')
    } else if (view === 'series' && episodes.length > 0 && selectedSeason) {
      setEpisodes([])
      setSelectedSeason(null)
    } else if (view === 'series') {
      setView('browse')
      setSelectedItem(null)
      setSeasons([])
    }
  }

  if (view === 'player' && playingItem) {
    return (
      <div className="w-full h-full">
        <MediaPlayer
          itemId={playingItem}
          title={playingTitle}
          onClose={goBack}
          onNext={episodeList.length > 0 && playingIndex < episodeList.length - 1 ? handleNext : null}
          onPrevious={episodeList.length > 0 && playingIndex > 0 ? handlePrevious : null}
        />
      </div>
    )
  }

  if (view === 'series' && selectedItem) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={goBack} className="p-2 hover:bg-secondary rounded-lg transition-colors">
            <ArrowLeft size={20} />
          </button>
          <div className="flex-1">
            <h2 className="text-2xl font-bold">{selectedItem.Name}</h2>
            {selectedItem.ProductionYear && (
              <span className="text-sm text-muted-foreground">{selectedItem.ProductionYear}</span>
            )}
          </div>
        </div>

        {/* Series banner */}
        <div className="relative h-40 rounded-lg overflow-hidden bg-secondary">
          <img
            src={`/api/jellyfin/image/${selectedItem.Id}?type=Backdrop&maxWidth=800`}
            alt={selectedItem.Name}
            className="w-full h-full object-cover opacity-60"
            onError={(e) => { e.target.style.display = 'none' }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent" />
          <div className="absolute bottom-3 left-4 right-4">
            {selectedItem.Overview && (
              <p className="text-sm text-white/80 line-clamp-2">{selectedItem.Overview}</p>
            )}
          </div>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto" />
          </div>
        )}

        {/* Seasons list or Episodes list */}
        {!selectedSeason ? (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Temporadas</h3>
            {seasons.map((season) => (
              <button
                key={season.Id}
                onClick={() => handleSeasonClick(season)}
                className="w-full flex items-center gap-3 p-3 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors text-left"
              >
                <div className="w-16 h-24 rounded overflow-hidden bg-background flex-shrink-0">
                  <img
                    src={`/api/jellyfin/image/${season.Id}?type=Primary&maxWidth=120`}
                    alt={season.Name}
                    className="w-full h-full object-cover"
                    onError={(e) => { e.target.onerror = null; e.target.style.display = 'none' }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold">{season.Name}</h4>
                  {season.ChildCount && (
                    <p className="text-sm text-muted-foreground">{season.ChildCount} episodios</p>
                  )}
                </div>
                <ChevronRight size={20} className="text-muted-foreground" />
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">{selectedSeason.Name}</h3>
            {episodes.map((episode, index) => (
              <button
                key={episode.Id}
                onClick={() => handleEpisodePlay(episode, index)}
                className="w-full flex items-center gap-3 p-3 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors text-left group"
              >
                <div className="relative w-28 h-16 rounded overflow-hidden bg-background flex-shrink-0">
                  <img
                    src={`/api/jellyfin/image/${episode.Id}?type=Primary&maxWidth=200`}
                    alt={episode.Name}
                    className="w-full h-full object-cover"
                    onError={(e) => { e.target.onerror = null; e.target.style.display = 'none' }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Play size={24} className="text-white" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold truncate">
                    <span className="text-purple-400">E{episode.IndexNumber || '?'}</span>{' '}
                    {episode.Name}
                  </h4>
                  {episode.Overview && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{episode.Overview}</p>
                  )}
                  {episode.RunTimeTicks && (
                    <span className="text-xs text-muted-foreground">
                      {Math.round(episode.RunTimeTicks / 600000000)} min
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    )
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

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {jellyfinItems.length === 0 ? (
          <div className="col-span-full text-center py-8 text-muted-foreground">
            Nenhum item recente encontrado
          </div>
        ) : (
          jellyfinItems.map((item, index) => (
            <button
              key={index}
              onClick={() => handleItemClick(item)}
              className="bg-secondary rounded-lg overflow-hidden hover:ring-2 hover:ring-purple-500 transition-all text-left group"
            >
              <div className="relative aspect-video bg-background">
                <img
                  src={`/api/jellyfin/image/${item.Id}?type=${item.ImageTags?.Primary ? 'Primary' : 'Backdrop'}&maxWidth=400`}
                  alt={item.Name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.onerror = null
                    e.target.style.display = 'none'
                  }}
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="bg-purple-500 p-3 rounded-full">
                    <Play size={24} className="text-white" />
                  </div>
                </div>
                <div className="absolute top-2 left-2">
                  <span className="px-2 py-0.5 bg-black/70 text-white text-xs rounded">
                    {item.Type === 'Movie' ? 'Filme' : item.Type === 'Series' ? 'Serie' : item.Type}
                  </span>
                </div>
              </div>
              <div className="p-3">
                <h3 className="font-semibold truncate">{item.Name}</h3>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                  {item.ProductionYear && <span>{item.ProductionYear}</span>}
                  {item.Genres && item.Genres.length > 0 && (
                    <>
                      <span>•</span>
                      <span className="truncate">{item.Genres.slice(0, 2).join(', ')}</span>
                    </>
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

export default JellyfinApp
