import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDraftStore } from '../hooks/useDraftStore'
import { useWebSocket } from '../hooks/useWebSocket'

export default function DraftRoom() {
  const { draftId } = useParams<{ draftId: string }>()
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
  } = useDraftStore()

  const { isConnected, makePick } = useWebSocket({
    draftId: draftId!,
    onStateUpdate: setDraftState,
    onPickMade: (data) => {
      updatePick({
        pick_number: data.pick_number,
        team_id: data.team_id,
        team_name: '', // TODO: Get from state
        pokemon_id: data.pokemon_id,
        pokemon_name: '', // TODO: Get from state
        picked_at: new Date().toISOString(),
      })
    },
    onTimerTick: (data) => setSecondsRemaining(data.seconds_remaining),
    onError: (data) => console.error('Draft error:', data.message),
  })

  const currentTeam = getCurrentTeam()
  const filteredPokemon = getFilteredPokemon()

  const handleMakePick = () => {
    if (selectedPokemon) {
      makePick(selectedPokemon.id)
      setSelectedPokemon(null)
    }
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
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">Draft Room</h1>
            <p className="text-sm text-gray-500">
              Pick {draftState.current_pick + 1} of {draftState.teams.length * draftState.roster_size}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            {secondsRemaining !== null && (
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
          {draftState.teams.map((team) => (
            <div
              key={team.team_id}
              className={`card p-4 ${currentTeam?.team_id === team.team_id ? 'ring-2 ring-pokemon-blue' : ''}`}
            >
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">{team.display_name}</span>
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
                {team.pokemon.map((pokemonId) => (
                  <div
                    key={pokemonId}
                    className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-xs"
                  >
                    {pokemonId}
                  </div>
                ))}
              </div>
            </div>
          ))}
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
                  {pokemon.sprite && (
                    <img
                      src={pokemon.sprite}
                      alt={pokemon.name}
                      className="w-16 h-16 mx-auto"
                    />
                  )}
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
                {selectedPokemon.sprite && (
                  <img
                    src={selectedPokemon.sprite}
                    alt={selectedPokemon.name}
                    className="w-32 h-32 mx-auto"
                  />
                )}
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
                  className="btn btn-primary w-full mt-4"
                  disabled={draftState.status !== 'live'}
                >
                  Confirm Pick
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
