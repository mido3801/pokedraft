import { PokemonBoxEntry, PokemonFilters } from '../types'

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

/**
 * Generate a CSV template for assigning point values to Pokemon
 */
export function generatePointsCsv(
  pokemon: PokemonBoxEntry[],
  filters: PokemonFilters,
  existingPoints: Record<number, number>
): string {
  const headers = ['id', 'name', 'types', 'generation', 'bst', 'is_legendary', 'is_mythical', 'points']

  const rows = pokemon
    .filter(p => pokemonPassesFilters(p, filters))
    .sort((a, b) => a.id - b.id)
    .map(p => {
      const points = existingPoints[p.id] !== undefined ? existingPoints[p.id].toString() : ''
      return [
        p.id.toString(),
        p.name,
        `"${p.types.join(',')}"`,
        p.generation.toString(),
        p.bst.toString(),
        p.is_legendary.toString(),
        p.is_mythical.toString(),
        points
      ].join(',')
    })

  return [headers.join(','), ...rows].join('\n')
}

/**
 * Parse a CSV file and extract point values for each Pokemon ID
 */
export function parsePointsCsv(
  csvContent: string
): { points: Record<number, number>, errors: string[], warnings: string[] } {
  const points: Record<number, number> = {}
  const errors: string[] = []
  const warnings: string[] = []

  const lines = csvContent.trim().split('\n')
  if (lines.length < 2) {
    errors.push('CSV file is empty or missing data rows')
    return { points, errors, warnings }
  }

  // Parse header to find column indices
  const header = lines[0].toLowerCase().split(',').map(h => h.trim().replace(/"/g, ''))
  const idIndex = header.indexOf('id')
  const pointsIndex = header.indexOf('points')

  if (idIndex === -1) {
    errors.push('CSV must have an "id" column')
    return { points, errors, warnings }
  }
  if (pointsIndex === -1) {
    errors.push('CSV must have a "points" column')
    return { points, errors, warnings }
  }

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    // Simple CSV parsing (handles quoted fields)
    const values: string[] = []
    let current = ''
    let inQuotes = false

    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    values.push(current.trim())

    const idStr = values[idIndex]?.replace(/"/g, '')
    const pointsStr = values[pointsIndex]?.replace(/"/g, '')

    const pokemonId = parseInt(idStr, 10)
    if (isNaN(pokemonId) || pokemonId <= 0) {
      warnings.push(`Row ${i + 1}: Invalid Pokemon ID "${idStr}"`)
      continue
    }

    // Empty points = no value assigned (skip)
    if (!pointsStr || pointsStr === '') {
      continue
    }

    const pointsValue = parseInt(pointsStr, 10)
    if (isNaN(pointsValue)) {
      warnings.push(`Row ${i + 1}: Invalid points value "${pointsStr}" for Pokemon #${pokemonId}`)
      continue
    }

    if (pointsValue < 0) {
      errors.push(`Row ${i + 1}: Negative points value (${pointsValue}) not allowed for Pokemon #${pokemonId}`)
      continue
    }

    points[pokemonId] = pointsValue
  }

  return { points, errors, warnings }
}

/**
 * Generate a CSV template for defining a Pokemon pool (without points)
 */
export function generatePoolCsv(
  pokemon: PokemonBoxEntry[],
  filters: PokemonFilters
): string {
  const headers = ['id', 'name', 'types', 'generation', 'bst', 'is_legendary', 'is_mythical']

  const rows = pokemon
    .filter(p => pokemonPassesFilters(p, filters))
    .sort((a, b) => a.id - b.id)
    .map(p => {
      return [
        p.id.toString(),
        p.name,
        `"${p.types.join(',')}"`,
        p.generation.toString(),
        p.bst.toString(),
        p.is_legendary.toString(),
        p.is_mythical.toString(),
      ].join(',')
    })

  return [headers.join(','), ...rows].join('\n')
}

/**
 * Parse a CSV file and extract Pokemon IDs for the pool (no points required)
 */
export function parsePoolCsv(
  csvContent: string
): { pokemonIds: number[], errors: string[], warnings: string[] } {
  const pokemonIds: number[] = []
  const errors: string[] = []
  const warnings: string[] = []

  const lines = csvContent.trim().split('\n')
  if (lines.length < 2) {
    errors.push('CSV file is empty or missing data rows')
    return { pokemonIds, errors, warnings }
  }

  // Parse header to find column indices
  const header = lines[0].toLowerCase().split(',').map(h => h.trim().replace(/"/g, ''))
  const idIndex = header.indexOf('id')

  if (idIndex === -1) {
    errors.push('CSV must have an "id" column')
    return { pokemonIds, errors, warnings }
  }

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    // Simple CSV parsing (handles quoted fields)
    const values: string[] = []
    let current = ''
    let inQuotes = false

    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    values.push(current.trim())

    const idStr = values[idIndex]?.replace(/"/g, '')
    const pokemonId = parseInt(idStr, 10)

    if (isNaN(pokemonId) || pokemonId <= 0) {
      warnings.push(`Row ${i + 1}: Invalid Pokemon ID "${idStr}"`)
      continue
    }

    if (!pokemonIds.includes(pokemonId)) {
      pokemonIds.push(pokemonId)
    }
  }

  return { pokemonIds, errors, warnings }
}

/**
 * Download content as a file
 */
export function downloadFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
