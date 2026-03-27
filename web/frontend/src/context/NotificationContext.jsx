import React, { createContext, useContext, useState, useCallback } from 'react'
import { systemEvents, SYSTEM_EVENTS } from '../utils/eventEmitter'

const NotificationContext = createContext()

export const useNotification = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider')
  }
  return context
}

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([])

  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random()
    const newNotification = {
      id,
      type: 'info',
      duration: 5000,
      ...notification,
    }

    setNotifications(prev => [...prev, newNotification])

    if (newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }

    return id
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const success = useCallback((message, options = {}) => {
    return addNotification({
      type: 'success',
      message,
      ...options,
    })
  }, [addNotification])

  const error = useCallback((message, options = {}) => {
    return addNotification({
      type: 'error',
      message,
      duration: 7000,
      ...options,
    })
  }, [addNotification])

  const warning = useCallback((message, options = {}) => {
    return addNotification({
      type: 'warning',
      message,
      ...options,
    })
  }, [addNotification])

  const info = useCallback((message, options = {}) => {
    return addNotification({
      type: 'info',
      message,
      ...options,
    })
  }, [addNotification])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  React.useEffect(() => {
    const unsubscribe = systemEvents.on(SYSTEM_EVENTS.NOTIFICATION_SHOW, (notification) => {
      addNotification(notification)
    })

    return unsubscribe
  }, [addNotification])

  const value = {
    notifications,
    addNotification,
    removeNotification,
    success,
    error,
    warning,
    info,
    clearAll,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}
