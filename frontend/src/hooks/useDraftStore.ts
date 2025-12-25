import { create } from 'zustand'
import { DraftState, DraftPick, Pokemon, DraftTeam } from '../types'

interface DraftStore {
  // State
  draftState: DraftState | null
  secondsRemaining: number | null
  selectedPokemon: Pokemon | null
  searchQuery: string
  typeFilter: string | null

  // Actions
  setDraftState: (state: DraftState) => void
  updatePick: (pick: DraftPick) => void
  setTimerEnd: (timerEnd: string) => void
  setSecondsRemaining: (seconds: number) => void
  setSelectedPokemon: (pokemon: Pokemon | null) => void
  setSearchQuery: (query: string) => void
  setTypeFilter: (type: string | null) => void
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

  // Actions
  setDraftState: (state) => set({ draftState: state }),

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

  reset: () =>
    set({
      draftState: null,
      secondsRemaining: null,
      selectedPokemon: null,
      searchQuery: '',
      typeFilter: null,
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
    const { draftState, searchQuery, typeFilter } = get()
    if (!draftState) return []

    let filtered = draftState.available_pokemon

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((p) => p.name.toLowerCase().includes(query))
    }

    if (typeFilter) {
      filtered = filtered.filter((p) => p.types.includes(typeFilter.toLowerCase()))
    }

    return filtered
  },

  isMyTurn: (myTeamId) => {
    const currentTeam = get().getCurrentTeam()
    return currentTeam?.team_id === myTeamId
  },
}))
