import { api } from './api'
import { Team, TeamPokemon } from '../types'

export const teamService = {
  async getTeams(params: { season_id?: string; draft_id?: string }): Promise<Team[]> {
    const queryParams = new URLSearchParams()
    if (params.season_id) queryParams.append('season_id', params.season_id)
    if (params.draft_id) queryParams.append('draft_id', params.draft_id)
    return api.get<Team[]>(`/teams?${queryParams.toString()}`)
  },

  async getTeam(teamId: string): Promise<Team> {
    return api.get<Team>(`/teams/${teamId}`)
  },

  async getTeamPokemon(teamId: string): Promise<TeamPokemon[]> {
    return api.get<TeamPokemon[]>(`/teams/${teamId}/pokemon`)
  },

  async updateTeam(teamId: string, params: { display_name?: string }): Promise<Team> {
    return api.put<Team>(`/teams/${teamId}`, params)
  },
}
