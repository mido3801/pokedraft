import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { pokemonService } from '../services/pokemon'
import { queryKeys } from '../services/queryKeys'
import { Pokemon } from '../types'
import { SpriteStyle } from '../context/SpriteContext'

/**
 * Cache time constants for Pokemon data
 * Pokemon data is essentially static, so we can cache it for a long time
 */
const POKEMON_STALE_TIME = 1000 * 60 * 60 // 1 hour - data rarely changes
const POKEMON_GC_TIME = 1000 * 60 * 60 * 24 // 24 hours - keep in memory longer

/**
 * Hook to fetch all Pokemon for the box view (draft pool selection)
 * This is one of the most commonly used queries, so it benefits from aggressive caching
 */
export function usePokemonBox(spriteStyle: SpriteStyle = 'default') {
  return useQuery({
    queryKey: queryKeys.pokemon.box(spriteStyle),
    queryFn: () => pokemonService.getAllForBox(spriteStyle),
    staleTime: POKEMON_STALE_TIME,
    gcTime: POKEMON_GC_TIME,
  })
}

/**
 * Hook to fetch Pokemon types
 * Types never change, so we can cache indefinitely
 */
export function usePokemonTypes() {
  return useQuery({
    queryKey: queryKeys.pokemon.types,
    queryFn: () => pokemonService.getTypes(),
    staleTime: Infinity, // Types never change
    gcTime: POKEMON_GC_TIME,
  })
}

/**
 * Hook to fetch a single Pokemon by ID
 */
export function usePokemonById(
  id: number,
  spriteStyle?: SpriteStyle,
  options?: Omit<UseQueryOptions<Pokemon, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.pokemon.byId(id, spriteStyle),
    queryFn: () => pokemonService.getPokemon(id, spriteStyle),
    staleTime: POKEMON_STALE_TIME,
    gcTime: POKEMON_GC_TIME,
    ...options,
  })
}

/**
 * Hook to fetch a single Pokemon by name
 */
export function usePokemonByName(
  name: string,
  spriteStyle?: SpriteStyle,
  options?: Omit<UseQueryOptions<Pokemon, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: queryKeys.pokemon.byName(name, spriteStyle),
    queryFn: () => pokemonService.getPokemonByName(name, spriteStyle),
    staleTime: POKEMON_STALE_TIME,
    gcTime: POKEMON_GC_TIME,
    enabled: !!name,
    ...options,
  })
}

/**
 * Type for the return value of usePokemonBox
 */
export type UsePokemonBoxResult = ReturnType<typeof usePokemonBox>
