import React, { useState } from 'react'
import { X, Minimize2, Maximize2 } from 'lucide-react'

const Window = ({ title, children, onClose, onFocus, zIndex = 0 }) => {
  const [position, setPosition] = useState({ x: 100, y: 100 })
  const [size, setSize] = useState({ width: 800, height: 600 })
  const [isMaximized, setIsMaximized] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  const handleMouseDown = (e) => {
    if (e.target.closest('.window-controls')) return
    setIsDragging(true)
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
    onFocus()
  }

  const handleMouseMove = (e) => {
    if (!isDragging) return
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  React.useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  const toggleMaximize = () => {
    setIsMaximized(!isMaximized)
  }

  const windowStyle = isMaximized
    ? { top: 0, left: 0, right: 0, bottom: '3.5rem', width: '100%', height: 'calc(100vh - 3.5rem)' }
    : { top: position.y, left: position.x, width: size.width, height: size.height }

  return (
    <div
      className="os-window fixed"
      style={{ ...windowStyle, zIndex: 10 + zIndex }}
      onClick={onFocus}
    >
      <div
        className="os-titlebar cursor-move select-none"
        onMouseDown={handleMouseDown}
      >
        <span className="font-semibold text-sm">{title}</span>
        <div className="window-controls flex gap-2">
          <button
            onClick={toggleMaximize}
            className="hover:bg-white/10 p-1 rounded transition-colors"
          >
            {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button
            onClick={onClose}
            className="hover:bg-red-500 p-1 rounded transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
      <div className="os-content overflow-auto" style={{ height: 'calc(100% - 40px)' }}>
        {children}
      </div>
    </div>
  )
}

export default Window
