import React, { useState, useEffect, useRef } from 'react'
import axios from '../../utils/axios'
import {
  Folder,
  File as FileIcon,
  Upload,
  Download,
  Trash2,
  Edit2,
  FolderPlus,
  ArrowLeft,
  RefreshCw,
  Search,
  X,
  Check,
  MoreVertical,
  FileText,
  Image as ImageIcon,
  Film,
  Music,
  Archive,
  Code
} from 'lucide-react'

const FileManagerApp = () => {
  const [currentPath, setCurrentPath] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedItems, setSelectedItems] = useState(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [showNewFolder, setShowNewFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [renamingItem, setRenamingItem] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [uploadProgress, setUploadProgress] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadFiles()
  }, [currentPath])

  const loadFiles = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/files/list', {
        params: { path: currentPath }
      })
      setItems(response.data.items || [])
    } catch (error) {
      console.error('Error loading files:', error)
    } finally {
      setLoading(false)
    }
  }

  const navigateToFolder = (folderPath) => {
    setCurrentPath(folderPath)
    setSelectedItems(new Set())
  }

  const navigateUp = () => {
    if (currentPath) {
      const parts = currentPath.split('/').filter(Boolean)
      parts.pop()
      setCurrentPath(parts.join('/'))
      setSelectedItems(new Set())
    }
  }

  const handleItemClick = (item) => {
    if (item.type === 'directory') {
      navigateToFolder(item.path)
    }
  }

  const handleItemSelect = (item, event) => {
    event.stopPropagation()
    const newSelected = new Set(selectedItems)
    if (newSelected.has(item.path)) {
      newSelected.delete(item.path)
    } else {
      newSelected.add(item.path)
    }
    setSelectedItems(newSelected)
  }

  const handleUpload = async (files) => {
    for (const file of files) {
      try {
        setUploadProgress({ name: file.name, progress: 0 })
        const formData = new FormData()
        formData.append('file', file)
        formData.append('path', currentPath)

        await axios.post('/api/files/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress({ name: file.name, progress })
          }
        })
      } catch (error) {
        console.error('Upload error:', error)
        alert(`Erro ao enviar ${file.name}`)
      }
    }
    setUploadProgress(null)
    loadFiles()
  }

  const handleFileInputChange = (event) => {
    const files = Array.from(event.target.files)
    if (files.length > 0) {
      handleUpload(files)
    }
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragOver(false)
    const files = Array.from(event.dataTransfer.files)
    if (files.length > 0) {
      handleUpload(files)
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDownload = async (item) => {
    try {
      const response = await axios.get('/api/files/download', {
        params: { path: item.path },
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', item.name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      alert('Erro ao baixar arquivo')
    }
  }

  const handleDelete = async (paths) => {
    if (!confirm(`Tem certeza que deseja excluir ${paths.length} item(ns)?`)) {
      return
    }

    for (const path of paths) {
      try {
        await axios.delete('/api/files/delete', {
          params: { path }
        })
      } catch (error) {
        console.error('Delete error:', error)
        alert(`Erro ao excluir ${path}`)
      }
    }
    setSelectedItems(new Set())
    loadFiles()
  }

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return

    try {
      await axios.post('/api/files/create-folder', null, {
        params: {
          path: currentPath,
          name: newFolderName
        }
      })
      setShowNewFolder(false)
      setNewFolderName('')
      loadFiles()
    } catch (error) {
      console.error('Create folder error:', error)
      alert('Erro ao criar pasta')
    }
  }

  const handleRename = async (item) => {
    if (!renameValue.trim() || renameValue === item.name) {
      setRenamingItem(null)
      return
    }

    try {
      await axios.post('/api/files/rename', null, {
        params: {
          path: item.path,
          new_name: renameValue
        }
      })
      setRenamingItem(null)
      setRenameValue('')
      loadFiles()
    } catch (error) {
      console.error('Rename error:', error)
      alert('Erro ao renomear')
    }
  }

  const startRename = (item) => {
    setRenamingItem(item.path)
    setRenameValue(item.name)
  }

  const getFileIcon = (item) => {
    if (item.type === 'directory') {
      return <Folder className="text-yellow-500" size={20} />
    }

    const ext = item.name.split('.').pop().toLowerCase()
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
      return <ImageIcon className="text-blue-500" size={20} />
    }
    if (['mp4', 'mkv', 'avi', 'mov', 'webm'].includes(ext)) {
      return <Film className="text-purple-500" size={20} />
    }
    if (['mp3', 'wav', 'flac', 'ogg', 'm4a'].includes(ext)) {
      return <Music className="text-green-500" size={20} />
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
      return <Archive className="text-orange-500" size={20} />
    }
    if (['js', 'jsx', 'py', 'java', 'cpp', 'c', 'html', 'css', 'json'].includes(ext)) {
      return <Code className="text-cyan-500" size={20} />
    }
    if (['txt', 'md', 'pdf', 'doc', 'docx'].includes(ext)) {
      return <FileText className="text-gray-400" size={20} />
    }

    return <FileIcon className="text-gray-400" size={20} />
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (isoDate) => {
    return new Date(isoDate).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : []

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="bg-secondary p-3 border-b border-border space-y-3">
        <div className="flex items-center gap-2">
          <button
            onClick={navigateUp}
            disabled={!currentPath}
            className="p-2 hover:bg-background rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Voltar"
          >
            <ArrowLeft size={20} />
          </button>

          <button
            onClick={loadFiles}
            className="p-2 hover:bg-background rounded transition-colors"
            title="Atualizar"
          >
            <RefreshCw size={20} />
          </button>

          <div className="h-6 w-px bg-border" />

          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            <Upload size={16} />
            <span className="text-sm">Upload</span>
          </button>

          <button
            onClick={() => setShowNewFolder(true)}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors"
          >
            <FolderPlus size={16} />
            <span className="text-sm">Nova Pasta</span>
          </button>

          {selectedItems.size > 0 && (
            <>
              <div className="h-6 w-px bg-border" />
              <button
                onClick={() => handleDelete(Array.from(selectedItems))}
                className="flex items-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
              >
                <Trash2 size={16} />
                <span className="text-sm">Excluir ({selectedItems.size})</span>
              </button>
            </>
          )}

          <div className="flex-1" />

          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <input
              type="text"
              placeholder="Buscar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-9 py-2 bg-background rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={() => navigateToFolder('')}
            className="px-2 py-1 hover:bg-background rounded transition-colors"
          >
            <Folder size={16} className="inline mr-1" />
            Home
          </button>
          {pathParts.map((part, index) => (
            <React.Fragment key={index}>
              <span className="text-muted-foreground">/</span>
              <button
                onClick={() => navigateToFolder(pathParts.slice(0, index + 1).join('/'))}
                className="px-2 py-1 hover:bg-background rounded transition-colors"
              >
                {part}
              </button>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* File List */}
      <div
        className="flex-1 overflow-auto p-4"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {dragOver && (
          <div className="fixed inset-0 bg-blue-500/20 border-4 border-dashed border-blue-500 flex items-center justify-center z-50 pointer-events-none">
            <div className="bg-background p-8 rounded-lg shadow-xl">
              <Upload size={48} className="mx-auto mb-4 text-blue-500" />
              <p className="text-xl font-semibold">Solte os arquivos aqui</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <Folder size={64} className="mb-4 opacity-50" />
            <p className="text-lg">
              {searchQuery ? 'Nenhum arquivo encontrado' : 'Pasta vazia'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-1">
            {filteredItems.map((item) => (
              <div
                key={item.path}
                className={`flex items-center gap-3 p-3 rounded hover:bg-secondary transition-colors cursor-pointer group ${
                  selectedItems.has(item.path) ? 'bg-blue-500/20' : ''
                }`}
                onClick={() => handleItemClick(item)}
              >
                <input
                  type="checkbox"
                  checked={selectedItems.has(item.path)}
                  onChange={(e) => handleItemSelect(item, e)}
                  onClick={(e) => e.stopPropagation()}
                  className="w-4 h-4"
                />

                {getFileIcon(item)}

                {renamingItem === item.path ? (
                  <div className="flex-1 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRename(item)
                        if (e.key === 'Escape') setRenamingItem(null)
                      }}
                      className="flex-1 px-2 py-1 bg-background border border-blue-500 rounded text-sm focus:outline-none"
                      autoFocus
                    />
                    <button
                      onClick={() => handleRename(item)}
                      className="p-1 hover:bg-green-600 rounded text-green-500 hover:text-white"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={() => setRenamingItem(null)}
                      className="p-1 hover:bg-red-600 rounded text-red-500 hover:text-white"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{item.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.type === 'directory' ? 'Pasta' : formatFileSize(item.size)} • {formatDate(item.modified)}
                      </p>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.type === 'file' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDownload(item)
                          }}
                          className="p-2 hover:bg-blue-600 rounded transition-colors"
                          title="Download"
                        >
                          <Download size={16} />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startRename(item)
                        }}
                        className="p-2 hover:bg-yellow-600 rounded transition-colors"
                        title="Renomear"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete([item.path])
                        }}
                        className="p-2 hover:bg-red-600 rounded transition-colors"
                        title="Excluir"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="bg-secondary border-t border-border p-4">
          <div className="flex items-center gap-3">
            <Upload size={20} className="text-blue-500" />
            <div className="flex-1">
              <p className="text-sm font-medium">{uploadProgress.name}</p>
              <div className="w-full bg-background rounded-full h-2 mt-1">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress.progress}%` }}
                />
              </div>
            </div>
            <span className="text-sm text-muted-foreground">{uploadProgress.progress}%</span>
          </div>
        </div>
      )}

      {/* New Folder Dialog */}
      {showNewFolder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background border border-border rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Nova Pasta</h3>
            <input
              type="text"
              placeholder="Nome da pasta"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateFolder()
                if (e.key === 'Escape') setShowNewFolder(false)
              }}
              className="w-full px-3 py-2 bg-secondary border border-border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => {
                  setShowNewFolder(false)
                  setNewFolderName('')
                }}
                className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateFolder}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
              >
                Criar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileInputChange}
        className="hidden"
      />
    </div>
  )
}

export default FileManagerApp
