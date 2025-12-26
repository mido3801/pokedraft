import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { leagueService } from '../services/league'
import { useAuth } from '../context/AuthContext'
import { DraftFormat } from '../types'

export default function LeagueSettings() {
  const { leagueId } = useParams<{ leagueId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false,
    settings: {
      draft_format: 'snake' as DraftFormat,
      roster_size: 6,
      timer_seconds: 90,
      budget_enabled: false,
      budget_per_team: 100,
      trade_approval_required: false,
    },
  })
  const [error, setError] = useState('')

  const { data: league, isLoading, error: loadError } = useQuery({
    queryKey: ['league', leagueId],
    queryFn: () => leagueService.getLeague(leagueId!),
    enabled: !!leagueId,
  })

  // Populate form when league loads
  useEffect(() => {
    if (league) {
      setFormData({
        name: league.name,
        description: league.description || '',
        is_public: league.is_public,
        settings: {
          draft_format: league.settings.draft_format,
          roster_size: league.settings.roster_size,
          timer_seconds: league.settings.timer_seconds,
          budget_enabled: league.settings.budget_enabled,
          budget_per_team: league.settings.budget_per_team || 100,
          trade_approval_required: league.settings.trade_approval_required,
        },
      })
    }
  }, [league])

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) => leagueService.updateLeague(leagueId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['league', leagueId] })
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

            <div className="flex items-center">
              <input
                type="checkbox"
                id="isPublic"
                checked={formData.is_public}
                onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                className="h-4 w-4 text-pokemon-red rounded border-gray-300"
              />
              <label htmlFor="isPublic" className="ml-2 text-sm text-gray-700">
                Public league (anyone can view and request to join)
              </label>
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
