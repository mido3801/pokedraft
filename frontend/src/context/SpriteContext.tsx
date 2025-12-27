import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { storage, type SpriteStyle } from '../utils/storage'

export type { SpriteStyle }

// Sprite URL paths for each style (using PokeAPI CDN)
const SPRITE_PATHS: Record<SpriteStyle, string> = {
  'default': '',
  'official-artwork': 'other/official-artwork',
  'home': 'other/home',
}

const SPRITE_BASE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon'

interface SpriteContextType {
  spriteStyle: SpriteStyle
  setSpriteStyle: (style: SpriteStyle) => void
  getSpriteStyleLabel: (style: SpriteStyle) => string
  getSpriteUrl: (pokemonId: number) => string
}

const SpriteContext = createContext<SpriteContextType | undefined>(undefined)

export function SpriteProvider({ children }: { children: ReactNode }) {
  const [spriteStyle, setSpriteStyleState] = useState<SpriteStyle>(() => {
    return storage.getSpriteStyle()
  })

  const setSpriteStyle = (style: SpriteStyle) => {
    setSpriteStyleState(style)
    storage.setSpriteStyle(style)
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
