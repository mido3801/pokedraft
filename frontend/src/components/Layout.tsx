import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, isAuthenticated, login, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-pokemon-red text-white shadow-lg">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-xl font-bold">
                PokeDraft
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
                  <span className="text-sm">{user?.display_name}</span>
                  <button
                    onClick={logout}
                    className="px-3 py-1 rounded bg-white/10 hover:bg-white/20"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <button
                  onClick={login}
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
