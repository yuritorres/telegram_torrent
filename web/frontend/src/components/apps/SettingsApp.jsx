import React from 'react'
import { useSystem } from '../../context/SystemContext'
import { Wallpaper, Check } from 'lucide-react'

const SettingsApp = () => {
  const { wallpaper, changeWallpaper } = useSystem()

  const wallpapers = [
    {
      id: 'gradient-1',
      name: 'Gradiente Azul',
      preview: 'from-slate-900 via-blue-900 to-slate-900'
    },
    {
      id: 'gradient-2',
      name: 'Gradiente Roxo',
      preview: 'from-purple-900 via-pink-900 to-purple-900'
    },
    {
      id: 'gradient-3',
      name: 'Gradiente Verde',
      preview: 'from-emerald-900 via-teal-900 to-emerald-900'
    },
    {
      id: 'gradient-4',
      name: 'Gradiente Laranja',
      preview: 'from-orange-900 via-red-900 to-orange-900'
    },
    {
      id: 'gradient-5',
      name: 'Gradiente Ciano',
      preview: 'from-cyan-900 via-blue-900 to-cyan-900'
    },
    {
      id: 'gradient-6',
      name: 'Noite Escura',
      preview: 'from-gray-900 via-slate-900 to-black'
    },
    {
      id: 'gradient-7',
      name: 'Aurora Boreal',
      preview: 'from-indigo-900 via-purple-900 to-pink-900'
    },
    {
      id: 'gradient-8',
      name: 'Pôr do Sol',
      preview: 'from-yellow-900 via-orange-900 to-red-900'
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Wallpaper size={28} className="text-primary" />
        <h2 className="text-2xl font-bold">Configurações</h2>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Papel de Parede</h3>
        <div className="grid grid-cols-2 gap-4">
          {wallpapers.map((wp) => (
            <button
              key={wp.id}
              onClick={() => changeWallpaper(wp.id)}
              className={`relative group rounded-lg overflow-hidden transition-all ${
                wallpaper === wp.id
                  ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
                  : 'hover:ring-2 hover:ring-primary/50'
              }`}
            >
              <div
                className={`h-24 bg-gradient-to-br ${wp.preview} flex items-center justify-center`}
              >
                {wallpaper === wp.id && (
                  <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                    <Check size={32} className="text-white" />
                  </div>
                )}
              </div>
              <div className="bg-secondary p-2 text-center">
                <p className="text-sm font-medium">{wp.name}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SettingsApp
