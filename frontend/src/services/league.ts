import { api } from './api'
import { League, Season } from '../types'

interface CreateLeagueParams {
  name: string
  description?: string
  settings?: {
    draft_format?: string
    roster_size?: number
    timer_seconds?: number
    budget_enabled?: boolean
    budget_per_team?: number
    trade_approval_required?: boolean
  }
  template_id?: string
}

export const leagueService = {
  async createLeague(params: CreateLeagueParams): Promise<League> {
    return api.post<League>('/leagues', params)
  },

  async getLeagues(): Promise<League[]> {
    return api.get<League[]>('/leagues')
  },

  async getLeague(leagueId: string): Promise<League> {
    return api.get<League>(`/leagues/${leagueId}`)
  },

  async updateLeague(leagueId: string, params: Partial<CreateLeagueParams>): Promise<League> {
    return api.put<League>(`/leagues/${leagueId}`, params)
  },

  async joinLeague(leagueId: string, inviteCode?: string): Promise<League> {
    return api.post<League>(`/leagues/${leagueId}/join${inviteCode ? `?invite_code=${inviteCode}` : ''}`)
  },

  async leaveLeague(leagueId: string): Promise<void> {
    await api.delete(`/leagues/${leagueId}/leave`)
  },

  async createSeason(leagueId: string, params: { keep_teams?: boolean; settings?: Record<string, unknown> }): Promise<Season> {
    return api.post<Season>(`/leagues/${leagueId}/seasons`, params)
  },

  async getSeasons(leagueId: string): Promise<Season[]> {
    return api.get<Season[]>(`/leagues/${leagueId}/seasons`)
  },

  async regenerateInvite(leagueId: string): Promise<{ invite_code: string; invite_url: string }> {
    return api.post(`/leagues/${leagueId}/invite`)
  },
}
