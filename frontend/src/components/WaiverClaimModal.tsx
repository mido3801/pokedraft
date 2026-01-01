import { useState, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Team, FreeAgentPokemon, TYPE_COLORS } from '../types'
import { waiverService } from '../services/waiver'
import { queryKeys } from '../services/queryKeys'
import { useSprite } from '../context/SpriteContext'
import { X, Search, AlertCircle } from 'lucide-react'

interface WaiverClaimModalProps {
  isOpen: boolean
  onClose: () => void
  seasonId: string
  myTeam: Team
  requireDrop: boolean
}

// Format Pokemon name for display
function formatName(name: string): string {
  return name
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export default function WaiverClaimModal({
  isOpen,
  onClose,
  seasonId,
  myTeam,
  requireDrop,
}: WaiverClaimModalProps) {
  const queryClient = useQueryClient()
  const { getSpriteUrl } = useSprite()

  const [selectedPokemon, setSelectedPokemon] = useState<FreeAgentPokemon | null>(null)
  const [dropPokemonId, setDropPokemonId] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [hoveredPokemon, setHoveredPokemon] = useState<FreeAgentPokemon | null>(null)

  // Fetch free agents
  const { data: freeAgents, isLoading: loadingFreeAgents } = useQuery({
    queryKey: queryKeys.seasonFreeAgents(seasonId),
    queryFn: () => waiverService.getFreeAgents(seasonId),
    enabled: isOpen,
  })

  // Fetch pending claims to know which Pokemon are already claimed by this user
  const { data: pendingClaims } = useQuery({
    queryKey: queryKeys.seasonWaiverClaims(seasonId),
    queryFn: () => waiverService.getClaims(seasonId, 'pending', myTeam.id),
    enabled: isOpen,
  })

  // Get set of Pokemon IDs that user already has pending claims for
  const pendingClaimPokemonIds = useMemo(() => {
    if (!pendingClaims?.claims) return new Set<number>()
    return new Set(pendingClaims.claims.map((c) => c.pokemon_id))
  }, [pendingClaims])

  // Filter and categorize Pokemon
  const { availablePokemon, unavailablePokemon } = useMemo(() => {
    if (!freeAgents?.pokemon) return { availablePokemon: [], unavailablePokemon: [] }

    const term = searchTerm.toLowerCase()
    const filtered = freeAgents.pokemon.filter(
      (p) =>
        !searchTerm ||
        p.name.toLowerCase().includes(term) ||
        p.types.some((t) => t.toLowerCase().includes(term))
    )

    // Separate into available and unavailable (already claimed by user)
    const available: FreeAgentPokemon[] = []
    const unavailable: FreeAgentPokemon[] = []

    for (const pokemon of filtered) {
      if (pendingClaimPokemonIds.has(pokemon.pokemon_id)) {
        unavailable.push(pokemon)
      } else {
        available.push(pokemon)
      }
    }

    return { availablePokemon: available, unavailablePokemon: unavailable }
  }, [freeAgents, searchTerm, pendingClaimPokemonIds])

  const allFilteredPokemon = useMemo(() => {
    // Sort: available first, then unavailable
    return [...availablePokemon, ...unavailablePokemon]
  }, [availablePokemon, unavailablePokemon])

  const claimMutation = useMutation({
    mutationFn: () =>
      waiverService.createClaim({
        season_id: seasonId,
        pokemon_id: selectedPokemon!.pokemon_id,
        drop_pokemon_id: dropPokemonId || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonFreeAgents(seasonId) })
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to submit waiver claim')
    },
  })

  const handleClose = () => {
    setSelectedPokemon(null)
    setDropPokemonId('')
    setSearchTerm('')
    setError(null)
    setHoveredPokemon(null)
    onClose()
  }

  const handlePokemonClick = (pokemon: FreeAgentPokemon) => {
    // Don't allow selecting Pokemon with pending claims
    if (pendingClaimPokemonIds.has(pokemon.pokemon_id)) return
    setSelectedPokemon(pokemon)
  }

  const canSubmit =
    selectedPokemon !== null && (!requireDrop || dropPokemonId) && !claimMutation.isPending

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center bg-gradient-to-r from-pokemon-blue to-blue-600">
          <h2 className="text-xl font-bold text-white">Claim Free Agent</h2>
          <button
            onClick={handleClose}
            className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by name or type..."
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all"
              />
            </div>
          </div>

          {/* Pokemon Box */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Available Free Agents
              </label>
              <div className="text-sm text-gray-500">
                <span className="font-semibold text-green-600">{availablePokemon.length}</span>
                <span className="text-gray-400"> / </span>
                <span>{freeAgents?.total || 0}</span>
                <span className="text-gray-400 ml-1">available</span>
              </div>
            </div>

            {loadingFreeAgents ? (
              <div className="flex items-center justify-center h-64 bg-gray-100 rounded-xl">
                <div className="text-center">
                  <div className="loader w-8 h-8 mx-auto mb-2" />
                  <p className="text-gray-600">Loading free agents...</p>
                </div>
              </div>
            ) : allFilteredPokemon.length > 0 ? (
              <>
                {/* Pokemon tooltip */}
                {hoveredPokemon && (
                  <div
                    className="fixed z-[60] bg-white shadow-xl rounded-xl p-4 pointer-events-none border border-gray-200"
                    style={{
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      minWidth: '220px',
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <img
                        src={hoveredPokemon.sprite || getSpriteUrl(hoveredPokemon.pokemon_id)}
                        alt={hoveredPokemon.name}
                        className="w-16 h-16"
                      />
                      <div>
                        <p className="font-bold text-gray-900">
                          #{hoveredPokemon.pokemon_id} {formatName(hoveredPokemon.name)}
                        </p>
                        <div className="flex gap-1 mt-1">
                          {hoveredPokemon.types.map((type) => (
                            <span
                              key={type}
                              className="px-2 py-0.5 rounded text-xs text-white font-medium"
                              style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                            >
                              {type.toUpperCase()}
                            </span>
                          ))}
                        </div>
                        {hoveredPokemon.base_stat_total && (
                          <p className="text-xs text-gray-500 mt-1">
                            BST: {hoveredPokemon.base_stat_total}
                            {hoveredPokemon.generation && ` | Gen ${hoveredPokemon.generation}`}
                          </p>
                        )}
                        {pendingClaimPokemonIds.has(hoveredPokemon.pokemon_id) && (
                          <p className="text-xs text-amber-600 font-medium mt-1">
                            You have a pending claim
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Pokemon grid */}
                <div
                  className="bg-gray-100 rounded-xl p-3 overflow-y-auto border-2 border-gray-200"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(48px, 1fr))',
                    gap: '4px',
                    maxHeight: '320px',
                  }}
                >
                  {allFilteredPokemon.map((pokemon) => {
                    const isPendingClaim = pendingClaimPokemonIds.has(pokemon.pokemon_id)
                    const isSelected = selectedPokemon?.pokemon_id === pokemon.pokemon_id

                    return (
                      <button
                        type="button"
                        key={pokemon.pokemon_id}
                        onClick={() => handlePokemonClick(pokemon)}
                        onMouseEnter={() => setHoveredPokemon(pokemon)}
                        onMouseLeave={() => setHoveredPokemon(null)}
                        disabled={isPendingClaim}
                        className={`
                          relative w-12 h-12 rounded-lg transition-all duration-150
                          ${
                            isPendingClaim
                              ? 'bg-gray-200 opacity-40 cursor-not-allowed'
                              : isSelected
                                ? 'bg-blue-100 ring-2 ring-blue-500 scale-110 z-10'
                                : 'bg-white hover:bg-blue-50 hover:ring-2 hover:ring-blue-300 cursor-pointer'
                          }
                        `}
                        title={`#${pokemon.pokemon_id} ${formatName(pokemon.name)}${isPendingClaim ? ' (Pending claim)' : ''}`}
                      >
                        <img
                          src={pokemon.sprite || getSpriteUrl(pokemon.pokemon_id)}
                          alt={pokemon.name}
                          className={`w-full h-full object-contain ${isPendingClaim ? 'grayscale' : ''}`}
                          loading="lazy"
                        />
                        {isPendingClaim && (
                          <div className="absolute inset-0 flex items-center justify-center bg-gray-500/20 rounded-lg">
                            <span className="text-amber-500 text-xs font-bold">CLAIMED</span>
                          </div>
                        )}
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-xs">✓</span>
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* Legend */}
                <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>Click to select</span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-blue-500"></span> Selected
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-gray-300 opacity-40"></span> Already claimed
                  </span>
                </div>
              </>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
                <p className="text-gray-500">
                  {searchTerm ? 'No Pokemon match your search.' : 'No free agents available.'}
                </p>
              </div>
            )}
          </div>

          {/* Selected Pokemon Preview */}
          {selectedPokemon && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <h4 className="text-sm font-medium text-blue-800 mb-2">Selected Pokemon:</h4>
              <div className="flex items-center gap-4">
                <img
                  src={selectedPokemon.sprite || getSpriteUrl(selectedPokemon.pokemon_id)}
                  alt={selectedPokemon.name}
                  className="w-20 h-20"
                />
                <div>
                  <p className="text-lg font-bold text-gray-900">{formatName(selectedPokemon.name)}</p>
                  <div className="flex gap-1 mt-1">
                    {selectedPokemon.types.map((type) => (
                      <span
                        key={type}
                        className="px-2 py-0.5 rounded text-xs text-white font-medium"
                        style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                  {selectedPokemon.base_stat_total && (
                    <p className="text-sm text-gray-600 mt-1">BST: {selectedPokemon.base_stat_total}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Drop Pokemon Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Drop a Pokemon {requireDrop ? <span className="text-red-500">*</span> : '(Optional)'}
            </label>
            {myTeam.pokemon && myTeam.pokemon.length > 0 ? (
              <select
                value={dropPokemonId}
                onChange={(e) => setDropPokemonId(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all bg-white"
              >
                <option value="">
                  {requireDrop ? 'Select a Pokemon to drop...' : 'No drop (keep roster as is)'}
                </option>
                {myTeam.pokemon.map((pokemon) => (
                  <option key={pokemon.id} value={pokemon.id}>
                    {pokemon.pokemon_name} ({pokemon.types.join('/')})
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm text-gray-500 p-4 border border-gray-200 rounded-xl bg-gray-50">
                You have no Pokemon to drop.
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
          <button onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={() => claimMutation.mutate()}
            disabled={!canSubmit}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {claimMutation.isPending ? (
              <>
                <div className="loader w-5 h-5 border-2 border-white/30 border-t-white" />
                Submitting...
              </>
            ) : (
              'Submit Claim'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
