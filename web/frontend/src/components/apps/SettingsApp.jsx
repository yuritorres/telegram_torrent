import React, { useState, useEffect } from 'react'
import { useSystem } from '../../context/SystemContext'
import { 
  Settings, Wallpaper, Check, Monitor, Wifi, HardDrive, Users, 
  Bell, Shield, Info, ChevronRight, Cpu, MemoryStick, 
  Network, Server, Database, Activity, Globe, Lock,
  Eye, EyeOff, Save, RefreshCw, AlertCircle, CheckCircle2,
  Smartphone, Mail, Key, User, UserPlus, Trash2, Edit2
} from 'lucide-react'
import axios from '../../utils/axios'

const SettingsApp = () => {
  const { wallpaper, changeWallpaper, systemStatus } = useSystem()
  const [activeSection, setActiveSection] = useState('system')
  const [systemInfo, setSystemInfo] = useState(null)
  const [networkInfo, setNetworkInfo] = useState(null)
  const [storageInfo, setStorageInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [notification, setNotification] = useState(null)

  useEffect(() => {
    loadSystemInfo()
    loadNetworkInfo()
    loadStorageInfo()
  }, [])

  const loadSystemInfo = async () => {
    try {
      const response = await axios.get('/api/system/info')
      setSystemInfo(response.data)
    } catch (error) {
      console.error('Error loading system info:', error)
    }
  }

  const loadNetworkInfo = async () => {
    try {
      const response = await axios.get('/api/system/network')
      setNetworkInfo(response.data)
    } catch (error) {
      console.error('Error loading network info:', error)
    }
  }

  const loadStorageInfo = async () => {
    try {
      const response = await axios.get('/api/system/storage')
      setStorageInfo(response.data)
    } catch (error) {
      console.error('Error loading storage info:', error)
    }
  }

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A'
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${days}d ${hours}h ${minutes}m`
  }

  const wallpapers = [
    { id: 'gradient-1', name: 'Gradiente Azul', preview: 'from-slate-900 via-blue-900 to-slate-900' },
    { id: 'gradient-2', name: 'Gradiente Roxo', preview: 'from-purple-900 via-pink-900 to-purple-900' },
    { id: 'gradient-3', name: 'Gradiente Verde', preview: 'from-emerald-900 via-teal-900 to-emerald-900' },
    { id: 'gradient-4', name: 'Gradiente Laranja', preview: 'from-orange-900 via-red-900 to-orange-900' },
    { id: 'gradient-5', name: 'Gradiente Ciano', preview: 'from-cyan-900 via-blue-900 to-cyan-900' },
    { id: 'gradient-6', name: 'Noite Escura', preview: 'from-gray-900 via-slate-900 to-black' },
    { id: 'gradient-7', name: 'Aurora Boreal', preview: 'from-indigo-900 via-purple-900 to-pink-900' },
    { id: 'gradient-8', name: 'Pôr do Sol', preview: 'from-yellow-900 via-orange-900 to-red-900' }
  ]

  const sections = [
    { id: 'system', name: 'Informações do Sistema', icon: Monitor },
    { id: 'network', name: 'Rede', icon: Wifi },
    { id: 'storage', name: 'Armazenamento', icon: HardDrive },
    { id: 'users', name: 'Usuários', icon: Users },
    { id: 'appearance', name: 'Aparência', icon: Wallpaper },
    { id: 'security', name: 'Segurança', icon: Shield },
    { id: 'notifications', name: 'Notificações', icon: Bell },
    { id: 'about', name: 'Sobre', icon: Info }
  ]

  const renderSystemSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Monitor className="text-blue-400" />
          Informações do Sistema
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoCard icon={Cpu} label="CPU" value={systemInfo?.cpu || 'N/A'} />
          <InfoCard icon={MemoryStick} label="Memória" value={systemInfo?.memory ? `${systemInfo.memory.used_percent}%` : 'N/A'} />
          <InfoCard icon={Server} label="Sistema Operacional" value={systemInfo?.os || 'N/A'} />
          <InfoCard icon={Activity} label="Uptime" value={formatUptime(systemInfo?.uptime)} />
        </div>
      </div>

      {systemInfo?.memory && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <MemoryStick size={18} className="text-purple-400" />
            Uso de Memória
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Usado: {formatBytes(systemInfo.memory.used)}</span>
              <span>Total: {formatBytes(systemInfo.memory.total)}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all"
                style={{ width: `${systemInfo.memory.used_percent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {systemInfo?.cpu_usage && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Cpu size={18} className="text-green-400" />
            Uso de CPU
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Uso Atual</span>
              <span className="font-bold">{systemInfo.cpu_usage}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full transition-all"
                style={{ width: `${systemInfo.cpu_usage}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderNetworkSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Wifi className="text-blue-400" />
          Configurações de Rede
        </h3>
        <div className="space-y-4">
          {networkInfo?.interfaces?.map((iface, idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <Network size={18} className="text-cyan-400" />
                  {iface.name}
                </h4>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  iface.status === 'up' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {iface.status === 'up' ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">IP:</span>
                  <span className="ml-2 font-mono">{iface.ip || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400">MAC:</span>
                  <span className="ml-2 font-mono text-xs">{iface.mac || 'N/A'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <Globe size={18} className="text-blue-400" />
          Configurações DNS
        </h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">DNS Primário:</span>
            <span className="font-mono">{networkInfo?.dns?.primary || '8.8.8.8'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">DNS Secundário:</span>
            <span className="font-mono">{networkInfo?.dns?.secondary || '8.8.4.4'}</span>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStorageSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <HardDrive className="text-purple-400" />
          Armazenamento
        </h3>
        <div className="space-y-4">
          {storageInfo?.disks?.map((disk, idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <Database size={18} className="text-purple-400" />
                  {disk.mountpoint}
                </h4>
                <span className="text-sm text-gray-400">{disk.device}</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Usado: {formatBytes(disk.used)}</span>
                  <span>Total: {formatBytes(disk.total)}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all ${
                      disk.percent > 90 ? 'bg-gradient-to-r from-red-500 to-orange-500' :
                      disk.percent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                      'bg-gradient-to-r from-purple-500 to-pink-500'
                    }`}
                    style={{ width: `${disk.percent}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Livre: {formatBytes(disk.free)}</span>
                  <span className="font-bold">{disk.percent}%</span>
                </div>
              </div>

              {disk.health && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="flex items-center gap-2 text-sm">
                    <Activity size={16} className="text-green-400" />
                    <span className="text-gray-400">Saúde do Disco:</span>
                    <span className={`font-medium ${
                      disk.health === 'good' ? 'text-green-400' : 
                      disk.health === 'warning' ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {disk.health === 'good' ? 'Bom' : disk.health === 'warning' ? 'Atenção' : 'Crítico'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderUsersSection = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <Users className="text-blue-400" />
          Gerenciamento de Usuários
        </h3>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 transition-colors">
          <UserPlus size={18} />
          Adicionar Usuário
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="divide-y divide-gray-700">
          <UserRow name="Admin" email="admin@telegram-torrent.local" role="Administrador" isActive={true} />
          <UserRow name="Usuário" email="user@telegram-torrent.local" role="Usuário" isActive={true} />
        </div>
      </div>
    </div>
  )

  const renderAppearanceSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Wallpaper className="text-purple-400" />
          Papel de Parede
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {wallpapers.map((wp) => (
            <button
              key={wp.id}
              onClick={() => {
                changeWallpaper(wp.id)
                showNotification('Papel de parede alterado!')
              }}
              className={`relative group rounded-lg overflow-hidden transition-all ${
                wallpaper === wp.id
                  ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-900'
                  : 'hover:ring-2 hover:ring-blue-400/50'
              }`}
            >
              <div className={`h-24 bg-gradient-to-br ${wp.preview} flex items-center justify-center`}>
                {wallpaper === wp.id && (
                  <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                    <Check size={32} className="text-white" />
                  </div>
                )}
              </div>
              <div className="bg-gray-800 p-2 text-center">
                <p className="text-sm font-medium">{wp.name}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="font-semibold mb-3">Tema</h4>
        <div className="flex gap-3">
          <button className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
            Escuro (Atual)
          </button>
          <button className="flex-1 px-4 py-3 bg-gray-700/50 hover:bg-gray-600 rounded-lg transition-colors opacity-50 cursor-not-allowed">
            Claro (Em breve)
          </button>
        </div>
      </div>
    </div>
  )

  const renderSecuritySection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Shield className="text-red-400" />
          Segurança
        </h3>
        
        <div className="space-y-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Lock size={18} className="text-yellow-400" />
              Autenticação
            </h4>
            <div className="space-y-3">
              <SettingToggle label="Autenticação de dois fatores" enabled={false} />
              <SettingToggle label="Exigir senha forte" enabled={true} />
              <SettingToggle label="Timeout de sessão automático" enabled={true} />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Key size={18} className="text-blue-400" />
              Alterar Senha
            </h4>
            <div className="space-y-3">
              <input 
                type="password" 
                placeholder="Senha atual" 
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <input 
                type="password" 
                placeholder="Nova senha" 
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <input 
                type="password" 
                placeholder="Confirmar nova senha" 
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center gap-2 transition-colors">
                <Save size={18} />
                Salvar Nova Senha
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderNotificationsSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Bell className="text-yellow-400" />
          Notificações
        </h3>
        
        <div className="space-y-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3">Notificações do Sistema</h4>
            <div className="space-y-3">
              <SettingToggle label="Torrents concluídos" enabled={true} />
              <SettingToggle label="Novos itens no Jellyfin" enabled={true} />
              <SettingToggle label="Containers Docker parados" enabled={false} />
              <SettingToggle label="Atualizações do sistema" enabled={true} />
              <SettingToggle label="Alertas de armazenamento" enabled={true} />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Smartphone size={18} className="text-blue-400" />
              Notificações Telegram
            </h4>
            <div className="space-y-3">
              <SettingToggle label="Enviar notificações via Telegram" enabled={true} />
              <SettingToggle label="Notificações de erro" enabled={true} />
              <SettingToggle label="Resumo diário" enabled={false} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderAboutSection = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Info className="text-blue-400" />
          Sobre o Sistema
        </h3>
        
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <Settings size={40} className="text-white" />
          </div>
          <h4 className="text-2xl font-bold mb-2">Telegram Torrent</h4>
          <p className="text-gray-400 mb-4">Sistema de gerenciamento integrado</p>
          <div className="inline-block px-4 py-2 bg-blue-600/20 text-blue-400 rounded-full text-sm font-medium mb-6">
            Versão 0.0.1.2-alpha
          </div>
          
          <div className="space-y-3 text-sm text-left">
            <InfoRow label="Desenvolvedor" value="Yuri Torres" />
            <InfoRow label="Licença" value="MIT" />
            <InfoRow label="Repositório" value="github.com/yuritorres/telegram_torrent" />
            <InfoRow label="Última atualização" value="Abril 2026" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="font-semibold mb-3">Componentes do Sistema</h4>
          <div className="space-y-2 text-sm">
            <ComponentRow name="qBittorrent" version="4.6.x" status="running" />
            <ComponentRow name="Jellyfin" version="10.8.x" status="running" />
            <ComponentRow name="Docker" version="24.x" status="running" />
            <ComponentRow name="Telegram Bot" version="20.x" status="running" />
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="flex h-full bg-gray-900 text-gray-100">
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 ${
          notification.type === 'success' ? 'bg-green-600' : 'bg-red-600'
        }`}>
          {notification.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      <div className="w-64 bg-gray-800 border-r border-gray-700 overflow-y-auto">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Settings size={24} className="text-blue-400" />
            Configurações
          </h2>
        </div>
        <nav className="p-2">
          {sections.map((section) => {
            const Icon = section.icon
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg mb-1 transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-600 text-white'
                    : 'hover:bg-gray-700 text-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={20} />
                  <span className="font-medium">{section.name}</span>
                </div>
                <ChevronRight size={16} />
              </button>
            )
          })}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeSection === 'system' && renderSystemSection()}
        {activeSection === 'network' && renderNetworkSection()}
        {activeSection === 'storage' && renderStorageSection()}
        {activeSection === 'users' && renderUsersSection()}
        {activeSection === 'appearance' && renderAppearanceSection()}
        {activeSection === 'security' && renderSecuritySection()}
        {activeSection === 'notifications' && renderNotificationsSection()}
        {activeSection === 'about' && renderAboutSection()}
      </div>
    </div>
  )
}

const InfoCard = ({ icon: Icon, label, value }) => (
  <div className="bg-gray-800 rounded-lg p-4">
    <div className="flex items-center gap-3 mb-2">
      <Icon size={20} className="text-blue-400" />
      <span className="text-sm text-gray-400">{label}</span>
    </div>
    <div className="text-lg font-bold">{value}</div>
  </div>
)

const InfoRow = ({ label, value }) => (
  <div className="flex justify-between py-2 border-b border-gray-700 last:border-0">
    <span className="text-gray-400">{label}:</span>
    <span className="font-medium">{value}</span>
  </div>
)

const ComponentRow = ({ name, version, status }) => (
  <div className="flex items-center justify-between py-2 px-3 bg-gray-700/50 rounded">
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${
        status === 'running' ? 'bg-green-400' : 'bg-red-400'
      }`} />
      <span className="font-medium">{name}</span>
    </div>
    <span className="text-gray-400">{version}</span>
  </div>
)

const UserRow = ({ name, email, role, isActive }) => (
  <div className="p-4 hover:bg-gray-700/50 transition-colors">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
          <User size={20} className="text-white" />
        </div>
        <div>
          <div className="font-medium">{name}</div>
          <div className="text-sm text-gray-400">{email}</div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">{role}</span>
        <div className="flex gap-2">
          <button className="p-2 hover:bg-gray-600 rounded transition-colors">
            <Edit2 size={16} />
          </button>
          <button className="p-2 hover:bg-red-600 rounded transition-colors">
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  </div>
)

const SettingToggle = ({ label, enabled }) => {
  const [isEnabled, setIsEnabled] = React.useState(enabled)
  
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm">{label}</span>
      <button
        onClick={() => setIsEnabled(!isEnabled)}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          isEnabled ? 'bg-blue-600' : 'bg-gray-600'
        }`}
      >
        <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
          isEnabled ? 'translate-x-6' : 'translate-x-0'
        }`} />
      </button>
    </div>
  )
}

export default SettingsApp
