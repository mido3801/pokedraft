import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { leagueService } from '../services/league'
import { League } from '../types'

export default function LeagueList() {
  const [showCreateModal, setShowCreateModal] = useState(false)

  const { data: leagues, isLoading } = useQuery({
    queryKey: ['leagues'],
    queryFn: leagueService.getLeagues,
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Leagues</h1>
          <p className="text-gray-600">Manage your Pokemon draft leagues.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          Create League
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pokemon-red mx-auto"></div>
        </div>
      ) : leagues && leagues.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leagues.map((league) => (
            <LeagueCard key={league.id} league={league} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No leagues yet</h3>
          <p className="text-gray-500 mb-4">
            Create a league to start organizing draft competitions with friends.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            Create Your First League
          </button>
        </div>
      )}

      {/* Create Modal - placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Create League</h2>
            <p className="text-gray-500 mb-4">League creation coming soon...</p>
            <button
              onClick={() => setShowCreateModal(false)}
              className="btn btn-secondary"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function LeagueCard({ league }: { league: League }) {
  return (
    <Link to={`/leagues/${league.id}`} className="card hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">{league.name}</h3>
        {league.is_public && (
          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
            Public
          </span>
        )}
      </div>
      {league.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{league.description}</p>
      )}
      <div className="flex justify-between text-sm text-gray-500">
        <span>{league.member_count || 0} members</span>
        <span>Season {league.current_season || 0}</span>
      </div>
    </Link>
  )
}
