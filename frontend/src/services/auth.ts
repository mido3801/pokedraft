import { api } from './api'
import { User } from '../types'

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

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },
}
