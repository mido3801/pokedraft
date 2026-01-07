import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function DiscordLink() {
  const { user, isAuthenticated, loading, linkDiscord, syncDiscord } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<'checking' | 'syncing' | 'linking' | 'done'>('checking')

  useEffect(() => {
    const handleLink = async () => {
      if (loading) return

      if (!isAuthenticated) return

      // If already linked, redirect to settings
      if (user?.discord_id) {
        setStatus('done')
        navigate('/settings', { replace: true })
        return
      }

      // Try to sync first (in case they linked via Discord login)
      setStatus('syncing')
      const syncResult = await syncDiscord()
      if (!syncResult.error) {
        // Sync succeeded - Discord was already linked in Supabase
        setStatus('done')
        navigate('/settings', { replace: true })
        return
      }

      // Need to initiate OAuth flow
      setStatus('linking')
      const { error } = await linkDiscord()
      if (error) {
        setError(error.message)
      }
      // If successful, Supabase will redirect to Discord OAuth
    }

    handleLink()
  }, [loading, isAuthenticated, user?.discord_id, linkDiscord, syncDiscord, navigate])

  if (loading || status === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login?redirect=/auth/discord" replace />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Error Linking Discord</h2>
            <p>{error}</p>
          </div>
          <a
            href="/settings"
            className="mt-4 inline-block text-pokemon-red hover:underline"
          >
            Go to Settings
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">
          {status === 'syncing' ? 'Checking Discord link...' : 'Redirecting to Discord...'}
        </p>
      </div>
    </div>
  )
}
