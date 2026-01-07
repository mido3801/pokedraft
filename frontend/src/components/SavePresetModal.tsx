import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { presetService } from '../services/preset'
import { queryKeys } from '../services/queryKeys'
import { PokemonBoxEntry, PokemonPointsMap, PokemonFilters } from '../types'
import { Globe, Lock, X, Filter } from 'lucide-react'

interface SavePresetModalProps {
  isOpen: boolean
  onClose: () => void
  pokemon: PokemonBoxEntry[]
  filters: PokemonFilters
  pokemonPoints: PokemonPointsMap
}

// Helper to check if a Pokemon passes filters
function pokemonPassesFilters(p: PokemonBoxEntry, filters: PokemonFilters): boolean {
  if (filters.custom_inclusions.includes(p.id)) return true
  if (filters.custom_exclusions.includes(p.id)) return false
  if (!filters.generations.includes(p.generation)) return false
  if (!filters.evolution_stages.includes(p.evolution_stage)) return false
  if (!filters.include_legendary && p.is_legendary) return false
  if (!filters.include_mythical && p.is_mythical) return false
  if (filters.types.length > 0 && !p.types.some(t => filters.types.includes(t))) return false
  if (p.bst < filters.bst_min || p.bst > filters.bst_max) return false
  return true
}

export default function SavePresetModal({
  isOpen,
  onClose,
  pokemon,
  filters,
  pokemonPoints,
}: SavePresetModalProps) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [saveFilters, setSaveFilters] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: presetService.createPreset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.presets })
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to save preset')
    },
  })

  const handleClose = () => {
    setName('')
    setDescription('')
    setIsPublic(false)
    setSaveFilters(true)
    setError(null)
    onClose()
  }

  const handleSave = () => {
    if (!name.trim()) {
      setError('Please enter a name')
      return
    }

    // Build pokemon_pool from current state
    const pool: Record<string, unknown> = {}
    for (const p of pokemon) {
      if (pokemonPassesFilters(p, filters)) {
        pool[p.id.toString()] = {
          name: p.name,
          points: pokemonPoints[p.id] ?? null,
          types: p.types,
          generation: p.generation,
          bst: p.bst,
          evolution_stage: p.evolution_stage,
          is_legendary: p.is_legendary,
          is_mythical: p.is_mythical,
        }
      }
    }

    if (Object.keys(pool).length === 0) {
      setError('No Pokémon in pool to save')
      return
    }

    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
      pokemon_pool: pool,
      pokemon_filters: saveFilters ? filters : undefined,
      is_public: isPublic,
    })
  }

  const filteredCount = pokemon.filter(p => pokemonPassesFilters(p, filters)).length
  const pointsCount = pokemon.filter(p => pokemonPassesFilters(p, filters) && pokemonPoints[p.id] !== undefined).length

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Save Pool Preset</h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
            <p>This preset will save <strong>{filteredCount}</strong> Pokémon.</p>
            {pointsCount > 0 && (
              <p className="mt-1">{pointsCount} Pokémon have point values assigned.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Custom Pool"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              maxLength={100}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              rows={2}
              maxLength={500}
            />
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Filter className={`w-5 h-5 ${saveFilters ? 'text-purple-500' : 'text-gray-400'}`} />
              <div>
                <p className="font-medium text-gray-900">
                  Save Filter Settings
                </p>
                <p className="text-xs text-gray-500">
                  {saveFilters ? 'Filters can be restored when loading' : 'Only Pokemon list will be saved'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setSaveFilters(!saveFilters)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                saveFilters ? 'bg-purple-500' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  saveFilters ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              {isPublic ? (
                <Globe className="w-5 h-5 text-green-500" />
              ) : (
                <Lock className="w-5 h-5 text-gray-400" />
              )}
              <div>
                <p className="font-medium text-gray-900">
                  {isPublic ? 'Public' : 'Private'}
                </p>
                <p className="text-xs text-gray-500">
                  {isPublic ? 'Anyone can use this preset' : 'Only you can see this'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsPublic(!isPublic)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isPublic ? 'bg-green-500' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isPublic ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={createMutation.isPending}
            className="btn btn-primary"
          >
            {createMutation.isPending ? 'Saving...' : 'Save Preset'}
          </button>
        </div>
      </div>
    </div>
  )
}
