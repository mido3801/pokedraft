import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Play,
  Trophy,
  Users,
  Zap,
  Clock,
  ArrowRight,
  Plus,
  Sparkles,
} from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-pokemon-red to-red-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              {user?.display_name?.charAt(0).toUpperCase() || 'T'}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {user?.display_name || 'Trainer'}
              </h1>
              <p className="text-gray-600 mt-1">
                Manage your leagues, teams, and drafts
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-pokemon-blue/10 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-pokemon-blue" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Quick Actions</h2>
            </div>
            <div className="space-y-3">
              <Link
                to="/draft/create"
                className="group flex items-center justify-between w-full px-4 py-3 rounded-xl bg-gradient-to-r from-pokemon-red to-red-600 text-white font-medium hover:shadow-lg hover:scale-[1.02] transition-all"
              >
                <span className="flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Start a Quick Draft
                </span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/leagues"
                className="group flex items-center justify-between w-full px-4 py-3 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-pokemon-yellow" />
                  View My Leagues
                </span>
                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </Link>
              <Link
                to="/draft/join"
                className="group flex items-center justify-between w-full px-4 py-3 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-pokemon-blue" />
                  Join a Draft
                </span>
                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </Link>
            </div>
          </div>

          {/* Active Drafts */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-type-electric/20 rounded-xl flex items-center justify-center">
                <Clock className="w-5 h-5 text-type-electric" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Active Drafts</h2>
            </div>
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 mb-4">
                No active drafts right now
              </p>
              <Link
                to="/draft/create"
                className="inline-flex items-center gap-2 text-pokemon-red font-medium hover:underline"
              >
                <Plus className="w-4 h-4" />
                Start one now
              </Link>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-type-psychic/20 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-type-psychic" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Recent Activity</h2>
            </div>
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500">
                No recent activity to show
              </p>
            </div>
          </div>

          {/* My Leagues - Full Width */}
          <div className="md:col-span-2 lg:col-span-3 bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-pokemon-yellow/20 rounded-xl flex items-center justify-center">
                  <Trophy className="w-5 h-5 text-pokemon-yellow" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">My Leagues</h2>
              </div>
              <Link
                to="/leagues"
                className="flex items-center gap-1 text-pokemon-red font-medium hover:underline"
              >
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border-2 border-dashed border-gray-200">
              <div className="w-20 h-20 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-4">
                <Trophy className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No leagues yet
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Join an existing league or create your own to start competing with friends.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link
                  to="/leagues/public"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-white border border-gray-200 rounded-xl font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-colors"
                >
                  <Users className="w-4 h-4" />
                  Browse Public Leagues
                </Link>
                <Link
                  to="/leagues/create"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-pokemon-red text-white rounded-xl font-medium hover:bg-red-600 shadow-sm hover:shadow-md transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Create a League
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
