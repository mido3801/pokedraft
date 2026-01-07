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
  // Waiver wire settings
  waiver_enabled?: boolean
  waiver_approval_type?: WaiverApprovalType
  waiver_processing_type?: WaiverProcessingType
  waiver_max_per_week?: number
  waiver_require_drop?: boolean
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
  // Auction-specific settings
  nomination_timer_seconds?: number
  bid_timer_seconds?: number
  min_bid?: number
  bid_increment?: number
}

export interface DraftSummary {
  id: string
  season_id?: string
  rejoin_code?: string
  format: DraftFormat
  status: DraftStatus
  roster_size: number
  team_count: number
  created_at: string
  started_at?: string
  completed_at?: string
  expires_at?: string
}

export interface DraftState {
  draft_id: string
  rejoin_code?: string
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
  // Auction-specific settings
  nomination_timer_seconds?: number
  bid_timer_seconds?: number
  min_bid?: number
  bid_increment?: number
  // Auction state (populated during auction)
  auction_phase?: 'nominating' | 'bidding' | 'idle'
  current_nomination?: {
    pokemon_id: number
    pokemon_name: string
    nominator_id: string
    nominator_name: string
  }
  current_highest_bid?: {
    team_id: string
    team_name: string
    amount: number
  }
  bid_timer_end?: string
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
  bst?: number
  evolution_stage?: number // 0=unevolved, 1=middle, 2=fully evolved
}

export interface PokemonStats {
  hp: number
  attack: number
  defense: number
  'special-attack': number
  'special-defense': number
  speed: number
}

// Pokemon box display (optimized data)
export interface PokemonBoxEntry {
  id: number
  name: string
  sprite: string
  types: string[]
  generation: number
  bst: number
  evolution_stage: number // 0=unevolved, 1=middle, 2=fully evolved
  is_legendary: boolean
  is_mythical: boolean
}

// Point values map (pokemon_id -> points)
export type PokemonPointsMap = Record<number, number>

export interface PokemonBoxResponse {
  pokemon: PokemonBoxEntry[]
  total: number
}

// Pokemon filters for draft creation
export interface PokemonFilters {
  generations: number[]
  evolution_stages: number[]
  include_legendary: boolean
  include_mythical: boolean
  types: string[]
  bst_min: number
  bst_max: number
  custom_exclusions: number[]
  custom_inclusions: number[]
}

// Default filters (all Pokemon included)
export const DEFAULT_POKEMON_FILTERS: PokemonFilters = {
  generations: [1, 2, 3, 4, 5, 6, 7, 8, 9],
  evolution_stages: [0, 1, 2],
  include_legendary: true,
  include_mythical: true,
  types: [],
  bst_min: 0,
  bst_max: 999,
  custom_exclusions: [],
  custom_inclusions: [],
}

// Pokemon type colors
export const TYPE_COLORS: Record<string, string> = {
  normal: '#A8A878',
  fire: '#F08030',
  water: '#6890F0',
  electric: '#F8D030',
  grass: '#78C850',
  ice: '#98D8D8',
  fighting: '#C03028',
  poison: '#A040A0',
  ground: '#E0C068',
  flying: '#A890F0',
  psychic: '#F85888',
  bug: '#A8B820',
  rock: '#B8A038',
  ghost: '#705898',
  dragon: '#7038F8',
  dark: '#705848',
  steel: '#B8B8D0',
  fairy: '#EE99AC',
}

// Match types
export type ScheduleFormat = 'round_robin' | 'double_round_robin' | 'single_elimination' | 'double_elimination'

export interface Match {
  id: string
  season_id: string
  week: number
  team_a_id?: string
  team_b_id?: string
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
  // Bracket-specific fields
  schedule_format?: ScheduleFormat
  bracket_round?: number
  bracket_position?: number
  next_match_id?: string
  loser_next_match_id?: string
  seed_a?: number
  seed_b?: number
  is_bye: boolean
  is_bracket_reset: boolean
  round_name?: string
}

export interface BracketState {
  season_id: string
  format: 'single_elimination' | 'double_elimination'
  team_count: number
  total_rounds: number
  winners_bracket: Match[][] // [round][matches in round]
  losers_bracket?: Match[][] // For double elim
  grand_finals?: Match[] // For double elim (may have 2 matches)
  champion_id?: string
  champion_name?: string
}

export type SeedingMode = 'standings' | 'manual' | 'random'

export interface GenerateScheduleParams {
  format: ScheduleFormat
  use_standings_seeding?: boolean
  manual_seeds?: string[] // Team IDs in seed order
  include_bracket_reset?: boolean
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
  // Extended details from response builder
  proposer_pokemon_details?: TradePokemonDetail[]
  recipient_pokemon_details?: TradePokemonDetail[]
}

export interface TradePokemonDetail {
  id: string
  pokemon_id: number
  name: string
  types: string[]
}

// Trade WebSocket event types
export type TradeWebSocketEvent =
  | { event: 'trade_proposed'; data: { trade: Trade } }
  | { event: 'trade_accepted'; data: { trade_id: string; requires_approval: boolean; trade?: Trade } }
  | { event: 'trade_rejected'; data: { trade_id: string } }
  | { event: 'trade_cancelled'; data: { trade_id: string } }
  | { event: 'trade_approved'; data: { trade_id: string; trade: Trade } }
  | { event: 'error'; data: { message: string; code: string } }

// WebSocket event types
export type WebSocketEvent =
  | { event: 'draft_state'; data: DraftState }
  | { event: 'pick_made'; data: { team_id: string; pokemon_id: number; pick_number: number; points_spent?: number } }
  | { event: 'turn_start'; data: { team_id: string; timer_end?: string; phase?: string } }
  | { event: 'timer_tick'; data: { seconds_remaining: number } }
  | { event: 'bid_update'; data: { pokemon_id: number; bidder_id: string; bidder_name: string; amount: number; bid_timer_end: string } }
  | { event: 'nomination'; data: { pokemon_id: number; pokemon_name: string; nominator_id: string; nominator_name: string; min_bid: number; current_bid: number; current_bidder_id: string; current_bidder_name: string; bid_timer_end: string } }
  | { event: 'draft_complete'; data: { final_teams: DraftTeam[] } }
  | { event: 'draft_started'; data: { status: string; pick_order: string[]; current_team_id: string; current_team_name: string; timer_end?: string } }
  | { event: 'user_joined'; data: { team_id: string; display_name: string } }
  | { event: 'user_left'; data: { team_id: string; display_name: string } }
  | { event: 'error'; data: { message: string; code: string } }

// Pool Preset types
export interface PoolPreset {
  id: string
  user_id: string
  name: string
  description?: string
  pokemon_pool: Record<string, PokemonPoolEntry>
  pokemon_filters?: PokemonFilters
  pokemon_count: number
  is_public: boolean
  created_at: string
  updated_at: string
  creator_name?: string
}

export interface PoolPresetSummary {
  id: string
  user_id: string
  name: string
  description?: string
  pokemon_count: number
  is_public: boolean
  has_filters: boolean
  created_at: string
  creator_name?: string
}

export interface CreatePresetParams {
  name: string
  description?: string
  pokemon_pool: Record<string, unknown>
  pokemon_filters?: PokemonFilters
  is_public: boolean
}

export interface UpdatePresetParams {
  name?: string
  description?: string
  pokemon_pool?: Record<string, unknown>
  pokemon_filters?: PokemonFilters
  is_public?: boolean
}

// Pokemon pool entry stored in presets
export interface PokemonPoolEntry {
  name: string
  points: number | null
  types: string[]
  generation?: number
  bst?: number
  evolution_stage?: number
  is_legendary?: boolean
  is_mythical?: boolean
}

// Waiver Wire / Free Agent types
export type WaiverClaimStatus = 'pending' | 'approved' | 'rejected' | 'cancelled' | 'expired'
export type WaiverProcessingType = 'immediate' | 'next_week'
export type WaiverApprovalType = 'none' | 'admin' | 'league_vote'

export interface WaiverClaim {
  id: string
  season_id: string
  team_id: string
  team_name?: string
  pokemon_id: number
  drop_pokemon_id?: string
  pokemon_name?: string
  pokemon_types?: string[]
  pokemon_sprite?: string
  drop_pokemon_name?: string
  drop_pokemon_types?: string[]
  status: WaiverClaimStatus
  priority: number
  requires_approval: boolean
  admin_approved?: boolean
  admin_notes?: string
  votes_for: number
  votes_against: number
  votes_required?: number
  processing_type: WaiverProcessingType
  process_after?: string
  week_number?: number
  created_at: string
  resolved_at?: string
}

export interface WaiverClaimList {
  claims: WaiverClaim[]
  total: number
  pending_count: number
}

export interface FreeAgentPokemon {
  pokemon_id: number
  name: string
  types: string[]
  sprite?: string
  base_stat_total?: number
  generation?: number
}

export interface FreeAgentList {
  pokemon: FreeAgentPokemon[]
  total: number
}

export interface WaiverVote {
  id: string
  waiver_claim_id: string
  user_id: string
  vote: boolean
  created_at: string
}

// Waiver WebSocket event types
export type WaiverWebSocketEvent =
  | { event: 'waiver_claim_created'; data: { claim: WaiverClaim } }
  | { event: 'waiver_claim_cancelled'; data: { claim_id: string } }
  | { event: 'waiver_claim_approved'; data: { claim: WaiverClaim } }
  | { event: 'waiver_claim_rejected'; data: { claim: WaiverClaim } }
  | { event: 'waiver_vote_cast'; data: { claim_id: string; votes_for: number; votes_against: number } }
  | { event: 'error'; data: { message: string; code: string } }

// Extended league settings with waiver options
export interface WaiverSettings {
  waiver_enabled: boolean
  waiver_approval_type: WaiverApprovalType
  waiver_processing_type: WaiverProcessingType
  waiver_max_per_week?: number
  waiver_require_drop: boolean
}
