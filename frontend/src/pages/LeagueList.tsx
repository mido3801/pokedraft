import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { leagueService } from '../services/league'
import { League } from '../types'
import {
  Trophy,
  Plus,
  Users,
  Calendar,
  Globe,
  Lock,
  ArrowRight,
  Sparkles,
  X,
} from 'lucide-react'

export default function LeagueList() {
  const [showCreateModal, setShowCreateModal] = useState(false)

  const { data: leagues, isLoading } = useQuery({
    queryKey: ['leagues'],
    queryFn: leagueService.getLeagues,
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-pokemon-yellow to-yellow-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Trophy className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">My Leagues</h1>
                <p className="text-gray-600 mt-1">Manage your Pokemon draft leagues</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              <Plus className="w-5 h-5" />
              Create League
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="loader w-12 h-12 mb-4"></div>
            <p className="text-gray-500">Loading your leagues...</p>
          </div>
        ) : leagues && leagues.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
            {leagues.map((league, index) => (
              <LeagueCard key={league.id} league={league} index={index} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-12 text-center animate-fade-in">
            <div className="w-24 h-24 bg-gradient-to-br from-pokemon-yellow/20 to-yellow-100 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <Trophy className="w-12 h-12 text-pokemon-yellow" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No leagues yet</h3>
            <p className="text-gray-500 mb-8 max-w-md mx-auto text-lg">
              Create your first league to start organizing draft competitions with friends.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-pokemon-red to-red-600 text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all"
              >
                <Plus className="w-5 h-5" />
                Create Your First League
              </button>
              <Link
                to="/leagues/public"
                className="inline-flex items-center gap-2 px-6 py-4 bg-white border-2 border-gray-200 text-gray-700 rounded-xl font-semibold hover:border-gray-300 hover:bg-gray-50 transition-all"
              >
                <Globe className="w-5 h-5" />
                Browse Public Leagues
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl animate-scale-in relative">
            <button
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>

            <div className="w-16 h-16 bg-gradient-to-br from-pokemon-yellow to-yellow-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
              <Trophy className="w-8 h-8 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-center mb-2">Create League</h2>
            <p className="text-gray-500 text-center mb-6">
              League creation coming soon...
            </p>

            <div className="flex items-center justify-center gap-2 py-4 px-6 bg-gray-50 rounded-xl mb-6">
              <Sparkles className="w-5 h-5 text-pokemon-yellow" />
              <span className="text-sm text-gray-600">
                This feature is under development
              </span>
            </div>

            <button
              onClick={() => setShowCreateModal(false)}
              className="w-full btn btn-secondary py-3"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function LeagueCard({ league, index }: { league: League; index: number }) {
  const gradients = [
    'from-type-dragon/10 to-type-dragon/5',
    'from-type-fire/10 to-type-fire/5',
    'from-type-water/10 to-type-water/5',
    'from-type-grass/10 to-type-grass/5',
    'from-type-psychic/10 to-type-psychic/5',
    'from-type-electric/10 to-type-electric/5',
  ]

  const iconColors = [
    'text-type-dragon',
    'text-type-fire',
    'text-type-water',
    'text-type-grass',
    'text-type-psychic',
    'text-type-electric',
  ]

  const gradient = gradients[index % gradients.length]
  const iconColor = iconColors[index % iconColors.length]

  return (
    <Link
      to={`/leagues/${league.id}`}
      className="group card-interactive"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity`} />

      <div className="relative">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 bg-gradient-to-br ${gradient} rounded-xl flex items-center justify-center`}>
              <Trophy className={`w-6 h-6 ${iconColor}`} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 group-hover:text-pokemon-red transition-colors">
                {league.name}
              </h3>
              {league.is_public ? (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700">
                  <Globe className="w-3 h-3" />
                  Public
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500">
                  <Lock className="w-3 h-3" />
                  Private
                </span>
              )}
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-gray-400 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
        </div>

        {league.description && (
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{league.description}</p>
        )}

        <div className="flex items-center gap-4 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <Users className="w-4 h-4" />
            <span>{league.member_count || 0} members</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            <Calendar className="w-4 h-4" />
            <span>Season {league.current_season || 1}</span>
          </div>
        </div>
      </div>
    </Link>
  )
}
