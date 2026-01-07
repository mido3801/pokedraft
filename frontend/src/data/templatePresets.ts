import { PokemonFilters, DEFAULT_POKEMON_FILTERS } from '../types'

export interface TemplatePreset {
  id: string
  name: string
  description: string
  filters: Partial<PokemonFilters>
  // Draft settings that may be overridden
  rosterSize?: number
  budgetEnabled?: boolean
  budgetPerTeam?: number
}

export const TEMPLATE_PRESETS: Record<string, TemplatePreset> = {
  '': {
    id: '',
    name: 'All Pokemon',
    description: 'Include all Pokemon from all generations',
    filters: {},
  },
  little_cup: {
    id: 'little_cup',
    name: 'Little Cup',
    description: 'Unevolved Pokemon only (first stage)',
    filters: {
      evolution_stages: [0], // Unevolved only
      include_legendary: false,
      include_mythical: false,
      bst_max: 500, // LC typically has BST limits
    },
  },
}

// Helper to apply a template's filters to the default filters
export function applyTemplate(templateId: string): PokemonFilters {
  const template = TEMPLATE_PRESETS[templateId]
  if (!template) {
    return { ...DEFAULT_POKEMON_FILTERS }
  }
  return {
    ...DEFAULT_POKEMON_FILTERS,
    ...template.filters,
  }
}

// Helper to get template list for dropdown
export function getTemplateOptions(): Array<{ value: string; label: string; description: string }> {
  return Object.values(TEMPLATE_PRESETS).map(t => ({
    value: t.id,
    label: t.name,
    description: t.description,
  }))
}
