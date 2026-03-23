import React, { useState, useEffect, useMemo } from 'react'
import { Search, X, Star, Download, ExternalLink, ArrowLeft, Package, Grid, List } from 'lucide-react'
import axios from 'axios'

const AppStoreApp = () => {
  const [categories, setCategories] = useState([])
  const [apps, setApps] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedApp, setSelectedApp] = useState(null)
  const [viewMode, setViewMode] = useState('grid')
  const [loading, setLoading] = useState(false)
  const [installing, setInstalling] = useState({})

  useEffect(() => {
    fetchCategories()
    fetchApps()
  }, [])

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/appstore/categories')
      setCategories(response.data.categories || [])
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchApps = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/appstore/apps')
      setApps(response.data.apps || [])
    } catch (error) {
      console.error('Error fetching apps:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredApps = useMemo(() => {
    let filtered = apps

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(app => app.category === selectedCategory)
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(app =>
        app.name?.toLowerCase().includes(query) ||
        app.tagline?.toLowerCase().includes(query) ||
        app.description?.toLowerCase().includes(query)
      )
    }

    return filtered
  }, [apps, selectedCategory, searchQuery])

  const featuredApps = useMemo(() => {
    return apps.filter(app => app.featured)
  }, [apps])

  const handleInstall = async (appId) => {
    try {
      setInstalling(prev => ({ ...prev, [appId]: true }))
      await axios.post(`/api/appstore/apps/${appId}/install`)
      alert('App instalado com sucesso!')
    } catch (error) {
      console.error('Error installing app:', error)
      alert('Erro ao instalar app: ' + (error.response?.data?.detail || error.message))
    } finally {
      setInstalling(prev => ({ ...prev, [appId]: false }))
    }
  }

  const handleUninstall = async (appId) => {
    if (!confirm('Tem certeza que deseja desinstalar este app?')) return
    
    try {
      setInstalling(prev => ({ ...prev, [appId]: true }))
      await axios.post(`/api/appstore/apps/${appId}/uninstall`)
      alert('App desinstalado com sucesso!')
    } catch (error) {
      console.error('Error uninstalling app:', error)
      alert('Erro ao desinstalar app: ' + (error.response?.data?.detail || error.message))
    } finally {
      setInstalling(prev => ({ ...prev, [appId]: false }))
    }
  }

  if (selectedApp) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setSelectedApp(null)}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={20} />
          Voltar
        </button>

        <div className="bg-secondary rounded-lg p-6 space-y-6">
          {/* Header */}
          <div className="flex items-start gap-4">
            <img
              src={selectedApp.icon}
              alt={selectedApp.name}
              className="w-20 h-20 rounded-lg"
              onError={(e) => { e.target.style.display = 'none' }}
            />
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold">{selectedApp.name}</h2>
                  <p className="text-muted-foreground">{selectedApp.tagline}</p>
                </div>
                {selectedApp.featured && (
                  <div className="flex items-center gap-1 bg-yellow-500/20 text-yellow-500 px-3 py-1 rounded-full text-sm">
                    <Star size={14} fill="currentColor" />
                    Destaque
                  </div>
                )}
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <span>v{selectedApp.version}</span>
                <span>•</span>
                <span>{selectedApp.developer}</span>
                <span>•</span>
                <span>Porta: {selectedApp.port}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => handleInstall(selectedApp.id)}
              disabled={installing[selectedApp.id]}
              className="flex items-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-purple-500/50 rounded-lg transition-colors font-semibold"
            >
              <Download size={20} />
              {installing[selectedApp.id] ? 'Instalando...' : 'Instalar'}
            </button>
            <button
              onClick={() => handleUninstall(selectedApp.id)}
              disabled={installing[selectedApp.id]}
              className="flex items-center gap-2 px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
            >
              <X size={20} />
              Desinstalar
            </button>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Sobre</h3>
            <p className="text-muted-foreground leading-relaxed">{selectedApp.description}</p>
          </div>

          {/* Screenshots */}
          {selectedApp.screenshots && selectedApp.screenshots.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Screenshots</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {selectedApp.screenshots.map((screenshot, index) => (
                  <img
                    key={index}
                    src={screenshot}
                    alt={`Screenshot ${index + 1}`}
                    className="w-full rounded-lg border border-border"
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Technical Details */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-background rounded-lg">
            <div>
              <div className="text-sm text-muted-foreground">Categoria</div>
              <div className="font-semibold capitalize">{selectedApp.category}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Arquiteturas</div>
              <div className="font-semibold">{selectedApp.architectures?.join(', ')}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Autor</div>
              <div className="font-semibold">{selectedApp.author}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Versão</div>
              <div className="font-semibold">{selectedApp.version}</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">App Store</h2>
          <p className="text-muted-foreground">Descubra e instale aplicações Docker</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-purple-500' : 'bg-secondary hover:bg-secondary/80'}`}
          >
            <Grid size={20} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-purple-500' : 'bg-secondary hover:bg-secondary/80'}`}
          >
            <List size={20} />
          </button>
        </div>
      </div>

      {/* Featured Apps */}
      {featuredApps.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Star size={20} className="text-yellow-500" fill="currentColor" />
            Apps em Destaque
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredApps.map(app => (
              <button
                key={app.id}
                onClick={() => setSelectedApp(app)}
                className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg p-4 text-left hover:border-purple-500/50 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <img
                    src={app.icon}
                    alt={app.name}
                    className="w-12 h-12 rounded-lg"
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold truncate group-hover:text-purple-400 transition-colors">{app.name}</h4>
                    <p className="text-sm text-muted-foreground truncate">{app.tagline}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
          <input
            type="text"
            placeholder="Buscar apps..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 bg-secondary rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              selectedCategory === 'all'
                ? 'bg-purple-500 text-white'
                : 'bg-secondary hover:bg-secondary/80'
            }`}
          >
            Todos
          </button>
          {categories.map(category => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                selectedCategory === category.id
                  ? 'bg-purple-500 text-white'
                  : 'bg-secondary hover:bg-secondary/80'
              }`}
            >
              <span className="mr-1">{category.icon}</span>
              {category.name}
            </button>
          ))}
        </div>
      </div>

      {/* Apps Grid/List */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">
            {searchQuery || selectedCategory !== 'all' ? 'Resultados' : 'Todos os Apps'}
            <span className="text-sm text-muted-foreground ml-2">({filteredApps.length})</span>
          </h3>
        </div>

        {loading ? (
          <div className="text-center py-12 text-muted-foreground">
            <Package size={48} className="mx-auto mb-4 animate-pulse" />
            Carregando apps...
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Package size={48} className="mx-auto mb-4 opacity-50" />
            Nenhum app encontrado
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredApps.map(app => (
              <button
                key={app.id}
                onClick={() => setSelectedApp(app)}
                className="bg-secondary rounded-lg p-4 text-left hover:ring-2 hover:ring-purple-500 transition-all group"
              >
                <div className="flex items-start gap-3 mb-3">
                  <img
                    src={app.icon}
                    alt={app.name}
                    className="w-12 h-12 rounded-lg"
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold truncate group-hover:text-purple-400 transition-colors">{app.name}</h4>
                    <p className="text-xs text-muted-foreground">v{app.version}</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{app.tagline}</p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{app.category}</span>
                  {app.featured && (
                    <Star size={14} className="text-yellow-500" fill="currentColor" />
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredApps.map(app => (
              <button
                key={app.id}
                onClick={() => setSelectedApp(app)}
                className="w-full bg-secondary rounded-lg p-4 text-left hover:ring-2 hover:ring-purple-500 transition-all group flex items-center gap-4"
              >
                <img
                  src={app.icon}
                  alt={app.name}
                  className="w-16 h-16 rounded-lg flex-shrink-0"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold group-hover:text-purple-400 transition-colors">{app.name}</h4>
                    {app.featured && (
                      <Star size={14} className="text-yellow-500" fill="currentColor" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1 mb-1">{app.tagline}</p>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>v{app.version}</span>
                    <span>•</span>
                    <span className="capitalize">{app.category}</span>
                    <span>•</span>
                    <span>{app.developer}</span>
                  </div>
                </div>
                <ExternalLink size={20} className="text-muted-foreground group-hover:text-purple-400 transition-colors flex-shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default AppStoreApp
