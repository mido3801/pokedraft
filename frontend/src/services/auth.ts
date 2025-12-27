import { api, setStoredToken, clearStoredToken } from './api'
import { User } from '../types'

interface DevLoginResponse {
  access_token: string
  token_type: string
  user: User
}

export const authService = {
  async getCurrentUser(): Promise<User | null> {
    try {
      return await api.get<User>('/auth/me')
    } catch {
      return null
    }
  },

  async login(): Promise<void> {
    // Redirect to Supabase OAuth
    window.location.href = '/api/v1/auth/login'
  },

  async devLogin(userNumber: number = 1): Promise<User> {
    const response = await api.post<DevLoginResponse>(`/auth/dev-login/${userNumber}`)
    setStoredToken(response.access_token)
    return response.user
  },

  async logout(): Promise<void> {
    clearStoredToken()
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore errors - token is already cleared
    }
  },
}
