import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { DraftFormat, PokemonFilters, PokemonBoxEntry, PokemonPointsMap, DEFAULT_POKEMON_FILTERS } from '../types'
import { draftService } from '../services/draft'
import { pokemonService } from '../services/pokemon'
import { storage } from '../utils/storage'
import PokemonBox from '../components/PokemonBox'
import PokemonFiltersComponent from '../components/PokemonFilters'
import PointsManager from '../components/PointsManager'
import { TEMPLATE_PRESETS, applyTemplate, getTemplateOptions } from '../data/templatePresets'

// Helper to check if a Pokemon passes filters
function pokemonPassesFilters(p: PokemonBoxEntry, filters: PokemonFilters): boolean {
  if (filters.custom_inclusions.includes(p.id)) return true
  if (filters.custom_exclusions.includes(p.id)) return false
  if (!filters.generations.includes(p.generation)) return false
  if (!filters.evolution_stages.includes(p.evolution_stage)) return false
  if (!filters.include_legendary && p.is_legendary) return false
  if (!filters.include_mythical && p.is_mythical) return false
  if (filters.types.length > 0 && !p.types.some(t => filters.types.includes(t))) return false
  if (p.bst < filters.bst_min || p.bst > filters.bst_max) return false
  return true
}

export default function CreateDraft() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    displayName: '',
    format: 'snake' as DraftFormat,
    rosterSize: 6,
    timerSeconds: 90,
    budgetEnabled: false,
    budgetPerTeam: 100,
    template: '',
    // Auction-specific settings
    nominationTimerSeconds: 30,
    minBid: 1,
    bidIncrement: 1,
  })
  const [filters, setFilters] = useState<PokemonFilters>(DEFAULT_POKEMON_FILTERS)
  const [allPokemon, setAllPokemon] = useState<PokemonBoxEntry[]>([])
  const [isLoadingPokemon, setIsLoadingPokemon] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPokemonPool, setShowPokemonPool] = useState(false)
  // Point value state for budget mode
  const [pokemonPoints, setPokemonPoints] = useState<PokemonPointsMap>({})
  const [pointsEditMode, setPointsEditMode] = useState(false)
  const [createdDraft, setCreatedDraft] = useState<{
    draftId: string
    rejoinCode: string
    joinUrl: string
    sessionToken: string
  } | null>(null)

  // Load all Pokemon on mount
  useEffect(() => {
    const loadPokemon = async () => {
      try {
        setIsLoadingPokemon(true)
        const response = await pokemonService.getAllForBox()
        setAllPokemon(response.pokemon)
      } catch (err) {
        console.error('Failed to load Pokemon:', err)
        setError('Failed to load Pokemon data')
      } finally {
        setIsLoadingPokemon(false)
      }
    }
    loadPokemon()
  }, [])

  // Handle template change - apply preset filters and settings
  const handleTemplateChange = (templateId: string) => {
    setFormData(prev => {
      const template = TEMPLATE_PRESETS[templateId]
      return {
        ...prev,
        template: templateId,
        // Apply template settings if defined
        ...(template?.rosterSize && { rosterSize: template.rosterSize }),
        ...(template?.budgetEnabled !== undefined && { budgetEnabled: template.budgetEnabled }),
        ...(template?.budgetPerTeam && { budgetPerTeam: template.budgetPerTeam }),
      }
    })
    // Apply template filters
    setFilters(applyTemplate(templateId))
  }

  // Calculate stats for budget mode validation (NOT for auction - auction doesn't use point values)
  const budgetStats = useMemo(() => {
    // Auction drafts don't need point values - teams just bid freely
    if (formData.format === 'auction' || !formData.budgetEnabled) return null
    const filtered = allPokemon.filter(p => pokemonPassesFilters(p, filters))
    const withPoints = filtered.filter(p => pokemonPoints[p.id] !== undefined)
    return {
      total: filtered.length,
      withPoints: withPoints.length,
      withoutPoints: filtered.length - withPoints.length,
    }
  }, [formData.format, formData.budgetEnabled, allPokemon, filters, pokemonPoints])

  // Handle point value change
  const handlePointChange = useCallback((pokemonId: number, points: number | null) => {
    setPokemonPoints(prev => {
      if (points === null) {
        const { [pokemonId]: _, ...rest } = prev
        return rest
      }
      return { ...prev, [pokemonId]: points }
    })
  }, [])

  // Toggle custom exclusion/inclusion
  const handleToggleExclusion = useCallback((pokemonId: number) => {
    setFilters(prev => {
      const isExcluded = prev.custom_exclusions.includes(pokemonId)
      const isIncluded = prev.custom_inclusions.includes(pokemonId)

      if (isExcluded) {
        // Remove from exclusions, add to inclusions
        return {
          ...prev,
          custom_exclusions: prev.custom_exclusions.filter(id => id !== pokemonId),
          custom_inclusions: [...prev.custom_inclusions, pokemonId],
        }
      } else if (isIncluded) {
        // Remove from inclusions (back to default state)
        return {
          ...prev,
          custom_inclusions: prev.custom_inclusions.filter(id => id !== pokemonId),
        }
      } else {
        // Add to exclusions
        return {
          ...prev,
          custom_exclusions: [...prev.custom_exclusions, pokemonId],
        }
      }
    })
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validation for point cap mode (NOT auction - auction doesn't need point values)
    if (formData.format !== 'auction' && formData.budgetEnabled && budgetStats) {
      if (budgetStats.withPoints === 0) {
        setError('You must assign point values to at least one Pokemon when point cap is enabled.')
        return
      }
      if (budgetStats.withoutPoints > 0) {
        const confirmed = confirm(
          `${budgetStats.withoutPoints} Pokemon do not have point values assigned and will be excluded from the draft. Continue?`
        )
        if (!confirmed) return
      }
    }

    setIsLoading(true)

    try {
      const isAuction = formData.format === 'auction'

      // Build pokemon_pool with points when point cap mode is enabled (NOT for auction)
      let pokemon_pool: Array<{
        pokemon_id: number
        name: string
        points: number | null
        types: string[]
        generation: number
      }> | undefined

      if (!isAuction && formData.budgetEnabled) {
        // Only include Pokemon that pass filters AND have points assigned
        pokemon_pool = allPokemon
          .filter(p => pokemonPassesFilters(p, filters) && pokemonPoints[p.id] !== undefined)
          .map(p => ({
            pokemon_id: p.id,
            name: p.name,
            points: pokemonPoints[p.id],
            types: p.types,
            generation: p.generation,
          }))
      }

      // For auction: budget_enabled means they have a starting budget to bid with
      // For snake/linear: budget_enabled means point cap mode (need point values)
      const budgetEnabled = isAuction || formData.budgetEnabled

      const response = await draftService.createAnonymousDraft({
        display_name: formData.displayName,
        format: formData.format,
        roster_size: formData.rosterSize,
        timer_seconds: formData.timerSeconds,
        budget_enabled: budgetEnabled,
        budget_per_team: budgetEnabled ? formData.budgetPerTeam : undefined,
        // For auction: use filters normally. For point cap: no filters (use explicit pool)
        pokemon_filters: (isAuction || !formData.budgetEnabled) ? filters : undefined,
        pokemon_pool: pokemon_pool,
        template_id: formData.template || undefined,
        // Auction-specific settings
        nomination_timer_seconds: isAuction ? formData.nominationTimerSeconds : undefined,
        min_bid: isAuction ? formData.minBid : undefined,
        bid_increment: isAuction ? formData.bidIncrement : undefined,
      })

      // Store session token, team ID, and rejoin code for reconnection
      storage.setDraftSession(response.id, {
        session: response.session_token,
        team: response.team_id,
        rejoin: response.rejoin_code,
      })

      setCreatedDraft({
        draftId: response.id,
        rejoinCode: response.rejoin_code,
        joinUrl: response.join_url,
        sessionToken: response.session_token,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create draft')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEnterDraft = () => {
    if (createdDraft) {
      navigate(`/d/${createdDraft.draftId}`)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  // Show success screen after draft creation
  if (createdDraft) {
    return (
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Draft Created!</h1>
          <p className="text-gray-600">Share the code below with others to join.</p>
        </div>

        <div className="card space-y-6">
          <div>
            <label className="label">Rejoin Code</label>
            <div className="flex gap-2">
              <div className="input text-center text-2xl tracking-widest font-bold flex-1 bg-gray-50">
                {createdDraft.rejoinCode}
              </div>
              <button
                onClick={() => copyToClipboard(createdDraft.rejoinCode)}
                className="btn btn-secondary px-4"
                title="Copy code"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label className="label">Share Link</label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/d/${createdDraft.draftId}`}
                className="input flex-1 text-sm bg-gray-50"
              />
              <button
                onClick={() => copyToClipboard(`${window.location.origin}/d/${createdDraft.draftId}`)}
                className="btn btn-secondary px-4"
                title="Copy link"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          <button onClick={handleEnterDraft} className="btn btn-primary w-full py-3 text-lg">
            Enter Draft Room
          </button>
        </div>

        <p className="text-center text-gray-500 mt-6 text-sm">
          Others can join at{' '}
          <a href="/draft/join" className="text-pokemon-red hover:underline">
            /draft/join
          </a>
        </p>
      </div>
    )
  }

  const templateOptions = getTemplateOptions()

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Create a Draft</h1>
      <p className="text-gray-600 mb-8">
        Set up a quick draft session. No account required!
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Your Info</h2>
          <div>
            <label className="label">Display Name</label>
            <input
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
              className="input"
              placeholder="Enter your name"
              required
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Draft Settings</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Draft Format</label>
              <select
                value={formData.format}
                onChange={(e) => {
                  const newFormat = e.target.value as DraftFormat
                  setFormData(prev => ({
                    ...prev,
                    format: newFormat,
                    // Auto-enable budget for auction drafts
                    budgetEnabled: newFormat === 'auction' ? true : prev.budgetEnabled,
                  }))
                }}
                className="input"
                disabled={isLoading}
              >
                <option value="snake">Snake Draft</option>
                <option value="linear">Linear Draft</option>
                <option value="auction">Auction Draft</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                {formData.format === 'snake' && 'Pick order reverses each round (1→8, 8→1, 1→8...)'}
                {formData.format === 'linear' && 'Same pick order every round (1→8, 1→8...)'}
                {formData.format === 'auction' && 'Pokemon are nominated and teams bid. Highest bidder wins.'}
              </p>
            </div>

            {/* Auction-specific settings */}
            {formData.format === 'auction' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
                <h3 className="font-medium text-blue-800">Auction Settings</h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="label">Starting Budget</label>
                    <input
                      type="number"
                      value={formData.budgetPerTeam}
                      onChange={(e) => setFormData({ ...formData, budgetPerTeam: parseInt(e.target.value) })}
                      className="input"
                      min={1}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Credits per team</p>
                  </div>

                  <div>
                    <label className="label">Minimum Bid</label>
                    <input
                      type="number"
                      value={formData.minBid}
                      onChange={(e) => setFormData({ ...formData, minBid: parseInt(e.target.value) })}
                      className="input"
                      min={1}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Starting bid amount</p>
                  </div>

                  <div>
                    <label className="label">Bid Increment</label>
                    <input
                      type="number"
                      value={formData.bidIncrement}
                      onChange={(e) => setFormData({ ...formData, bidIncrement: parseInt(e.target.value) })}
                      className="input"
                      min={1}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Minimum raise</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Nomination Timer (seconds)</label>
                    <input
                      type="number"
                      value={formData.nominationTimerSeconds}
                      onChange={(e) => setFormData({ ...formData, nominationTimerSeconds: parseInt(e.target.value) })}
                      className="input"
                      min={10}
                      max={300}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Time to nominate a Pokemon</p>
                  </div>

                  <div>
                    <label className="label">Bid Timer (seconds)</label>
                    <input
                      type="number"
                      value={formData.timerSeconds}
                      onChange={(e) => setFormData({ ...formData, timerSeconds: parseInt(e.target.value) })}
                      className="input"
                      min={5}
                      max={120}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">Time for each bid</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="label">Roster Size</label>
              <input
                type="number"
                value={formData.rosterSize}
                onChange={(e) => setFormData({ ...formData, rosterSize: parseInt(e.target.value) })}
                className="input"
                min={1}
                max={20}
                disabled={isLoading}
              />
            </div>

            {/* Timer and budget settings - only for non-auction formats */}
            {formData.format !== 'auction' && (
              <>
                <div>
                  <label className="label">Timer (seconds per pick)</label>
                  <input
                    type="number"
                    value={formData.timerSeconds}
                    onChange={(e) => setFormData({ ...formData, timerSeconds: parseInt(e.target.value) })}
                    className="input"
                    min={30}
                    max={600}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="budgetEnabled"
                    checked={formData.budgetEnabled}
                    onChange={(e) => setFormData({ ...formData, budgetEnabled: e.target.checked })}
                    className="h-4 w-4 text-pokemon-red rounded border-gray-300"
                    disabled={isLoading}
                  />
                  <label htmlFor="budgetEnabled" className="ml-2 text-sm text-gray-700">
                    Enable point cap
                  </label>
                </div>

                {formData.budgetEnabled && (
                  <div>
                    <label className="label">Point Budget Per Team</label>
                    <input
                      type="number"
                      value={formData.budgetPerTeam}
                      onChange={(e) => setFormData({ ...formData, budgetPerTeam: parseInt(e.target.value) })}
                      className="input"
                      min={1}
                      disabled={isLoading}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Each Pokemon costs points based on their assigned value
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Point Values Section - only shown for point cap mode (NOT auction) */}
        {formData.format !== 'auction' && formData.budgetEnabled && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Point Values</h2>
            <PointsManager
              pokemon={allPokemon}
              filters={filters}
              pokemonPoints={pokemonPoints}
              onPointsChange={setPokemonPoints}
              editMode={pointsEditMode}
              onEditModeChange={setPointsEditMode}
            />
          </div>
        )}

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Pokemon Pool</h2>

          {/* Template Selection */}
          <div className="mb-4">
            <label className="label">Template</label>
            <select
              value={formData.template}
              onChange={(e) => handleTemplateChange(e.target.value)}
              className="input"
              disabled={isLoading}
            >
              {templateOptions.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {formData.template && TEMPLATE_PRESETS[formData.template] && (
              <p className="text-sm text-gray-500 mt-1">
                {TEMPLATE_PRESETS[formData.template].description}
              </p>
            )}
          </div>

          {/* Toggle to show/hide Pokemon pool customization */}
          <button
            type="button"
            onClick={() => setShowPokemonPool(!showPokemonPool)}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mb-4"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showPokemonPool ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {showPokemonPool ? 'Hide' : 'Show'} Pokemon Pool Customization
          </button>

          {showPokemonPool && (
            <div className="space-y-4">
              {/* Filters */}
              <PokemonFiltersComponent
                filters={filters}
                onChange={setFilters}
              />

              {/* Pokemon Box */}
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Pokemon Pool Preview</h3>
                <PokemonBox
                  pokemon={allPokemon}
                  filters={filters}
                  onToggleExclusion={handleToggleExclusion}
                  isLoading={isLoadingPokemon}
                  showPoints={formData.format !== 'auction' && formData.budgetEnabled}
                  pokemonPoints={pokemonPoints}
                  onPointChange={handlePointChange}
                  editablePoints={formData.format !== 'auction' && formData.budgetEnabled && pointsEditMode}
                />
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary w-full py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Creating Draft...
            </span>
          ) : (
            'Create Draft'
          )}
        </button>
      </form>
    </div>
  )
}
