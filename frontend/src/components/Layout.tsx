import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

function DevUserSwitcher() {
  const { user, devLogin } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [switching, setSwitching] = useState(false)

  // Extract current user number from ID (last digit)
  const currentUserNum = user?.id?.endsWith('1') ? 1
    : user?.id?.endsWith('2') ? 2
    : user?.id?.endsWith('3') ? 3
    : user?.id?.endsWith('4') ? 4
    : null

  const handleSwitch = async (num: number) => {
    if (num === currentUserNum) {
      setIsOpen(false)
      return
    }
    setSwitching(true)
    try {
      await devLogin(num)
      // Reload to clear all cached data and refresh with new user
      window.location.reload()
    } catch (error) {
      console.error('Failed to switch user:', error)
      setSwitching(false)
      setIsOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-yellow-500 text-yellow-900 hover:bg-yellow-400 font-medium"
        title="Switch test user"
      >
        <span>U{currentUserNum || '?'}</span>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg border z-20 py-1">
            <div className="px-3 py-1 text-xs text-gray-500 border-b">Switch User</div>
            {[1, 2, 3, 4].map((num) => (
              <button
                key={num}
                onClick={() => handleSwitch(num)}
                disabled={switching}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 disabled:opacity-50 flex items-center justify-between ${
                  num === currentUserNum ? 'bg-yellow-50 text-yellow-800' : 'text-gray-700'
                }`}
              >
                <span>Test User {num}</span>
                {num === currentUserNum && (
                  <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [showHelp, setShowHelp] = useState(false)

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-pokemon-red text-white shadow-lg">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-2">
                <Link to="/" className="text-xl font-bold">
                  PokéDraft
                </Link>
                <button
                  onClick={() => setShowHelp(true)}
                  className="p-1 rounded-full hover:bg-white/20"
                  title="Help"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>
              <div className="hidden md:flex space-x-4">
                <Link to="/draft/create" className="hover:text-gray-200">
                  Quick Draft
                </Link>
                {isAuthenticated && (
                  <>
                    <Link to="/leagues" className="hover:text-gray-200">
                      My Leagues
                    </Link>
                    <Link to="/dashboard" className="hover:text-gray-200">
                      Dashboard
                    </Link>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  {import.meta.env.DEV && <DevUserSwitcher />}
                  <Link
                    to="/settings"
                    className="text-sm hover:text-gray-200 hover:underline"
                  >
                    {user?.display_name}
                  </Link>
                  <button
                    onClick={logout}
                    className="px-3 py-1 rounded bg-white/10 hover:bg-white/20"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <button
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 rounded bg-white text-pokemon-red font-medium hover:bg-gray-100"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-gray-800 text-gray-300 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-xs text-gray-500 text-center">
            Pokémon and all respective names are trademarks and © of The Pokémon Company, Nintendo, Game Freak, and Creatures Inc. This is a fan-made project and is not affiliated with or endorsed by The Pokémon Company.
          </p>
        </div>
      </footer>

      {showHelp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowHelp(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-900">About PokéDraft</h2>
              <button
                onClick={() => setShowHelp(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-gray-600 mb-4">
              A free platform to run Pokémon draft leagues with friends.
            </p>
            <ul className="text-gray-600 text-sm mb-5 space-y-1">
              <li>Quick draft without an account</li>
              <li>Manage leagues season to season</li>
              <li>Customizable settings and shareable draft pools</li>
            </ul>
            <div className="flex items-center gap-3">
              <a
                href="https://discord.gg/pokedraft"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
                Join Discord
              </a>
              <span className="text-sm text-gray-500">for bugs & feature requests</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
