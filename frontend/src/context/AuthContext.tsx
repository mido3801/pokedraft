import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User } from '../types'
import { authService } from '../services/auth'
import { supabase } from '../lib/supabase'

interface AuthContextType {
  user: User | null
  loading: boolean
  signInWithEmail: (email: string) => Promise<{ error: Error | null }>
  signInWithDiscord: () => Promise<{ error: Error | null }>
  linkDiscord: () => Promise<{ error: Error | null }>
  devLogin: (userNumber?: number) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount (Supabase or dev token)
    const initAuth = async () => {
      try {
        // First check for Supabase session
        const session = await authService.getSession()
        if (session?.access_token) {
          authService.syncSession(session.access_token)
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
          return
        }

        // Fall back to checking for stored dev token
        const currentUser = await authService.getCurrentUser()
        if (currentUser) {
          setUser(currentUser)
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
      } finally {
        setLoading(false)
      }
    }

    initAuth()

    // Subscribe to Supabase auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session?.access_token) {
          authService.syncSession(session.access_token)
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
        } else if (event === 'SIGNED_OUT') {
          authService.syncSession(null)
          setUser(null)
        } else if (event === 'TOKEN_REFRESHED' && session?.access_token) {
          authService.syncSession(session.access_token)
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signInWithEmail = async (email: string) => {
    return authService.signInWithEmail(email)
  }

  const signInWithDiscord = async () => {
    return authService.signInWithDiscord()
  }

  const linkDiscord = async () => {
    return authService.linkDiscord()
  }

  const devLogin = async (userNumber: number = 1) => {
    try {
      const user = await authService.devLogin(userNumber)
      setUser(user)
    } catch (error) {
      console.error('Dev login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    await authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithEmail,
        signInWithDiscord,
        linkDiscord,
        devLogin,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
