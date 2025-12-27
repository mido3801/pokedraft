import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { presetService } from '../services/preset'
import { queryKeys } from '../services/queryKeys'
import { PoolPresetSummary, PokemonPointsMap } from '../types'
import { Globe, Lock, Check, X } from 'lucide-react'

interface LoadPresetModalProps {
  isOpen: boolean
  onClose: () => void
  onLoad: (poolData: Record<string, unknown>, points: PokemonPointsMap) => void
}

export default function LoadPresetModal({
  isOpen,
  onClose,
  onLoad,
}: LoadPresetModalProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: presets, isLoading: presetsLoading } = useQuery({
    queryKey: queryKeys.presets,
    queryFn: presetService.getPresets,
    enabled: isOpen,
  })

  const loadMutation = useMutation({
    mutationFn: (presetId: string) => presetService.getPreset(presetId),
    onSuccess: (preset) => {
      // Extract points from pokemon_pool
      const points: PokemonPointsMap = {}

      for (const [idStr, data] of Object.entries(preset.pokemon_pool)) {
        const id = parseInt(idStr)
        const entry = data as { points?: number | null }
        if (entry.points !== null && entry.points !== undefined) {
          points[id] = entry.points
        }
      }

      onLoad(preset.pokemon_pool, points)
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to load preset')
    },
  })

  const handleClose = () => {
    setSelectedId(null)
    setError(null)
    onClose()
  }

  const handleLoad = () => {
    if (!selectedId) return
    loadMutation.mutate(selectedId)
  }

  const myPresets = presets?.filter(p => !p.creator_name) || []
  const publicPresets = presets?.filter(p => p.creator_name) || []

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Load Pool Preset</h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">
              {error}
            </div>
          )}

          {presetsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="loader w-6 h-6"></div>
            </div>
          ) : presets && presets.length > 0 ? (
            <div className="space-y-4">
              {myPresets.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Your Presets</h3>
                  <div className="space-y-2">
                    {myPresets.map((preset) => (
                      <PresetItem
                        key={preset.id}
                        preset={preset}
                        selected={selectedId === preset.id}
                        onSelect={() => setSelectedId(preset.id)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {publicPresets.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Public Presets</h3>
                  <div className="space-y-2">
                    {publicPresets.map((preset) => (
                      <PresetItem
                        key={preset.id}
                        preset={preset}
                        selected={selectedId === preset.id}
                        onSelect={() => setSelectedId(preset.id)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No presets available. Create one by configuring a pool and clicking "Save as Preset".
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleLoad}
            disabled={!selectedId || loadMutation.isPending}
            className="btn btn-primary disabled:opacity-50"
          >
            {loadMutation.isPending ? 'Loading...' : 'Load Preset'}
          </button>
        </div>
      </div>
    </div>
  )
}

function PresetItem({
  preset,
  selected,
  onSelect,
}: {
  preset: PoolPresetSummary
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-lg border transition-colors ${
        selected
          ? 'border-purple-500 bg-purple-50'
          : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {preset.is_public ? (
            <Globe className="w-4 h-4 text-green-500" />
          ) : (
            <Lock className="w-4 h-4 text-gray-400" />
          )}
          <span className="font-medium">{preset.name}</span>
        </div>
        {selected && <Check className="w-4 h-4 text-purple-600" />}
      </div>
      <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
        <span>{preset.pokemon_count} Pokemon</span>
        {preset.creator_name && (
          <span>by {preset.creator_name}</span>
        )}
      </div>
      {preset.description && (
        <p className="text-sm text-gray-500 mt-1 line-clamp-1">
          {preset.description}
        </p>
      )}
    </button>
  )
}
