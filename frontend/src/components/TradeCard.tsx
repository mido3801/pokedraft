import { Trade, TradeStatus, TYPE_COLORS } from '../types'
import { useSprite } from '../context/SpriteContext'

interface TradeCardProps {
  trade: Trade
  currentUserTeamId?: string
  isLeagueOwner: boolean
  onAccept?: () => void
  onReject?: () => void
  onCancel?: () => void
  onApprove?: () => void
  isLoading?: boolean
}

export default function TradeCard({
  trade,
  currentUserTeamId,
  isLeagueOwner,
  onAccept,
  onReject,
  onCancel,
  onApprove,
  isLoading = false,
}: TradeCardProps) {
  const { getSpriteUrl } = useSprite()

  const getStatusBadge = (status: TradeStatus, requiresApproval: boolean, adminApproved?: boolean) => {
    const styles: Record<TradeStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    }

    let label = status.charAt(0).toUpperCase() + status.slice(1)
    if (status === 'accepted' && requiresApproval && !adminApproved) {
      label = 'Awaiting Approval'
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {label}
      </span>
    )
  }

  // Determine what actions are available
  const canRespond = trade.status === 'pending' && currentUserTeamId === trade.recipient_team_id
  const canCancel = trade.status === 'pending' && currentUserTeamId === trade.proposer_team_id
  const canApprove =
    trade.status === 'accepted' &&
    trade.requires_approval &&
    !trade.admin_approved &&
    isLeagueOwner

  const renderPokemonList = (details: Trade['proposer_pokemon_details'], fallbackCount: number) => {
    if (details && details.length > 0) {
      return (
        <div className="space-y-1">
          {details.map((pokemon) => (
            <div key={pokemon.id} className="flex items-center gap-2 text-sm">
              <img
                src={getSpriteUrl(pokemon.pokemon_id)}
                alt={pokemon.name}
                className="w-6 h-6"
              />
              <span className="capitalize">{pokemon.name}</span>
              <div className="flex gap-1">
                {pokemon.types.map((type) => (
                  <span
                    key={type}
                    className="px-1.5 py-0.5 rounded text-xs text-white"
                    style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                  >
                    {type}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )
    }
    return <p className="text-sm text-gray-500">{fallbackCount} Pokémon</p>
  }

  return (
    <div className="p-4 border rounded-lg">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="text-sm text-gray-500">
          {new Date(trade.created_at).toLocaleDateString()}
        </div>
        {getStatusBadge(trade.status, trade.requires_approval, trade.admin_approved)}
      </div>

      {/* Trade content */}
      <div className="flex items-start gap-4">
        {/* Proposer side */}
        <div className="flex-1">
          <p className="font-medium mb-2">{trade.proposer_team_name || 'Proposer'}</p>
          {renderPokemonList(trade.proposer_pokemon_details, trade.proposer_pokemon.length)}
        </div>

        {/* Arrow */}
        <div className="flex items-center py-4">
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
            />
          </svg>
        </div>

        {/* Recipient side */}
        <div className="flex-1 text-right">
          <p className="font-medium mb-2">{trade.recipient_team_name || 'Recipient'}</p>
          <div className="flex flex-col items-end">
            {trade.recipient_pokemon_details && trade.recipient_pokemon_details.length > 0 ? (
              <div className="space-y-1">
                {trade.recipient_pokemon_details.map((pokemon) => (
                  <div key={pokemon.id} className="flex items-center gap-2 text-sm justify-end">
                    <div className="flex gap-1">
                      {pokemon.types.map((type) => (
                        <span
                          key={type}
                          className="px-1.5 py-0.5 rounded text-xs text-white"
                          style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                    <span className="capitalize">{pokemon.name}</span>
                    <img
                      src={getSpriteUrl(pokemon.pokemon_id)}
                      alt={pokemon.name}
                      className="w-6 h-6"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">{trade.recipient_pokemon.length} Pokémon</p>
            )}
          </div>
        </div>
      </div>

      {/* Message */}
      {trade.message && (
        <p className="text-sm text-gray-600 mt-3 italic border-t pt-2">"{trade.message}"</p>
      )}

      {/* Awaiting approval notice */}
      {trade.status === 'accepted' && trade.requires_approval && !trade.admin_approved && (
        <p className="text-sm text-yellow-700 bg-yellow-50 rounded p-2 mt-3">
          This trade has been accepted and is awaiting league owner approval.
        </p>
      )}

      {/* Action buttons */}
      {(canRespond || canCancel || canApprove) && (
        <div className="flex gap-2 mt-4 pt-3 border-t">
          {canRespond && (
            <>
              <button
                onClick={onAccept}
                disabled={isLoading}
                className="btn btn-primary flex-1"
              >
                {isLoading ? 'Processing...' : 'Accept'}
              </button>
              <button
                onClick={onReject}
                disabled={isLoading}
                className="btn btn-secondary flex-1"
              >
                {isLoading ? 'Processing...' : 'Reject'}
              </button>
            </>
          )}
          {canCancel && (
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="btn btn-secondary flex-1"
            >
              {isLoading ? 'Processing...' : 'Cancel Trade'}
            </button>
          )}
          {canApprove && (
            <button
              onClick={onApprove}
              disabled={isLoading}
              className="btn btn-primary flex-1"
            >
              {isLoading ? 'Processing...' : 'Approve Trade'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
