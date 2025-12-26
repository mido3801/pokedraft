import { useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { PokemonBoxEntry, PokemonFilters, PokemonPointsMap, TYPE_COLORS } from '../types'
import { useSprite } from '../context/SpriteContext'

interface PokemonBoxProps {
  pokemon: PokemonBoxEntry[]
  filters: PokemonFilters
  onToggleExclusion: (pokemonId: number) => void
  isLoading?: boolean
  // Point value props
  showPoints?: boolean
  pokemonPoints?: PokemonPointsMap
  onPointChange?: (pokemonId: number, points: number | null) => void
  editablePoints?: boolean
}

// Check if a Pokemon passes the current filters
function pokemonPassesFilters(p: PokemonBoxEntry, filters: PokemonFilters): boolean {
  // Force include if in custom_inclusions
  if (filters.custom_inclusions.includes(p.id)) {
    return true
  }

  // Exclude if in custom_exclusions
  if (filters.custom_exclusions.includes(p.id)) {
    return false
  }

  // Check generation
  if (!filters.generations.includes(p.generation)) {
    return false
  }

  // Check evolution stage
  if (!filters.evolution_stages.includes(p.evolution_stage)) {
    return false
  }

  // Check legendary
  if (!filters.include_legendary && p.is_legendary) {
    return false
  }

  // Check mythical
  if (!filters.include_mythical && p.is_mythical) {
    return false
  }

  // Check types (if filter is active)
  if (filters.types.length > 0) {
    if (!p.types.some(t => filters.types.includes(t))) {
      return false
    }
  }

  // Check BST
  if (p.bst < filters.bst_min || p.bst > filters.bst_max) {
    return false
  }

  return true
}

// Format Pokemon name for display (capitalize, handle hyphens)
function formatName(name: string): string {
  return name
    .split('-')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export default function PokemonBox({
  pokemon,
  filters,
  onToggleExclusion,
  isLoading,
  showPoints = false,
  pokemonPoints = {},
  onPointChange,
  editablePoints = false,
}: PokemonBoxProps) {
  const { getSpriteUrl } = useSprite()
  const [searchQuery, setSearchQuery] = useState('')
  const [hoveredPokemon, setHoveredPokemon] = useState<PokemonBoxEntry | null>(null)
  const [editingPokemonId, setEditingPokemonId] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')
  const editInputRef = useRef<HTMLInputElement>(null)

  // Focus input when editing starts
  useEffect(() => {
    if (editingPokemonId !== null && editInputRef.current) {
      editInputRef.current.focus()
      editInputRef.current.select()
    }
  }, [editingPokemonId])

  // Calculate which Pokemon pass filters
  const pokemonWithStatus = useMemo(() => {
    return pokemon.map(p => ({
      ...p,
      included: pokemonPassesFilters(p, filters),
      isCustomExcluded: filters.custom_exclusions.includes(p.id),
      isCustomIncluded: filters.custom_inclusions.includes(p.id),
      points: pokemonPoints[p.id],
      hasPoints: pokemonPoints[p.id] !== undefined,
    }))
  }, [pokemon, filters, pokemonPoints])

  // Filter by search query
  const filteredPokemon = useMemo(() => {
    if (!searchQuery.trim()) {
      return pokemonWithStatus
    }
    const query = searchQuery.toLowerCase()
    return pokemonWithStatus.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.id.toString() === query
    )
  }, [pokemonWithStatus, searchQuery])

  // Count included Pokemon
  const includedCount = useMemo(() => {
    return pokemonWithStatus.filter(p => p.included).length
  }, [pokemonWithStatus])

  const handleClick = useCallback((pokemonId: number) => {
    if (editablePoints && onPointChange) {
      // In edit mode, open the point editor
      const currentPoints = pokemonPoints[pokemonId]
      setEditValue(currentPoints !== undefined ? currentPoints.toString() : '')
      setEditingPokemonId(pokemonId)
    } else {
      onToggleExclusion(pokemonId)
    }
  }, [editablePoints, onPointChange, pokemonPoints, onToggleExclusion])

  const handleSavePoints = useCallback(() => {
    if (editingPokemonId !== null && onPointChange) {
      const trimmed = editValue.trim()
      if (trimmed === '') {
        onPointChange(editingPokemonId, null)
      } else {
        const num = parseInt(trimmed, 10)
        if (!isNaN(num) && num >= 0) {
          onPointChange(editingPokemonId, num)
        }
      }
      setEditingPokemonId(null)
      setEditValue('')
    }
  }, [editingPokemonId, editValue, onPointChange])

  const handleCancelEdit = useCallback(() => {
    setEditingPokemonId(null)
    setEditValue('')
  }, [])

  const handleEditKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSavePoints()
    } else if (e.key === 'Escape') {
      handleCancelEdit()
    }
  }, [handleSavePoints, handleCancelEdit])

  if (isLoading) {
    return (
      <div className="pokemon-box-loading flex items-center justify-center h-64 bg-gray-100 rounded-lg">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 text-pokemon-red mx-auto mb-2" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading Pokemon...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pokemon-box">
      {/* Header with search and count */}
      <div className="flex items-center justify-between mb-3 gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search Pokemon..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-full text-sm"
          />
        </div>
        <div className="text-sm text-gray-600 whitespace-nowrap">
          <span className="font-semibold text-green-600">{includedCount}</span>
          <span className="text-gray-400"> / </span>
          <span>{pokemon.length}</span>
          <span className="text-gray-400 ml-1">included</span>
        </div>
      </div>

      {/* Pokemon tooltip */}
      {hoveredPokemon && !editingPokemonId && (
        <div className="fixed z-50 bg-white shadow-lg rounded-lg p-3 pointer-events-none border border-gray-200"
             style={{
               top: '50%',
               left: '50%',
               transform: 'translate(-50%, -50%)',
               minWidth: '200px'
             }}>
          <div className="flex items-center gap-3">
            <img
              src={getSpriteUrl(hoveredPokemon.id)}
              alt={hoveredPokemon.name}
              className="w-16 h-16"
            />
            <div>
              <p className="font-bold text-gray-900">
                #{hoveredPokemon.id} {formatName(hoveredPokemon.name)}
              </p>
              <div className="flex gap-1 mt-1">
                {hoveredPokemon.types.map(type => (
                  <span
                    key={type}
                    className="px-2 py-0.5 rounded text-xs text-white font-medium"
                    style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                  >
                    {type.toUpperCase()}
                  </span>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Gen {hoveredPokemon.generation} | BST: {hoveredPokemon.bst}
                {hoveredPokemon.is_legendary && ' | Legendary'}
                {hoveredPokemon.is_mythical && ' | Mythical'}
              </p>
              {showPoints && (
                <p className={`text-sm font-semibold mt-1 ${
                  pokemonPoints[hoveredPokemon.id] !== undefined
                    ? 'text-green-600'
                    : 'text-amber-600'
                }`}>
                  {pokemonPoints[hoveredPokemon.id] !== undefined
                    ? `Points: ${pokemonPoints[hoveredPokemon.id]}`
                    : 'No points assigned'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Point editor popup */}
      {editingPokemonId !== null && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/20"
          onClick={handleCancelEdit}
        >
          <div
            className="bg-white rounded-lg shadow-xl p-4 min-w-[200px]"
            onClick={e => e.stopPropagation()}
          >
            {(() => {
              const p = pokemon.find(p => p.id === editingPokemonId)
              if (!p) return null
              return (
                <>
                  <div className="flex items-center gap-2 mb-3">
                    <img src={getSpriteUrl(p.id)} alt={p.name} className="w-10 h-10" />
                    <div>
                      <p className="font-semibold">#{p.id} {formatName(p.name)}</p>
                      <p className="text-xs text-gray-500">Set point value</p>
                    </div>
                  </div>
                  <input
                    ref={editInputRef}
                    type="number"
                    min="0"
                    value={editValue}
                    onChange={e => setEditValue(e.target.value)}
                    onKeyDown={handleEditKeyDown}
                    className="input w-full mb-3"
                    placeholder="Enter points..."
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleSavePoints}
                      className="btn btn-primary flex-1 text-sm"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (onPointChange) {
                          onPointChange(editingPokemonId, null)
                        }
                        setEditingPokemonId(null)
                        setEditValue('')
                      }}
                      className="btn btn-secondary text-sm text-red-600"
                    >
                      Clear
                    </button>
                  </div>
                </>
              )
            })()}
          </div>
        </div>
      )}

      {/* Pokemon grid */}
      <div
        className="pokemon-grid bg-gray-100 rounded-lg p-2 overflow-y-auto border-2 border-gray-300"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(40px, 1fr))',
          gap: '2px',
          maxHeight: '400px',
        }}
      >
        {filteredPokemon.map(p => (
          <button
            type="button"
            key={p.id}
            onClick={() => handleClick(p.id)}
            onMouseEnter={() => setHoveredPokemon(p)}
            onMouseLeave={() => setHoveredPokemon(null)}
            className={`
              relative w-10 h-10 rounded transition-all duration-150
              ${p.included
                ? 'bg-white hover:bg-blue-50 hover:ring-2 hover:ring-blue-400'
                : 'bg-gray-200 opacity-40 hover:opacity-60'
              }
              ${p.isCustomExcluded ? 'ring-2 ring-red-400' : ''}
              ${p.isCustomIncluded ? 'ring-2 ring-green-400' : ''}
              ${showPoints && p.included && !p.hasPoints ? 'ring-2 ring-amber-400 bg-amber-50' : ''}
              ${editablePoints ? 'cursor-pointer' : ''}
            `}
            title={`#${p.id} ${formatName(p.name)}${showPoints && p.hasPoints ? ` (${p.points} pts)` : ''}`}
          >
            <img
              src={getSpriteUrl(p.id)}
              alt={p.name}
              className={`w-full h-full object-contain ${!p.included ? 'grayscale' : ''}`}
              loading="lazy"
            />
            {p.isCustomExcluded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-red-500 text-lg font-bold">×</span>
              </div>
            )}
            {p.isCustomIncluded && !showPoints && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full" />
            )}
            {/* Point value badge */}
            {showPoints && p.hasPoints && (
              <div className="absolute -bottom-1 -right-1 bg-green-600 text-white text-[8px] font-bold rounded px-1 min-w-[14px] text-center leading-tight py-0.5">
                {p.points}
              </div>
            )}
            {/* Missing points indicator */}
            {showPoints && p.included && !p.hasPoints && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-amber-500 rounded-full flex items-center justify-center">
                <span className="text-white text-[8px] font-bold">?</span>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-gray-500">
        <span>{editablePoints ? 'Click to edit points' : 'Click to toggle'}</span>
        {!showPoints && (
          <>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded border-2 border-red-400"></span> Manually excluded
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded border-2 border-green-400"></span> Manually included
            </span>
          </>
        )}
        {showPoints && (
          <>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-green-600"></span> Has points
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded border-2 border-amber-400 bg-amber-50"></span> Missing points
            </span>
          </>
        )}
      </div>
    </div>
  )
}
