import { useParams } from 'react-router-dom'
import { useDraftStore } from '../hooks/useDraftStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { useEffect, useState, useCallback } from 'react'
import { draftService } from '../services/draft'
import { useSprite } from '../context/SpriteContext'

export default function DraftRoom() {
  const { draftId } = useParams<{ draftId: string }>()
  const { getSpriteUrl } = useSprite()

  // Read team ID and session token synchronously to avoid race condition with WebSocket
  const [myTeamId] = useState<string | null>(() =>
    draftId ? localStorage.getItem(`draft_team_${draftId}`) : null
  )
  const [sessionToken] = useState<string | null>(() =>
    draftId ? localStorage.getItem(`draft_session_${draftId}`) : null
  )

  const [showExportModal, setShowExportModal] = useState(false)
  const [exportContent, setExportContent] = useState('')

  const {
    draftState,
    secondsRemaining,
    selectedPokemon,
    setDraftState,
    updatePick,
    setSecondsRemaining,
    setSelectedPokemon,
    getCurrentTeam,
    getFilteredPokemon,
    searchQuery,
    setSearchQuery,
    typeFilter,
    setTypeFilter,
    reset,
  } = useDraftStore()

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      reset()
    }
  }, [reset])

  // Helper to look up team name from current state
  const getTeamName = useCallback((teamId: string): string => {
    const state = useDraftStore.getState().draftState
    const team = state?.teams.find(t => t.team_id === teamId)
    return team?.display_name || 'Unknown Team'
  }, [])

  // Helper to look up pokemon name from current state
  const getPokemonName = useCallback((pokemonId: number): string => {
    const state = useDraftStore.getState().draftState
    const pokemon = state?.available_pokemon.find(p => p.id === pokemonId)
    return pokemon?.name || `Pokemon #${pokemonId}`
  }, [])

  const { isConnected, makePick } = useWebSocket({
    draftId: draftId!,
    teamId: myTeamId,
    sessionToken,
    onStateUpdate: (state) => {
      setDraftState(state)
    },
    onPickMade: (data) => {
      updatePick({
        pick_number: data.pick_number,
        team_id: data.team_id,
        team_name: getTeamName(data.team_id),
        pokemon_id: data.pokemon_id,
        pokemon_name: getPokemonName(data.pokemon_id),
        picked_at: new Date().toISOString(),
      })
    },
    onTimerTick: (data) => setSecondsRemaining(data.seconds_remaining),
    onError: (data) => console.error('Draft error:', data.message),
  })

  const currentTeam = getCurrentTeam()
  const filteredPokemon = getFilteredPokemon()
  const isMyTurn = myTeamId && currentTeam?.team_id === myTeamId

  const handleMakePick = () => {
    if (selectedPokemon && isMyTurn) {
      makePick(selectedPokemon.id)
      setSelectedPokemon(null)
    }
  }

  const handleExport = async (teamId: string) => {
    if (!draftId) return
    try {
      const result = await draftService.exportTeam(draftId, teamId, 'showdown')
      setExportContent(result.content)
      setShowExportModal(true)
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  const copyExport = () => {
    navigator.clipboard.writeText(exportContent)
  }

  if (!draftState) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {isConnected ? 'Loading draft...' : 'Connecting...'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Export Team</h2>
              <button onClick={() => setShowExportModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <pre className="bg-gray-100 p-4 rounded text-sm font-mono whitespace-pre-wrap mb-4">
              {exportContent}
            </pre>
            <div className="flex gap-2">
              <button onClick={copyExport} className="btn btn-primary">
                Copy to Clipboard
              </button>
              <button onClick={() => setShowExportModal(false)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">Draft Room</h1>
            {draftState.status === 'completed' ? (
              <p className="text-sm text-green-600 font-medium">Draft Complete!</p>
            ) : (
              <p className="text-sm text-gray-500">
                Pick {draftState.current_pick + 1} of {draftState.teams.length * draftState.roster_size}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-4">
            {isMyTurn && draftState.status === 'live' && (
              <span className="bg-pokemon-blue text-white px-3 py-1 rounded-full text-sm font-medium animate-pulse">
                Your Turn!
              </span>
            )}
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            {secondsRemaining !== null && draftState.status === 'live' && (
              <div className={`text-2xl font-bold ${secondsRemaining < 10 ? 'text-red-600' : ''}`}>
                {secondsRemaining}s
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-12 gap-6">
        {/* Teams Panel */}
        <div className="col-span-3 space-y-4">
          <h2 className="font-semibold text-gray-700">Teams</h2>
          {draftState.teams.map((team) => {
            const isCurrentTurn = currentTeam?.team_id === team.team_id
            const isMyTeam = myTeamId === team.team_id
            return (
              <div
                key={team.team_id}
                className={`card p-4 ${isCurrentTurn ? 'ring-2 ring-pokemon-blue' : ''} ${isMyTeam ? 'bg-blue-50' : ''}`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">
                    {team.display_name}
                    {isMyTeam && <span className="text-xs text-pokemon-blue ml-1">(You)</span>}
                  </span>
                  <span className="text-sm text-gray-500">
                    {team.pokemon.length}/{draftState.roster_size}
                  </span>
                </div>
                {draftState.budget_enabled && (
                  <div className="text-sm text-gray-500">
                    Budget: {team.budget_remaining}
                  </div>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {team.pokemon.map((pokemonId) => {
                    const pokemon = draftState.picks.find(p => p.pokemon_id === pokemonId)
                    return (
                      <div
                        key={pokemonId}
                        className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-xs"
                        title={pokemon?.pokemon_name || `#${pokemonId}`}
                      >
                        {pokemonId}
                      </div>
                    )
                  })}
                </div>
                {draftState.status === 'completed' && (
                  <button
                    onClick={() => handleExport(team.team_id)}
                    className="btn btn-secondary text-xs w-full mt-2"
                  >
                    Export Team
                  </button>
                )}
              </div>
            )
          })}
        </div>

        {/* Pokemon Selection */}
        <div className="col-span-6">
          <div className="card">
            <div className="flex gap-4 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Pokemon..."
                className="input flex-1"
              />
              <select
                value={typeFilter || ''}
                onChange={(e) => setTypeFilter(e.target.value || null)}
                className="input w-32"
              >
                <option value="">All Types</option>
                <option value="normal">Normal</option>
                <option value="fire">Fire</option>
                <option value="water">Water</option>
                <option value="electric">Electric</option>
                <option value="grass">Grass</option>
                <option value="ice">Ice</option>
                <option value="fighting">Fighting</option>
                <option value="poison">Poison</option>
                <option value="ground">Ground</option>
                <option value="flying">Flying</option>
                <option value="psychic">Psychic</option>
                <option value="bug">Bug</option>
                <option value="rock">Rock</option>
                <option value="ghost">Ghost</option>
                <option value="dragon">Dragon</option>
                <option value="dark">Dark</option>
                <option value="steel">Steel</option>
                <option value="fairy">Fairy</option>
              </select>
            </div>

            <div className="grid grid-cols-4 gap-2 max-h-96 overflow-y-auto">
              {filteredPokemon.map((pokemon) => (
                <div
                  key={pokemon.id}
                  onClick={() => setSelectedPokemon(pokemon)}
                  className={`pokemon-card p-2 text-center ${
                    selectedPokemon?.id === pokemon.id ? 'border-pokemon-blue bg-blue-50' : ''
                  }`}
                >
                  <img
                    src={getSpriteUrl(pokemon.id)}
                    alt={pokemon.name}
                    className="w-16 h-16 mx-auto"
                  />
                  <div className="text-sm font-medium capitalize">{pokemon.name}</div>
                  <div className="flex justify-center gap-1 mt-1">
                    {pokemon.types.map((type) => (
                      <span
                        key={type}
                        className={`type-badge bg-type-${type}`}
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Selection Panel */}
        <div className="col-span-3">
          <div className="card sticky top-6">
            <h2 className="font-semibold text-gray-700 mb-4">Your Pick</h2>
            {selectedPokemon ? (
              <div className="text-center">
                <img
                  src={getSpriteUrl(selectedPokemon.id)}
                  alt={selectedPokemon.name}
                  className="w-32 h-32 mx-auto"
                />
                <div className="text-xl font-bold capitalize mt-2">
                  {selectedPokemon.name}
                </div>
                <div className="flex justify-center gap-1 mt-2">
                  {selectedPokemon.types.map((type) => (
                    <span key={type} className={`type-badge bg-type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
                <button
                  onClick={handleMakePick}
                  className="btn btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={draftState.status !== 'live' || !isMyTurn}
                >
                  {isMyTurn ? 'Confirm Pick' : "Waiting for your turn..."}
                </button>
              </div>
            ) : (
              <p className="text-gray-500 text-center">
                Select a Pokemon to pick
              </p>
            )}
          </div>

          {/* Recent Picks */}
          <div className="card mt-4">
            <h2 className="font-semibold text-gray-700 mb-4">Recent Picks</h2>
            <div className="space-y-2">
              {draftState.picks.slice(-5).reverse().map((pick) => (
                <div key={pick.pick_number} className="text-sm">
                  <span className="text-gray-500">#{pick.pick_number + 1}</span>{' '}
                  <span className="font-medium">{pick.team_name}</span>:{' '}
                  <span className="capitalize">{pick.pokemon_name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
