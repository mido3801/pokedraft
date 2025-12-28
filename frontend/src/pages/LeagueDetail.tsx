import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { leagueService } from '../services/league'
import { queryKeys } from '../services/queryKeys'
import { useAuth } from '../context/AuthContext'
import { Season } from '../types'

export default function LeagueDetail() {
  const { leagueId } = useParams<{ leagueId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showSeasonModal, setShowSeasonModal] = useState(false)
  const [keepTeams, setKeepTeams] = useState(false)

  const { data: league, isLoading: leagueLoading, error: leagueError } = useQuery({
    queryKey: queryKeys.league(leagueId!),
    queryFn: () => leagueService.getLeague(leagueId!),
    enabled: !!leagueId,
  })

  const { data: seasons, isLoading: seasonsLoading } = useQuery({
    queryKey: queryKeys.leagueSeasons(leagueId!),
    queryFn: () => leagueService.getSeasons(leagueId!),
    enabled: !!leagueId,
  })

  const createSeasonMutation = useMutation({
    mutationFn: () => leagueService.createSeason(leagueId!, { keep_teams: keepTeams }),
    onSuccess: (newSeason) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leagueSeasons(leagueId!) })
      setShowSeasonModal(false)
      navigate(`/seasons/${newSeason.id}`)
    },
  })

  const regenerateInviteMutation = useMutation({
    mutationFn: () => leagueService.regenerateInvite(leagueId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.league(leagueId!) })
    },
  })

  const leaveLeagueMutation = useMutation({
    mutationFn: () => leagueService.leaveLeague(leagueId!),
    onSuccess: () => {
      navigate('/leagues')
    },
  })

  const isOwner = user?.id === league?.owner_id

  const copyInviteCode = () => {
    if (league) {
      navigator.clipboard.writeText(league.invite_code)
    }
  }

  const copyInviteLink = () => {
    if (league) {
      navigator.clipboard.writeText(`${window.location.origin}/leagues/${leagueId}/join?code=${league.invite_code}`)
    }
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

  if (leagueLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-8"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (leagueError || !league) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-700">Failed to load league. It may not exist or you don't have access.</p>
          <Link to="/leagues" className="btn btn-secondary mt-4">
            Back to Leagues
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Invite Players</h2>
              <button onClick={() => setShowInviteModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Invite Code</label>
                <div className="flex gap-2">
                  <div className="input flex-1 bg-gray-50 font-mono text-center text-lg">
                    {league.invite_code}
                  </div>
                  <button onClick={copyInviteCode} className="btn btn-secondary">
                    Copy
                  </button>
                </div>
              </div>

              <div>
                <label className="label">Invite Link</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={`${window.location.origin}/leagues/${leagueId}/join?code=${league.invite_code}`}
                    className="input flex-1 bg-gray-50 text-sm"
                  />
                  <button onClick={copyInviteLink} className="btn btn-secondary">
                    Copy
                  </button>
                </div>
              </div>

              {isOwner && (
                <button
                  onClick={() => regenerateInviteMutation.mutate()}
                  className="text-sm text-pokemon-red hover:underline"
                  disabled={regenerateInviteMutation.isPending}
                >
                  {regenerateInviteMutation.isPending ? 'Regenerating...' : 'Generate New Code'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* New Season Modal */}
      {showSeasonModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Start New Season</h2>
              <button onClick={() => setShowSeasonModal(false)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-gray-600 mb-4">
              This will create Season {(seasons?.length || 0) + 1} for {league.name}.
            </p>

            <div className="flex items-center mb-6">
              <input
                type="checkbox"
                id="keepTeams"
                checked={keepTeams}
                onChange={(e) => setKeepTeams(e.target.checked)}
                className="h-4 w-4 text-pokemon-red rounded border-gray-300"
              />
              <label htmlFor="keepTeams" className="ml-2 text-sm text-gray-700">
                Keep teams from previous season (keeper league)
              </label>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => createSeasonMutation.mutate()}
                className="btn btn-primary flex-1"
                disabled={createSeasonMutation.isPending}
              >
                {createSeasonMutation.isPending ? 'Creating...' : 'Create Season'}
              </button>
              <button
                onClick={() => setShowSeasonModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{league.name}</h1>
          {league.description && (
            <p className="text-gray-600">{league.description}</p>
          )}
          <p className="text-sm text-gray-500 mt-2">
            {league.member_count || 0} members · {seasons?.length || 0} seasons
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowInviteModal(true)} className="btn btn-secondary">
            Invite Players
          </button>
          {isOwner && (
            <button onClick={() => setShowSeasonModal(true)} className="btn btn-primary">
              New Season
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Seasons List */}
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Seasons</h2>
            {seasonsLoading ? (
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-gray-100 rounded"></div>
                ))}
              </div>
            ) : seasons && seasons.length > 0 ? (
              <div className="space-y-3">
                {seasons.map((season) => (
                  <Link
                    key={season.id}
                    to={`/seasons/${season.id}`}
                    className="block p-4 border rounded-lg hover:border-pokemon-blue hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium">Season {season.season_number}</span>
                        <span className="text-gray-500 text-sm ml-2">
                          {season.team_count || 0} teams
                        </span>
                      </div>
                      {getStatusBadge(season.status)}
                    </div>
                    {season.started_at && (
                      <p className="text-sm text-gray-500 mt-1">
                        Started {new Date(season.started_at).toLocaleDateString()}
                      </p>
                    )}
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No seasons yet.</p>
                {isOwner && (
                  <button
                    onClick={() => setShowSeasonModal(true)}
                    className="btn btn-primary mt-4"
                  >
                    Start First Season
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* League Settings */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Settings</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Draft Format</dt>
                <dd className="font-medium capitalize">{league.settings.draft_format}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Roster Size</dt>
                <dd className="font-medium">{league.settings.roster_size} Pokémon</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Timer</dt>
                <dd className="font-medium">{league.settings.timer_seconds}s per pick</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Budget Mode</dt>
                <dd className="font-medium">{league.settings.budget_enabled ? 'Enabled' : 'Disabled'}</dd>
              </div>
              {league.settings.budget_enabled && league.settings.budget_per_team && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Budget Per Team</dt>
                  <dd className="font-medium">{league.settings.budget_per_team} pts</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-gray-500">Trade Approval</dt>
                <dd className="font-medium">{league.settings.trade_approval_required ? 'Required' : 'Auto-approved'}</dd>
              </div>
            </dl>
          </div>

          {/* Actions */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Actions</h2>
            <div className="space-y-2">
              {isOwner && (
                <Link to={`/leagues/${leagueId}/settings`} className="btn btn-secondary w-full block text-center">
                  Edit Settings
                </Link>
              )}
              {!isOwner && (
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to leave this league?')) {
                      leaveLeagueMutation.mutate()
                    }
                  }}
                  className="btn btn-secondary w-full text-red-600 hover:bg-red-50"
                  disabled={leaveLeagueMutation.isPending}
                >
                  {leaveLeagueMutation.isPending ? 'Leaving...' : 'Leave League'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
