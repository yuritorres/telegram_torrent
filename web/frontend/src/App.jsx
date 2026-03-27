import React from 'react'
import { BrowserRouter as Router } from 'react-router-dom'
import Desktop from './components/Desktop'
import Login from './components/Login'
import { SystemProvider } from './context/SystemContext'
import { AuthProvider, useAuth } from './context/AuthContext'

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login />
  }

  return (
    <SystemProvider>
      <Router>
        <div className="desktop">
          <Desktop />
        </div>
      </Router>
    </SystemProvider>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
