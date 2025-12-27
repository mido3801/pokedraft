import { api } from './api'
import { PoolPreset, PoolPresetSummary, CreatePresetParams, UpdatePresetParams } from '../types'

export const presetService = {
  async getPresets(): Promise<PoolPresetSummary[]> {
    return api.get<PoolPresetSummary[]>('/presets')
  },

  async getPreset(presetId: string): Promise<PoolPreset> {
    return api.get<PoolPreset>(`/presets/${presetId}`)
  },

  async createPreset(params: CreatePresetParams): Promise<PoolPreset> {
    return api.post<PoolPreset>('/presets', params)
  },

  async updatePreset(presetId: string, params: UpdatePresetParams): Promise<PoolPreset> {
    return api.put<PoolPreset>(`/presets/${presetId}`, params)
  },

  async deletePreset(presetId: string): Promise<void> {
    await api.delete(`/presets/${presetId}`)
  },
}
