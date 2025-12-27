/**
 * Centralized localStorage utility with typed keys.
 * Provides type-safe access to all localStorage operations.
 */

// Storage key constants
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'pokedraft_token',
  SPRITE_STYLE: 'pokemon-sprite-style',
  LAST_DRAFT_ID: 'last_draft_id',
} as const

// Draft-specific keys (dynamic)
export const getDraftKeys = (draftId: string) => ({
  session: `draft_session_${draftId}`,
  team: `draft_team_${draftId}`,
  rejoin: `draft_rejoin_${draftId}`,
})

// Type for sprite styles
export type SpriteStyle = 'default' | 'official-artwork' | 'home'

// Generic storage helpers
export const storage = {
  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch {
      return localStorage.getItem(key) as T | null
    }
  },

  set<T>(key: string, value: T): void {
    if (typeof value === 'string') {
      localStorage.setItem(key, value)
    } else {
      localStorage.setItem(key, JSON.stringify(value))
    }
  },

  remove(key: string): void {
    localStorage.removeItem(key)
  },

  // Auth token helpers
  getToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
  },

  setToken(token: string): void {
    localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token)
  },

  clearToken(): void {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
  },

  // Sprite style helpers
  getSpriteStyle(): SpriteStyle {
    const stored = localStorage.getItem(STORAGE_KEYS.SPRITE_STYLE)
    if (stored && ['default', 'official-artwork', 'home'].includes(stored)) {
      return stored as SpriteStyle
    }
    return 'official-artwork'
  },

  setSpriteStyle(style: SpriteStyle): void {
    localStorage.setItem(STORAGE_KEYS.SPRITE_STYLE, style)
  },

  // Draft session helpers
  getDraftSession(draftId: string): { session: string | null; team: string | null; rejoin: string | null } {
    const keys = getDraftKeys(draftId)
    return {
      session: localStorage.getItem(keys.session),
      team: localStorage.getItem(keys.team),
      rejoin: localStorage.getItem(keys.rejoin),
    }
  },

  setDraftSession(draftId: string, data: { session: string; team: string; rejoin: string }): void {
    const keys = getDraftKeys(draftId)
    localStorage.setItem(keys.session, data.session)
    localStorage.setItem(keys.team, data.team)
    localStorage.setItem(keys.rejoin, data.rejoin)
    localStorage.setItem(STORAGE_KEYS.LAST_DRAFT_ID, draftId)
  },

  clearDraftSession(draftId: string): void {
    const keys = getDraftKeys(draftId)
    localStorage.removeItem(keys.session)
    localStorage.removeItem(keys.team)
    localStorage.removeItem(keys.rejoin)
  },

  getLastDraftId(): string | null {
    return localStorage.getItem(STORAGE_KEYS.LAST_DRAFT_ID)
  },
}
