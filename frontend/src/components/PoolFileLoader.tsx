import { useRef, useState } from 'react'
import { PokemonBoxEntry, PokemonFilters } from '../types'
import { generatePoolCsv, parsePoolCsv, downloadFile } from '../utils/csvUtils'

interface PoolFileLoaderProps {
  pokemon: PokemonBoxEntry[]
  filters: PokemonFilters
  loadedPoolIds: number[]
  onPoolLoad: (ids: number[]) => void
  onClear: () => void
}

export default function PoolFileLoader({
  pokemon,
  filters,
  loadedPoolIds,
  onPoolLoad,
  onClear,
}: PoolFileLoaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadWarnings, setUploadWarnings] = useState<string[]>([])
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)

  const handleDownloadCsv = () => {
    const csv = generatePoolCsv(pokemon, filters)
    const timestamp = new Date().toISOString().slice(0, 10)
    downloadFile(csv, `pokemon_pool_${timestamp}.csv`)
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
      const { pokemonIds, errors, warnings } = parsePoolCsv(content)

      if (errors.length > 0) {
        setUploadError(errors.join('\n'))
        return
      }

      if (warnings.length > 0) {
        setUploadWarnings(warnings)
      }

      if (pokemonIds.length === 0) {
        setUploadError('No valid Pokemon IDs found in the CSV file')
        return
      }

      // Validate that the IDs exist in our pokemon list
      const validIds = pokemonIds.filter(id => pokemon.some(p => p.id === id))
      const invalidCount = pokemonIds.length - validIds.length

      if (invalidCount > 0) {
        setUploadWarnings(prev => [...prev, `${invalidCount} Pokemon ID(s) not found in database and were skipped`])
      }

      onPoolLoad(validIds)
      setUploadSuccess(`Successfully loaded ${validIds.length} Pokemon into the pool`)
    } catch (err) {
      setUploadError('Failed to read CSV file')
    }

    // Reset file input so same file can be selected again
    e.target.value = ''
  }

  const handleClear = () => {
    if (confirm('Are you sure you want to clear the loaded pool?')) {
      onClear()
      setUploadSuccess(null)
      setUploadWarnings([])
      setUploadError(null)
    }
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-blue-800">Load Pool from File</h3>
          <p className="text-sm text-blue-700 mt-1">
            Upload a CSV file containing the Pokemon IDs you want in your draft pool.
            The CSV must have an "id" column. Download a template to get started.
          </p>
        </div>
      </div>

      {/* Status */}
      {loadedPoolIds.length > 0 && (
        <div className="flex items-center gap-2 text-sm">
          <span className="font-semibold text-green-600">{loadedPoolIds.length}</span>
          <span className="text-gray-600">Pokemon loaded in pool</span>
        </div>
      )}

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

        {loadedPoolIds.length > 0 && (
          <button
            type="button"
            onClick={handleClear}
            className="btn btn-secondary text-sm text-red-600 hover:text-red-700"
          >
            Clear Pool
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
        <p><strong>CSV Format:</strong> Download the template, remove rows for Pokemon you don't want, then upload.</p>
        <p><strong>Tip:</strong> The template includes all Pokemon matching your current filters. Edit to customize.</p>
      </div>
    </div>
  )
}
