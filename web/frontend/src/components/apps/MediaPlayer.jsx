import React, { useRef, useEffect, useState, useCallback } from 'react'
import { X, Play, Pause, Volume2, VolumeX, Maximize, SkipBack, SkipForward, Subtitles, Languages, Settings } from 'lucide-react'
import axios from '../../utils/axios'
import { saveWatchProgress, getItemProgress, removeItemProgress } from '../../utils/watchProgress'

const MediaPlayer = ({ itemId, title, serverUrl, onClose, onNext, onPrevious }) => {
  const videoRef = useRef(null)
  const containerRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [showControls, setShowControls] = useState(true)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const hideTimer = useRef(null)

  const [audioTracks, setAudioTracks] = useState([])
  const [subtitleTracks, setSubtitleTracks] = useState([])
  const [mediaSourceId, setMediaSourceId] = useState(null)
  const [selectedAudio, setSelectedAudio] = useState(null)
  const [selectedSubtitle, setSelectedSubtitle] = useState(-1)
  const [showSettingsMenu, setShowSettingsMenu] = useState(null)

  const buildStreamUrl = useCallback((audioIdx, needsTranscode = false) => {
    let url = `/api/jellyfin/stream/${itemId}`
    const params = []
    if (audioIdx !== null && audioIdx !== undefined) {
      params.push(`audioStreamIndex=${audioIdx}`)
    }
    if (serverUrl) {
      params.push(`server_url=${encodeURIComponent(serverUrl)}`)
    }
    // Request transcoding if audio codec is EAC3 (not supported by browsers)
    if (needsTranscode) {
      params.push(`transcode=true`)
    }
    // Add JWT token for authentication (video element cannot send custom headers)
    const token = localStorage.getItem('auth_token')
    if (token) {
      params.push(`token=${encodeURIComponent(token)}`)
    }
    if (params.length > 0) {
      url += `?${params.join('&')}`
    }
    return url
  }, [itemId, serverUrl])

  useEffect(() => {
    const fetchPlaybackInfo = async () => {
      try {
        const params = {}
        if (serverUrl) {
          params.server_url = serverUrl
        }
        const resp = await axios.get(`/api/jellyfin/playback-info/${itemId}`, { params })
        const sources = resp.data?.MediaSources || []
        if (sources.length > 0) {
          const source = sources[0]
          setMediaSourceId(source.Id)
          const streams = source.MediaStreams || []
          const audio = streams.filter(s => s.Type === 'Audio').map(s => ({
            index: s.Index,
            label: s.DisplayTitle || s.Language || `Audio ${s.Index}`,
            language: s.Language || '',
            codec: s.Codec || '',
            isDefault: s.IsDefault || false,
            needsTranscode: (s.Codec || '').toLowerCase() === 'eac3' || (s.Codec || '').toLowerCase() === 'ac3',
          }))
          const subs = streams.filter(s => s.Type === 'Subtitle').map(s => ({
            index: s.Index,
            label: s.DisplayTitle || s.Language || `Legenda ${s.Index}`,
            language: s.Language || '',
            codec: s.Codec || '',
            isExternal: s.IsExternal || false,
            isDefault: s.IsDefault || false,
          }))
          setAudioTracks(audio)
          setSubtitleTracks(subs)
          const defaultAudio = audio.find(a => a.isDefault)
          if (defaultAudio) setSelectedAudio(defaultAudio.index)
          else if (audio.length > 0) setSelectedAudio(audio[0].index)
        }
      } catch (err) {
        console.error('Failed to fetch playback info:', err)
      }
    }
    setIsLoading(true)
    setError(null)
    setIsPlaying(false)
    setCurrentTime(0)
    setDuration(0)
    setAudioTracks([])
    setSubtitleTracks([])
    setMediaSourceId(null)
    setSelectedSubtitle(-1)
    setShowSettingsMenu(null)
    fetchPlaybackInfo()
  }, [itemId])

  useEffect(() => {
    return () => {
      if (hideTimer.current) clearTimeout(hideTimer.current)
    }
  }, [])

  const handlePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play().catch(() => {})
      }
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime
      setCurrentTime(time)
      
      if (duration > 0 && time > 5) {
        saveWatchProgress(itemId, {
          position: time,
          duration: duration,
          title: title,
        })
      }
      
      if (duration > 0 && time >= duration * 0.95) {
        removeItemProgress(itemId)
      }
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
      setIsLoading(false)
      
      const savedProgress = getItemProgress(itemId)
      if (savedProgress && savedProgress.position > 5) {
        videoRef.current.currentTime = savedProgress.position
      }
    }
  }

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    if (videoRef.current && duration) {
      videoRef.current.currentTime = percent * duration
    }
  }

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value)
    setVolume(val)
    if (videoRef.current) {
      videoRef.current.volume = val
      setIsMuted(val === 0)
    }
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        containerRef.current.requestFullscreen()
      }
    }
  }

  const handleMouseMove = () => {
    setShowControls(true)
    if (hideTimer.current) clearTimeout(hideTimer.current)
    hideTimer.current = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false)
        setShowSettingsMenu(null)
      }
    }, 3000)
  }

  const handleAudioChange = (audioIndex) => {
    setSelectedAudio(audioIndex)
    setShowSettingsMenu(null)
    if (videoRef.current) {
      const wasPlaying = !videoRef.current.paused
      const savedTime = videoRef.current.currentTime
      const track = audioTracks.find(t => t.index === audioIndex)
      const needsTranscode = track?.needsTranscode || false
      videoRef.current.src = buildStreamUrl(audioIndex, needsTranscode)
      videoRef.current.currentTime = savedTime
      if (wasPlaying) videoRef.current.play().catch(() => {})
    }
  }

  const handleSubtitleChange = (subIndex) => {
    setSelectedSubtitle(subIndex)
    setShowSettingsMenu(null)
    if (videoRef.current) {
      const tracks = videoRef.current.textTracks
      for (let i = 0; i < tracks.length; i++) {
        tracks[i].mode = 'disabled'
      }
      if (subIndex >= 0) {
        const trackElements = videoRef.current.querySelectorAll('track')
        for (let i = 0; i < trackElements.length; i++) {
          if (parseInt(trackElements[i].dataset.subIndex) === subIndex) {
            tracks[i].mode = 'showing'
            break
          }
        }
      }
    }
  }

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)
    if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0
  const selectedTrack = audioTracks.find(t => t.index === selectedAudio)
  const needsTranscode = selectedTrack?.needsTranscode || false
  const streamUrl = buildStreamUrl(selectedAudio, needsTranscode)

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-black flex flex-col"
      onMouseMove={handleMouseMove}
      onClick={() => setShowSettingsMenu(null)}
    >
      {/* Close button */}
      <button
        onClick={(e) => { e.stopPropagation(); onClose(); }}
        className="absolute top-4 right-4 z-50 bg-black/60 hover:bg-black/80 text-white p-2 rounded-full transition-colors"
      >
        <X size={20} />
      </button>

      {/* Title overlay */}
      <div className={`absolute top-0 left-0 right-0 z-40 p-4 bg-gradient-to-b from-black/70 to-transparent transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
        <h3 className="text-white text-lg font-semibold pr-12 truncate">{title}</h3>
      </div>

      {/* Video */}
      <div className="flex-1 flex items-center justify-center cursor-pointer" onClick={(e) => { e.stopPropagation(); handlePlay(); }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-30 pointer-events-none">
            <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin" />
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center z-30 pointer-events-none">
            <div className="text-center text-white">
              <p className="text-lg font-semibold mb-2">Erro ao reproduzir</p>
              <p className="text-sm text-white/70">{error}</p>
            </div>
          </div>
        )}
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          src={streamUrl}
          crossOrigin="anonymous"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onError={() => setError('Formato não suportado pelo navegador ou mídia indisponível')}
          onCanPlay={() => setIsLoading(false)}
          onWaiting={() => setIsLoading(true)}
          autoPlay
        >
          {mediaSourceId && subtitleTracks.map((sub) => {
            let subUrl = `/api/jellyfin/subtitles/${itemId}/${mediaSourceId}/${sub.index}`
            if (serverUrl) {
              subUrl += `?server_url=${encodeURIComponent(serverUrl)}`
            }
            return (
              <track
                key={sub.index}
                kind="subtitles"
                label={sub.label}
                srcLang={sub.language || 'und'}
                src={subUrl}
                data-sub-index={sub.index}
                default={sub.isDefault}
              />
            )
          })}
        </video>
      </div>

      {/* Controls overlay */}
      <div
        className={`absolute bottom-0 left-0 right-0 z-40 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Progress bar */}
        <div
          className="w-full h-1.5 bg-white/20 rounded-full cursor-pointer mb-3 group hover:h-2.5 transition-all"
          onClick={handleSeek}
        >
          <div
            className="h-full bg-purple-500 rounded-full relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {onPrevious && (
              <button onClick={onPrevious} className="text-white hover:text-purple-400 transition-colors">
                <SkipBack size={20} />
              </button>
            )}
            <button onClick={handlePlay} className="text-white hover:text-purple-400 transition-colors">
              {isPlaying ? <Pause size={24} /> : <Play size={24} />}
            </button>
            {onNext && (
              <button onClick={onNext} className="text-white hover:text-purple-400 transition-colors">
                <SkipForward size={20} />
              </button>
            )}
            <span className="text-white/80 text-sm ml-2">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Audio track selector */}
            {audioTracks.length > 1 && (
              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setShowSettingsMenu(showSettingsMenu === 'audio' ? null : 'audio') }}
                  className={`text-white hover:text-purple-400 transition-colors ${showSettingsMenu === 'audio' ? 'text-purple-400' : ''}`}
                  title="Audio"
                >
                  <Languages size={20} />
                </button>
                {showSettingsMenu === 'audio' && (
                  <div className="absolute bottom-10 right-0 bg-black/95 rounded-lg border border-white/10 py-2 min-w-[200px] max-h-60 overflow-y-auto">
                    <div className="px-3 py-1.5 text-xs text-white/50 font-semibold uppercase">Audio</div>
                    {audioTracks.map((track) => (
                      <button
                        key={track.index}
                        onClick={() => handleAudioChange(track.index)}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${
                          selectedAudio === track.index ? 'text-purple-400' : 'text-white'
                        }`}
                      >
                        <span className="block">{track.label}</span>
                        {track.codec && <span className="text-xs text-white/40">{track.codec.toUpperCase()}</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Subtitle selector */}
            {subtitleTracks.length > 0 && (
              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setShowSettingsMenu(showSettingsMenu === 'subs' ? null : 'subs') }}
                  className={`text-white hover:text-purple-400 transition-colors ${showSettingsMenu === 'subs' || selectedSubtitle >= 0 ? 'text-purple-400' : ''}`}
                  title="Legendas"
                >
                  <Subtitles size={20} />
                </button>
                {showSettingsMenu === 'subs' && (
                  <div className="absolute bottom-10 right-0 bg-black/95 rounded-lg border border-white/10 py-2 min-w-[200px] max-h-60 overflow-y-auto">
                    <div className="px-3 py-1.5 text-xs text-white/50 font-semibold uppercase">Legendas</div>
                    <button
                      onClick={() => handleSubtitleChange(-1)}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${
                        selectedSubtitle === -1 ? 'text-purple-400' : 'text-white'
                      }`}
                    >
                      Desativadas
                    </button>
                    {subtitleTracks.map((track) => (
                      <button
                        key={track.index}
                        onClick={() => handleSubtitleChange(track.index)}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${
                          selectedSubtitle === track.index ? 'text-purple-400' : 'text-white'
                        }`}
                      >
                        <span className="block">{track.label}</span>
                        {track.codec && <span className="text-xs text-white/40">{track.codec.toUpperCase()}</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button onClick={toggleMute} className="text-white hover:text-purple-400 transition-colors">
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-20 accent-purple-500"
            />
            <button onClick={toggleFullscreen} className="text-white hover:text-purple-400 transition-colors">
              <Maximize size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MediaPlayer
