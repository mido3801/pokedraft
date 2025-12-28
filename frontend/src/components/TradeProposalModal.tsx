import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Team, TYPE_COLORS } from '../types'
import { tradeService } from '../services/trade'
import { queryKeys } from '../services/queryKeys'
import { useSprite } from '../context/SpriteContext'

interface TradeProposalModalProps {
  isOpen: boolean
  onClose: () => void
  seasonId: string
  myTeam: Team
  otherTeams: Team[]
}

export default function TradeProposalModal({
  isOpen,
  onClose,
  seasonId,
  myTeam,
  otherTeams,
}: TradeProposalModalProps) {
  const queryClient = useQueryClient()
  const { getSpriteUrl } = useSprite()

  const [recipientTeamId, setRecipientTeamId] = useState<string>('')
  const [selectedMyPokemon, setSelectedMyPokemon] = useState<string[]>([])
  const [selectedTheirPokemon, setSelectedTheirPokemon] = useState<string[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)

  const recipientTeam = useMemo(
    () => otherTeams.find((t) => t.id === recipientTeamId),
    [otherTeams, recipientTeamId]
  )

  const proposeMutation = useMutation({
    mutationFn: () =>
      tradeService.proposeTrade({
        season_id: seasonId,
        recipient_team_id: recipientTeamId,
        proposer_pokemon: selectedMyPokemon,
        recipient_pokemon: selectedTheirPokemon,
        message: message || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.seasonTrades(seasonId) })
      handleClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to propose trade')
    },
  })

  const handleClose = () => {
    setRecipientTeamId('')
    setSelectedMyPokemon([])
    setSelectedTheirPokemon([])
    setMessage('')
    setError(null)
    onClose()
  }

  const toggleMyPokemon = (pokemonId: string) => {
    setSelectedMyPokemon((prev) =>
      prev.includes(pokemonId) ? prev.filter((id) => id !== pokemonId) : [...prev, pokemonId]
    )
  }

  const toggleTheirPokemon = (pokemonId: string) => {
    setSelectedTheirPokemon((prev) =>
      prev.includes(pokemonId) ? prev.filter((id) => id !== pokemonId) : [...prev, pokemonId]
    )
  }

  const canSubmit =
    recipientTeamId &&
    selectedMyPokemon.length > 0 &&
    selectedTheirPokemon.length > 0 &&
    !proposeMutation.isPending

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Propose Trade</h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* Recipient selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Trade With</label>
            <select
              value={recipientTeamId}
              onChange={(e) => {
                setRecipientTeamId(e.target.value)
                setSelectedTheirPokemon([])
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a team...</option>
              {otherTeams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.display_name}
                </option>
              ))}
            </select>
          </div>

          {/* Pokemon selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Your Pokemon */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Your Pokémon (select to offer)
              </h3>
              {myTeam.pokemon && myTeam.pokemon.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto border rounded-lg p-2">
                  {myTeam.pokemon.map((pokemon) => (
                    <label
                      key={pokemon.id}
                      className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${
                        selectedMyPokemon.includes(pokemon.id)
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-gray-50 border border-transparent'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedMyPokemon.includes(pokemon.id)}
                        onChange={() => toggleMyPokemon(pokemon.id)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <img
                        src={getSpriteUrl(pokemon.pokemon_id)}
                        alt={pokemon.pokemon_name}
                        className="w-8 h-8"
                      />
                      <span className="capitalize flex-1">{pokemon.pokemon_name}</span>
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
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 p-4 border rounded-lg">
                  You have no Pokémon to trade.
                </p>
              )}
              {selectedMyPokemon.length > 0 && (
                <p className="text-sm text-blue-600 mt-2">
                  {selectedMyPokemon.length} Pokémon selected
                </p>
              )}
            </div>

            {/* Their Pokemon */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Their Pokémon (select to request)
              </h3>
              {recipientTeam ? (
                recipientTeam.pokemon && recipientTeam.pokemon.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto border rounded-lg p-2">
                    {recipientTeam.pokemon.map((pokemon) => (
                      <label
                        key={pokemon.id}
                        className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${
                          selectedTheirPokemon.includes(pokemon.id)
                            ? 'bg-green-50 border border-green-200'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedTheirPokemon.includes(pokemon.id)}
                          onChange={() => toggleTheirPokemon(pokemon.id)}
                          className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
                        />
                        <img
                          src={getSpriteUrl(pokemon.pokemon_id)}
                          alt={pokemon.pokemon_name}
                          className="w-8 h-8"
                        />
                        <span className="capitalize flex-1">{pokemon.pokemon_name}</span>
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
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 p-4 border rounded-lg">
                    This team has no Pokémon.
                  </p>
                )
              ) : (
                <p className="text-sm text-gray-500 p-4 border rounded-lg">
                  Select a team to see their Pokémon.
                </p>
              )}
              {selectedTheirPokemon.length > 0 && (
                <p className="text-sm text-green-600 mt-2">
                  {selectedTheirPokemon.length} Pokémon selected
                </p>
              )}
            </div>
          </div>

          {/* Message */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message (optional)
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Add a message to your trade proposal..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={2}
              maxLength={500}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <button onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={() => proposeMutation.mutate()}
            disabled={!canSubmit}
            className="btn btn-primary"
          >
            {proposeMutation.isPending ? 'Proposing...' : 'Propose Trade'}
          </button>
        </div>
      </div>
    </div>
  )
}
