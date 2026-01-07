import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { draftService } from '../services/draft'
import { storage } from '../utils/storage'

interface JoinResponse {
  draft_id: string
  team_id: string
  session_token: string
}

export default function JoinDraft() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const codeFromUrl = searchParams.get('code')

  const [rejoinCode, setRejoinCode] = useState(codeFromUrl?.toUpperCase() || '')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!rejoinCode.trim()) {
      setError('Please enter an invite code')
      return
    }

    if (!displayName.trim()) {
      setError('Please enter your display name')
      return
    }

    setIsLoading(true)

    try {
      const response = await draftService.joinAnonymousDraft(
        rejoinCode.trim(),
        displayName.trim()
      ) as JoinResponse

      // Store session token and rejoin code for reconnection
      storage.setDraftSession(response.draft_id, {
        session: response.session_token,
        team: response.team_id,
        rejoin: rejoinCode.trim().toUpperCase(),
      })

      navigate(`/d/${response.draft_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join draft. Check your code and try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Join a Draft</h1>
      <p className="text-gray-600 mb-8 text-center">
        Enter your Invite code to join an active draft session.
      </p>

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <label className="label">Invite Code</label>
          <input
            type="text"
            value={rejoinCode}
            onChange={(e) => setRejoinCode(e.target.value.toUpperCase())}
            className="input text-center text-2xl tracking-widest"
            placeholder="PIKA-1234"
            maxLength={9}
            disabled={isLoading}
          />
          <p className="text-sm text-gray-500 mt-1">
            The code was displayed when the draft was created.
          </p>
        </div>

        <div>
          <label className="label">Your Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="input"
            placeholder="Enter your name"
            required
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Joining...
            </span>
          ) : (
            'Join Draft'
          )}
        </button>
      </form>

      <p className="text-center text-gray-500 mt-6 text-sm">
        Don't have a code?{' '}
        <a href="/draft/create" className="text-pokemon-red hover:underline">
          Create a new draft
        </a>
      </p>
    </div>
  )
}
