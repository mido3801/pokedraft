import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { teamService } from '../services/team'
import { matchService, ScheduleFormat } from '../services/match'
import { tradeService } from '../services/trade'
import { Season, Match, Trade } from '../types'
import { api } from '../services/api'
import { useSprite } from '../context/SpriteContext'

// Need to add a season service endpoint
const getSeason = async (seasonId: string): Promise<Season & { league_name?: string; league_id?: string; draft_id?: string }> => {
  return api.get(`/seasons/${seasonId}`)
}

export default function SeasonDetail() {
  const { seasonId } = useParams<{ seasonId: string }>()
  const queryClient = useQueryClient()
  const { getSpriteUrl } = useSprite()
  const [activeTab, setActiveTab] = useState<'standings' | 'schedule' | 'teams' | 'trades'>('standings')
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [scheduleFormat, setScheduleFormat] = useState<ScheduleFormat>('round_robin')
  const [showResultModal, setShowResultModal] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null)
  const [resultForm, setResultForm] = useState<{ winner_id: string; is_tie: boolean; replay_url: string; notes: string }>({
    winner_id: '',
    is_tie: false,
    replay_url: '',
    notes: '',
  })

  const { data: season, isLoading: seasonLoading } = useQuery({
    queryKey: ['season', seasonId],
    queryFn: () => getSeason(seasonId!),
    enabled: !!seasonId,
  })

  const { data: teams } = useQuery({
    queryKey: ['season-teams', seasonId],
    queryFn: () => teamService.getTeams({ season_id: seasonId }),
    enabled: !!seasonId,
  })

  const { data: standings } = useQuery({
    queryKey: ['season-standings', seasonId],
    queryFn: () => matchService.getStandings(seasonId!),
    enabled: !!seasonId && (season?.status === 'active' || season?.status === 'completed'),
  })

  const { data: schedule } = useQuery({
    queryKey: ['season-schedule', seasonId],
    queryFn: () => matchService.getSchedule(seasonId!),
    enabled: !!seasonId,
  })

  const { data: trades } = useQuery({
    queryKey: ['season-trades', seasonId],
    queryFn: () => tradeService.getTrades(seasonId!),
    enabled: !!seasonId,
  })

  const generateScheduleMutation = useMutation({
    mutationFn: () => matchService.generateSchedule(seasonId!, { format: scheduleFormat }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['season-schedule', seasonId] })
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
      queryClient.invalidateQueries({ queryKey: ['season-schedule', seasonId] })
      queryClient.invalidateQueries({ queryKey: ['season-standings', seasonId] })
      setShowResultModal(false)
      setSelectedMatch(null)
    },
  })

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

  const getTradeStatusBadge = (status: Trade['status']) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
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
                  <option value="swiss">Swiss (match similar records)</option>
                  <option value="single_elimination">Single Elimination Bracket</option>
                  <option value="double_elimination">Double Elimination Bracket</option>
                </select>
              </div>

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
          {['standings', 'schedule', 'teams', 'trades'].map((tab) => (
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
            {season.status === 'active' && schedule && schedule.length === 0 && (
              <button onClick={() => setShowScheduleModal(true)} className="btn btn-secondary text-sm">
                Generate Schedule
              </button>
            )}
          </div>
          {schedule && schedule.length > 0 ? (
            <div className="space-y-4">
              {/* Group matches by week */}
              {Array.from(new Set(schedule.map((m) => m.week))).map((week) => (
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
                        <div className="flex gap-1">
                          {pokemon.types.map((type) => (
                            <span key={type} className={`type-badge text-xs bg-type-${type}`}>
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No Pokemon yet</p>
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
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Trades</h2>
          {trades && trades.length > 0 ? (
            <div className="space-y-4">
              {trades.map((trade) => (
                <div key={trade.id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-sm text-gray-500">
                      {new Date(trade.created_at).toLocaleDateString()}
                    </div>
                    {getTradeStatusBadge(trade.status)}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <p className="font-medium">{trade.proposer_team_name}</p>
                      <p className="text-sm text-gray-500">
                        Sends: {trade.proposer_pokemon.length} Pokemon
                      </p>
                    </div>
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                    <div className="flex-1 text-right">
                      <p className="font-medium">{trade.recipient_team_name}</p>
                      <p className="text-sm text-gray-500">
                        Sends: {trade.recipient_pokemon.length} Pokemon
                      </p>
                    </div>
                  </div>
                  {trade.message && (
                    <p className="text-sm text-gray-600 mt-2 italic">"{trade.message}"</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No trades yet this season.</p>
          )}
        </div>
      )}
    </div>
  )
}
