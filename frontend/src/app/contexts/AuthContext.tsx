'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

// Types
interface User {
  id: number
  email: string
  is_active: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load token from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window === 'undefined') {
      setIsLoading(false)
      return
    }

    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
      // Fetch user info
      fetchUserInfo(storedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  // Fetch current user info
  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('auth_token')
        setToken(null)
        setUser(null)
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      localStorage.removeItem('auth_token')
      setToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  // Register function
  const register = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    const data = await response.json()
    const newToken = data.access_token

    // Store token (client-side only)
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', newToken)
    }
    setToken(newToken)

    // Fetch user info
    await fetchUserInfo(newToken)
  }

  // Login function
  const login = async (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', email) // OAuth2 uses 'username' field
    formData.append('password', password)

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    const newToken = data.access_token

    // Store token (client-side only)
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', newToken)
    }
    setToken(newToken)

    // Fetch user info
    await fetchUserInfo(newToken)
  }

  // Logout function
  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isLoading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
