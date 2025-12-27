import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom'
import { leagueService } from '../services/league'
import { useAuth } from '../context/AuthContext'

export default function JoinLeague() {
  const { leagueId } = useParams<{ leagueId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()

  const [isJoining, setIsJoining] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // For manual code entry mode
  const [inviteCodeInput, setInviteCodeInput] = useState(searchParams.get('code') || '')

  const inviteCodeFromUrl = searchParams.get('code')

  // Auto-join when we have both leagueId and code from URL
  useEffect(() => {
    if (authLoading) return

    if (!user) {
      // Redirect to login with return URL
      const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
      navigate(`/login?redirect=${returnUrl}`)
      return
    }

    // Only auto-join if we have both leagueId and invite code from URL
    if (!leagueId || !inviteCodeFromUrl) {
      return
    }

    const joinLeague = async () => {
      setIsJoining(true)
      setError(null)

      try {
        await leagueService.joinLeague(leagueId, inviteCodeFromUrl)
        setSuccess(true)
        // Redirect to league page after short delay
        setTimeout(() => {
          navigate(`/leagues/${leagueId}`)
        }, 1500)
      } catch (err) {
        if (err instanceof Error) {
          // Check for common error cases
          if (err.message.includes('already a member')) {
            // Already a member, just redirect
            navigate(`/leagues/${leagueId}`)
            return
          }
          setError(err.message)
        } else {
          setError('Failed to join league. The invite code may be invalid or expired.')
        }
      } finally {
        setIsJoining(false)
      }
    }

    joinLeague()
  }, [leagueId, inviteCodeFromUrl, user, authLoading, navigate])

  // Handle manual code submission
  const handleManualJoin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!inviteCodeInput.trim()) {
      setError('Please enter an invite code')
      return
    }

    setIsJoining(true)
    setError(null)

    try {
      const league = await leagueService.joinLeagueByCode(inviteCodeInput.trim())
      setSuccess(true)
      // Redirect to league page after short delay
      setTimeout(() => {
        navigate(`/leagues/${league.id}`)
      }, 1500)
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('already a member')) {
          setError('You are already a member of this league')
        } else {
          setError(err.message)
        }
      } else {
        setError('Failed to join league. The invite code may be invalid.')
      }
    } finally {
      setIsJoining(false)
    }
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red"></div>
      </div>
    )
  }

  // If no user, the useEffect will redirect to login
  if (!user) {
    return null
  }

  // Link-based joining (has leagueId and code)
  if (leagueId && inviteCodeFromUrl) {
    return (
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="card text-center">
          {isJoining && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red mx-auto mb-4"></div>
              <h2 className="text-xl font-semibold text-gray-900">Joining League...</h2>
              <p className="text-gray-600 mt-2">Please wait while we add you to the league.</p>
            </>
          )}

          {success && (
            <>
              <div className="text-green-500 text-5xl mb-4">✓</div>
              <h2 className="text-xl font-semibold text-gray-900">Successfully Joined!</h2>
              <p className="text-gray-600 mt-2">Redirecting you to the league...</p>
            </>
          )}

          {error && (
            <>
              <div className="text-red-500 text-5xl mb-4">✕</div>
              <h2 className="text-xl font-semibold text-gray-900">Unable to Join</h2>
              <p className="text-red-600 mt-2">{error}</p>
              <div className="mt-6 space-y-3">
                <Link to="/leagues" className="btn btn-primary w-full">
                  Browse Leagues
                </Link>
                <Link to="/dashboard" className="btn btn-secondary w-full">
                  Go to Dashboard
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  // Manual code entry mode (no leagueId in URL)
  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Join a League</h1>
      <p className="text-gray-600 mb-8 text-center">
        Enter the invite code to join an existing league.
      </p>

      {success ? (
        <div className="card text-center">
          <div className="text-green-500 text-5xl mb-4">✓</div>
          <h2 className="text-xl font-semibold text-gray-900">Successfully Joined!</h2>
          <p className="text-gray-600 mt-2">Redirecting you to the league...</p>
        </div>
      ) : (
        <form onSubmit={handleManualJoin} className="card space-y-6">
          <div>
            <label className="label">Invite Code</label>
            <input
              type="text"
              value={inviteCodeInput}
              onChange={(e) => setInviteCodeInput(e.target.value)}
              className="input text-center text-lg tracking-wider"
              placeholder="Enter invite code"
              disabled={isJoining}
              autoFocus
            />
            <p className="text-sm text-gray-500 mt-1">
              Get the code from a league owner or an invite link.
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isJoining}
          >
            {isJoining ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Joining...
              </span>
            ) : (
              'Join League'
            )}
          </button>
        </form>
      )}

      <p className="text-center text-gray-500 mt-6 text-sm">
        Don't have a code?{' '}
        <Link to="/leagues" className="text-pokemon-red hover:underline">
          Browse your leagues
        </Link>
      </p>
    </div>
  )
}
