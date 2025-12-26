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
  ou: {
    id: 'ou',
    name: 'OU (OverUsed)',
    description: 'Standard competitive format with all fully evolved Pokemon',
    filters: {
      evolution_stages: [2], // Fully evolved only
    },
  },
  uu: {
    id: 'uu',
    name: 'UU (UnderUsed)',
    description: 'Lower tier competitive format, excludes legendaries',
    filters: {
      evolution_stages: [2],
      include_legendary: false,
      include_mythical: false,
    },
  },
  monotype: {
    id: 'monotype',
    name: 'Monotype',
    description: 'All Pokemon, typically used with type restrictions',
    filters: {
      // No specific filters - type selection is usually done per-team
    },
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
  draft_league: {
    id: 'draft_league',
    name: 'Draft League',
    description: 'Standard draft league format with point values',
    filters: {
      evolution_stages: [2],
    },
    rosterSize: 11,
    budgetEnabled: true,
    budgetPerTeam: 100,
  },
  nfe: {
    id: 'nfe',
    name: 'NFE (Not Fully Evolved)',
    description: 'Pokemon that can still evolve',
    filters: {
      evolution_stages: [0, 1], // Unevolved and middle stage
      include_legendary: false,
      include_mythical: false,
    },
  },
  gen1: {
    id: 'gen1',
    name: 'Gen 1 Only',
    description: 'Kanto Pokemon only (Generation 1)',
    filters: {
      generations: [1],
    },
  },
  gen1to3: {
    id: 'gen1to3',
    name: 'Gens 1-3',
    description: 'Classic Pokemon (Kanto, Johto, Hoenn)',
    filters: {
      generations: [1, 2, 3],
    },
  },
  no_legends: {
    id: 'no_legends',
    name: 'No Legendaries',
    description: 'All Pokemon except Legendaries and Mythicals',
    filters: {
      include_legendary: false,
      include_mythical: false,
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
