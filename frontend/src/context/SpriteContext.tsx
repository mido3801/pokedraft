import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

export type SpriteStyle = 'default' | 'official-artwork' | 'home'

// Sprite URL paths for each style
const SPRITE_PATHS: Record<SpriteStyle, string> = {
  'default': '',
  'official-artwork': 'other/official-artwork',
  'home': 'other/home',
}

const SPRITE_BASE_URL = '/static/sprites'

interface SpriteContextType {
  spriteStyle: SpriteStyle
  setSpriteStyle: (style: SpriteStyle) => void
  getSpriteStyleLabel: (style: SpriteStyle) => string
  getSpriteUrl: (pokemonId: number) => string
}

const STORAGE_KEY = 'pokemon-sprite-style'

const SpriteContext = createContext<SpriteContextType | undefined>(undefined)

export function SpriteProvider({ children }: { children: ReactNode }) {
  const [spriteStyle, setSpriteStyleState] = useState<SpriteStyle>(() => {
    // Load from localStorage on init
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && ['default', 'official-artwork', 'home'].includes(stored)) {
      return stored as SpriteStyle
    }
    return 'official-artwork'
  })

  const setSpriteStyle = (style: SpriteStyle) => {
    setSpriteStyleState(style)
    localStorage.setItem(STORAGE_KEY, style)
  }

  const getSpriteStyleLabel = (style: SpriteStyle): string => {
    switch (style) {
      case 'default':
        return 'Pixel Art'
      case 'official-artwork':
        return 'Official Artwork'
      case 'home':
        return 'Home 3D'
      default:
        return style
    }
  }

  const getSpriteUrl = useCallback((pokemonId: number): string => {
    const subpath = SPRITE_PATHS[spriteStyle]
    if (subpath) {
      return `${SPRITE_BASE_URL}/${subpath}/${pokemonId}.png`
    }
    return `${SPRITE_BASE_URL}/${pokemonId}.png`
  }, [spriteStyle])

  return (
    <SpriteContext.Provider
      value={{
        spriteStyle,
        setSpriteStyle,
        getSpriteStyleLabel,
        getSpriteUrl,
      }}
    >
      {children}
    </SpriteContext.Provider>
  )
}

export function useSprite() {
  const context = useContext(SpriteContext)
  if (context === undefined) {
    throw new Error('useSprite must be used within a SpriteProvider')
  }
  return context
}
