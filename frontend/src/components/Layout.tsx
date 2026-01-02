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

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-pokemon-red text-white shadow-lg">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-xl font-bold">
                PokéDraft
              </Link>
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

      <footer className="bg-gray-800 text-gray-300 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <p className="text-sm">
              Pokemon Draft League Platform
            </p>
            <div className="flex space-x-6 text-sm">
              <a href="#" className="hover:text-white">About</a>
              <a href="#" className="hover:text-white">Help</a>
              <a href="#" className="hover:text-white">Discord</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
