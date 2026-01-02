import { api, setStoredToken, clearStoredToken } from './api'
import { supabase } from '../lib/supabase'
import { User } from '../types'

interface DevLoginResponse {
  access_token: string
  token_type: string
  user: User
}

interface UserUpdate {
  display_name?: string
  avatar_url?: string
}

export const authService = {
  async getCurrentUser(): Promise<User | null> {
    try {
      return await api.get<User>('/auth/me')
    } catch {
      return null
    }
  },

  async signInWithEmail(email: string): Promise<{ error: Error | null }> {
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    return { error: error ? new Error(error.message) : null }
  },

  async signInWithDiscord(): Promise<{ error: Error | null }> {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'discord',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    return { error: error ? new Error(error.message) : null }
  },

  async linkDiscord(): Promise<{ error: Error | null }> {
    const { error } = await supabase.auth.linkIdentity({
      provider: 'discord',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    return { error: error ? new Error(error.message) : null }
  },

  async getSession() {
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error || !session) {
      return null
    }
    return session
  },

  async logout(): Promise<void> {
    clearStoredToken()
    await supabase.auth.signOut()
  },

  // Dev-only login
  async devLogin(userNumber: number = 1): Promise<User> {
    const response = await api.post<DevLoginResponse>(`/auth/dev-login/${userNumber}`)
    setStoredToken(response.access_token)
    return response.user
  },

  // Sync Supabase session to local storage (called by AuthContext)
  syncSession(accessToken: string | null) {
    if (accessToken) {
      setStoredToken(accessToken)
    } else {
      clearStoredToken()
    }
  },

  async updateUser(update: UserUpdate): Promise<User> {
    return api.put<User>('/auth/me', update)
  },
}
