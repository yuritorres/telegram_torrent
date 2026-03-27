import React from 'react'
import { useNotification } from '../context/NotificationContext'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

const Notifications = () => {
  const { notifications, removeNotification } = useNotification()

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getStyles = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-500/10 border-green-500/50'
      case 'error':
        return 'bg-red-500/10 border-red-500/50'
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/50'
      case 'info':
      default:
        return 'bg-blue-500/10 border-blue-500/50'
    }
  }

  if (notifications.length === 0) return null

  return (
    <div className="fixed top-20 right-4 z-[9999] space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-start gap-3 p-4 rounded-lg border backdrop-blur-sm shadow-lg animate-in slide-in-from-right ${getStyles(
            notification.type
          )}`}
        >
          <div className="flex-shrink-0 mt-0.5">
            {getIcon(notification.type)}
          </div>
          
          <div className="flex-1 min-w-0">
            {notification.title && (
              <h4 className="font-semibold text-sm mb-1">{notification.title}</h4>
            )}
            <p className="text-sm text-foreground/90">{notification.message}</p>
          </div>

          <button
            onClick={() => removeNotification(notification.id)}
            className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}

export default Notifications
