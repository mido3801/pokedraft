import { useState } from 'react'
import { PokemonFilters as FiltersType, TYPE_COLORS, DEFAULT_POKEMON_FILTERS } from '../types'

interface PokemonFiltersProps {
  filters: FiltersType
  onChange: (filters: FiltersType) => void
}

const GENERATIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
const EVOLUTION_STAGES = [
  { value: 0, label: 'Unevolved' },
  { value: 1, label: 'Middle' },
  { value: 2, label: 'Fully Evolved' },
]
const POKEMON_TYPES = [
  'normal', 'fire', 'water', 'electric', 'grass', 'ice',
  'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
  'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy',
]

export default function PokemonFilters({ filters, onChange }: PokemonFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const toggleGeneration = (gen: number) => {
    const newGens = filters.generations.includes(gen)
      ? filters.generations.filter(g => g !== gen)
      : [...filters.generations, gen].sort((a, b) => a - b)
    onChange({ ...filters, generations: newGens })
  }

  const toggleAllGenerations = (include: boolean) => {
    onChange({ ...filters, generations: include ? [...GENERATIONS] : [] })
  }

  const toggleEvolutionStage = (stage: number) => {
    const newStages = filters.evolution_stages.includes(stage)
      ? filters.evolution_stages.filter(s => s !== stage)
      : [...filters.evolution_stages, stage].sort((a, b) => a - b)
    onChange({ ...filters, evolution_stages: newStages })
  }

  const toggleType = (type: string) => {
    const newTypes = filters.types.includes(type)
      ? filters.types.filter(t => t !== type)
      : [...filters.types, type]
    onChange({ ...filters, types: newTypes })
  }

  const clearTypes = () => {
    onChange({ ...filters, types: [] })
  }

  const resetAllFilters = () => {
    onChange({ ...DEFAULT_POKEMON_FILTERS })
  }

  return (
    <div className="pokemon-filters bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
      >
        <h3 className="font-semibold text-gray-900">Pokemon Filters</h3>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="p-4 pt-0 space-y-6">
          {/* Generation Filter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Generations</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => toggleAllGenerations(true)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  type="button"
                  onClick={() => toggleAllGenerations(false)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  None
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {GENERATIONS.map(gen => (
                <button
                  type="button"
                  key={gen}
                  onClick={() => toggleGeneration(gen)}
                  className={`
                    px-3 py-1.5 rounded text-sm font-medium transition-colors
                    ${filters.generations.includes(gen)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }
                  `}
                >
                  Gen {gen}
                </button>
              ))}
            </div>
          </div>

          {/* Evolution Stage Filter */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Evolution Stage</label>
            <div className="flex flex-wrap gap-2">
              {EVOLUTION_STAGES.map(stage => (
                <button
                  type="button"
                  key={stage.value}
                  onClick={() => toggleEvolutionStage(stage.value)}
                  className={`
                    px-3 py-1.5 rounded text-sm font-medium transition-colors
                    ${filters.evolution_stages.includes(stage.value)
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }
                  `}
                >
                  {stage.label}
                </button>
              ))}
            </div>
          </div>

          {/* Legendary/Mythical Toggles */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Special Pokemon</label>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.include_legendary}
                  onChange={(e) => onChange({ ...filters, include_legendary: e.target.checked })}
                  className="h-4 w-4 text-yellow-500 rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">Include Legendaries</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.include_mythical}
                  onChange={(e) => onChange({ ...filters, include_mythical: e.target.checked })}
                  className="h-4 w-4 text-pink-500 rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">Include Mythicals</span>
              </label>
            </div>
          </div>

          {/* Type Filter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Types {filters.types.length > 0 && (
                  <span className="text-gray-400 font-normal">
                    ({filters.types.length} selected)
                  </span>
                )}
              </label>
              {filters.types.length > 0 && (
                <button
                  type="button"
                  onClick={clearTypes}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Clear
                </button>
              )}
            </div>
            <p className="text-xs text-gray-500 mb-2">
              {filters.types.length === 0
                ? 'All types included. Select types to filter.'
                : 'Only Pokemon with selected types will be included.'
              }
            </p>
            <div className="flex flex-wrap gap-1.5">
              {POKEMON_TYPES.map(type => (
                <button
                  type="button"
                  key={type}
                  onClick={() => toggleType(type)}
                  className={`
                    px-2 py-1 rounded text-xs font-medium transition-all
                    ${filters.types.includes(type)
                      ? 'text-white ring-2 ring-offset-1 ring-gray-400'
                      : 'text-white opacity-60 hover:opacity-80'
                    }
                  `}
                  style={{
                    backgroundColor: TYPE_COLORS[type] || '#888',
                  }}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* BST Range */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Base Stat Total Range
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                value={filters.bst_min}
                onChange={(e) => onChange({ ...filters, bst_min: Math.max(0, parseInt(e.target.value) || 0) })}
                className="input w-24 text-sm"
                min={0}
                max={filters.bst_max}
                placeholder="Min"
              />
              <span className="text-gray-400">to</span>
              <input
                type="number"
                value={filters.bst_max}
                onChange={(e) => onChange({ ...filters, bst_max: Math.min(999, parseInt(e.target.value) || 999) })}
                className="input w-24 text-sm"
                min={filters.bst_min}
                max={999}
                placeholder="Max"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Common ranges: Little Cup (~300), NFE (~400), OU (~500-600)
            </p>
          </div>

          {/* Reset Button */}
          <div className="pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={resetAllFilters}
              className="text-sm text-red-600 hover:text-red-700 hover:underline"
            >
              Reset all filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
