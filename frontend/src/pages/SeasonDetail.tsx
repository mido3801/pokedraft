import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import { teamService } from '../services/team'
import { matchService, ScheduleFormat } from '../services/match'
import { tradeService } from '../services/trade'
import { waiverService } from '../services/waiver'
import { draftService, CreateDraftParams } from '../services/draft'
import { queryKeys } from '../services/queryKeys'
import { Season, Match, SeedingMode, DraftFormat, PokemonFilters, LeagueSettings, DEFAULT_POKEMON_FILTERS, WaiverApprovalType } from '../types'
import { api } from '../services/api'
import { useSprite } from '../context/SpriteContext'
import { useAuth } from '../context/AuthContext'
import { storage } from '../utils/storage'
import BracketDisplay from '../components/BracketDisplay'
import PokemonFiltersComponent from '../components/PokemonFilters'
import TradeCard from '../components/TradeCard'
import TradeProposalModal from '../components/TradeProposalModal'
import WaiverClaimCard from '../components/WaiverClaimCard'
import WaiverClaimModal from '../components/WaiverClaimModal'
import { useTradeWebSocket } from '../hooks/useTradeWebSocket'
import { useWaiverWebSocket } from '../hooks/useWaiverWebSocket'

// Need to add a season service endpoint
const getSeason = async (seasonId: string): Promise<Season & {
  league_name?: string
  league_id?: string
  draft_id?: string
  is_owner?: boolean
  league_settings?: LeagueSettings
}> => {
  return api.get(`/seasons/${seasonId}`)
}

export default function SeasonDetail() {
  const { seasonId } = useParams<{ seasonId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { getSpriteUrl } = useSprite()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'standings' | 'schedule' | 'teams' | 'trades' | 'waivers'>('standings')
  const [showTradeModal, setShowTradeModal] = useState(false)
  const [showWaiverModal, setShowWaiverModal] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [scheduleFormat, setScheduleFormat] = useState<ScheduleFormat>('round_robin')
  const [seedingMode, setSeedingMode] = useState<SeedingMode>('standings')
  const [includeBracketReset, setIncludeBracketReset] = useState(true)
  const [showResultModal, setShowResultModal] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null)
  const [resultForm, setResultForm] = useState<{ winner_id: string; is_tie: boolean; replay_url: string; notes: string }>({
    winner_id: '',
    is_tie: false,
    replay_url: '',
    notes: '',
  })
  // Draft creation state
  const [showDraftModal, setShowDraftModal] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [draftForm, setDraftForm] = useState<{
    format: DraftFormat
    rosterSize: number
    timerSeconds: number
    budgetEnabled: boolean
    budgetPerTeam: number
    nominationTimerSeconds: number
    minBid: number
    bidIncrement: number
  }>({
    format: 'snake',
    rosterSize: 6,
    timerSeconds: 90,
    budgetEnabled: false,
    budgetPerTeam: 100,
    nominationTimerSeconds: 30,
    minBid: 1,
    bidIncrement: 1,
  })
  const [pokemonFilters, setPokemonFilters] = useState<PokemonFilters>(DEFAULT_POKEMON_FILTERS)

  const { data: season, isLoading: seasonLoading } = useQuery({
    queryKey: queryKeys.season(seasonId!),
    queryFn: () => getSeason(seasonId!),
    enabled: !!seasonId,
  })

  const { data: teams } = useQuery({
    queryKey: queryKeys.seasonTeams(seasonId!),
    queryFn: () => teamService.getTeams({ season_id: seasonId }),
    enabled: !!seasonId,
  })

  const { data: standings } = useQuery({
    queryKey: queryKeys.seasonStandings(seasonId!),
    queryFn: () => matchService.getStandings(seasonId!),
    enabled: !!seasonId && (season?.status === 'active' || season?.status === 'completed'),
  })

  const { data: schedule } = useQuery({
    queryKey: queryKeys.seasonSchedule(seasonId!),
    queryFn: () => matchService.getSchedule(seasonId!),
    enabled: !!seasonId,
  })

  // Check if schedule is a bracket format
  const isBracketFormat = schedule && schedule.length > 0 &&
    (schedule[0].schedule_format === 'single_elimination' || schedule[0].schedule_format === 'double_elimination')

  const { data: bracket } = useQuery({
    queryKey: queryKeys.seasonBracket(seasonId!),
    queryFn: () => matchService.getBracket(seasonId!),
    enabled: !!seasonId && isBracketFormat,
  })

  const { data: trades } = useQuery({
    queryKey: queryKeys.seasonTrades(seasonId!),
    queryFn: () => tradeService.getTrades(seasonId!),
    enabled: !!seasonId,
  })

  const { data: waiverClaims } = useQuery({
    queryKey: queryKeys.seasonWaiverClaims(seasonId!),
    queryFn: () => waiverService.getClaims(seasonId!),
    enabled: !!seasonId && (season?.status === 'active' || season?.status === 'completed'),
  })

  // Fetch draft data to get roster size limit
  const { data: draft } = useQuery({
    queryKey: queryKeys.draft(season?.draft_id || ''),
    queryFn: () => draftService.getDraft(season!.draft_id!),
    enabled: !!season?.draft_id,
  })

  // Find current user's team in this season
  const myTeam = useMemo(() => {
    if (!user || !teams) return null
    return teams.find((t) => t.user_id === user.id) || null
  }, [user, teams])

  // Calculate if a drop is required for waiver claims
  const requireDrop = useMemo(() => {
    if (!myTeam || !draft) return false
    const currentRosterSize = myTeam.pokemon?.length || 0
    return currentRosterSize >= draft.roster_size
  }, [myTeam, draft])

  // Trade mutations
  const acceptTradeMutation = useMutation({
    mutationFn: (tradeId: string) => tradeService.acceptTrade(tradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTeams(seasonId!) })
    },
  })

  const rejectTradeMutation = useMutation({
    mutationFn: (tradeId: string) => tradeService.rejectTrade(tradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
  })

  const cancelTradeMutation = useMutation({
    mutationFn: (tradeId: string) => tradeService.cancelTrade(tradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
  })

  const approveTradeMutation = useMutation({
    mutationFn: (tradeId: string) => tradeService.approveTrade(tradeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTeams(seasonId!) })
    },
  })

  // Waiver mutations
  const cancelWaiverMutation = useMutation({
    mutationFn: (claimId: string) => waiverService.cancelClaim(claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
  })

  const approveWaiverMutation = useMutation({
    mutationFn: (claimId: string) => waiverService.adminAction(claimId, { approved: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTeams(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonFreeAgents(seasonId!) })
    },
  })

  const rejectWaiverMutation = useMutation({
    mutationFn: (claimId: string) => waiverService.adminAction(claimId, { approved: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
  })

  const voteForWaiverMutation = useMutation({
    mutationFn: (claimId: string) => waiverService.vote(claimId, { vote: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
  })

  const voteAgainstWaiverMutation = useMutation({
    mutationFn: (claimId: string) => waiverService.vote(claimId, { vote: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
  })

  // Real-time trade updates via WebSocket
  useTradeWebSocket({
    seasonId: seasonId!,
    enabled: !!seasonId && season?.status === 'active',
    onTradeProposed: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
    onTradeAccepted: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
    onTradeRejected: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
    onTradeCancelled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
    },
    onTradeApproved: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTeams(seasonId!) })
    },
  })

  // Real-time waiver updates via WebSocket
  useWaiverWebSocket({
    seasonId: seasonId!,
    enabled: !!seasonId && season?.status === 'active',
    onClaimCreated: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
    onClaimApproved: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTeams(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonFreeAgents(seasonId!) })
    },
    onClaimRejected: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
    onClaimCancelled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
    onVoteCast: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonWaiverClaims(seasonId!) })
    },
  })

  const generateScheduleMutation = useMutation({
    mutationFn: () => matchService.generateSchedule(seasonId!, {
      format: scheduleFormat,
      use_standings_seeding: seedingMode === 'standings',
      include_bracket_reset: includeBracketReset,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonSchedule(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonBracket(seasonId!) })
      setShowScheduleModal(false)
    },
  })

  const recordResultMutation = useMutation({
    mutationFn: ({ matchId, params }: { matchId: string; params: typeof resultForm }) =>
      matchService.recordResult(matchId, {
        winner_id: params.is_tie ? undefined : params.winner_id || undefined,
        is_tie: params.is_tie,
        replay_url: params.replay_url || undefined,
        notes: params.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonSchedule(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonStandings(seasonId!) })
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonBracket(seasonId!) })
      setShowResultModal(false)
      setSelectedMatch(null)
    },
  })

  const createDraftMutation = useMutation({
    mutationFn: (params: CreateDraftParams) => draftService.createDraft(seasonId!, params),
    onSuccess: (data: { id: string; team_id?: string }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.season(seasonId!) })
      setShowDraftModal(false)
      // Store team_id in localStorage for the draft room to identify us
      if (data.team_id) {
        const draftId = String(data.id)
        storage.setDraftSession(draftId, {
          session: '', // No session token for league drafts
          team: data.team_id,
          rejoin: '', // No rejoin code for league drafts
        })
      }
      // Navigate to the draft room
      navigate(`/d/${data.id}`)
    },
  })

  const handleCreateDraft = () => {
    const isAuction = draftForm.format === 'auction'
    const params: CreateDraftParams = {
      format: draftForm.format,
      roster_size: draftForm.rosterSize,
      timer_seconds: draftForm.timerSeconds,
      budget_enabled: isAuction || draftForm.budgetEnabled,
      budget_per_team: (isAuction || draftForm.budgetEnabled) ? draftForm.budgetPerTeam : undefined,
      pokemon_filters: pokemonFilters,
      nomination_timer_seconds: isAuction ? draftForm.nominationTimerSeconds : undefined,
      min_bid: isAuction ? draftForm.minBid : undefined,
      bid_increment: isAuction ? draftForm.bidIncrement : undefined,
    }
    createDraftMutation.mutate(params)
  }

  // Initialize draft form with league settings when modal opens
  const openDraftModal = () => {
    if (season?.league_settings) {
      setDraftForm(prev => ({
        ...prev,
        format: season.league_settings?.draft_format || 'snake',
        rosterSize: season.league_settings?.roster_size || 6,
        timerSeconds: season.league_settings?.timer_seconds || 90,
        budgetEnabled: season.league_settings?.budget_enabled || false,
        budgetPerTeam: season.league_settings?.budget_per_team || 100,
      }))
    }
    setShowDraftModal(true)
  }

  const getStatusBadge = (status: Season['status']) => {
    const styles = {
      pre_draft: 'bg-yellow-100 text-yellow-800',
      drafting: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
    }
    const labels = {
      pre_draft: 'Pre-Draft',
      drafting: 'Drafting',
      active: 'Active',
      completed: 'Completed',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  const openResultModal = (match: Match) => {
    setSelectedMatch(match)
    setResultForm({
      winner_id: match.winner_id || '',
      is_tie: match.is_tie || false,
      replay_url: match.replay_url || '',
      notes: match.notes || '',
    })
    setShowResultModal(true)
  }

  if (seasonLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-8"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!season) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-700">Failed to load season.</p>
          <Link to="/leagues" className="btn btn-secondary mt-4">
            Back to Leagues
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Schedule Generation Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Generate Schedule</h2>
              <button onClick={() => setShowScheduleModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Schedule Format</label>
                <select
                  value={scheduleFormat}
                  onChange={(e) => setScheduleFormat(e.target.value as ScheduleFormat)}
                  className="input"
                >
                  <option value="round_robin">Round Robin (everyone plays once)</option>
                  <option value="double_round_robin">Double Round Robin (everyone plays twice)</option>
                  <option value="single_elimination">Single Elimination Bracket</option>
                  <option value="double_elimination">Double Elimination Bracket</option>
                </select>
              </div>

              {/* Seeding options for bracket formats */}
              {(scheduleFormat === 'single_elimination' || scheduleFormat === 'double_elimination') && (
                <>
                  <div>
                    <label className="label">Seeding</label>
                    <select
                      value={seedingMode}
                      onChange={(e) => setSeedingMode(e.target.value as SeedingMode)}
                      className="input"
                    >
                      <option value="standings">Auto-seed from Standings</option>
                      <option value="random">Random Seeding</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {seedingMode === 'standings'
                        ? 'Top ranked teams will be seeded higher (1 vs 8, 4 vs 5, etc.)'
                        : 'Teams will be randomly assigned bracket positions'}
                    </p>
                  </div>

                  {scheduleFormat === 'double_elimination' && (
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="bracketReset"
                        checked={includeBracketReset}
                        onChange={(e) => setIncludeBracketReset(e.target.checked)}
                        className="h-4 w-4 text-pokemon-red rounded border-gray-300"
                      />
                      <label htmlFor="bracketReset" className="ml-2 text-sm text-gray-700">
                        Include bracket reset in Grand Finals
                      </label>
                    </div>
                  )}
                </>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => generateScheduleMutation.mutate()}
                  className="btn btn-primary flex-1"
                  disabled={generateScheduleMutation.isPending}
                >
                  {generateScheduleMutation.isPending ? 'Generating...' : 'Generate'}
                </button>
                <button onClick={() => setShowScheduleModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Record Result Modal */}
      {showResultModal && selectedMatch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Record Result</h2>
              <button onClick={() => setShowResultModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-gray-600 mb-4">
              {selectedMatch.team_a_name} vs {selectedMatch.team_b_name}
            </p>

            <div className="space-y-4">
              {/* Only show tie option for non-bracket matches */}
              {selectedMatch.schedule_format !== 'single_elimination' && selectedMatch.schedule_format !== 'double_elimination' && (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isTie"
                    checked={resultForm.is_tie}
                    onChange={(e) => setResultForm({ ...resultForm, is_tie: e.target.checked, winner_id: '' })}
                    className="h-4 w-4 text-pokemon-red rounded border-gray-300"
                  />
                  <label htmlFor="isTie" className="ml-2 text-sm text-gray-700">
                    Match ended in a tie
                  </label>
                </div>
              )}

              {!resultForm.is_tie && (
                <div>
                  <label className="label">Winner</label>
                  <select
                    value={resultForm.winner_id}
                    onChange={(e) => setResultForm({ ...resultForm, winner_id: e.target.value })}
                    className="input"
                  >
                    <option value="">Select winner...</option>
                    <option value={selectedMatch.team_a_id}>{selectedMatch.team_a_name}</option>
                    <option value={selectedMatch.team_b_id}>{selectedMatch.team_b_name}</option>
                  </select>
                </div>
              )}

              <div>
                <label className="label">Replay URL (optional)</label>
                <input
                  type="url"
                  value={resultForm.replay_url}
                  onChange={(e) => setResultForm({ ...resultForm, replay_url: e.target.value })}
                  className="input"
                  placeholder="https://replay.pokemonshowdown.com/..."
                />
              </div>

              <div>
                <label className="label">Notes (optional)</label>
                <textarea
                  value={resultForm.notes}
                  onChange={(e) => setResultForm({ ...resultForm, notes: e.target.value })}
                  className="input"
                  rows={2}
                  placeholder="Any additional notes..."
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => recordResultMutation.mutate({ matchId: selectedMatch.id, params: resultForm })}
                  className="btn btn-primary flex-1"
                  disabled={recordResultMutation.isPending || (!resultForm.is_tie && !resultForm.winner_id)}
                >
                  {recordResultMutation.isPending ? 'Saving...' : 'Save Result'}
                </button>
                <button onClick={() => setShowResultModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Draft Creation Modal */}
      {showDraftModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Start Draft</h2>
              <button onClick={() => setShowDraftModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {createDraftMutation.isError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {createDraftMutation.error instanceof Error ? createDraftMutation.error.message : 'Failed to create draft'}
              </div>
            )}

            <div className="space-y-4">
              {/* Draft Format */}
              <div>
                <label className="label">Draft Format</label>
                <select
                  value={draftForm.format}
                  onChange={(e) => setDraftForm({ ...draftForm, format: e.target.value as DraftFormat })}
                  className="input"
                >
                  <option value="snake">Snake Draft</option>
                  <option value="linear">Linear Draft</option>
                  <option value="auction">Auction Draft</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {draftForm.format === 'snake' && 'Pick order reverses each round (1→8, 8→1, 1→8...)'}
                  {draftForm.format === 'linear' && 'Same pick order every round (1→8, 1→8...)'}
                  {draftForm.format === 'auction' && 'Pokémon are nominated and teams bid. Highest bidder wins.'}
                </p>
              </div>

              {/* Auction-specific settings */}
              {draftForm.format === 'auction' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
                  <h3 className="font-medium text-blue-800">Auction Settings</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <label className="label">Starting Budget</label>
                      <input
                        type="number"
                        value={draftForm.budgetPerTeam}
                        onChange={(e) => setDraftForm({ ...draftForm, budgetPerTeam: parseInt(e.target.value) })}
                        className="input"
                        min={1}
                      />
                    </div>
                    <div>
                      <label className="label">Minimum Bid</label>
                      <input
                        type="number"
                        value={draftForm.minBid}
                        onChange={(e) => setDraftForm({ ...draftForm, minBid: parseInt(e.target.value) })}
                        className="input"
                        min={1}
                      />
                    </div>
                    <div>
                      <label className="label">Bid Increment</label>
                      <input
                        type="number"
                        value={draftForm.bidIncrement}
                        onChange={(e) => setDraftForm({ ...draftForm, bidIncrement: parseInt(e.target.value) })}
                        className="input"
                        min={1}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="label">Nomination Timer (seconds)</label>
                      <input
                        type="number"
                        value={draftForm.nominationTimerSeconds}
                        onChange={(e) => setDraftForm({ ...draftForm, nominationTimerSeconds: parseInt(e.target.value) })}
                        className="input"
                        min={10}
                        max={300}
                      />
                    </div>
                    <div>
                      <label className="label">Bid Timer (seconds)</label>
                      <input
                        type="number"
                        value={draftForm.timerSeconds}
                        onChange={(e) => setDraftForm({ ...draftForm, timerSeconds: parseInt(e.target.value) })}
                        className="input"
                        min={5}
                        max={120}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Roster Size */}
              <div>
                <label className="label">Roster Size</label>
                <input
                  type="number"
                  value={draftForm.rosterSize}
                  onChange={(e) => setDraftForm({ ...draftForm, rosterSize: parseInt(e.target.value) })}
                  className="input"
                  min={1}
                  max={20}
                />
              </div>

              {/* Timer and budget for non-auction formats */}
              {draftForm.format !== 'auction' && (
                <>
                  <div>
                    <label className="label">Timer (seconds per pick)</label>
                    <input
                      type="number"
                      value={draftForm.timerSeconds}
                      onChange={(e) => setDraftForm({ ...draftForm, timerSeconds: parseInt(e.target.value) })}
                      className="input"
                      min={30}
                      max={600}
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="budgetEnabled"
                      checked={draftForm.budgetEnabled}
                      onChange={(e) => setDraftForm({ ...draftForm, budgetEnabled: e.target.checked })}
                      className="h-4 w-4 text-pokemon-red rounded border-gray-300"
                    />
                    <label htmlFor="budgetEnabled" className="ml-2 text-sm text-gray-700">
                      Enable point cap
                    </label>
                  </div>

                  {draftForm.budgetEnabled && (
                    <div>
                      <label className="label">Point Budget Per Team</label>
                      <input
                        type="number"
                        value={draftForm.budgetPerTeam}
                        onChange={(e) => setDraftForm({ ...draftForm, budgetPerTeam: parseInt(e.target.value) })}
                        className="input"
                        min={1}
                      />
                    </div>
                  )}
                </>
              )}

              {/* Pokemon Filters */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {showFilters ? 'Hide' : 'Show'} Pokémon Pool Filters
                </button>

                {showFilters && (
                  <div className="mt-4">
                    <PokemonFiltersComponent
                      filters={pokemonFilters}
                      onChange={setPokemonFilters}
                    />
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4">
                <button
                  onClick={handleCreateDraft}
                  className="btn btn-primary flex-1"
                  disabled={createDraftMutation.isPending}
                >
                  {createDraftMutation.isPending ? 'Creating Draft...' : 'Create & Enter Draft'}
                </button>
                <button onClick={() => setShowDraftModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          {season.league_id && (
            <Link to={`/leagues/${season.league_id}`} className="text-pokemon-blue hover:underline text-sm mb-2 inline-block">
              ← Back to {season.league_name || 'League'}
            </Link>
          )}
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-gray-900">Season {season.season_number}</h1>
            {getStatusBadge(season.status)}
          </div>
          <p className="text-sm text-gray-500">
            {teams?.length || 0} teams · {schedule?.length || 0} matches
          </p>
        </div>
        <div className="flex gap-2">
          {season.status === 'pre_draft' && !season.draft_id && season.is_owner && (
            <button onClick={openDraftModal} className="btn btn-primary">
              Start Draft
            </button>
          )}
          {season.status === 'pre_draft' && season.draft_id && (
            <Link to={`/d/${season.draft_id}`} className="btn btn-primary">
              Go to Draft
            </Link>
          )}
          {season.status === 'drafting' && season.draft_id && (
            <Link to={`/d/${season.draft_id}`} className="btn btn-primary">
              Join Draft
            </Link>
          )}
          {season.status === 'active' && (!schedule || schedule.length === 0) && (
            <button onClick={() => setShowScheduleModal(true)} className="btn btn-primary">
              Generate Schedule
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['standings', 'schedule', 'teams', 'trades', 'waivers'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as typeof activeTab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-pokemon-blue text-pokemon-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'standings' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Standings</h2>
          {standings && standings.standings.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-gray-500">
                  <th className="pb-2 pr-4">#</th>
                  <th className="pb-2 pr-4">Team</th>
                  <th className="pb-2 pr-4 text-center">W</th>
                  <th className="pb-2 pr-4 text-center">L</th>
                  <th className="pb-2 pr-4 text-center">T</th>
                  <th className="pb-2 text-center">Pts</th>
                </tr>
              </thead>
              <tbody>
                {standings.standings.map((standing, index) => (
                  <tr key={standing.team_id} className="border-b last:border-0">
                    <td className="py-3 pr-4 text-gray-500">{index + 1}</td>
                    <td className="py-3 pr-4 font-medium">{standing.team_name}</td>
                    <td className="py-3 pr-4 text-center">{standing.wins}</td>
                    <td className="py-3 pr-4 text-center">{standing.losses}</td>
                    <td className="py-3 pr-4 text-center">{standing.ties}</td>
                    <td className="py-3 text-center font-medium">{standing.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {season.status === 'pre_draft' || season.status === 'drafting'
                ? 'Standings will appear once the season begins.'
                : 'No standings available yet.'}
            </p>
          )}
        </div>
      )}

      {activeTab === 'schedule' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Schedule</h2>
            {season.status === 'active' && (!schedule || schedule.length === 0) && (
              <button onClick={() => setShowScheduleModal(true)} className="btn btn-secondary text-sm">
                Generate Schedule
              </button>
            )}
          </div>

          {/* Show bracket display for bracket formats */}
          {bracket ? (
            <BracketDisplay bracket={bracket} onRecordResult={openResultModal} />
          ) : schedule && schedule.length > 0 ? (
            <div className="space-y-4">
              {/* Group matches by week for round-robin formats */}
              {Array.from(new Set(schedule.map((m) => m.week))).sort((a, b) => a - b).map((week) => (
                <div key={week}>
                  <h3 className="font-medium text-gray-700 mb-2">Week {week}</h3>
                  <div className="space-y-2">
                    {schedule
                      .filter((m) => m.week === week)
                      .map((match) => (
                        <div
                          key={match.id}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div className="flex items-center space-x-4">
                            <span className={match.winner_id === match.team_a_id ? 'font-bold' : ''}>
                              {match.team_a_name}
                            </span>
                            <span className="text-gray-400">vs</span>
                            <span className={match.winner_id === match.team_b_id ? 'font-bold' : ''}>
                              {match.team_b_name}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {match.winner_id ? (
                              <span className="text-sm text-green-600">
                                {match.winner_name} won
                              </span>
                            ) : match.is_tie ? (
                              <span className="text-sm text-gray-500">Tie</span>
                            ) : (
                              <button
                                onClick={() => openResultModal(match)}
                                className="text-sm text-pokemon-blue hover:underline"
                              >
                                Record Result
                              </button>
                            )}
                            {match.replay_url && (
                              <a
                                href={match.replay_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-pokemon-blue hover:underline"
                              >
                                Replay
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {season.status === 'active'
                ? 'No schedule generated yet. Click "Generate Schedule" to create one.'
                : 'Schedule will be available once the draft is complete.'}
            </p>
          )}
        </div>
      )}

      {activeTab === 'teams' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams && teams.length > 0 ? (
            teams.map((team) => (
              <div key={team.id} className="card">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold">{team.display_name}</h3>
                  <span className="text-sm text-gray-500">
                    {team.wins}-{team.losses}-{team.ties}
                  </span>
                </div>
                {team.pokemon && team.pokemon.length > 0 ? (
                  <div className="space-y-1">
                    {team.pokemon.map((pokemon) => (
                      <div key={pokemon.id} className="flex items-center gap-2 text-sm">
                        <img src={getSpriteUrl(pokemon.pokemon_id)} alt={pokemon.pokemon_name} className="w-6 h-6" />
                        <span className="capitalize">{pokemon.pokemon_name}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No Pokémon yet</p>
                )}
              </div>
            ))
          ) : (
            <div className="col-span-full text-center py-8 text-gray-500">
              <p>No teams in this season yet.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'trades' && (
        <div className="space-y-6">
          {/* Admin Approval Panel */}
          {season?.is_owner && season?.league_settings?.trade_approval_required && (
            (() => {
              const pendingApprovalTrades = trades?.filter(
                (t) => t.status === 'accepted' && t.requires_approval && !t.admin_approved
              ) || []
              if (pendingApprovalTrades.length === 0) return null
              return (
                <div className="card border-yellow-200 bg-yellow-50">
                  <h2 className="text-lg font-semibold mb-4 text-yellow-800">
                    Trades Awaiting Approval ({pendingApprovalTrades.length})
                  </h2>
                  <div className="space-y-4">
                    {pendingApprovalTrades.map((trade) => (
                      <TradeCard
                        key={trade.id}
                        trade={trade}
                        currentUserTeamId={myTeam?.id}
                        isLeagueOwner={season?.is_owner ?? false}
                        onApprove={() => approveTradeMutation.mutate(trade.id)}
                        isLoading={approveTradeMutation.isPending}
                      />
                    ))}
                  </div>
                </div>
              )
            })()
          )}

          {/* Main Trades Card */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Trades</h2>
              {myTeam && season?.status === 'active' && (
                <button
                  onClick={() => setShowTradeModal(true)}
                  className="btn btn-primary"
                >
                  Propose Trade
                </button>
              )}
            </div>

            {trades && trades.length > 0 ? (
              <div className="space-y-4">
                {trades.map((trade) => (
                  <TradeCard
                    key={trade.id}
                    trade={trade}
                    currentUserTeamId={myTeam?.id}
                    isLeagueOwner={season?.is_owner ?? false}
                    onAccept={() => acceptTradeMutation.mutate(trade.id)}
                    onReject={() => rejectTradeMutation.mutate(trade.id)}
                    onCancel={() => cancelTradeMutation.mutate(trade.id)}
                    onApprove={() => approveTradeMutation.mutate(trade.id)}
                    isLoading={
                      acceptTradeMutation.isPending ||
                      rejectTradeMutation.isPending ||
                      cancelTradeMutation.isPending ||
                      approveTradeMutation.isPending
                    }
                  />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No trades yet this season.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'waivers' && (
        <div className="space-y-6">
          {/* Admin Approval Panel for Waivers */}
          {season?.is_owner && season?.league_settings?.waiver_approval_type === 'admin' && (
            (() => {
              const pendingApprovalClaims = waiverClaims?.claims?.filter(
                (c) => c.status === 'pending' && c.requires_approval
              ) || []
              if (pendingApprovalClaims.length === 0) return null
              return (
                <div className="card border-yellow-200 bg-yellow-50">
                  <h2 className="text-lg font-semibold mb-4 text-yellow-800">
                    Waiver Claims Awaiting Approval ({pendingApprovalClaims.length})
                  </h2>
                  <div className="space-y-4">
                    {pendingApprovalClaims.map((claim) => (
                      <WaiverClaimCard
                        key={claim.id}
                        claim={claim}
                        currentUserTeamId={myTeam?.id}
                        isLeagueOwner={season?.is_owner ?? false}
                        approvalType={season?.league_settings?.waiver_approval_type as WaiverApprovalType || 'none'}
                        onApprove={() => approveWaiverMutation.mutate(claim.id)}
                        onReject={() => rejectWaiverMutation.mutate(claim.id)}
                        isLoading={approveWaiverMutation.isPending || rejectWaiverMutation.isPending}
                      />
                    ))}
                  </div>
                </div>
              )
            })()
          )}

          {/* Main Waivers Card */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Free Agent Claims</h2>
              {myTeam && season?.status === 'active' && (
                <button
                  onClick={() => setShowWaiverModal(true)}
                  disabled={!season?.league_settings?.waiver_enabled}
                  className={`btn ${season?.league_settings?.waiver_enabled ? 'btn-primary' : 'btn-secondary opacity-50 cursor-not-allowed'}`}
                  title={!season?.league_settings?.waiver_enabled ? 'Waiver wire is disabled for this league' : undefined}
                >
                  Claim Free Agent
                </button>
              )}
            </div>

            {/* Waivers Disabled Notice */}
            {!season?.league_settings?.waiver_enabled && (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-4">
                Waiver wire is disabled for this league. The league owner can enable it in league settings.
              </div>
            )}

            {/* Weekly Limit Info */}
            {season?.league_settings?.waiver_enabled && season?.league_settings?.waiver_max_per_week && season.league_settings.waiver_max_per_week > 0 && (
              <p className="text-sm text-gray-600 mb-4">
                Weekly limit: {season.league_settings.waiver_max_per_week} claim{season.league_settings.waiver_max_per_week > 1 ? 's' : ''} per team
              </p>
            )}

            {waiverClaims && waiverClaims.claims && waiverClaims.claims.length > 0 ? (
              <div className="space-y-4">
                {waiverClaims.claims.map((claim) => (
                  <WaiverClaimCard
                    key={claim.id}
                    claim={claim}
                    currentUserTeamId={myTeam?.id}
                    isLeagueOwner={season?.is_owner ?? false}
                    approvalType={season?.league_settings?.waiver_approval_type as WaiverApprovalType || 'none'}
                    onCancel={() => cancelWaiverMutation.mutate(claim.id)}
                    onApprove={() => approveWaiverMutation.mutate(claim.id)}
                    onReject={() => rejectWaiverMutation.mutate(claim.id)}
                    onVoteFor={() => voteForWaiverMutation.mutate(claim.id)}
                    onVoteAgainst={() => voteAgainstWaiverMutation.mutate(claim.id)}
                    isLoading={
                      cancelWaiverMutation.isPending ||
                      approveWaiverMutation.isPending ||
                      rejectWaiverMutation.isPending ||
                      voteForWaiverMutation.isPending ||
                      voteAgainstWaiverMutation.isPending
                    }
                  />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No waiver claims yet this season.</p>
            )}
          </div>
        </div>
      )}

      {/* Trade Proposal Modal */}
      {showTradeModal && myTeam && teams && (
        <TradeProposalModal
          isOpen={showTradeModal}
          onClose={() => setShowTradeModal(false)}
          seasonId={seasonId!}
          myTeam={myTeam}
          otherTeams={teams.filter((t) => t.id !== myTeam.id)}
        />
      )}

      {/* Waiver Claim Modal */}
      {showWaiverModal && myTeam && (
        <WaiverClaimModal
          isOpen={showWaiverModal}
          onClose={() => setShowWaiverModal(false)}
          seasonId={seasonId!}
          myTeam={myTeam}
          requireDrop={requireDrop}
        />
      )}
    </div>
  )
}
