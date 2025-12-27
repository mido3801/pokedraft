/**
 * Centralized React Query key constants.
 * Using factory functions ensures type safety and consistency across the app.
 */

export const queryKeys = {
  // Leagues
  leagues: ['leagues'] as const,
  league: (leagueId: string) => ['league', leagueId] as const,
  leagueSeasons: (leagueId: string) => ['league-seasons', leagueId] as const,

  // Seasons
  season: (seasonId: string) => ['season', seasonId] as const,
  seasonTeams: (seasonId: string) => ['season-teams', seasonId] as const,
  seasonStandings: (seasonId: string) => ['season-standings', seasonId] as const,
  seasonSchedule: (seasonId: string) => ['season-schedule', seasonId] as const,
  seasonBracket: (seasonId: string) => ['season-bracket', seasonId] as const,
  seasonTrades: (seasonId: string) => ['season-trades', seasonId] as const,

  // Drafts
  myDrafts: ['my-drafts'] as const,

  // Presets
  presets: ['presets'] as const,
  preset: (presetId: string) => ['preset', presetId] as const,
} as const

// Type helper for query key values
export type QueryKeys = typeof queryKeys
