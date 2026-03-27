import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from '../utils/axios'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
      verifyToken(storedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  const verifyToken = async (tokenToVerify) => {
    try {
      const response = await axios.get('/api/auth/verify')
      setIsAuthenticated(true)
      setUser({ username: response.data.username })
      setIsLoading(false)
    } catch (error) {
      console.error('Token verification failed:', error)
      logout()
    }
  }

  const login = async (username, password) => {
    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password,
      })

      const { access_token } = response.data
      
      localStorage.setItem('auth_token', access_token)
      setToken(access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      setIsAuthenticated(true)
      setUser({ username })
      
      return { success: true }
    } catch (error) {
      console.error('Login failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || 'Login falhou. Verifique suas credenciais.',
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setIsAuthenticated(false)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
    setIsLoading(false)
  }

  const value = {
    isAuthenticated,
    isLoading,
    user,
    token,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
