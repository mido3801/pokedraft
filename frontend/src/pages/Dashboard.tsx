import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome, {user?.display_name}
        </h1>
        <p className="text-gray-600">
          Manage your leagues, teams, and drafts.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/draft/create"
              className="block w-full text-left px-4 py-3 rounded-lg bg-gray-50 hover:bg-gray-100"
            >
              Start a Quick Draft
            </Link>
            <Link
              to="/leagues"
              className="block w-full text-left px-4 py-3 rounded-lg bg-gray-50 hover:bg-gray-100"
            >
              View My Leagues
            </Link>
            <Link
              to="/draft/join"
              className="block w-full text-left px-4 py-3 rounded-lg bg-gray-50 hover:bg-gray-100"
            >
              Join a Draft
            </Link>
          </div>
        </div>

        {/* Active Drafts */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Active Drafts</h2>
          <p className="text-gray-500 text-sm">
            No active drafts. Start one or join using a code.
          </p>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <p className="text-gray-500 text-sm">
            No recent activity.
          </p>
        </div>

        {/* My Leagues */}
        <div className="card md:col-span-2 lg:col-span-3">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">My Leagues</h2>
            <Link to="/leagues" className="text-pokemon-red hover:underline text-sm">
              View all
            </Link>
          </div>
          <p className="text-gray-500 text-sm">
            You are not a member of any leagues yet.{' '}
            <Link to="/leagues/public" className="text-pokemon-red hover:underline">
              Browse public leagues
            </Link>{' '}
            or create your own.
          </p>
        </div>
      </div>
    </div>
  )
}
