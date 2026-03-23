const STORAGE_KEY = 'jellyfin_watch_progress'

export const getWatchProgress = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : {}
  } catch (e) {
    console.error('Failed to load watch progress:', e)
    return {}
  }
}

export const saveWatchProgress = (itemId, progress) => {
  try {
    const allProgress = getWatchProgress()
    allProgress[itemId] = {
      ...progress,
      lastWatched: Date.now(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(allProgress))
  } catch (e) {
    console.error('Failed to save watch progress:', e)
  }
}

export const getItemProgress = (itemId) => {
  const allProgress = getWatchProgress()
  return allProgress[itemId] || null
}

export const removeItemProgress = (itemId) => {
  try {
    const allProgress = getWatchProgress()
    delete allProgress[itemId]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(allProgress))
  } catch (e) {
    console.error('Failed to remove watch progress:', e)
  }
}

export const getContinueWatching = (limit = 10) => {
  const allProgress = getWatchProgress()
  return Object.entries(allProgress)
    .filter(([_, progress]) => progress.position > 30 && progress.position < progress.duration * 0.95)
    .sort((a, b) => b[1].lastWatched - a[1].lastWatched)
    .slice(0, limit)
    .map(([itemId, progress]) => ({ itemId, ...progress }))
}
