import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { leagueService } from '../services/league'
import { draftService } from '../services/draft'
import { queryKeys } from '../services/queryKeys'
import { DraftSummary } from '../types'
import PoolPresetsCard from '../components/PoolPresetsCard'
import {
  Play,
  Trophy,
  Users,
  Zap,
  Clock,
  ArrowRight,
  Plus,
  Sparkles,
  Calendar,
  ExternalLink,
  Trash2,
} from 'lucide-react'

function formatDraftStatus(status: string) {
  switch (status) {
    case 'pending': return 'Waiting to start'
    case 'live': return 'In progress'
    case 'paused': return 'Paused'
    case 'completed': return 'Completed'
    default: return status
  }
}

function getDraftStatusColor(status: string) {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800'
    case 'live': return 'bg-green-100 text-green-800'
    case 'paused': return 'bg-orange-100 text-orange-800'
    case 'completed': return 'bg-gray-100 text-gray-600'
    default: return 'bg-gray-100 text-gray-600'
  }
}

function formatTimeRemaining(expiresAt: string | undefined) {
  if (!expiresAt) return null
  const now = new Date()
  const expires = new Date(expiresAt)
  const diff = expires.getTime() - now.getTime()
  if (diff <= 0) return 'Expired'
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  if (hours > 0) return `${hours}h ${minutes}m left`
  return `${minutes}m left`
}

export default function Dashboard() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [deletingDraftId, setDeletingDraftId] = useState<string | null>(null)

  const { data: leagues, isLoading: leaguesLoading } = useQuery({
    queryKey: queryKeys.leagues,
    queryFn: leagueService.getLeagues,
  })

  const { data: myDrafts, isLoading: draftsLoading } = useQuery({
    queryKey: queryKeys.myDrafts,
    queryFn: draftService.getMyDrafts,
  })

  // Filter to show active drafts (pending or live) and recent completed ones
  const activeDrafts = myDrafts?.filter((d: DraftSummary) => d.status === 'pending' || d.status === 'live') || []
  const recentDrafts = myDrafts?.slice(0, 5) || []

  const handleDeleteDraft = async (draftId: string, e: React.MouseEvent) => {
    e.preventDefault() // Prevent navigation when clicking delete
    e.stopPropagation()

    if (!confirm('Are you sure you want to delete this draft? This cannot be undone.')) {
      return
    }

    setDeletingDraftId(draftId)
    try {
      await draftService.deleteDraft(draftId)
      queryClient.invalidateQueries({ queryKey: queryKeys.myDrafts })
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete draft')
    } finally {
      setDeletingDraftId(null)
    }
  }

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
            {draftsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="loader w-6 h-6"></div>
              </div>
            ) : activeDrafts.length > 0 ? (
              <div className="space-y-3">
                {activeDrafts.map((draft: DraftSummary) => (
                  <Link
                    key={draft.id}
                    to={`/d/${draft.id}`}
                    className="group flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:border-pokemon-red/30 hover:shadow-sm transition-all"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getDraftStatusColor(draft.status)}`}>
                          {formatDraftStatus(draft.status)}
                        </span>
                        <span className="text-xs text-gray-500 capitalize">{draft.format}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {draft.team_count} teams
                        </span>
                        {draft.rejoin_code && (
                          <span className="font-mono text-gray-400">{draft.rejoin_code}</span>
                        )}
                        {draft.status === 'pending' && draft.expires_at && (
                          <span className="text-orange-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatTimeRemaining(draft.expires_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {draft.status === 'pending' && (
                        <button
                          onClick={(e) => handleDeleteDraft(draft.id, e)}
                          disabled={deletingDraftId === draft.id}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                          title="Delete draft"
                        >
                          {deletingDraftId === draft.id ? (
                            <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      )}
                      <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-pokemon-red transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
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
            )}
          </div>

          {/* Recent Drafts */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-type-psychic/20 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-type-psychic" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Recent Drafts</h2>
            </div>
            {draftsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="loader w-6 h-6"></div>
              </div>
            ) : recentDrafts.length > 0 ? (
              <div className="space-y-2">
                {recentDrafts.map((draft: DraftSummary) => (
                  <Link
                    key={draft.id}
                    to={`/d/${draft.id}`}
                    className="group flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${draft.status === 'completed' ? 'bg-gray-300' : draft.status === 'live' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                      <span className="text-sm text-gray-700 capitalize">{draft.format} draft</span>
                      <span className="text-xs text-gray-400">
                        {new Date(draft.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {draft.status === 'pending' && (
                        <button
                          onClick={(e) => handleDeleteDraft(draft.id, e)}
                          disabled={deletingDraftId === draft.id}
                          className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                          title="Delete draft"
                        >
                          {deletingDraftId === draft.id ? (
                            <div className="w-3.5 h-3.5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getDraftStatusColor(draft.status)}`}>
                        {formatDraftStatus(draft.status)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Clock className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-500">
                  No drafts yet
                </p>
              </div>
            )}
          </div>

          {/* Pool Presets */}
          <PoolPresetsCard />

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

            {leaguesLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="loader w-8 h-8"></div>
              </div>
            ) : leagues && leagues.length > 0 ? (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {leagues.slice(0, 3).map((league) => (
                  <Link
                    key={league.id}
                    to={`/leagues/${league.id}`}
                    className="group p-4 rounded-xl border border-gray-200 hover:border-pokemon-red/30 hover:shadow-md transition-all"
                  >
                    <h3 className="font-semibold text-gray-900 group-hover:text-pokemon-red transition-colors mb-2">
                      {league.name}
                    </h3>
                    {league.description && (
                      <p className="text-sm text-gray-500 mb-3 line-clamp-2">{league.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {league.member_count || 1}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Season {league.current_season || 1}
                      </span>
                    </div>
                  </Link>
                ))}
                {leagues.length > 3 && (
                  <Link
                    to="/leagues"
                    className="flex items-center justify-center p-4 rounded-xl border-2 border-dashed border-gray-200 hover:border-gray-300 text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    <span className="font-medium">+{leagues.length - 3} more</span>
                  </Link>
                )}
              </div>
            ) : (
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
                <Link
                  to="/leagues"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-pokemon-red text-white rounded-xl font-medium hover:bg-red-600 shadow-sm hover:shadow-md transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Create a League
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
