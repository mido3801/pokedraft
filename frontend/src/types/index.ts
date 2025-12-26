// User types
export interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  discord_id?: string
  discord_username?: string
  is_active: boolean
  created_at: string
}

// League types
export interface League {
  id: string
  name: string
  owner_id: string
  invite_code: string
  is_public: boolean
  description?: string
  settings: LeagueSettings
  created_at: string
  member_count?: number
  current_season?: number
}

export interface LeagueSettings {
  draft_format: DraftFormat
  roster_size: number
  timer_seconds: number
  budget_enabled: boolean
  budget_per_team?: number
  trade_approval_required: boolean
}

// Season types
export type SeasonStatus = 'pre_draft' | 'drafting' | 'active' | 'completed'

export interface Season {
  id: string
  league_id: string
  season_number: number
  status: SeasonStatus
  keep_teams: boolean
  settings: Record<string, unknown>
  started_at?: string
  completed_at?: string
  created_at: string
  team_count?: number
}

// Draft types
export type DraftFormat = 'snake' | 'linear' | 'auction'
export type DraftStatus = 'pending' | 'live' | 'paused' | 'completed'

export interface Draft {
  id: string
  season_id?: string
  rejoin_code?: string
  format: DraftFormat
  timer_seconds?: number
  budget_enabled: boolean
  budget_per_team?: number
  roster_size: number
  status: DraftStatus
  current_pick: number
  pokemon_pool: Record<string, unknown>
  pick_order: string[]
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface DraftState {
  draft_id: string
  status: DraftStatus
  format: DraftFormat
  current_pick: number
  roster_size: number
  timer_seconds?: number
  timer_end?: string
  pick_order: string[]
  teams: DraftTeam[]
  picks: DraftPick[]
  available_pokemon: Pokemon[]
  budget_enabled: boolean
  budget_per_team?: number
}

export interface DraftTeam {
  team_id: string
  display_name: string
  draft_position: number
  budget_remaining?: number
  pokemon: number[]
}

export interface DraftPick {
  pick_number: number
  team_id: string
  team_name: string
  pokemon_id: number
  pokemon_name: string
  points_spent?: number
  picked_at: string
}

// Team types
export type AcquisitionType = 'drafted' | 'traded' | 'free_agent'

export interface Team {
  id: string
  season_id?: string
  user_id?: string
  display_name: string
  draft_position?: number
  budget_remaining?: number
  wins: number
  losses: number
  ties: number
  created_at: string
  pokemon: TeamPokemon[]
}

export interface TeamPokemon {
  id: string
  pokemon_id: number
  pokemon_name: string
  pick_number?: number
  acquisition_type: AcquisitionType
  points_spent?: number
  acquired_at: string
  types: string[]
  sprite_url?: string
}

// Pokemon types
export interface Pokemon {
  id: number
  name: string
  types: string[]
  sprite?: string
  points?: number
  generation?: number
  stats?: PokemonStats
  abilities?: string[]
  is_legendary?: boolean
  is_mythical?: boolean
}

export interface PokemonStats {
  hp: number
  attack: number
  defense: number
  'special-attack': number
  'special-defense': number
  speed: number
}

// Match types
export interface Match {
  id: string
  season_id: string
  week: number
  team_a_id: string
  team_b_id: string
  team_a_name?: string
  team_b_name?: string
  scheduled_at?: string
  winner_id?: string
  winner_name?: string
  is_tie: boolean
  replay_url?: string
  notes?: string
  recorded_at?: string
  created_at: string
}

export interface Standings {
  season_id: string
  standings: TeamStanding[]
}

export interface TeamStanding {
  team_id: string
  team_name: string
  wins: number
  losses: number
  ties: number
  points: number
  games_played: number
}

// Trade types
export type TradeStatus = 'pending' | 'accepted' | 'rejected' | 'cancelled'

export interface Trade {
  id: string
  season_id: string
  proposer_team_id: string
  recipient_team_id: string
  proposer_team_name?: string
  recipient_team_name?: string
  proposer_pokemon: string[]
  recipient_pokemon: string[]
  status: TradeStatus
  requires_approval: boolean
  admin_approved?: boolean
  message?: string
  created_at: string
  resolved_at?: string
}

// WebSocket event types
export type WebSocketEvent =
  | { event: 'draft_state'; data: DraftState }
  | { event: 'pick_made'; data: { team_id: string; pokemon_id: number; pick_number: number } }
  | { event: 'turn_start'; data: { team_id: string; timer_end: string } }
  | { event: 'timer_tick'; data: { seconds_remaining: number } }
  | { event: 'bid_update'; data: { pokemon_id: number; bidder_id: string; amount: number } }
  | { event: 'draft_complete'; data: { final_teams: DraftTeam[] } }
  | { event: 'user_joined'; data: { user_id: string; display_name: string } }
  | { event: 'user_left'; data: { user_id: string } }
  | { event: 'error'; data: { message: string; code: string } }
