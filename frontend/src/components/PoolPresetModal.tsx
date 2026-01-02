import { useState, useEffect, useRef, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { presetService } from '../services/preset'
import { pokemonService } from '../services/pokemon'
import { queryKeys } from '../services/queryKeys'
import { useSprite } from '../context/SpriteContext'
import {
  PoolPreset,
  PokemonBoxEntry,
  PokemonPoolEntry,
  PokemonFilters,
  DEFAULT_POKEMON_FILTERS,
} from '../types'
import { parsePoolCsv, generatePoolCsv, downloadFile } from '../utils/csvUtils'
import { TEMPLATE_PRESETS, applyTemplate, getTemplateOptions } from '../data/templatePresets'
import PokemonBox from './PokemonBox'
import PokemonFiltersComponent from './PokemonFilters'
import { Globe, Lock, X, Upload, Download } from 'lucide-react'

interface PoolPresetModalProps {
  isOpen: boolean
  onClose: () => void
  editPreset?: PoolPreset | null
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

export default function PoolPresetModal({
  isOpen,
  onClose,
  editPreset,
}: PoolPresetModalProps) {
  const queryClient = useQueryClient()
  const { spriteStyle } = useSprite()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filters and template
  const [filters, setFilters] = useState<PokemonFilters>(DEFAULT_POKEMON_FILTERS)
  const [template, setTemplate] = useState('')

  // File upload state
  const [poolSource, setPoolSource] = useState<'filters' | 'file'>('filters')
  const [loadedPoolIds, setLoadedPoolIds] = useState<number[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadWarnings, setUploadWarnings] = useState<string[]>([])
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)

  // Fetch all pokemon for the pool
  const { data: pokemonData, isLoading: pokemonLoading } = useQuery({
    queryKey: queryKeys.pokemonBox(spriteStyle),
    queryFn: () => pokemonService.getAllForBox(spriteStyle),
    enabled: isOpen,
  })

  const pokemon = pokemonData?.pokemon || []

  // Reset form when modal opens/closes or editPreset changes
  useEffect(() => {
    if (isOpen) {
      if (editPreset) {
        // Editing mode - populate from preset
        setName(editPreset.name)
        setDescription(editPreset.description || '')
        setIsPublic(editPreset.is_public)

        // If preset has filters, use them
        if (editPreset.pokemon_filters) {
          setFilters(editPreset.pokemon_filters)
          setPoolSource('filters')
        } else {
          // Use custom inclusions for the preset's pokemon
          const presetIds = Object.keys(editPreset.pokemon_pool).map(id => parseInt(id, 10))
          setFilters({
            ...DEFAULT_POKEMON_FILTERS,
            custom_inclusions: presetIds,
            generations: [],
            evolution_stages: [],
            include_legendary: false,
            include_mythical: false,
          })
          setPoolSource('filters')
        }
        setTemplate('')
      } else {
        // Create mode - reset to defaults
        setName('')
        setDescription('')
        setIsPublic(false)
        setFilters(DEFAULT_POKEMON_FILTERS)
        setTemplate('')
        setPoolSource('filters')
        setLoadedPoolIds([])
      }
      setError(null)
      setUploadError(null)
      setUploadWarnings([])
      setUploadSuccess(null)
    }
  }, [isOpen, editPreset])

  const createMutation = useMutation({
    mutationFn: presetService.createPreset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.presets })
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to create preset')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, params }: { id: string; params: Parameters<typeof presetService.updatePreset>[1] }) =>
      presetService.updatePreset(id, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.presets })
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to update preset')
    },
  })

  const handleClose = () => {
    setName('')
    setDescription('')
    setIsPublic(false)
    setFilters(DEFAULT_POKEMON_FILTERS)
    setTemplate('')
    setPoolSource('filters')
    setLoadedPoolIds([])
    setError(null)
    setUploadError(null)
    setUploadWarnings([])
    setUploadSuccess(null)
    onClose()
  }

  // Handle template change
  const handleTemplateChange = (templateId: string) => {
    setTemplate(templateId)
    setFilters(applyTemplate(templateId))
  }

  // Toggle custom exclusion/inclusion
  const handleToggleExclusion = useCallback((pokemonId: number) => {
    setFilters(prev => {
      const isExcluded = prev.custom_exclusions.includes(pokemonId)
      const isIncluded = prev.custom_inclusions.includes(pokemonId)

      if (isExcluded) {
        // Remove from exclusions, add to inclusions
        return {
          ...prev,
          custom_exclusions: prev.custom_exclusions.filter(id => id !== pokemonId),
          custom_inclusions: [...prev.custom_inclusions, pokemonId],
        }
      } else if (isIncluded) {
        // Remove from inclusions (back to default state)
        return {
          ...prev,
          custom_inclusions: prev.custom_inclusions.filter(id => id !== pokemonId),
        }
      } else {
        // Add to exclusions
        return {
          ...prev,
          custom_exclusions: [...prev.custom_exclusions, pokemonId],
        }
      }
    })
  }, [])

  const handleSave = () => {
    if (!name.trim()) {
      setError('Please enter a name')
      return
    }

    // Build pokemon_pool based on pool source
    const pool: Record<string, PokemonPoolEntry> = {}

    if (poolSource === 'file' && loadedPoolIds.length > 0) {
      // Use loaded IDs from file
      for (const p of pokemon) {
        if (loadedPoolIds.includes(p.id)) {
          pool[p.id.toString()] = {
            name: p.name,
            points: null,
            types: p.types,
            generation: p.generation,
            bst: p.bst,
            evolution_stage: p.evolution_stage,
            is_legendary: p.is_legendary,
            is_mythical: p.is_mythical,
          }
        }
      }
    } else {
      // Use filters
      for (const p of pokemon) {
        if (pokemonPassesFilters(p, filters)) {
          pool[p.id.toString()] = {
            name: p.name,
            points: null,
            types: p.types,
            generation: p.generation,
            bst: p.bst,
            evolution_stage: p.evolution_stage,
            is_legendary: p.is_legendary,
            is_mythical: p.is_mythical,
          }
        }
      }
    }

    if (Object.keys(pool).length === 0) {
      setError('Pool must contain at least one Pokemon')
      return
    }

    if (editPreset) {
      // Update existing
      updateMutation.mutate({
        id: editPreset.id,
        params: {
          name: name.trim(),
          description: description.trim() || undefined,
          pokemon_pool: pool,
          pokemon_filters: poolSource === 'filters' ? filters : undefined,
          is_public: isPublic,
        },
      })
    } else {
      // Create new
      createMutation.mutate({
        name: name.trim(),
        description: description.trim() || undefined,
        pokemon_pool: pool,
        pokemon_filters: poolSource === 'filters' ? filters : undefined,
        is_public: isPublic,
      })
    }
  }

  const handleDownloadCsv = () => {
    const csv = generatePoolCsv(pokemon, filters)
    const timestamp = new Date().toISOString().slice(0, 10)
    downloadFile(csv, `pokemon_pool_${timestamp}.csv`)
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Reset states
    setUploadError(null)
    setUploadWarnings([])
    setUploadSuccess(null)

    try {
      const content = await file.text()
      const { pokemonIds, errors, warnings } = parsePoolCsv(content)

      if (errors.length > 0) {
        setUploadError(errors.join('\n'))
        return
      }

      if (warnings.length > 0) {
        setUploadWarnings(warnings)
      }

      if (pokemonIds.length === 0) {
        setUploadError('No valid Pokemon IDs found in the CSV file')
        return
      }

      // Validate that the IDs exist in our pokemon list
      const validIds = pokemonIds.filter(id => pokemon.some(p => p.id === id))
      const invalidCount = pokemonIds.length - validIds.length

      if (invalidCount > 0) {
        setUploadWarnings(prev => [...prev, `${invalidCount} Pokemon ID(s) not found in database and were skipped`])
      }

      setLoadedPoolIds(validIds)
      setPoolSource('file')
      setUploadSuccess(`Successfully loaded ${validIds.length} Pokemon into the pool`)
    } catch {
      setUploadError('Failed to read CSV file')
    }

    // Reset file input so same file can be selected again
    e.target.value = ''
  }

  const handleClearLoadedPool = () => {
    setLoadedPoolIds([])
    setPoolSource('filters')
    setUploadSuccess(null)
    setUploadWarnings([])
  }

  // Calculate pool count
  const poolCount = poolSource === 'file' && loadedPoolIds.length > 0
    ? loadedPoolIds.length
    : pokemon.filter(p => pokemonPassesFilters(p, filters)).length

  const isPending = createMutation.isPending || updateMutation.isPending
  const templateOptions = getTemplateOptions()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center flex-shrink-0">
          <div>
            <h2 className="text-xl font-semibold">
              {editPreset ? 'Edit Pool Preset' : 'Create Pool Preset'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {poolCount} Pokemon in pool
            </p>
          </div>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}

          {/* Name and Description */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                maxLength={500}
              />
            </div>
          </div>

          {/* Pool Source Selection */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">Pool Source</h3>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="poolSource"
                    value="filters"
                    checked={poolSource === 'filters'}
                    onChange={() => {
                      setPoolSource('filters')
                      setUploadSuccess(null)
                    }}
                    className="text-purple-600"
                  />
                  <span className="text-sm">Use Filters</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="poolSource"
                    value="file"
                    checked={poolSource === 'file'}
                    onChange={() => setPoolSource('file')}
                    className="text-purple-600"
                  />
                  <span className="text-sm">Load from File</span>
                </label>
              </div>
            </div>

            {/* File Upload Section */}
            {poolSource === 'file' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handleDownloadCsv}
                    disabled={pokemonLoading}
                    className="btn btn-secondary text-sm flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download CSV Template
                  </button>

                  <button
                    type="button"
                    onClick={handleUploadClick}
                    disabled={pokemonLoading}
                    className="btn btn-secondary text-sm flex items-center gap-2"
                  >
                    <Upload className="w-4 h-4" />
                    Upload CSV
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />

                  {loadedPoolIds.length > 0 && (
                    <button
                      type="button"
                      onClick={handleClearLoadedPool}
                      className="btn btn-secondary text-sm text-red-600 hover:text-red-700"
                    >
                      Clear
                    </button>
                  )}
                </div>

                {/* Status */}
                {loadedPoolIds.length > 0 && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-semibold text-green-600">{loadedPoolIds.length}</span>
                    <span className="text-gray-600">Pokemon loaded from file</span>
                  </div>
                )}

                {/* Messages */}
                {uploadError && (
                  <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
                    <p className="font-medium">Error:</p>
                    <p className="mt-1 whitespace-pre-line">{uploadError}</p>
                  </div>
                )}

                {uploadWarnings.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                    <p className="font-medium">Warnings ({uploadWarnings.length}):</p>
                    <ul className="mt-1 list-disc list-inside max-h-20 overflow-y-auto">
                      {uploadWarnings.slice(0, 5).map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                      {uploadWarnings.length > 5 && (
                        <li>...and {uploadWarnings.length - 5} more</li>
                      )}
                    </ul>
                  </div>
                )}

                {uploadSuccess && (
                  <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-700">
                    {uploadSuccess}
                  </div>
                )}

                <p className="text-xs text-gray-500">
                  Download a template, remove Pokemon you don't want, then upload.
                </p>
              </div>
            )}
          </div>

          {/* Filters Section - only show when using filters */}
          {poolSource === 'filters' && (
            <>
              {/* Template Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template</label>
                <select
                  value={template}
                  onChange={(e) => handleTemplateChange(e.target.value)}
                  className="input"
                  disabled={pokemonLoading}
                >
                  {templateOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {template && TEMPLATE_PRESETS[template] && (
                  <p className="text-sm text-gray-500 mt-1">
                    {TEMPLATE_PRESETS[template].description}
                  </p>
                )}
              </div>

              {/* Pokemon Filters */}
              <PokemonFiltersComponent
                filters={filters}
                onChange={setFilters}
              />
            </>
          )}

          {/* Pokemon Box */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Pokemon Pool Preview
            </h3>
            {poolSource === 'file' && loadedPoolIds.length > 0 ? (
              <PokemonBox
                pokemon={pokemon.filter(p => loadedPoolIds.includes(p.id))}
                filters={{
                  ...DEFAULT_POKEMON_FILTERS,
                  custom_inclusions: loadedPoolIds,
                  generations: [],
                  evolution_stages: [],
                }}
                onToggleExclusion={() => {}}
                isLoading={pokemonLoading}
                showPoints={false}
                pokemonPoints={{}}
                onPointChange={() => {}}
                editablePoints={false}
              />
            ) : (
              <PokemonBox
                pokemon={pokemon}
                filters={filters}
                onToggleExclusion={handleToggleExclusion}
                isLoading={pokemonLoading}
                showPoints={false}
                pokemonPoints={{}}
                onPointChange={() => {}}
                editablePoints={false}
              />
            )}
          </div>

          {/* Public/Private toggle */}
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
        <div className="px-6 py-4 border-t flex justify-end gap-3 flex-shrink-0">
          <button onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isPending || pokemonLoading}
            className="btn btn-primary"
          >
            {isPending ? 'Saving...' : editPreset ? 'Save Changes' : 'Create Preset'}
          </button>
        </div>
      </div>
    </div>
  )
}
