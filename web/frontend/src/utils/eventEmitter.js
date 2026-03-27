class EventEmitter {
  constructor() {
    this.events = {}
  }

  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = []
    }
    this.events[event].push(listener)
    
    return () => this.off(event, listener)
  }

  off(event, listenerToRemove) {
    if (!this.events[event]) return

    this.events[event] = this.events[event].filter(
      listener => listener !== listenerToRemove
    )
  }

  emit(event, ...args) {
    if (!this.events[event]) return

    this.events[event].forEach(listener => {
      try {
        listener(...args)
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error)
      }
    })
  }

  once(event, listener) {
    const onceWrapper = (...args) => {
      listener(...args)
      this.off(event, onceWrapper)
    }
    return this.on(event, onceWrapper)
  }

  removeAllListeners(event) {
    if (event) {
      delete this.events[event]
    } else {
      this.events = {}
    }
  }

  listenerCount(event) {
    return this.events[event]?.length || 0
  }
}

export const systemEvents = new EventEmitter()

export const SYSTEM_EVENTS = {
  TORRENT_ADDED: 'torrent:added',
  TORRENT_COMPLETED: 'torrent:completed',
  TORRENT_DELETED: 'torrent:deleted',
  FILE_UPLOADED: 'file:uploaded',
  FILE_DELETED: 'file:deleted',
  DOCKER_CONTAINER_STARTED: 'docker:container:started',
  DOCKER_CONTAINER_STOPPED: 'docker:container:stopped',
  JELLYFIN_ITEM_PLAYED: 'jellyfin:item:played',
  NOTIFICATION_SHOW: 'notification:show',
  APP_OPENED: 'app:opened',
  APP_CLOSED: 'app:closed',
}

export default EventEmitter
