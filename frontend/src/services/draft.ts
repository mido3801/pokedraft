import { api } from './api'
import { Draft, DraftState, DraftSummary, PokemonFilters } from '../types'

export interface CreateDraftParams {
  format: string
  timer_seconds?: number
  budget_enabled?: boolean
  budget_per_team?: number
  roster_size: number
  pokemon_pool?: unknown[]
  pokemon_filters?: PokemonFilters
  // Auction-specific settings
  nomination_timer_seconds?: number
  min_bid?: number
  bid_increment?: number
}

interface CreateAnonymousDraftParams extends CreateDraftParams {
  display_name: string
}

interface AnonymousDraftResponse extends Draft {
  session_token: string
  rejoin_code: string
  join_url: string
  team_id: string
}

export const draftService = {
  async createDraft(seasonId: string, params: CreateDraftParams): Promise<Draft> {
    return api.post<Draft>(`/drafts?season_id=${seasonId}`, params)
  },

  async createAnonymousDraft(params: CreateAnonymousDraftParams): Promise<AnonymousDraftResponse> {
    return api.post<AnonymousDraftResponse>('/drafts/anonymous', params)
  },

  async joinAnonymousDraft(rejoinCode: string, displayName: string): Promise<unknown> {
    return api.post(`/drafts/anonymous/join?rejoin_code=${rejoinCode}&display_name=${encodeURIComponent(displayName)}`, null)
  },

  async getDraft(draftId: string): Promise<Draft> {
    return api.get<Draft>(`/drafts/${draftId}`)
  },

  async getDraftState(draftId: string): Promise<DraftState> {
    return api.get<DraftState>(`/drafts/${draftId}/state`)
  },

  async startDraft(draftId: string): Promise<void> {
    await api.post(`/drafts/${draftId}/start`)
  },

  async pauseDraft(draftId: string): Promise<void> {
    await api.post(`/drafts/${draftId}/pause`)
  },

  async resumeDraft(draftId: string): Promise<void> {
    await api.post(`/drafts/${draftId}/resume`)
  },

  async exportTeam(draftId: string, teamId: string, format = 'showdown'): Promise<{ content: string; filename: string }> {
    return api.get(`/drafts/${draftId}/export?team_id=${teamId}&format=${format}`)
  },

  async getMyTeam(draftId: string): Promise<{ team_id: string; display_name: string }> {
    return api.get(`/drafts/${draftId}/my-team`)
  },

  async getMyDrafts(): Promise<DraftSummary[]> {
    return api.get<DraftSummary[]>('/drafts/me')
  },

  async deleteDraft(draftId: string): Promise<void> {
    await api.delete(`/drafts/${draftId}`)
  },
}
