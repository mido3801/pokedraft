import { create } from 'zustand'
import { DraftState, DraftPick, Pokemon, DraftTeam } from '../types'

type StatKey = 'hp' | 'attack' | 'defense' | 'special-attack' | 'special-defense' | 'speed'

interface DraftStore {
  // State
  draftState: DraftState | null
  secondsRemaining: number | null
  selectedPokemon: Pokemon | null
  searchQuery: string
  typeFilter: string | null
  generationFilter: number | null
  bstMin: number | null
  bstMax: number | null
  statFilter: StatKey | null
  statMin: number | null
  abilityFilter: string
  legendaryFilter: 'all' | 'legendary' | 'mythical' | 'regular'

  // Actions
  setDraftState: (state: DraftState) => void
  updatePick: (pick: DraftPick) => void
  addTeam: (teamId: string, displayName: string) => void
  setTimerEnd: (timerEnd: string) => void
  setSecondsRemaining: (seconds: number) => void
  setSelectedPokemon: (pokemon: Pokemon | null) => void
  setSearchQuery: (query: string) => void
  setTypeFilter: (type: string | null) => void
  setGenerationFilter: (gen: number | null) => void
  setBstMin: (min: number | null) => void
  setBstMax: (max: number | null) => void
  setStatFilter: (stat: StatKey | null) => void
  setStatMin: (min: number | null) => void
  setAbilityFilter: (ability: string) => void
  setLegendaryFilter: (filter: 'all' | 'legendary' | 'mythical' | 'regular') => void
  clearFilters: () => void
  reset: () => void

  // Computed
  getCurrentTeam: () => DraftTeam | null
  getFilteredPokemon: () => Pokemon[]
  isMyTurn: (myTeamId: string | null) => boolean
}

export const useDraftStore = create<DraftStore>((set, get) => ({
  // Initial state
  draftState: null,
  secondsRemaining: null,
  selectedPokemon: null,
  searchQuery: '',
  typeFilter: null,
  generationFilter: null,
  bstMin: null,
  bstMax: null,
  statFilter: null,
  statMin: null,
  abilityFilter: '',
  legendaryFilter: 'all',

  // Actions
  setDraftState: (state) => set({ draftState: state }),

  addTeam: (teamId, displayName) =>
    set((store) => {
      if (!store.draftState) return store

      // Check if team already exists
      if (store.draftState.teams.some((t) => t.team_id === teamId)) {
        return store
      }

      const newTeam = {
        team_id: teamId,
        display_name: displayName,
        draft_position: store.draftState.teams.length,
        pokemon: [],
      }

      return {
        draftState: {
          ...store.draftState,
          teams: [...store.draftState.teams, newTeam],
        },
      }
    }),

  updatePick: (pick) =>
    set((store) => {
      if (!store.draftState) return store

      // Update picks list
      const picks = [...store.draftState.picks, pick]

      // Remove Pokemon from available list
      const available_pokemon = store.draftState.available_pokemon.filter(
        (p) => p.id !== pick.pokemon_id
      )

      // Update team's Pokemon list
      const teams = store.draftState.teams.map((team) => {
        if (team.team_id === pick.team_id) {
          return {
            ...team,
            pokemon: [...team.pokemon, pick.pokemon_id],
          }
        }
        return team
      })

      return {
        draftState: {
          ...store.draftState,
          picks,
          available_pokemon,
          teams,
          current_pick: store.draftState.current_pick + 1,
        },
      }
    }),

  setTimerEnd: (timerEnd) =>
    set((store) => ({
      draftState: store.draftState
        ? { ...store.draftState, timer_end: timerEnd }
        : null,
    })),

  setSecondsRemaining: (seconds) => set({ secondsRemaining: seconds }),

  setSelectedPokemon: (pokemon) => set({ selectedPokemon: pokemon }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setTypeFilter: (type) => set({ typeFilter: type }),

  setGenerationFilter: (gen) => set({ generationFilter: gen }),

  setBstMin: (min) => set({ bstMin: min }),

  setBstMax: (max) => set({ bstMax: max }),

  setStatFilter: (stat) => set({ statFilter: stat }),

  setStatMin: (min) => set({ statMin: min }),

  setAbilityFilter: (ability) => set({ abilityFilter: ability }),

  setLegendaryFilter: (filter) => set({ legendaryFilter: filter }),

  clearFilters: () =>
    set({
      searchQuery: '',
      typeFilter: null,
      generationFilter: null,
      bstMin: null,
      bstMax: null,
      statFilter: null,
      statMin: null,
      abilityFilter: '',
      legendaryFilter: 'all',
    }),

  reset: () =>
    set({
      draftState: null,
      secondsRemaining: null,
      selectedPokemon: null,
      searchQuery: '',
      typeFilter: null,
      generationFilter: null,
      bstMin: null,
      bstMax: null,
      statFilter: null,
      statMin: null,
      abilityFilter: '',
      legendaryFilter: 'all',
    }),

  // Computed values
  getCurrentTeam: () => {
    const { draftState } = get()
    if (!draftState || draftState.pick_order.length === 0) return null

    const currentPick = draftState.current_pick
    const numTeams = draftState.pick_order.length

    let teamIndex: number

    if (draftState.format === 'snake') {
      const round = Math.floor(currentPick / numTeams)
      const positionInRound = currentPick % numTeams
      teamIndex = round % 2 === 0 ? positionInRound : numTeams - 1 - positionInRound
    } else {
      teamIndex = currentPick % numTeams
    }

    const teamId = draftState.pick_order[teamIndex]
    return draftState.teams.find((t) => t.team_id === teamId) || null
  },

  getFilteredPokemon: () => {
    const {
      draftState,
      searchQuery,
      typeFilter,
      generationFilter,
      bstMin,
      bstMax,
      statFilter,
      statMin,
      abilityFilter,
      legendaryFilter,
    } = get()
    if (!draftState) return []

    let filtered = draftState.available_pokemon

    // Name search
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((p) => p.name.toLowerCase().includes(query))
    }

    // Type filter
    if (typeFilter) {
      filtered = filtered.filter((p) => p.types.includes(typeFilter.toLowerCase()))
    }

    // Generation filter
    if (generationFilter !== null) {
      filtered = filtered.filter((p) => p.generation === generationFilter)
    }

    // BST filters
    if (bstMin !== null || bstMax !== null) {
      filtered = filtered.filter((p) => {
        if (!p.stats) return false
        const bst =
          p.stats.hp +
          p.stats.attack +
          p.stats.defense +
          p.stats['special-attack'] +
          p.stats['special-defense'] +
          p.stats.speed
        if (bstMin !== null && bst < bstMin) return false
        if (bstMax !== null && bst > bstMax) return false
        return true
      })
    }

    // Specific stat filter
    if (statFilter && statMin !== null) {
      filtered = filtered.filter((p) => {
        if (!p.stats) return false
        return p.stats[statFilter] >= statMin
      })
    }

    // Ability filter
    if (abilityFilter) {
      const query = abilityFilter.toLowerCase()
      filtered = filtered.filter((p) =>
        p.abilities?.some((a) => a.toLowerCase().includes(query))
      )
    }

    // Legendary/Mythical filter
    if (legendaryFilter !== 'all') {
      filtered = filtered.filter((p) => {
        if (legendaryFilter === 'legendary') return p.is_legendary
        if (legendaryFilter === 'mythical') return p.is_mythical
        if (legendaryFilter === 'regular') return !p.is_legendary && !p.is_mythical
        return true
      })
    }

    return filtered
  },

  isMyTurn: (myTeamId) => {
    const currentTeam = get().getCurrentTeam()
    return currentTeam?.team_id === myTeamId
  },
}))
