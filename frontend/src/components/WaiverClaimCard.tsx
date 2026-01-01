import { WaiverClaim, WaiverClaimStatus, TYPE_COLORS } from '../types'
import { useSprite } from '../context/SpriteContext'

interface WaiverClaimCardProps {
  claim: WaiverClaim
  currentUserTeamId?: string
  isLeagueOwner: boolean
  approvalType: 'none' | 'admin' | 'league_vote'
  onCancel?: () => void
  onApprove?: () => void
  onReject?: () => void
  onVoteFor?: () => void
  onVoteAgainst?: () => void
  isLoading?: boolean
}

export default function WaiverClaimCard({
  claim,
  currentUserTeamId,
  isLeagueOwner,
  approvalType,
  onCancel,
  onApprove,
  onReject,
  onVoteFor,
  onVoteAgainst,
  isLoading = false,
}: WaiverClaimCardProps) {
  const { getSpriteUrl } = useSprite()

  const getStatusBadge = (status: WaiverClaimStatus) => {
    const styles: Record<WaiverClaimStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
      expired: 'bg-gray-100 text-gray-600',
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const getProcessingBadge = () => {
    if (claim.processing_type === 'next_week') {
      return (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          Next Week
        </span>
      )
    }
    return null
  }

  // Determine what actions are available
  const canCancel = claim.status === 'pending' && currentUserTeamId === claim.team_id
  const canAdminApprove = claim.status === 'pending' && claim.requires_approval && isLeagueOwner && approvalType === 'admin'
  const canVote = claim.status === 'pending' && claim.requires_approval && approvalType === 'league_vote'

  return (
    <div className="p-4 border rounded-lg">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="text-sm text-gray-500">
          {new Date(claim.created_at).toLocaleDateString()}
          {claim.week_number && <span className="ml-2">Week {claim.week_number}</span>}
        </div>
        <div className="flex gap-2">
          {getProcessingBadge()}
          {getStatusBadge(claim.status)}
        </div>
      </div>

      {/* Claim content */}
      <div className="flex items-start gap-4">
        {/* Team */}
        <div className="flex-1">
          <p className="font-medium text-sm text-gray-600 mb-2">
            {claim.team_name || 'Team'}
          </p>
        </div>

        {/* Claiming Pokemon */}
        <div className="flex-1">
          <p className="text-xs text-gray-500 mb-1">Claiming:</p>
          <div className="flex items-center gap-2">
            <img
              src={claim.pokemon_sprite || getSpriteUrl(claim.pokemon_id)}
              alt={claim.pokemon_name || 'Pokemon'}
              className="w-10 h-10"
            />
            <div>
              <p className="capitalize font-medium text-sm">{claim.pokemon_name || `#${claim.pokemon_id}`}</p>
              {claim.pokemon_types && (
                <div className="flex gap-1 mt-0.5">
                  {claim.pokemon_types.map((type) => (
                    <span
                      key={type}
                      className="px-1 py-0.5 rounded text-[10px] text-white"
                      style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                    >
                      {type}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Dropping Pokemon (if any) */}
        {claim.drop_pokemon_id && (
          <div className="flex-1">
            <p className="text-xs text-gray-500 mb-1">Dropping:</p>
            <div className="flex items-center gap-2">
              <div className="relative">
                <img
                  src={getSpriteUrl(claim.pokemon_id)} // Would need drop pokemon ID
                  alt={claim.drop_pokemon_name || 'Pokemon'}
                  className="w-10 h-10 opacity-60"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-red-500 text-2xl font-bold">×</span>
                </div>
              </div>
              <div>
                <p className="capitalize font-medium text-sm text-gray-600">
                  {claim.drop_pokemon_name || 'Unknown'}
                </p>
                {claim.drop_pokemon_types && (
                  <div className="flex gap-1 mt-0.5">
                    {claim.drop_pokemon_types.map((type) => (
                      <span
                        key={type}
                        className="px-1 py-0.5 rounded text-[10px] text-white opacity-70"
                        style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Vote progress for league vote */}
      {claim.requires_approval && approvalType === 'league_vote' && claim.votes_required && (
        <div className="mt-3 pt-3 border-t">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">Vote Progress</span>
            <span className="font-medium">
              {claim.votes_for} / {claim.votes_required} needed
            </span>
          </div>
          <div className="flex gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-green-500 h-full transition-all"
                style={{ width: `${Math.min(100, (claim.votes_for / claim.votes_required) * 100)}%` }}
              />
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{claim.votes_for} for</span>
            <span>{claim.votes_against} against</span>
          </div>
        </div>
      )}

      {/* Admin approval notice */}
      {claim.status === 'pending' && claim.requires_approval && approvalType === 'admin' && (
        <p className="text-sm text-yellow-700 bg-yellow-50 rounded p-2 mt-3">
          This claim is awaiting league owner approval.
        </p>
      )}

      {/* Admin notes */}
      {claim.admin_notes && (
        <p className="text-sm text-gray-600 mt-3 italic border-t pt-2">
          Admin note: "{claim.admin_notes}"
        </p>
      )}

      {/* Action buttons */}
      {(canCancel || canAdminApprove || canVote) && (
        <div className="flex gap-2 mt-4 pt-3 border-t">
          {canCancel && (
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="btn btn-secondary flex-1"
            >
              {isLoading ? 'Processing...' : 'Cancel Claim'}
            </button>
          )}
          {canAdminApprove && (
            <>
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="btn btn-primary flex-1"
              >
                {isLoading ? 'Processing...' : 'Approve'}
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
          {canVote && (
            <>
              <button
                onClick={onVoteFor}
                disabled={isLoading}
                className="btn btn-primary flex-1"
              >
                {isLoading ? 'Processing...' : 'Vote For'}
              </button>
              <button
                onClick={onVoteAgainst}
                disabled={isLoading}
                className="btn btn-secondary flex-1"
              >
                {isLoading ? 'Processing...' : 'Vote Against'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
