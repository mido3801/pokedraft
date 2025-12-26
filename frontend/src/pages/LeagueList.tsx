import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leagueService } from '../services/league'
import { League, DraftFormat } from '../types'
import {
  Trophy,
  Plus,
  Users,
  Calendar,
  Globe,
  Lock,
  ArrowRight,
  X,
  Settings,
  Clock,
  Coins,
  Check,
  Copy,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react'

interface CreateLeagueForm {
  name: string
  description: string
  isPublic: boolean
  settings: {
    draft_format: DraftFormat
    roster_size: number
    timer_seconds: number
    budget_enabled: boolean
    budget_per_team: number
    trade_approval_required: boolean
  }
}

const initialFormState: CreateLeagueForm = {
  name: '',
  description: '',
  isPublic: false,
  settings: {
    draft_format: 'snake',
    roster_size: 6,
    timer_seconds: 90,
    budget_enabled: false,
    budget_per_team: 100,
    trade_approval_required: false,
  },
}

export default function LeagueList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
  const [form, setForm] = useState<CreateLeagueForm>(initialFormState)
  const [createdLeague, setCreatedLeague] = useState<League | null>(null)
  const [copied, setCopied] = useState(false)

  const { data: leagues, isLoading } = useQuery({
    queryKey: ['leagues'],
    queryFn: leagueService.getLeagues,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      leagueService.createLeague({
        name: form.name,
        description: form.description || undefined,
        is_public: form.isPublic,
        settings: form.settings,
      }),
    onSuccess: (league) => {
      queryClient.invalidateQueries({ queryKey: ['leagues'] })
      setCreatedLeague(league)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    createMutation.mutate()
  }

  const handleClose = () => {
    setShowCreateModal(false)
    setForm(initialFormState)
    setCreatedLeague(null)
    setShowAdvancedSettings(false)
    createMutation.reset()
  }

  const copyInviteCode = async () => {
    if (!createdLeague) return
    const inviteUrl = `${window.location.origin}/leagues/${createdLeague.id}/join?code=${createdLeague.invite_code}`
    await navigator.clipboard.writeText(inviteUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

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
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in overflow-y-auto">
          <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl animate-scale-in relative my-8">
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>

            {createdLeague ? (
              /* Success State */
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Check className="w-8 h-8 text-white" />
                </div>

                <h2 className="text-2xl font-bold mb-2">League Created!</h2>
                <p className="text-gray-500 mb-6">
                  Your league <span className="font-semibold text-gray-700">{createdLeague.name}</span> is ready.
                </p>

                {/* Invite Code */}
                <div className="bg-gray-50 rounded-xl p-4 mb-6">
                  <p className="text-sm text-gray-500 mb-2">Share this invite link:</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-white px-3 py-2 rounded-lg text-sm font-mono border border-gray-200 truncate">
                      {createdLeague.invite_code}
                    </code>
                    <button
                      onClick={copyInviteCode}
                      className="px-3 py-2 bg-pokemon-blue text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-1"
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      {copied ? 'Copied!' : 'Copy Link'}
                    </button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleClose}
                    className="flex-1 btn btn-secondary py-3"
                  >
                    Create Another
                  </button>
                  <button
                    onClick={() => navigate(`/leagues/${createdLeague.id}`)}
                    className="flex-1 btn btn-primary py-3"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View League
                  </button>
                </div>
              </div>
            ) : (
              /* Create Form */
              <form onSubmit={handleSubmit}>
                <div className="w-16 h-16 bg-gradient-to-br from-pokemon-yellow to-yellow-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Trophy className="w-8 h-8 text-white" />
                </div>

                <h2 className="text-2xl font-bold text-center mb-2">Create League</h2>
                <p className="text-gray-500 text-center mb-6">
                  Set up your Pokemon draft league
                </p>

                {/* Error Message */}
                {createMutation.isError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                    {createMutation.error instanceof Error
                      ? createMutation.error.message
                      : 'Failed to create league. Please try again.'}
                  </div>
                )}

                {/* Basic Info */}
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      League Name *
                    </label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="My Awesome League"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                      placeholder="A brief description of your league..."
                      rows={2}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all resize-none"
                    />
                  </div>

                  {/* Visibility Toggle */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      {form.isPublic ? (
                        <Globe className="w-5 h-5 text-green-600" />
                      ) : (
                        <Lock className="w-5 h-5 text-gray-500" />
                      )}
                      <div>
                        <p className="font-medium text-gray-900">
                          {form.isPublic ? 'Public League' : 'Private League'}
                        </p>
                        <p className="text-sm text-gray-500">
                          {form.isPublic
                            ? 'Anyone can discover and join'
                            : 'Invite code required to join'}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setForm({ ...form, isPublic: !form.isPublic })}
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        form.isPublic ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          form.isPublic ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Advanced Settings Toggle */}
                <button
                  type="button"
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl mb-4 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Settings className="w-5 h-5 text-gray-500" />
                    <span className="font-medium text-gray-700">League Settings</span>
                  </div>
                  {showAdvancedSettings ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </button>

                {/* Advanced Settings */}
                {showAdvancedSettings && (
                  <div className="space-y-4 mb-6 p-4 border border-gray-200 rounded-xl animate-fade-in">
                    {/* Draft Format */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Draft Format
                      </label>
                      <select
                        value={form.settings.draft_format}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            settings: { ...form.settings, draft_format: e.target.value as DraftFormat },
                          })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all bg-white"
                      >
                        <option value="snake">Snake Draft</option>
                        <option value="linear">Linear Draft</option>
                        <option value="auction">Auction Draft</option>
                      </select>
                    </div>

                    {/* Roster Size & Timer */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Users className="w-4 h-4 inline mr-1" />
                          Roster Size
                        </label>
                        <input
                          type="number"
                          min={1}
                          max={20}
                          value={form.settings.roster_size}
                          onChange={(e) =>
                            setForm({
                              ...form,
                              settings: { ...form.settings, roster_size: parseInt(e.target.value) || 6 },
                            })
                          }
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Clock className="w-4 h-4 inline mr-1" />
                          Timer (sec)
                        </label>
                        <input
                          type="number"
                          min={10}
                          max={600}
                          value={form.settings.timer_seconds}
                          onChange={(e) =>
                            setForm({
                              ...form,
                              settings: { ...form.settings, timer_seconds: parseInt(e.target.value) || 90 },
                            })
                          }
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all"
                        />
                      </div>
                    </div>

                    {/* Budget Toggle */}
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                      <div className="flex items-center gap-2">
                        <Coins className="w-5 h-5 text-yellow-500" />
                        <span className="font-medium text-gray-700">Budget Mode</span>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          setForm({
                            ...form,
                            settings: { ...form.settings, budget_enabled: !form.settings.budget_enabled },
                          })
                        }
                        className={`relative w-12 h-6 rounded-full transition-colors ${
                          form.settings.budget_enabled ? 'bg-pokemon-yellow' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                            form.settings.budget_enabled ? 'translate-x-7' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    {form.settings.budget_enabled && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Budget Per Team
                        </label>
                        <input
                          type="number"
                          min={10}
                          max={1000}
                          value={form.settings.budget_per_team}
                          onChange={(e) =>
                            setForm({
                              ...form,
                              settings: { ...form.settings, budget_per_team: parseInt(e.target.value) || 100 },
                            })
                          }
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pokemon-blue focus:border-transparent transition-all"
                        />
                      </div>
                    )}

                    {/* Trade Approval */}
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                      <div>
                        <p className="font-medium text-gray-700">Trade Approval</p>
                        <p className="text-xs text-gray-500">Require admin approval for trades</p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          setForm({
                            ...form,
                            settings: {
                              ...form.settings,
                              trade_approval_required: !form.settings.trade_approval_required,
                            },
                          })
                        }
                        className={`relative w-12 h-6 rounded-full transition-colors ${
                          form.settings.trade_approval_required ? 'bg-pokemon-blue' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                            form.settings.trade_approval_required ? 'translate-x-7' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={!form.name.trim() || createMutation.isPending}
                  className="w-full btn btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? (
                    <>
                      <div className="loader w-5 h-5 border-2 border-white/30 border-t-white" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Trophy className="w-5 h-5" />
                      Create League
                    </>
                  )}
                </button>
              </form>
            )}
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
      className="group card-interactive relative overflow-hidden"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none`} />

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
