import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DraftFormat } from '../types'
import { draftService } from '../services/draft'

export default function CreateDraft() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    displayName: '',
    format: 'snake' as DraftFormat,
    rosterSize: 6,
    timerSeconds: 90,
    budgetEnabled: false,
    budgetPerTeam: 100,
    template: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdDraft, setCreatedDraft] = useState<{
    draftId: string
    rejoinCode: string
    joinUrl: string
    sessionToken: string
  } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await draftService.createAnonymousDraft({
        display_name: formData.displayName,
        format: formData.format,
        roster_size: formData.rosterSize,
        timer_seconds: formData.timerSeconds,
        budget_enabled: formData.budgetEnabled,
        budget_per_team: formData.budgetEnabled ? formData.budgetPerTeam : undefined,
        template_id: formData.template || undefined,
      })

      // Store session token and team ID for reconnection
      localStorage.setItem(`draft_session_${response.id}`, response.session_token)
      localStorage.setItem(`draft_team_${response.id}`, response.team_id)
      localStorage.setItem('last_draft_id', response.id)

      setCreatedDraft({
        draftId: response.id,
        rejoinCode: response.rejoin_code,
        joinUrl: response.join_url,
        sessionToken: response.session_token,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create draft')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEnterDraft = () => {
    if (createdDraft) {
      navigate(`/d/${createdDraft.draftId}`)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  // Show success screen after draft creation
  if (createdDraft) {
    return (
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Draft Created!</h1>
          <p className="text-gray-600">Share the code below with others to join.</p>
        </div>

        <div className="card space-y-6">
          <div>
            <label className="label">Rejoin Code</label>
            <div className="flex gap-2">
              <div className="input text-center text-2xl tracking-widest font-bold flex-1 bg-gray-50">
                {createdDraft.rejoinCode}
              </div>
              <button
                onClick={() => copyToClipboard(createdDraft.rejoinCode)}
                className="btn btn-secondary px-4"
                title="Copy code"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label className="label">Share Link</label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/d/${createdDraft.draftId}`}
                className="input flex-1 text-sm bg-gray-50"
              />
              <button
                onClick={() => copyToClipboard(`${window.location.origin}/d/${createdDraft.draftId}`)}
                className="btn btn-secondary px-4"
                title="Copy link"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          <button onClick={handleEnterDraft} className="btn btn-primary w-full py-3 text-lg">
            Enter Draft Room
          </button>
        </div>

        <p className="text-center text-gray-500 mt-6 text-sm">
          Others can join at{' '}
          <a href="/draft/join" className="text-pokemon-red hover:underline">
            /draft/join
          </a>
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Create a Draft</h1>
      <p className="text-gray-600 mb-8">
        Set up a quick draft session. No account required!
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Your Info</h2>
          <div>
            <label className="label">Display Name</label>
            <input
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
              className="input"
              placeholder="Enter your name"
              required
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Draft Settings</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Draft Format</label>
              <select
                value={formData.format}
                onChange={(e) => setFormData({ ...formData, format: e.target.value as DraftFormat })}
                className="input"
                disabled={isLoading}
              >
                <option value="snake">Snake Draft</option>
                <option value="linear">Linear Draft</option>
                <option value="auction">Auction Draft</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                {formData.format === 'snake' && 'Pick order reverses each round (1→8, 8→1, 1→8...)'}
                {formData.format === 'linear' && 'Same pick order every round (1→8, 1→8...)'}
                {formData.format === 'auction' && 'Pokemon are nominated and teams bid. Highest bidder wins.'}
              </p>
            </div>

            <div>
              <label className="label">Roster Size</label>
              <input
                type="number"
                value={formData.rosterSize}
                onChange={(e) => setFormData({ ...formData, rosterSize: parseInt(e.target.value) })}
                className="input"
                min={1}
                max={20}
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="label">Timer (seconds per pick)</label>
              <input
                type="number"
                value={formData.timerSeconds}
                onChange={(e) => setFormData({ ...formData, timerSeconds: parseInt(e.target.value) })}
                className="input"
                min={30}
                max={600}
                disabled={isLoading}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="budgetEnabled"
                checked={formData.budgetEnabled}
                onChange={(e) => setFormData({ ...formData, budgetEnabled: e.target.checked })}
                className="h-4 w-4 text-pokemon-red rounded border-gray-300"
                disabled={isLoading}
              />
              <label htmlFor="budgetEnabled" className="ml-2 text-sm text-gray-700">
                Enable salary cap / point budget
              </label>
            </div>

            {formData.budgetEnabled && (
              <div>
                <label className="label">Budget Per Team</label>
                <input
                  type="number"
                  value={formData.budgetPerTeam}
                  onChange={(e) => setFormData({ ...formData, budgetPerTeam: parseInt(e.target.value) })}
                  className="input"
                  min={1}
                  disabled={isLoading}
                />
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Pokemon Pool</h2>
          <div>
            <label className="label">Template</label>
            <select
              value={formData.template}
              onChange={(e) => setFormData({ ...formData, template: e.target.value })}
              className="input"
              disabled={isLoading}
            >
              <option value="">All Pokemon</option>
              <option value="ou">OU (OverUsed)</option>
              <option value="uu">UU (UnderUsed)</option>
              <option value="monotype">Monotype</option>
              <option value="little_cup">Little Cup</option>
              <option value="draft_league">Draft League (with points)</option>
            </select>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            You can customize the pool further after creating the draft.
          </p>
        </div>

        <button
          type="submit"
          className="btn btn-primary w-full py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Creating Draft...
            </span>
          ) : (
            'Create Draft'
          )}
        </button>
      </form>
    </div>
  )
}
