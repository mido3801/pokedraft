import { api } from './api'
import { Match, Standings } from '../types'

export type ScheduleFormat = 'round_robin' | 'double_round_robin' | 'swiss' | 'single_elimination' | 'double_elimination' | 'random_weekly' | 'custom'

interface GenerateScheduleParams {
  format: ScheduleFormat
  start_date?: string
}

interface RecordResultParams {
  winner_id?: string
  is_tie?: boolean
  replay_url?: string
  notes?: string
}

export const matchService = {
  async getSchedule(seasonId: string): Promise<Match[]> {
    return api.get<Match[]>(`/matches/schedule?season_id=${seasonId}`)
  },

  async generateSchedule(seasonId: string, params: GenerateScheduleParams): Promise<Match[]> {
    return api.post<Match[]>(`/matches/schedule?season_id=${seasonId}`, params)
  },

  async getStandings(seasonId: string): Promise<Standings> {
    return api.get<Standings>(`/matches/standings?season_id=${seasonId}`)
  },

  async getMatch(matchId: string): Promise<Match> {
    return api.get<Match>(`/matches/${matchId}`)
  },

  async recordResult(matchId: string, params: RecordResultParams): Promise<Match> {
    return api.post<Match>(`/matches/${matchId}/result`, params)
  },
}
