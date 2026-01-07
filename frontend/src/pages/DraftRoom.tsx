import { useParams } from 'react-router-dom'
import { useDraftStore } from '../hooks/useDraftStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { useEffect, useState, useCallback } from 'react'
import { draftService } from '../services/draft'
import { useSprite } from '../context/SpriteContext'
import { storage } from '../utils/storage'
import { TYPE_COLORS, type Pokemon } from '../types'

function TypeBadge({ type }: { type: string }) {
  return (
    <span
      className="px-2 py-0.5 rounded text-white text-[10px] font-bold uppercase"
      style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
    >
      {type}
    </span>
  )
}

function getBaseStatTotal(pokemon: Pokemon): number | null {
  if (!pokemon.stats) return null
  return (
    pokemon.stats.hp +
    pokemon.stats.attack +
    pokemon.stats.defense +
    pokemon.stats['special-attack'] +
    pokemon.stats['special-defense'] +
    pokemon.stats.speed
  )
}

export default function DraftRoom() {
  const { draftId } = useParams<{ draftId: string }>()
  const { getSpriteUrl, spriteStyle, setSpriteStyle, getSpriteStyleLabel } = useSprite()

  // Read team ID and session token from localStorage initially
  const [myTeamId, setMyTeamId] = useState<string | null>(() => {
    if (!draftId) return null
    const session = storage.getDraftSession(draftId)
    return session.team
  })
  const [sessionToken] = useState<string | null>(() => {
    if (!draftId) return null
    const session = storage.getDraftSession(draftId)
    return session.session
  })

  // For league drafts, fetch team_id from API if not in localStorage
  useEffect(() => {
    async function fetchMyTeam() {
      if (!draftId || myTeamId) return

      // Check if user has an auth token (league member)
      const token = storage.getToken()
      if (!token) return

      try {
        const result = await draftService.getMyTeam(draftId)
        if (result.team_id) {
          // Store in localStorage for future visits
          storage.setDraftSession(draftId, {
            session: '',
            team: result.team_id,
            rejoin: '',
          })
          setMyTeamId(result.team_id)
        }
      } catch (err) {
        // User might not be part of this draft - that's ok
        console.log('Could not fetch team for draft:', err)
      }
    }
    fetchMyTeam()
  }, [draftId, myTeamId])

  const [showExportModal, setShowExportModal] = useState(false)
  const [exportContent, setExportContent] = useState('')
  const [exportFilename, setExportFilename] = useState('')
  const [showShareModal, setShowShareModal] = useState(false)

  const {
    draftState,
    secondsRemaining,
    selectedPokemon,
    setDraftState,
    updatePick,
    addTeam,
    setSecondsRemaining,
    setSelectedPokemon,
    getCurrentTeam,
    getFilteredPokemon,
    searchQuery,
    setSearchQuery,
    typeFilter,
    setTypeFilter,
    generationFilter,
    setGenerationFilter,
    bstMin,
    setBstMin,
    bstMax,
    setBstMax,
    statFilter,
    setStatFilter,
    statMin,
    setStatMin,
    abilityFilter,
    setAbilityFilter,
    legendaryFilter,
    setLegendaryFilter,
    clearFilters,
    reset,
  } = useDraftStore()

  const [showFilters, setShowFilters] = useState(false)
  const [showTeamsPanel, setShowTeamsPanel] = useState(false)

  // Auction-specific state
  const [currentNomination, setCurrentNomination] = useState<{
    pokemon_id: number
    pokemon_name: string
    nominator_id: string
    nominator_name: string
    min_bid: number
  } | null>(null)
  const [currentBid, setCurrentBid] = useState<{
    bidder_id: string
    bidder_name: string
    amount: number
  } | null>(null)
  const [bidTimerEnd, setBidTimerEnd] = useState<string | null>(null)
  const [bidAmount, setBidAmount] = useState<number>(1)
  const [bidSecondsRemaining, setBidSecondsRemaining] = useState<number | null>(null)

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

  const { isConnected, makePick, startDraft, nominate, placeBid } = useWebSocket({
    draftId: draftId!,
    teamId: myTeamId,
    sessionToken,
    onStateUpdate: (state) => {
      setDraftState(state)
      // Initialize auction state from server state
      if (state.current_nomination) {
        setCurrentNomination({
          pokemon_id: state.current_nomination.pokemon_id,
          pokemon_name: state.current_nomination.pokemon_name,
          nominator_id: state.current_nomination.nominator_id,
          nominator_name: state.current_nomination.nominator_name,
          min_bid: state.min_bid || 1,
        })
      }
      if (state.current_highest_bid) {
        setCurrentBid({
          bidder_id: state.current_highest_bid.team_id,
          bidder_name: state.current_highest_bid.team_name,
          amount: state.current_highest_bid.amount,
        })
        setBidAmount(state.current_highest_bid.amount + (state.bid_increment || 1))
      }
      if (state.bid_timer_end) {
        setBidTimerEnd(state.bid_timer_end)
      }
    },
    onPickMade: (data) => {
      updatePick({
        pick_number: data.pick_number,
        team_id: data.team_id,
        team_name: getTeamName(data.team_id),
        pokemon_id: data.pokemon_id,
        pokemon_name: getPokemonName(data.pokemon_id),
        picked_at: new Date().toISOString(),
        points_spent: data.points_spent,
      })
      // Clear auction state after pick
      setCurrentNomination(null)
      setCurrentBid(null)
      setBidTimerEnd(null)
      setBidSecondsRemaining(null)
    },
    onDraftStarted: (data) => {
      // Update draft state when draft starts
      if (draftState) {
        setDraftState({
          ...draftState,
          status: 'live',
          pick_order: data.pick_order,
        })
      }
    },
    onDraftComplete: () => {
      // Update draft state when draft completes
      if (draftState) {
        setDraftState({
          ...draftState,
          status: 'completed',
        })
      }
    },
    onUserJoined: (data) => {
      addTeam(data.team_id, data.display_name)
    },
    onTimerTick: (data) => setSecondsRemaining(data.seconds_remaining),
    onError: (data) => console.error('Draft error:', data.message),
    // Auction handlers
    onNomination: (data) => {
      setCurrentNomination({
        pokemon_id: data.pokemon_id,
        pokemon_name: data.pokemon_name,
        nominator_id: data.nominator_id,
        nominator_name: data.nominator_name,
        min_bid: data.min_bid,
      })
      setCurrentBid({
        bidder_id: data.current_bidder_id,
        bidder_name: data.current_bidder_name,
        amount: data.current_bid,
      })
      setBidTimerEnd(data.bid_timer_end)
      setBidAmount(data.current_bid + (draftState?.bid_increment || 1))
    },
    onBidUpdate: (data) => {
      setCurrentBid({
        bidder_id: data.bidder_id,
        bidder_name: data.bidder_name,
        amount: data.amount,
      })
      setBidTimerEnd(data.bid_timer_end)
      setBidAmount(data.amount + (draftState?.bid_increment || 1))
    },
  })

  // Bid timer countdown effect
  useEffect(() => {
    if (!bidTimerEnd) {
      setBidSecondsRemaining(null)
      return
    }

    const updateTimer = () => {
      const end = new Date(bidTimerEnd).getTime()
      const now = Date.now()
      const remaining = Math.max(0, Math.ceil((end - now) / 1000))
      setBidSecondsRemaining(remaining)
    }

    updateTimer()
    const interval = setInterval(updateTimer, 100)
    return () => clearInterval(interval)
  }, [bidTimerEnd])

  const currentTeam = getCurrentTeam()
  const filteredPokemon = getFilteredPokemon()
  const isMyTurn = myTeamId && currentTeam?.team_id === myTeamId

  // Check if current user is the draft creator (draft_position === 0)
  const myTeam = draftState?.teams.find(t => t.team_id === myTeamId)
  const isCreator = myTeam?.draft_position === 0

  // Auction-specific computed values
  const isAuction = draftState?.format === 'auction'
  const isNominatingPhase = isAuction && !currentNomination
  const isBiddingPhase = isAuction && currentNomination !== null
  const isHighestBidder = currentBid && myTeamId === currentBid.bidder_id
  const canAffordBid = myTeam && myTeam.budget_remaining !== undefined
    ? myTeam.budget_remaining >= bidAmount
    : true
  const hasRosterSpace = myTeam
    ? myTeam.pokemon.length < (draftState?.roster_size || 6)
    : false

  const handleMakePick = () => {
    if (selectedPokemon && isMyTurn) {
      makePick(selectedPokemon.id)
      setSelectedPokemon(null)
    }
  }

  const handleNominate = () => {
    if (selectedPokemon && isMyTurn && isNominatingPhase) {
      nominate(selectedPokemon.id)
      setSelectedPokemon(null)
    }
  }

  const handlePlaceBid = () => {
    if (currentNomination && canAffordBid && hasRosterSpace && !isHighestBidder) {
      placeBid(currentNomination.pokemon_id, bidAmount)
    }
  }

  const handleExport = async (teamId: string) => {
    if (!draftId) return
    try {
      const result = await draftService.exportTeam(draftId, teamId, 'showdown')
      setExportContent(result.content)
      setExportFilename(result.filename)
      setShowExportModal(true)
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  const downloadExport = () => {
    const blob = new Blob([exportContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = exportFilename || 'team.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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
              <button onClick={downloadExport} className="btn btn-primary">
                Download .txt
              </button>
              <button onClick={copyExport} className="btn btn-secondary">
                Copy to Clipboard
              </button>
              <button onClick={() => setShowExportModal(false)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Share Draft</h2>
              <button onClick={() => setShowShareModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {draftState?.rejoin_code && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Invite Code</label>
                  <div className="flex gap-2">
                    <div className="input text-center text-2xl tracking-widest font-bold flex-1 bg-gray-50">
                      {draftState.rejoin_code}
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(draftState.rejoin_code!)}
                      className="btn btn-secondary px-3"
                      title="Copy code"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Join Link</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={`${window.location.origin}/draft/join`}
                    readOnly
                    className="input flex-1 bg-gray-50 text-sm"
                  />
                  <button
                    onClick={() => navigator.clipboard.writeText(`${window.location.origin}/draft/join`)}
                    className="btn btn-secondary px-3"
                    title="Copy link"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Share this link along with the code above
                </p>
              </div>

              <div className="pt-2">
                <button
                  onClick={() => setShowShareModal(false)}
                  className="btn btn-primary w-full"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3">
          {/* Top row: Title and timer/status */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-lg sm:text-xl font-bold">Draft Room</h1>
                {draftState.status === 'completed' ? (
                  <p className="text-sm text-green-600 font-medium">Draft Complete!</p>
                ) : draftState.status === 'pending' ? (
                  <p className="text-xs sm:text-sm text-gray-500">
                    {draftState.teams.length} team{draftState.teams.length !== 1 ? 's' : ''} joined
                    <span className="hidden sm:inline">
                      {draftState.teams.length < 2 && ' (need at least 2 to start)'}
                    </span>
                  </p>
                ) : (
                  <p className="text-xs sm:text-sm text-gray-500">
                    Pick {draftState.current_pick + 1} of {draftState.teams.length * draftState.roster_size}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              {/* Timer - always visible when live */}
              {secondsRemaining !== null && draftState.status === 'live' && (
                <div className={`text-xl sm:text-2xl font-bold ${secondsRemaining < 10 ? 'text-red-600' : ''}`}>
                  {secondsRemaining}s
                </div>
              )}
              {/* Your Turn indicator */}
              {isMyTurn && draftState.status === 'live' && (
                <span className="bg-pokemon-blue text-white px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium animate-pulse whitespace-nowrap">
                  Your Turn!
                </span>
              )}
              {/* Connection status */}
              <div className={`w-3 h-3 rounded-full flex-shrink-0 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} title={isConnected ? 'Connected' : 'Disconnected'} />
            </div>
          </div>

          {/* Bottom row: Actions and controls */}
          <div className="flex items-center justify-between mt-2 gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              {isCreator && draftState.status === 'pending' && (
                <button
                  onClick={startDraft}
                  disabled={draftState.teams.length < 2}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                >
                  Start Draft
                </button>
              )}
              {draftState.status === 'pending' && !isCreator && (
                <span className="bg-yellow-100 text-yellow-800 px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium">
                  Waiting for host...
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <select
                value={spriteStyle}
                onChange={(e) => setSpriteStyle(e.target.value as 'default' | 'official-artwork' | 'home')}
                className="text-xs sm:text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-pokemon-blue"
                title="Sprite style"
              >
                <option value="default">{getSpriteStyleLabel('default')}</option>
                <option value="official-artwork">{getSpriteStyleLabel('official-artwork')}</option>
                <option value="home">{getSpriteStyleLabel('home')}</option>
              </select>
              <button
                onClick={() => setShowShareModal(true)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Share draft"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile: Your Pick sticky bar at bottom */}
      {selectedPokemon && !isBiddingPhase && (
        <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-40 p-3">
          <div className="flex items-center gap-3">
            <img
              src={getSpriteUrl(selectedPokemon.id)}
              alt={selectedPokemon.name}
              className="w-12 h-12"
            />
            <div className="flex-1 min-w-0">
              <div className="font-bold capitalize truncate">{selectedPokemon.name}</div>
              <div className="flex gap-1">
                {selectedPokemon.types.map((type) => (
                  <TypeBadge key={type} type={type} />
                ))}
              </div>
            </div>
            {isAuction && isNominatingPhase ? (
              <button
                onClick={handleNominate}
                className="btn btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                disabled={draftState.status !== 'live' || !isMyTurn || !hasRosterSpace}
              >
                {isMyTurn ? 'Nominate' : 'Wait...'}
              </button>
            ) : (
              <button
                onClick={handleMakePick}
                className="btn btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                disabled={draftState.status !== 'live' || !isMyTurn}
              >
                {isMyTurn ? 'Pick' : 'Wait...'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Mobile: Auction bid bar at bottom */}
      {isBiddingPhase && currentNomination && currentBid && (
        <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-40 p-3">
          <div className="flex items-center gap-3">
            <img
              src={getSpriteUrl(currentNomination.pokemon_id)}
              alt={currentNomination.pokemon_name}
              className="w-12 h-12"
            />
            <div className="flex-1 min-w-0">
              <div className="font-bold capitalize truncate">{currentNomination.pokemon_name}</div>
              <div className="text-sm">
                {isHighestBidder ? (
                  <span className="text-green-600">Winning: {currentBid.amount}</span>
                ) : (
                  <span className="text-gray-600">High: {currentBid.amount} ({currentBid.bidder_name})</span>
                )}
              </div>
            </div>
            {bidSecondsRemaining !== null && (
              <span className={`text-lg font-bold ${bidSecondsRemaining <= 5 ? 'text-red-600' : 'text-gray-700'}`}>
                {bidSecondsRemaining}s
              </span>
            )}
            {!isHighestBidder && hasRosterSpace && (
              <button
                onClick={handlePlaceBid}
                className="btn btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                disabled={!canAffordBid}
              >
                Bid {bidAmount}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="mx-auto px-2 sm:px-4 py-4 pb-24 lg:pb-4">
        {/* Mobile: Collapsible Teams Panel */}
        <div className="lg:hidden mb-4">
          <button
            onClick={() => setShowTeamsPanel(!showTeamsPanel)}
            className="w-full flex items-center justify-between bg-white rounded-lg px-4 py-3 shadow-sm"
          >
            <span className="font-semibold text-gray-700">
              Teams ({draftState.teams.length})
            </span>
            <div className="flex items-center gap-2">
              {currentTeam && (
                <span className="text-xs text-pokemon-blue font-medium">
                  {currentTeam.display_name}'s turn
                </span>
              )}
              <svg
                className={`w-5 h-5 transition-transform ${showTeamsPanel ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>

          {showTeamsPanel && (
            <div className="mt-2 space-y-2">
              {draftState.teams.map((team) => {
                const isCurrentTurn = currentTeam?.team_id === team.team_id
                const isMyTeam = myTeamId === team.team_id
                return (
                  <div
                    key={team.team_id}
                    className={`card p-3 ${isCurrentTurn ? 'ring-2 ring-pokemon-blue' : ''} ${isMyTeam ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium text-sm truncate">
                        {team.display_name}
                        {isMyTeam && <span className="text-xs text-pokemon-blue ml-1">(You)</span>}
                      </span>
                      <span className="text-xs text-gray-500">
                        {team.pokemon.length}/{draftState.roster_size}
                      </span>
                    </div>
                    {draftState.budget_enabled && (
                      <div className="text-sm text-gray-500">
                        Budget: {team.budget_remaining}
                      </div>
                    )}
                    <div className="mt-2 flex flex-wrap gap-0.5">
                      {team.pokemon.map((pokemonId) => {
                        const pokemon = draftState.picks.find(p => p.pokemon_id === pokemonId)
                        return (
                          <img
                            key={pokemonId}
                            src={getSpriteUrl(pokemonId)}
                            alt={pokemon?.pokemon_name || `#${pokemonId}`}
                            title={pokemon?.pokemon_name || `#${pokemonId}`}
                            className="w-8 h-8"
                          />
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
          )}
        </div>

        {/* Desktop: 12-column grid layout */}
        <div className="hidden lg:grid grid-cols-12 gap-4">
          {/* Teams Panel - Desktop */}
          <div className="col-span-2 space-y-3">
            <h2 className="font-semibold text-gray-700">Teams</h2>
            {draftState.teams.map((team) => {
              const isCurrentTurn = currentTeam?.team_id === team.team_id
              const isMyTeam = myTeamId === team.team_id
              return (
                <div
                  key={team.team_id}
                  className={`card p-3 ${isCurrentTurn ? 'ring-2 ring-pokemon-blue' : ''} ${isMyTeam ? 'bg-blue-50' : ''}`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium text-sm truncate">
                      {team.display_name}
                      {isMyTeam && <span className="text-xs text-pokemon-blue ml-1">(You)</span>}
                    </span>
                    <span className="text-xs text-gray-500">
                      {team.pokemon.length}/{draftState.roster_size}
                    </span>
                  </div>
                  {draftState.budget_enabled && (
                    <div className="text-sm text-gray-500">
                      Budget: {team.budget_remaining}
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap gap-0.5">
                    {team.pokemon.map((pokemonId) => {
                      const pokemon = draftState.picks.find(p => p.pokemon_id === pokemonId)
                      return (
                        <img
                          key={pokemonId}
                          src={getSpriteUrl(pokemonId)}
                          alt={pokemon?.pokemon_name || `#${pokemonId}`}
                          title={pokemon?.pokemon_name || `#${pokemonId}`}
                          className="w-8 h-8"
                        />
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

          {/* Pokemon Selection - Desktop */}
          <div className="col-span-8">
          <div className="card">
            {/* Basic filters row */}
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Pokémon..."
                className="input flex-1"
              />
              <select
                value={typeFilter || ''}
                onChange={(e) => setTypeFilter(e.target.value || null)}
                className="input w-28"
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
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'} text-sm`}
              >
                {showFilters ? 'Hide Filters' : 'More Filters'}
              </button>
            </div>

            {/* Advanced filters */}
            {showFilters && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3 space-y-2">
                <div className="flex flex-wrap gap-2">
                  {/* Generation */}
                  <select
                    value={generationFilter ?? ''}
                    onChange={(e) => setGenerationFilter(e.target.value ? Number(e.target.value) : null)}
                    className="input w-24 text-sm py-2"
                  >
                    <option value="">All Gens</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((g) => (
                      <option key={g} value={g}>Gen {g}</option>
                    ))}
                  </select>

                  {/* Legendary filter */}
                  <select
                    value={legendaryFilter}
                    onChange={(e) => setLegendaryFilter(e.target.value as 'all' | 'legendary' | 'mythical' | 'regular')}
                    className="input w-28 text-sm py-2"
                  >
                    <option value="all">All Pokémon</option>
                    <option value="legendary">Legendary</option>
                    <option value="mythical">Mythical</option>
                    <option value="regular">Regular</option>
                  </select>

                  {/* BST Range */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-500">BST:</span>
                    <input
                      type="number"
                      value={bstMin ?? ''}
                      onChange={(e) => setBstMin(e.target.value ? Number(e.target.value) : null)}
                      placeholder="Min"
                      className="input w-20 text-sm py-2"
                    />
                    <span className="text-gray-400">-</span>
                    <input
                      type="number"
                      value={bstMax ?? ''}
                      onChange={(e) => setBstMax(e.target.value ? Number(e.target.value) : null)}
                      placeholder="Max"
                      className="input w-20 text-sm py-2"
                    />
                  </div>

                  {/* Stat filter */}
                  <div className="flex items-center gap-1">
                    <select
                      value={statFilter ?? ''}
                      onChange={(e) => setStatFilter(e.target.value ? e.target.value as 'hp' | 'attack' | 'defense' | 'special-attack' | 'special-defense' | 'speed' : null)}
                      className="input w-24 text-sm py-2"
                    >
                      <option value="">Stat...</option>
                      <option value="hp">HP</option>
                      <option value="attack">Attack</option>
                      <option value="defense">Defense</option>
                      <option value="special-attack">Sp. Atk</option>
                      <option value="special-defense">Sp. Def</option>
                      <option value="speed">Speed</option>
                    </select>
                    <input
                      type="number"
                      value={statMin ?? ''}
                      onChange={(e) => setStatMin(e.target.value ? Number(e.target.value) : null)}
                      placeholder="Min"
                      className="input w-16 text-sm py-2"
                      disabled={!statFilter}
                    />
                  </div>

                  {/* Ability search */}
                  <input
                    type="text"
                    value={abilityFilter}
                    onChange={(e) => setAbilityFilter(e.target.value)}
                    placeholder="Ability..."
                    className="input w-28 text-sm py-2"
                  />

                  {/* Clear all */}
                  <button
                    onClick={clearFilters}
                    className="btn btn-ghost text-sm py-2 px-3"
                  >
                    Clear All
                  </button>
                </div>

                {/* Active filter count */}
                <div className="text-xs text-gray-500">
                  {filteredPokemon.length} Pokemon shown
                </div>
              </div>
            )}

            <div className="grid grid-cols-5 gap-2 max-h-[calc(100vh-240px)] overflow-y-auto">
              {filteredPokemon.map((pokemon) => {
                const bst = getBaseStatTotal(pokemon)
                return (
                  <div
                    key={pokemon.id}
                    onClick={() => setSelectedPokemon(pokemon)}
                    className={`pokemon-card p-2 text-center relative ${
                      selectedPokemon?.id === pokemon.id ? 'border-pokemon-blue bg-blue-50' : ''
                    }`}
                  >
                    {(pokemon.is_legendary || pokemon.is_mythical) && (
                      <span className="absolute top-1 right-1 text-yellow-500 text-xs">★</span>
                    )}
                    <img
                      src={getSpriteUrl(pokemon.id)}
                      alt={pokemon.name}
                      className="w-20 h-20 mx-auto"
                    />
                    <div className="text-sm font-medium capitalize truncate">{pokemon.name}</div>
                    <div className="flex justify-center gap-1 mt-1 flex-wrap">
                      {pokemon.types.map((type) => (
                        <TypeBadge key={type} type={type} />
                      ))}
                    </div>
                    <div className="flex justify-center gap-2 text-[10px] text-gray-500 mt-1">
                      {pokemon.generation && <span>Gen {pokemon.generation}</span>}
                      {bst && <span>BST {bst}</span>}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Selection Panel */}
        <div className="col-span-2">
          {/* Auction: Active Bid Panel */}
          {isAuction && isBiddingPhase && currentNomination && currentBid && (
            <div className="card sticky top-6 mb-4 border-2 border-pokemon-blue">
              <div className="flex justify-between items-center mb-2">
                <h2 className="font-semibold text-pokemon-blue">Active Auction</h2>
                {bidSecondsRemaining !== null && (
                  <span className={`text-xl font-bold ${bidSecondsRemaining <= 5 ? 'text-red-600 animate-pulse' : 'text-gray-700'}`}>
                    {bidSecondsRemaining}s
                  </span>
                )}
              </div>
              <div className="text-center">
                <img
                  src={getSpriteUrl(currentNomination.pokemon_id)}
                  alt={currentNomination.pokemon_name}
                  className="w-20 h-20 mx-auto"
                />
                <div className="text-lg font-bold capitalize">
                  {currentNomination.pokemon_name}
                </div>
                <div className="text-xs text-gray-500 mb-3">
                  Nominated by {currentNomination.nominator_name}
                </div>

                {/* Current High Bid */}
                <div className={`p-3 rounded-lg mb-3 ${isHighestBidder ? 'bg-green-100' : 'bg-gray-100'}`}>
                  <div className="text-sm text-gray-600">Current Bid</div>
                  <div className="text-2xl font-bold">{currentBid.amount}</div>
                  <div className="text-sm">
                    {isHighestBidder ? (
                      <span className="text-green-600 font-medium">You are winning!</span>
                    ) : (
                      <span className="text-gray-600">{currentBid.bidder_name}</span>
                    )}
                  </div>
                </div>

                {/* Bid Controls */}
                {!isHighestBidder && hasRosterSpace && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setBidAmount(Math.max(currentBid.amount + (draftState?.bid_increment || 1), bidAmount - (draftState?.bid_increment || 1)))}
                        className="btn btn-secondary px-3 py-1"
                        disabled={bidAmount <= currentBid.amount + (draftState?.bid_increment || 1)}
                      >
                        -
                      </button>
                      <input
                        type="number"
                        value={bidAmount}
                        onChange={(e) => setBidAmount(Math.max(currentBid.amount + (draftState?.bid_increment || 1), Number(e.target.value)))}
                        className="input text-center w-20"
                        min={currentBid.amount + (draftState?.bid_increment || 1)}
                      />
                      <button
                        onClick={() => setBidAmount(bidAmount + (draftState?.bid_increment || 1))}
                        className="btn btn-secondary px-3 py-1"
                        disabled={!canAffordBid}
                      >
                        +
                      </button>
                    </div>
                    <button
                      onClick={handlePlaceBid}
                      className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={!canAffordBid || bidAmount <= currentBid.amount}
                    >
                      {canAffordBid ? `Bid ${bidAmount}` : 'Cannot Afford'}
                    </button>
                    {myTeam?.budget_remaining !== undefined && (
                      <div className="text-xs text-gray-500">
                        Your budget: {myTeam.budget_remaining}
                      </div>
                    )}
                  </div>
                )}
                {isHighestBidder && (
                  <div className="text-sm text-green-600 mt-2">
                    Waiting for other bids...
                  </div>
                )}
                {!hasRosterSpace && !isHighestBidder && (
                  <div className="text-sm text-red-600 mt-2">
                    Your roster is full
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="card sticky top-6">
            <h2 className="font-semibold text-gray-700 mb-4">
              {isAuction ? (isNominatingPhase ? 'Nominate' : 'Your Selection') : 'Your Pick'}
            </h2>
            {selectedPokemon ? (
              <div className="text-center">
                <div className="relative inline-block">
                  <img
                    src={getSpriteUrl(selectedPokemon.id)}
                    alt={selectedPokemon.name}
                    className="w-24 h-24 mx-auto"
                  />
                  {(selectedPokemon.is_legendary || selectedPokemon.is_mythical) && (
                    <span className="absolute top-0 right-0 text-yellow-500">★</span>
                  )}
                </div>
                <div className="text-lg font-bold capitalize mt-1">
                  {selectedPokemon.name}
                </div>
                <div className="flex justify-center gap-1 mt-1 flex-wrap">
                  {selectedPokemon.types.map((type) => (
                    <TypeBadge key={type} type={type} />
                  ))}
                </div>
                {selectedPokemon.stats && (
                  <div className="mt-3 text-left text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-gray-500">HP</span>
                      <span className="font-medium">{selectedPokemon.stats.hp}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Atk</span>
                      <span className="font-medium">{selectedPokemon.stats.attack}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Def</span>
                      <span className="font-medium">{selectedPokemon.stats.defense}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">SpA</span>
                      <span className="font-medium">{selectedPokemon.stats['special-attack']}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">SpD</span>
                      <span className="font-medium">{selectedPokemon.stats['special-defense']}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Spe</span>
                      <span className="font-medium">{selectedPokemon.stats.speed}</span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-gray-200">
                      <span className="text-gray-500 font-medium">BST</span>
                      <span className="font-bold">{getBaseStatTotal(selectedPokemon)}</span>
                    </div>
                  </div>
                )}
                {selectedPokemon.generation && (
                  <div className="text-xs text-gray-500 mt-2">
                    Generation {selectedPokemon.generation}
                  </div>
                )}
                {selectedPokemon.abilities && selectedPokemon.abilities.length > 0 && (
                  <div className="mt-2 text-left text-xs">
                    <span className="text-gray-500">Abilities: </span>
                    <span className="capitalize">
                      {selectedPokemon.abilities.map(a => a.replace('-', ' ')).join(', ')}
                    </span>
                  </div>
                )}
                {/* Auction: Nominate button */}
                {isAuction && isNominatingPhase && (
                  <button
                    onClick={handleNominate}
                    className="btn btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={draftState.status !== 'live' || !isMyTurn || !hasRosterSpace}
                  >
                    {!hasRosterSpace ? 'Roster Full' : isMyTurn ? 'Nominate' : `Waiting for ${currentTeam?.display_name || 'next team'}...`}
                  </button>
                )}
                {/* Regular draft: Confirm Pick button */}
                {!isAuction && (
                  <button
                    onClick={handleMakePick}
                    className="btn btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={draftState.status !== 'live' || !isMyTurn}
                  >
                    {isMyTurn ? 'Confirm Pick' : "Waiting for your turn..."}
                  </button>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center">
                {isAuction && isBiddingPhase
                  ? 'Auction in progress above'
                  : 'Select a Pokemon'}
              </p>
            )}
          </div>

          {/* Recent Picks */}
          <div className="card mt-4">
            <h2 className="font-semibold text-gray-700 mb-4">Recent Picks</h2>
            <div className="space-y-1">
              {draftState.picks.slice(-5).reverse().map((pick) => (
                <div key={pick.pick_number} className="flex items-center gap-2 text-sm">
                  <img
                    src={getSpriteUrl(pick.pokemon_id)}
                    alt={pick.pokemon_name}
                    className="w-8 h-8"
                  />
                  <div>
                    <span className="text-gray-500">#{pick.pick_number + 1}</span>{' '}
                    <span className="font-medium">{pick.team_name}</span>
                    <div className="capitalize text-xs text-gray-600">{pick.pokemon_name}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        </div>

        {/* Mobile: Pokemon Selection */}
        <div className="lg:hidden">
          <div className="card">
            {/* Mobile search and filters */}
            <div className="flex flex-col gap-2 mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Pokémon..."
                className="input w-full"
              />
              <div className="flex gap-2">
                <select
                  value={typeFilter || ''}
                  onChange={(e) => setTypeFilter(e.target.value || null)}
                  className="input flex-1 text-sm"
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
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'} text-sm px-3`}
                >
                  {showFilters ? 'Less' : 'More'}
                </button>
              </div>
            </div>

            {/* Mobile advanced filters */}
            {showFilters && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3 space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={generationFilter ?? ''}
                    onChange={(e) => setGenerationFilter(e.target.value ? Number(e.target.value) : null)}
                    className="input text-sm"
                  >
                    <option value="">All Gens</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((g) => (
                      <option key={g} value={g}>Gen {g}</option>
                    ))}
                  </select>
                  <select
                    value={legendaryFilter}
                    onChange={(e) => setLegendaryFilter(e.target.value as 'all' | 'legendary' | 'mythical' | 'regular')}
                    className="input text-sm"
                  >
                    <option value="all">All</option>
                    <option value="legendary">Legendary</option>
                    <option value="mythical">Mythical</option>
                    <option value="regular">Regular</option>
                  </select>
                </div>
                <div className="flex gap-2 items-center">
                  <span className="text-xs text-gray-500 whitespace-nowrap">BST:</span>
                  <input
                    type="number"
                    value={bstMin ?? ''}
                    onChange={(e) => setBstMin(e.target.value ? Number(e.target.value) : null)}
                    placeholder="Min"
                    className="input flex-1 text-sm"
                  />
                  <span className="text-gray-400">-</span>
                  <input
                    type="number"
                    value={bstMax ?? ''}
                    onChange={(e) => setBstMax(e.target.value ? Number(e.target.value) : null)}
                    placeholder="Max"
                    className="input flex-1 text-sm"
                  />
                </div>
                <button
                  onClick={clearFilters}
                  className="btn btn-ghost text-sm w-full"
                >
                  Clear Filters
                </button>
                <div className="text-xs text-gray-500 text-center">
                  {filteredPokemon.length} Pokémon shown
                </div>
              </div>
            )}

            {/* Mobile Pokemon grid - 3 columns for better touch targets */}
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-1 max-h-[60vh] overflow-y-auto">
              {filteredPokemon.map((pokemon) => {
                const bst = getBaseStatTotal(pokemon)
                return (
                  <div
                    key={pokemon.id}
                    onClick={() => setSelectedPokemon(pokemon)}
                    className={`pokemon-card p-1.5 text-center relative ${
                      selectedPokemon?.id === pokemon.id ? 'border-pokemon-blue bg-blue-50 ring-2 ring-pokemon-blue' : ''
                    }`}
                  >
                    {(pokemon.is_legendary || pokemon.is_mythical) && (
                      <span className="absolute top-0.5 right-0.5 text-yellow-500 text-[10px]">★</span>
                    )}
                    <img
                      src={getSpriteUrl(pokemon.id)}
                      alt={pokemon.name}
                      className="w-14 h-14 sm:w-16 sm:h-16 mx-auto"
                    />
                    <div className="text-xs font-medium capitalize truncate">{pokemon.name}</div>
                    <div className="flex justify-center gap-0.5 mt-0.5 flex-wrap">
                      {pokemon.types.map((type) => (
                        <span
                          key={type}
                          className="px-1 py-0.5 rounded text-white text-[8px] font-bold uppercase"
                          style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                        >
                          {type.slice(0, 3)}
                        </span>
                      ))}
                    </div>
                    {bst && (
                      <div className="text-[9px] text-gray-500 mt-0.5">
                        {bst}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Mobile Recent Picks */}
          <div className="card mt-4">
            <h2 className="font-semibold text-gray-700 mb-2 text-sm">Recent Picks</h2>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {draftState.picks.slice(-6).reverse().map((pick) => (
                <div key={pick.pick_number} className="flex-shrink-0 text-center">
                  <img
                    src={getSpriteUrl(pick.pokemon_id)}
                    alt={pick.pokemon_name}
                    className="w-10 h-10 mx-auto"
                  />
                  <div className="text-[10px] text-gray-600 truncate max-w-[60px]">{pick.team_name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
