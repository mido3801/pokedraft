import { api } from './api'
import { Pokemon, PokemonBoxResponse } from '../types'
import { SpriteStyle } from '../context/SpriteContext'

interface PokemonListResponse {
  pokemon: Pokemon[]
  total: number
  limit: number
  offset: number
}

interface PokemonType {
  id: number
  name: string
}

interface SpriteUrls {
  default: string
  'official-artwork': string
  home: string
  shiny: string
  'shiny-official-artwork': string
  'shiny-home': string
}

interface SearchParams {
  query?: string
  type?: string
  generation?: number
  is_legendary?: boolean
  is_mythical?: boolean
  limit?: number
  offset?: number
  sprite_style?: SpriteStyle
}

export const pokemonService = {
  async getPokemon(id: number, spriteStyle?: SpriteStyle): Promise<Pokemon> {
    const params = new URLSearchParams()
    if (spriteStyle) params.set('sprite_style', spriteStyle)
    const queryString = params.toString()
    return api.get<Pokemon>(`/pokemon/${id}${queryString ? `?${queryString}` : ''}`)
  },

  async getPokemonByName(name: string, spriteStyle?: SpriteStyle): Promise<Pokemon> {
    const params = new URLSearchParams()
    if (spriteStyle) params.set('sprite_style', spriteStyle)
    const queryString = params.toString()
    return api.get<Pokemon>(`/pokemon/name/${name}${queryString ? `?${queryString}` : ''}`)
  },

  async searchPokemon(params: SearchParams): Promise<PokemonListResponse> {
    const searchParams = new URLSearchParams()
    if (params.query) searchParams.set('query', params.query)
    if (params.type) searchParams.set('type', params.type)
    if (params.generation) searchParams.set('generation', params.generation.toString())
    if (params.is_legendary !== undefined) searchParams.set('is_legendary', params.is_legendary.toString())
    if (params.is_mythical !== undefined) searchParams.set('is_mythical', params.is_mythical.toString())
    if (params.limit) searchParams.set('limit', params.limit.toString())
    if (params.offset) searchParams.set('offset', params.offset.toString())
    if (params.sprite_style) searchParams.set('sprite_style', params.sprite_style)

    const queryString = searchParams.toString()
    return api.get<PokemonListResponse>(`/pokemon${queryString ? `?${queryString}` : ''}`)
  },

  async getGenerationPokemon(generation: number): Promise<Array<{ id: number; name: string }>> {
    return api.get(`/pokemon/generation/${generation}`)
  },

  async getTypes(): Promise<PokemonType[]> {
    return api.get<PokemonType[]>('/pokemon/types')
  },

  async getPokemonSprites(id: number): Promise<SpriteUrls> {
    return api.get<SpriteUrls>(`/pokemon/${id}/sprites`)
  },

  async getAllForBox(spriteStyle: SpriteStyle = 'default'): Promise<PokemonBoxResponse> {
    return api.get<PokemonBoxResponse>(`/pokemon/box?sprite_style=${spriteStyle}`)
  },
}
