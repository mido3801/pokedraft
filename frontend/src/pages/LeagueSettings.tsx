import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { leagueService } from '../services/league'
import { queryKeys } from '../services/queryKeys'
import { useAuth } from '../context/AuthContext'
import { DraftFormat, WaiverApprovalType, WaiverProcessingType } from '../types'

export default function LeagueSettings() {
  const { leagueId } = useParams<{ leagueId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    settings: {
      draft_format: 'snake' as DraftFormat,
      roster_size: 6,
      timer_seconds: 90,
      budget_enabled: false,
      budget_per_team: 100,
      trade_approval_required: false,
      waiver_approval_type: 'none' as WaiverApprovalType,
      waiver_processing_type: 'immediate' as WaiverProcessingType,
      waiver_max_per_week: 0,
    },
  })
  const [error, setError] = useState('')

  const { data: league, isLoading, error: loadError } = useQuery({
    queryKey: queryKeys.league(leagueId!),
    queryFn: () => leagueService.getLeague(leagueId!),
    enabled: !!leagueId,
  })

  // Populate form when league loads
  useEffect(() => {
    if (league) {
      setFormData({
        name: league.name,
        description: league.description || '',
        settings: {
          draft_format: league.settings.draft_format,
          roster_size: league.settings.roster_size,
          timer_seconds: league.settings.timer_seconds,
          budget_enabled: league.settings.budget_enabled,
          budget_per_team: league.settings.budget_per_team || 100,
          trade_approval_required: league.settings.trade_approval_required,
          waiver_approval_type: league.settings.waiver_approval_type || 'none',
          waiver_processing_type: league.settings.waiver_processing_type || 'immediate',
          waiver_max_per_week: league.settings.waiver_max_per_week || 0,
        },
      })
    }
  }, [league])

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => leagueService.updateLeague(leagueId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.league(leagueId!) })
      navigate(`/leagues/${leagueId}`)
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to update league')
    },
  })

  const isOwner = user?.id === league?.owner_id

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    updateMutation.mutate(formData)
  }

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (loadError || !league) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-700">Failed to load league settings.</p>
          <Link to="/leagues" className="btn btn-secondary mt-4">
            Back to Leagues
          </Link>
        </div>
      </div>
    )
  }

  if (!isOwner) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card bg-yellow-50 border-yellow-200">
          <p className="text-yellow-700">Only the league owner can edit settings.</p>
          <Link to={`/leagues/${leagueId}`} className="btn btn-secondary mt-4">
            Back to League
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <Link to={`/leagues/${leagueId}`} className="text-pokemon-blue hover:underline text-sm">
          &larr; Back to {league.name}
        </Link>
      </div>

      <h1 className="text-2xl font-bold mb-6">Edit League Settings</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">General</h2>

          <div className="space-y-4">
            <div>
              <label className="label">League Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Draft Settings</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Draft Format</label>
              <select
                value={formData.settings.draft_format}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, draft_format: e.target.value as DraftFormat },
                  })
                }
                className="input"
              >
                <option value="snake">Snake Draft</option>
                <option value="linear">Linear Draft</option>
                <option value="auction">Auction Draft</option>
              </select>
            </div>

            <div>
              <label className="label">Roster Size</label>
              <input
                type="number"
                value={formData.settings.roster_size}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, roster_size: parseInt(e.target.value) },
                  })
                }
                className="input"
                min={1}
                max={20}
              />
            </div>

            <div>
              <label className="label">Timer (seconds per pick)</label>
              <input
                type="number"
                value={formData.settings.timer_seconds}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, timer_seconds: parseInt(e.target.value) },
                  })
                }
                className="input"
                min={30}
                max={600}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="budgetEnabled"
                checked={formData.settings.budget_enabled}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, budget_enabled: e.target.checked },
                  })
                }
                className="h-4 w-4 text-pokemon-red rounded border-gray-300"
              />
              <label htmlFor="budgetEnabled" className="ml-2 text-sm text-gray-700">
                Enable budget/point cap
              </label>
            </div>

            {formData.settings.budget_enabled && (
              <div>
                <label className="label">Budget Per Team</label>
                <input
                  type="number"
                  value={formData.settings.budget_per_team}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      settings: { ...formData.settings, budget_per_team: parseInt(e.target.value) },
                    })
                  }
                  className="input"
                  min={1}
                />
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Trading</h2>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="tradeApproval"
              checked={formData.settings.trade_approval_required}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  settings: { ...formData.settings, trade_approval_required: e.target.checked },
                })
              }
              className="h-4 w-4 text-pokemon-red rounded border-gray-300"
            />
            <label htmlFor="tradeApproval" className="ml-2 text-sm text-gray-700">
              Require admin approval for trades
            </label>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Waiver Wire / Free Agency</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Approval Type</label>
              <select
                value={formData.settings.waiver_approval_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, waiver_approval_type: e.target.value as WaiverApprovalType },
                  })
                }
                className="input"
              >
                <option value="none">No approval required</option>
                <option value="admin">Admin approval required</option>
                <option value="league_vote">League vote required</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {formData.settings.waiver_approval_type === 'none' && 'Claims are processed automatically without approval.'}
                {formData.settings.waiver_approval_type === 'admin' && 'League owner must approve each claim before it is processed.'}
                {formData.settings.waiver_approval_type === 'league_vote' && 'Other team owners vote on claims. Majority approval required.'}
              </p>
            </div>

            <div>
              <label className="label">Processing Time</label>
              <select
                value={formData.settings.waiver_processing_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, waiver_processing_type: e.target.value as WaiverProcessingType },
                  })
                }
                className="input"
              >
                <option value="immediate">Immediate</option>
                <option value="next_week">Next Week</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {formData.settings.waiver_processing_type === 'immediate' && 'Claims are processed immediately once approved (or instantly if no approval required).'}
                {formData.settings.waiver_processing_type === 'next_week' && 'Claims are queued and processed at the start of the next week.'}
              </p>
            </div>

            <div>
              <label className="label">Max Claims Per Week (0 = unlimited)</label>
              <input
                type="number"
                value={formData.settings.waiver_max_per_week}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    settings: { ...formData.settings, waiver_max_per_week: parseInt(e.target.value) || 0 },
                  })
                }
                className="input"
                min={0}
                max={10}
              />
              <p className="text-xs text-gray-500 mt-1">
                Limit how many free agents each team can claim per week.
              </p>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            className="btn btn-primary flex-1"
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
          <Link to={`/leagues/${leagueId}`} className="btn btn-secondary">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
