import { api } from './api'
import { WaiverClaim, WaiverClaimList, FreeAgentList, WaiverVote } from '../types'

interface CreateWaiverClaimParams {
  season_id: string
  pokemon_id: number
  drop_pokemon_id?: string
}

interface AdminActionParams {
  approved: boolean
  notes?: string
}

interface VoteParams {
  vote: boolean
}

export const waiverService = {
  async createClaim(params: CreateWaiverClaimParams): Promise<WaiverClaim> {
    const { season_id, ...body } = params
    return api.post<WaiverClaim>(`/waivers?season_id=${season_id}`, body)
  },

  async getClaims(seasonId: string, status?: string, teamId?: string): Promise<WaiverClaimList> {
    let url = `/waivers?season_id=${seasonId}`
    if (status) url += `&status_filter=${status}`
    if (teamId) url += `&team_id=${teamId}`
    return api.get<WaiverClaimList>(url)
  },

  async getClaim(claimId: string): Promise<WaiverClaim> {
    return api.get<WaiverClaim>(`/waivers/${claimId}`)
  },

  async cancelClaim(claimId: string): Promise<WaiverClaim> {
    return api.post<WaiverClaim>(`/waivers/${claimId}/cancel`)
  },

  async adminAction(claimId: string, params: AdminActionParams): Promise<WaiverClaim> {
    return api.post<WaiverClaim>(`/waivers/${claimId}/approve`, params)
  },

  async vote(claimId: string, params: VoteParams): Promise<WaiverVote> {
    return api.post<WaiverVote>(`/waivers/${claimId}/vote`, params)
  },

  async getFreeAgents(seasonId: string): Promise<FreeAgentList> {
    return api.get<FreeAgentList>(`/waivers/free-agents/?season_id=${seasonId}`)
  },
}
