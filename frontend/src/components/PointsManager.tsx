import { useRef, useState, useMemo } from 'react'
import { PokemonBoxEntry, PokemonFilters, PokemonPointsMap } from '../types'
import { generatePointsCsv, parsePointsCsv, downloadFile } from '../utils/csvUtils'

interface PointsManagerProps {
  pokemon: PokemonBoxEntry[]
  filters: PokemonFilters
  pokemonPoints: PokemonPointsMap
  onPointsChange: (points: PokemonPointsMap) => void
  editMode: boolean
  onEditModeChange: (enabled: boolean) => void
}

// Check if a Pokemon passes filters (same logic as PokemonBox)
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

export default function PointsManager({
  pokemon,
  filters,
  pokemonPoints,
  onPointsChange,
  editMode,
  onEditModeChange,
}: PointsManagerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadWarnings, setUploadWarnings] = useState<string[]>([])
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)

  // Calculate stats
  const stats = useMemo(() => {
    const filteredPokemon = pokemon.filter(p => pokemonPassesFilters(p, filters))
    const withPoints = filteredPokemon.filter(p => pokemonPoints[p.id] !== undefined)
    const withoutPoints = filteredPokemon.length - withPoints.length

    return {
      total: filteredPokemon.length,
      withPoints: withPoints.length,
      withoutPoints,
    }
  }, [pokemon, filters, pokemonPoints])

  const handleDownloadCsv = () => {
    const csv = generatePointsCsv(pokemon, filters, pokemonPoints)
    const timestamp = new Date().toISOString().slice(0, 10)
    downloadFile(csv, `pokemon_points_${timestamp}.csv`)
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Reset states
    setUploadError(null)
    setUploadWarnings([])
    setUploadSuccess(null)

    try {
      const content = await file.text()
      const { points, errors, warnings } = parsePointsCsv(content)

      if (errors.length > 0) {
        setUploadError(errors.join('\n'))
        return
      }

      if (warnings.length > 0) {
        setUploadWarnings(warnings)
      }

      // Merge with existing points (new values override)
      const mergedPoints = { ...pokemonPoints, ...points }
      onPointsChange(mergedPoints)

      const count = Object.keys(points).length
      setUploadSuccess(`Successfully imported point values for ${count} Pokemon`)
    } catch (err) {
      setUploadError('Failed to read CSV file')
    }

    // Reset file input so same file can be selected again
    e.target.value = ''
  }

  const handleClearPoints = () => {
    if (confirm('Are you sure you want to clear all point values?')) {
      onPointsChange({})
      setUploadSuccess(null)
      setUploadWarnings([])
    }
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-amber-800">Point Values Required</h3>
          <p className="text-sm text-amber-700 mt-1">
            With point cap enabled, each Pokemon needs a point cost assigned. Teams can only draft Pokemon
            whose total points don't exceed their budget. Pokemon without assigned points will be excluded.
          </p>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-700">
          <span className={stats.withPoints > 0 ? 'font-semibold text-green-600' : 'text-gray-500'}>
            {stats.withPoints}
          </span>
          <span className="text-gray-400"> / </span>
          <span>{stats.total}</span>
          <span className="text-gray-500 ml-1">Pokémon have point values</span>
        </span>
        {stats.withoutPoints > 0 && (
          <span className="text-amber-600 font-medium">
            {stats.withoutPoints} will be excluded
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleDownloadCsv}
          className="btn btn-secondary text-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download CSV Template
        </button>

        <button
          type="button"
          onClick={handleUploadClick}
          className="btn btn-secondary text-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload CSV
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />

        <button
          type="button"
          onClick={() => onEditModeChange(!editMode)}
          className={`btn text-sm flex items-center gap-2 ${
            editMode ? 'btn-primary' : 'btn-secondary'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          {editMode ? 'Editing Points' : 'Edit Points Inline'}
        </button>

        {Object.keys(pokemonPoints).length > 0 && (
          <button
            type="button"
            onClick={handleClearPoints}
            className="btn btn-secondary text-sm text-red-600 hover:text-red-700"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Error/Warning/Success messages */}
      {uploadError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          <p className="font-medium">Error uploading CSV:</p>
          <p className="mt-1 whitespace-pre-line">{uploadError}</p>
        </div>
      )}

      {uploadWarnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          <p className="font-medium">Warnings ({uploadWarnings.length}):</p>
          <ul className="mt-1 list-disc list-inside max-h-24 overflow-y-auto">
            {uploadWarnings.slice(0, 10).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
            {uploadWarnings.length > 10 && (
              <li>...and {uploadWarnings.length - 10} more</li>
            )}
          </ul>
        </div>
      )}

      {uploadSuccess && (
        <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-700">
          {uploadSuccess}
        </div>
      )}

      {/* Instructions */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>CSV Format:</strong> Download the template, fill in the "points" column, then upload.</p>
        <p><strong>Inline Editing:</strong> Click on a Pokémon in the grid below to set its point value.</p>
      </div>
    </div>
  )
}
