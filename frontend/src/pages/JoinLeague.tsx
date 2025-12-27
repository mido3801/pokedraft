import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom'
import { leagueService } from '../services/league'
import { useAuth } from '../context/AuthContext'

export default function JoinLeague() {
  const { leagueId } = useParams<{ leagueId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user, isLoading: authLoading } = useAuth()

  const [isJoining, setIsJoining] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const inviteCode = searchParams.get('code')

  useEffect(() => {
    if (authLoading) return

    if (!user) {
      // Redirect to login with return URL
      const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
      navigate(`/login?redirect=${returnUrl}`)
      return
    }

    if (!leagueId || !inviteCode) {
      setError('Invalid invite link')
      return
    }

    const joinLeague = async () => {
      setIsJoining(true)
      setError(null)

      try {
        await leagueService.joinLeague(leagueId, inviteCode)
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
  }, [leagueId, inviteCode, user, authLoading, navigate])

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red"></div>
      </div>
    )
  }

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
