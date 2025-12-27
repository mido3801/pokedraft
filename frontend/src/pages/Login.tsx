import { useAuth } from '../context/AuthContext'
import { Navigate, useSearchParams } from 'react-router-dom'
import { useState } from 'react'

export default function Login() {
  const { isAuthenticated, signInWithEmail, signInWithDiscord, devLogin, loading } = useAuth()
  const [devLoading, setDevLoading] = useState(false)
  const [emailLoading, setEmailLoading] = useState(false)
  const [discordLoading, setDiscordLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchParams] = useSearchParams()
  const redirectTo = searchParams.get('redirect') || '/dashboard'

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setEmailLoading(true)
    setError(null)

    const { error } = await signInWithEmail(email)

    setEmailLoading(false)

    if (error) {
      setError(error.message)
    } else {
      setEmailSent(true)
    }
  }

  const handleDiscordLogin = async () => {
    setDiscordLoading(true)
    setError(null)

    const { error } = await signInWithDiscord()

    if (error) {
      setDiscordLoading(false)
      setError(error.message)
    }
    // If no error, user will be redirected to Discord
  }

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 text-center">
          <div className="text-6xl">📧</div>
          <h2 className="text-2xl font-bold text-gray-900">Check your email</h2>
          <p className="text-gray-600">
            We sent a magic link to <strong>{email}</strong>
          </p>
          <p className="text-sm text-gray-500">
            Click the link in the email to sign in. It may take a minute to arrive.
          </p>
          <button
            onClick={() => {
              setEmailSent(false)
              setEmail('')
            }}
            className="text-pokemon-red hover:underline"
          >
            Use a different email
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">
            Sign in to PokeDraft
          </h2>
          <p className="mt-2 text-gray-600">
            Sign in to access your leagues, save teams, and get Discord notifications.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-4">
          {/* Email Magic Link Form */}
          <form onSubmit={handleEmailSubmit} className="space-y-3">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pokemon-red focus:border-transparent"
                required
              />
            </div>
            <button
              type="submit"
              disabled={emailLoading || !email.trim()}
              className="w-full flex items-center justify-center px-4 py-3 bg-pokemon-red text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {emailLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Sending...
                </>
              ) : (
                'Continue with Email'
              )}
            </button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">or</span>
            </div>
          </div>

          {/* Discord OAuth Button */}
          <button
            onClick={handleDiscordLogin}
            disabled={discordLoading}
            className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {discordLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-2"></div>
                Connecting...
              </>
            ) : (
              <>
                <DiscordIcon className="w-5 h-5 mr-3" />
                Continue with Discord
              </>
            )}
          </button>

          {/* Dev login - only shown in development */}
          {import.meta.env.DEV && (
            <div className="border-2 border-dashed border-yellow-400 rounded-lg bg-yellow-50 p-4">
              <p className="text-sm text-yellow-700 mb-3 text-center font-medium">
                Dev Login (Local Only)
              </p>
              <div className="grid grid-cols-4 gap-2">
                {[1, 2, 3, 4].map((num) => (
                  <button
                    key={num}
                    onClick={async () => {
                      setDevLoading(true)
                      try {
                        await devLogin(num)
                      } finally {
                        setDevLoading(false)
                      }
                    }}
                    disabled={devLoading}
                    className="flex items-center justify-center px-3 py-2 rounded-md bg-yellow-100 text-yellow-800 hover:bg-yellow-200 disabled:opacity-50 font-medium text-sm"
                  >
                    User {num}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <p className="mt-8 text-center text-sm text-gray-500">
          Don't want to sign in?{' '}
          <a href="/draft/create" className="text-pokemon-red hover:underline">
            Create a quick draft
          </a>{' '}
          without an account.
        </p>
      </div>
    </div>
  )
}

function DiscordIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  )
}
