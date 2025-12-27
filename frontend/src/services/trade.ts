import { api } from './api'
import { Trade } from '../types'

interface ProposeTradeParams {
  season_id: string
  recipient_team_id: string
  proposer_pokemon: string[]
  recipient_pokemon: string[]
  message?: string
}

export const tradeService = {
  async proposeTrade(params: ProposeTradeParams): Promise<Trade> {
    const { season_id, ...body } = params
    return api.post<Trade>(`/trades?season_id=${season_id}`, body)
  },

  async getTrades(seasonId: string): Promise<Trade[]> {
    return api.get<Trade[]>(`/trades?season_id=${seasonId}`)
  },

  async getTrade(tradeId: string): Promise<Trade> {
    return api.get<Trade>(`/trades/${tradeId}`)
  },

  async acceptTrade(tradeId: string): Promise<Trade> {
    return api.post<Trade>(`/trades/${tradeId}/accept`)
  },

  async rejectTrade(tradeId: string): Promise<Trade> {
    return api.post<Trade>(`/trades/${tradeId}/reject`)
  },

  async cancelTrade(tradeId: string): Promise<Trade> {
    return api.post<Trade>(`/trades/${tradeId}/cancel`)
  },

  async approveTrade(tradeId: string): Promise<Trade> {
    return api.post<Trade>(`/trades/${tradeId}/approve`)
  },
}
