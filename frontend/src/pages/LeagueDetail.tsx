import { useParams } from 'react-router-dom'

export default function LeagueDetail() {
  const { leagueId } = useParams()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">League Details</h1>
      <div className="card">
        <p className="text-gray-500">
          League ID: {leagueId}
        </p>
        <p className="text-gray-500 mt-4">
          League detail page coming soon...
        </p>
      </div>
    </div>
  )
}
