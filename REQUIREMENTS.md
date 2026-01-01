# PokeDraft System Requirements Specification

**Version:** 1.0
**Date:** 2025-12-31
**Document Type:** Software Requirements Specification (NCOSE Standard)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional, non-functional, interface, and data requirements for the PokeDraft system - a web-based platform for managing Pokemon competitive draft leagues with real-time collaboration features.

### 1.2 Scope
PokeDraft provides users with capabilities to create and participate in Pokemon drafts, manage multi-season leagues, schedule matches, execute trades, and export teams for competitive play. The system supports both authenticated league play and anonymous quick drafts.

### 1.3 Document Conventions
- Requirements are uniquely identified with the format: `[TYPE]-[SUBSYSTEM]-[NUMBER]`
- Types: FR (Functional), NFR (Non-Functional), IR (Interface), DR (Data)
- Subsystems: AUTH, LEAGUE, SEASON, DRAFT, TEAM, TRADE, MATCH, POKE, UI, SYS
- Requirements use "shall" for mandatory capabilities

---

## 2. Functional Requirements

### 2.1 Authentication and User Management (AUTH)

**FR-AUTH-001:** The system shall support passwordless email magic link authentication via Supabase.

**FR-AUTH-002:** The system shall support Discord OAuth authentication for user login.

**FR-AUTH-003:** The system shall provide a development mode with quick login capability for four test users.

**FR-AUTH-004:** The system shall allow users to update their display name and avatar URL.

**FR-AUTH-005:** The system shall optionally link user accounts to Discord accounts for notification integration.

**FR-AUTH-006:** The system shall verify JWT tokens using ES256 algorithm for Supabase OAuth tokens.

**FR-AUTH-007:** The system shall verify JWT tokens using HS256 algorithm for development mode tokens.

**FR-AUTH-008:** The system shall automatically create user records from token metadata on first login.

**FR-AUTH-009:** The system shall maintain user sessions with automatic token refresh.

**FR-AUTH-010:** The system shall allow anonymous users to create and participate in drafts without authentication.

**FR-AUTH-011:** The system shall generate and validate session tokens for anonymous draft participants.

**FR-AUTH-012:** The system shall retrieve authenticated user information via API endpoint.

---

### 2.2 League Management (LEAGUE)

**FR-LEAGUE-001:** The system shall allow authenticated users to create new leagues with custom settings.

**FR-LEAGUE-002:** The system shall generate unique invite codes for each league upon creation.

**FR-LEAGUE-003:** The system shall allow users to join leagues using invite codes.

**FR-LEAGUE-004:** The system shall allow users to join leagues via shareable invite links.

**FR-LEAGUE-005:** The system shall designate the creator as the league owner.

**FR-LEAGUE-006:** The system shall allow league owners to update league settings.

**FR-LEAGUE-007:** The system shall allow league owners to regenerate invite codes.

**FR-LEAGUE-008:** The system shall allow league owners to remove members from the league.

**FR-LEAGUE-009:** The system shall allow non-owner members to leave a league.

**FR-LEAGUE-010:** The system shall list all leagues for which a user is a member.

**FR-LEAGUE-011:** The system shall display league details including name, member count, and current season.

**FR-LEAGUE-012:** The system shall store league settings in JSONB format for flexibility.

**FR-LEAGUE-013:** The system shall track league membership status (active/inactive).

**FR-LEAGUE-014:** The system shall allow league owners to configure default draft format settings.

**FR-LEAGUE-015:** The system shall allow league owners to configure trade approval requirements.

---

### 2.3 Season Management (SEASON)

**FR-SEASON-001:** The system shall allow league owners to create new seasons within a league.

**FR-SEASON-002:** The system shall track season status through states: pre_draft, drafting, active, completed.

**FR-SEASON-003:** The system shall automatically transition season status from pre_draft to drafting when a draft starts.

**FR-SEASON-004:** The system shall automatically transition season status from drafting to active when a draft completes.

**FR-SEASON-005:** The system shall allow league owners to manually update season settings.

**FR-SEASON-006:** The system shall list all seasons for a given league.

**FR-SEASON-007:** The system shall display season details including status and team count.

**FR-SEASON-008:** The system shall support multiple concurrent seasons per league.

**FR-SEASON-009:** The system shall store season-specific settings in JSONB format.

---

### 2.4 Draft Management (DRAFT)

#### 2.4.1 Draft Creation

**FR-DRAFT-001:** The system shall allow authenticated users to create league drafts tied to seasons.

**FR-DRAFT-002:** The system shall allow any user to create anonymous drafts without authentication.

**FR-DRAFT-003:** The system shall support three draft formats: snake, linear, and auction.

**FR-DRAFT-004:** The system shall allow draft creators to specify roster size (1-20 Pokemon per team).

**FR-DRAFT-005:** The system shall allow draft creators to configure timer duration per pick (30-600 seconds).

**FR-DRAFT-006:** The system shall allow draft creators to enable budget/point cap mode.

**FR-DRAFT-007:** The system shall allow draft creators to customize the Pokemon pool with filters.

**FR-DRAFT-008:** The system shall allow draft creators to assign point values to individual Pokemon.

**FR-DRAFT-009:** The system shall automatically create teams for all league members when creating a league draft.

**FR-DRAFT-010:** The system shall generate memorable rejoin codes for anonymous drafts (format: WORD-NNNN).

**FR-DRAFT-011:** The system shall allow users to join anonymous drafts using rejoin codes.

**FR-DRAFT-012:** The system shall limit users to a maximum of 3 pending anonymous drafts.

**FR-DRAFT-013:** The system shall expire pending anonymous drafts after 24 hours.

**FR-DRAFT-014:** The system shall store Pokemon pool configuration in JSONB format.

#### 2.4.2 Draft Execution

**FR-DRAFT-015:** The system shall allow draft creators to start pending drafts.

**FR-DRAFT-016:** The system shall validate that all teams are present before starting a draft.

**FR-DRAFT-017:** The system shall determine initial pick order based on draft format.

**FR-DRAFT-018:** The system shall reverse pick order each round for snake drafts.

**FR-DRAFT-019:** The system shall maintain consistent pick order for linear drafts.

**FR-DRAFT-020:** The system shall enforce turn-based picking where only the current team can select Pokemon.

**FR-DRAFT-021:** The system shall validate that selected Pokemon are available in the pool.

**FR-DRAFT-022:** The system shall validate that selected Pokemon have not been previously picked.

**FR-DRAFT-023:** The system shall validate budget constraints when point cap mode is enabled.

**FR-DRAFT-024:** The system shall record each pick with team ID, Pokemon ID, pick number, and points spent.

**FR-DRAFT-025:** The system shall advance to the next team after a valid pick is made.

**FR-DRAFT-026:** The system shall track remaining budget for each team in point cap mode.

**FR-DRAFT-027:** The system shall allow draft creators to pause live drafts.

**FR-DRAFT-028:** The system shall allow draft creators to resume paused drafts.

**FR-DRAFT-029:** The system shall automatically complete the draft when all roster slots are filled.

**FR-DRAFT-030:** The system shall persist draft state to database after each pick.

#### 2.4.3 Draft State Management

**FR-DRAFT-031:** The system shall provide full draft state for client reconnection.

**FR-DRAFT-032:** The system shall track user's assigned team for a given draft.

**FR-DRAFT-033:** The system shall list all active and pending drafts for a user.

**FR-DRAFT-034:** The system shall exclude expired anonymous drafts from user's draft list.

**FR-DRAFT-035:** The system shall allow draft creators to delete pending drafts.

**FR-DRAFT-036:** The system shall prevent deletion of drafts that have started.

#### 2.4.4 Pokemon Pool Customization

**FR-DRAFT-037:** The system shall allow filtering Pokemon pool by generation (1-9).

**FR-DRAFT-038:** The system shall allow filtering Pokemon pool by evolution stage (unevolved, middle, fully evolved).

**FR-DRAFT-039:** The system shall allow filtering Pokemon pool by type (all 18 types).

**FR-DRAFT-040:** The system shall allow filtering Pokemon pool by Base Stat Total range.

**FR-DRAFT-041:** The system shall allow filtering Pokemon pool by minimum individual stat values (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed).

**FR-DRAFT-042:** The system shall allow filtering Pokemon pool by ability name search.

**FR-DRAFT-043:** The system shall allow toggling inclusion of legendary Pokemon.

**FR-DRAFT-044:** The system shall allow toggling inclusion of mythical Pokemon.

**FR-DRAFT-045:** The system shall allow manual exclusion of specific Pokemon from the pool.

**FR-DRAFT-046:** The system shall allow manual inclusion of specific Pokemon to the pool.

#### 2.4.5 Auction Draft (Partial Implementation)

**FR-DRAFT-047:** The system shall support Pokemon nomination in auction drafts.

**FR-DRAFT-048:** The system shall support bidding on nominated Pokemon in auction drafts.

**FR-DRAFT-049:** The system shall configure starting budget for auction drafts.

**FR-DRAFT-050:** The system shall configure minimum bid amount for auction drafts.

**FR-DRAFT-051:** The system shall configure bid increment for auction drafts.

**FR-DRAFT-052:** The system shall configure nomination timer for auction drafts.

**FR-DRAFT-053:** The system shall configure bid timer for auction drafts.

---

### 2.5 Team Management (TEAM)

**FR-TEAM-001:** The system shall create teams for each league member when a season draft is created.

**FR-TEAM-002:** The system shall create teams for anonymous draft participants when they join.

**FR-TEAM-003:** The system shall link teams to users for league drafts.

**FR-TEAM-004:** The system shall link teams to session tokens for anonymous drafts.

**FR-TEAM-005:** The system shall track team wins, losses, and ties.

**FR-TEAM-006:** The system shall track team's remaining budget in point cap mode.

**FR-TEAM-007:** The system shall track team's draft position.

**FR-TEAM-008:** The system shall allow users to update their team name.

**FR-TEAM-009:** The system shall list all teams in a season or draft.

**FR-TEAM-010:** The system shall display team details including roster and statistics.

**FR-TEAM-011:** The system shall display all Pokemon on a team's roster.

**FR-TEAM-012:** The system shall export teams in Pokemon Showdown format.

**FR-TEAM-013:** The system shall export teams in JSON format with full metadata.

**FR-TEAM-014:** The system shall export teams in CSV format.

---

### 2.6 Trading System (TRADE)

**FR-TRADE-001:** The system shall allow teams to propose trades with other teams in the same season.

**FR-TRADE-002:** The system shall allow proposers to select multiple Pokemon to trade away.

**FR-TRADE-003:** The system shall allow proposers to select multiple Pokemon to receive.

**FR-TRADE-004:** The system shall allow proposers to include optional messages with trade proposals.

**FR-TRADE-005:** The system shall validate that proposer owns the Pokemon being traded away.

**FR-TRADE-006:** The system shall validate that recipient owns the Pokemon being requested.

**FR-TRADE-007:** The system shall track trade status: pending, accepted, rejected, cancelled.

**FR-TRADE-008:** The system shall allow trade recipients to accept trades.

**FR-TRADE-009:** The system shall allow trade recipients to reject trades.

**FR-TRADE-010:** The system shall allow trade proposers to cancel pending trades.

**FR-TRADE-011:** The system shall require admin approval for trades when league settings mandate it.

**FR-TRADE-012:** The system shall allow league owners to approve trades awaiting approval.

**FR-TRADE-013:** The system shall transfer Pokemon ownership when trades are accepted and approved.

**FR-TRADE-014:** The system shall update team rosters immediately upon trade execution.

**FR-TRADE-015:** The system shall list all trades for a given season.

**FR-TRADE-016:** The system shall display trade details including Pokemon involved and status.

**FR-TRADE-017:** The system shall prevent trades in seasons that are not in active status.

---

### 2.7 Waiver Wire / Free Agent System (WAIVER)

#### 2.7.1 Waiver Claim Creation

**FR-WAIVER-001:** The system shall allow teams to submit waiver claims for free agent Pokemon during active seasons.

**FR-WAIVER-002:** The system shall allow teams to specify a Pokemon to drop when submitting a waiver claim.

**FR-WAIVER-003:** The system shall validate that the claimed Pokemon is not already owned by a team in the season.

**FR-WAIVER-004:** The system shall validate that the team owns the Pokemon they are dropping (if specified).

**FR-WAIVER-005:** The system shall prevent duplicate pending claims for the same Pokemon by the same team.

**FR-WAIVER-006:** The system shall track waiver claims by week number for weekly limit enforcement.

#### 2.7.2 League Configuration

**FR-WAIVER-007:** The system shall allow league owners to enable/disable waiver wire functionality via league settings.

**FR-WAIVER-008:** The system shall allow league owners to configure waiver approval type: none (auto-approve), admin approval, or league vote.

**FR-WAIVER-009:** The system shall allow league owners to configure waiver processing timing: immediate or next week.

**FR-WAIVER-010:** The system shall allow league owners to configure maximum waiver claims per team per week (optional limit).

**FR-WAIVER-011:** The system shall allow league owners to require a drop Pokemon when claiming (optional requirement).

#### 2.7.3 Approval Workflows

**FR-WAIVER-012:** The system shall automatically approve and execute waiver claims when approval type is "none" and processing is "immediate".

**FR-WAIVER-013:** The system shall require league owner approval for waiver claims when approval type is "admin".

**FR-WAIVER-014:** The system shall allow league owners to approve or reject pending waiver claims with optional notes.

**FR-WAIVER-015:** The system shall support league vote approval where members vote to approve/reject claims.

**FR-WAIVER-016:** The system shall track vote counts (for and against) for league vote approval.

**FR-WAIVER-017:** The system shall automatically approve claims when vote threshold is reached.

**FR-WAIVER-018:** The system shall prevent duplicate votes by the same user on the same claim.

#### 2.7.4 Claim Status Management

**FR-WAIVER-019:** The system shall track waiver claim status: pending, approved, rejected, cancelled, expired.

**FR-WAIVER-020:** The system shall allow claim owners to cancel their pending claims.

**FR-WAIVER-021:** The system shall record resolved_at timestamp when claims reach final status.

**FR-WAIVER-022:** The system shall record admin_approved flag and admin_notes when admin takes action.

#### 2.7.5 Claim Execution

**FR-WAIVER-023:** The system shall create a new DraftPick record for the claimed Pokemon when approved.

**FR-WAIVER-024:** The system shall remove the dropped Pokemon from the team roster when claim is executed (if drop specified).

**FR-WAIVER-025:** The system shall update team rosters immediately upon waiver claim execution.

#### 2.7.6 Free Agent Pool

**FR-WAIVER-026:** The system shall list all free agent Pokemon available in a season (Pokemon in pool but not owned).

**FR-WAIVER-027:** The system shall display free agent Pokemon details including name, types, stats, and sprite.

#### 2.7.7 Waiver Claim Listing

**FR-WAIVER-028:** The system shall list all waiver claims for a season.

**FR-WAIVER-029:** The system shall allow filtering waiver claims by status.

**FR-WAIVER-030:** The system shall allow filtering waiver claims by team.

**FR-WAIVER-031:** The system shall display pending claim count for quick status overview.

---

### 2.8 Match and Tournament Management (MATCH)

#### 2.8.1 Match Management

**FR-MATCH-001:** The system shall allow league owners to generate match schedules for seasons.

**FR-MATCH-002:** The system shall support round-robin schedule format (each team plays once).

**FR-MATCH-003:** The system shall support double round-robin format (each team plays twice).

**FR-MATCH-004:** The system shall support single elimination tournament format.

**FR-MATCH-005:** The system shall support double elimination tournament format with winners and losers brackets.

**FR-MATCH-006:** The system shall allow league owners to record match results.

**FR-MATCH-007:** The system shall allow recording winner, tie status, replay URL, and notes for matches.

**FR-MATCH-008:** The system shall automatically update team win/loss/tie records when results are recorded.

**FR-MATCH-009:** The system shall display season schedule with match details.

**FR-MATCH-010:** The system shall display match details including teams, result, and metadata.

#### 2.8.2 Tournament Brackets

**FR-MATCH-011:** The system shall generate single elimination brackets for any number of teams.

**FR-MATCH-012:** The system shall automatically insert bye matches for non-power-of-2 team counts.

**FR-MATCH-013:** The system shall support seeding teams by standings or random order.

**FR-MATCH-014:** The system shall track bracket round, position, and seed information.

**FR-MATCH-015:** The system shall automatically progress winners to next round in elimination brackets.

**FR-MATCH-016:** The system shall generate double elimination brackets with separate winners and losers brackets.

**FR-MATCH-017:** The system shall route losers from winners bracket to appropriate losers bracket matches.

**FR-MATCH-018:** The system shall generate grand finals match for double elimination.

**FR-MATCH-019:** The system shall support optional bracket reset in grand finals if losers bracket winner wins first match.

**FR-MATCH-020:** The system shall provide bracket visualization data including round names and match progression.

**FR-MATCH-021:** The system shall identify champions when final match is complete.

#### 2.8.3 Standings

**FR-MATCH-022:** The system shall calculate season standings based on win/loss/tie records.

**FR-MATCH-023:** The system shall assign 3 points per win in standings calculation.

**FR-MATCH-024:** The system shall assign 1 point per tie in standings calculation.

**FR-MATCH-025:** The system shall assign 0 points per loss in standings calculation.

**FR-MATCH-026:** The system shall display standings with team names, records, and points.

**FR-MATCH-027:** The system shall sort standings by points (descending), then by win percentage.

---

### 2.8 Pokemon Data Management (POKE)

**FR-POKE-001:** The system shall maintain a local database of Pokemon data loaded from PokeAPI CSV files.

**FR-POKE-002:** The system shall store Pokemon species information including name, generation, and classification.

**FR-POKE-003:** The system shall store Pokemon type information (all 18 types).

**FR-POKE-004:** The system shall store Pokemon base stat values (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed).

**FR-POKE-005:** The system shall store Pokemon ability information.

**FR-POKE-006:** The system shall calculate Base Stat Total (BST) for each Pokemon.

**FR-POKE-007:** The system shall track evolution stage for each Pokemon (unevolved, middle, fully evolved).

**FR-POKE-008:** The system shall flag legendary Pokemon.

**FR-POKE-009:** The system shall flag mythical Pokemon.

**FR-POKE-010:** The system shall allow searching Pokemon by name (case-insensitive, partial match).

**FR-POKE-011:** The system shall allow filtering Pokemon by type.

**FR-POKE-012:** The system shall allow filtering Pokemon by generation.

**FR-POKE-013:** The system shall allow filtering Pokemon by evolution stage.

**FR-POKE-014:** The system shall allow filtering Pokemon by BST range.

**FR-POKE-015:** The system shall allow filtering Pokemon by minimum stat values.

**FR-POKE-016:** The system shall allow filtering Pokemon by ability.

**FR-POKE-017:** The system shall allow filtering Pokemon by legendary status.

**FR-POKE-018:** The system shall allow filtering Pokemon by mythical status.

**FR-POKE-019:** The system shall retrieve Pokemon by unique ID.

**FR-POKE-020:** The system shall retrieve Pokemon by name.

**FR-POKE-021:** The system shall provide optimized bulk Pokemon data for draft creation.

**FR-POKE-022:** The system shall list all Pokemon types.

**FR-POKE-023:** The system shall retrieve Pokemon by generation.

**FR-POKE-024:** The system shall provide sprite URLs for multiple styles (default, official-artwork, animated, home).

**FR-POKE-025:** The system shall support batch fetching of Pokemon data for efficiency.

---

### 2.9 Pool Preset Management (PRESET)

**FR-PRESET-001:** The system shall allow authenticated users to save Pokemon pool configurations as presets.

**FR-PRESET-002:** The system shall allow users to name presets.

**FR-PRESET-003:** The system shall allow users to provide descriptions for presets.

**FR-PRESET-004:** The system shall allow users to mark presets as public or private.

**FR-PRESET-005:** The system shall store complete Pokemon pool data in JSONB format within presets.

**FR-PRESET-006:** The system shall list all presets owned by a user.

**FR-PRESET-007:** The system shall list all public presets.

**FR-PRESET-008:** The system shall allow users to load presets when creating drafts.

**FR-PRESET-009:** The system shall allow preset owners to update their presets.

**FR-PRESET-010:** The system shall allow preset owners to delete their presets.

**FR-PRESET-011:** The system shall retrieve preset details including full pool data.

---

### 2.10 Real-Time Communication (WEBSOCKET)

#### 2.10.1 Draft Room WebSocket

**FR-WS-001:** The system shall provide WebSocket endpoint for draft room real-time updates.

**FR-WS-002:** The system shall authenticate draft room WebSocket connections via token or team ID.

**FR-WS-003:** The system shall send full draft state to clients upon connection.

**FR-WS-004:** The system shall broadcast draft_started event when draft begins.

**FR-WS-005:** The system shall broadcast pick_made event when a team makes a pick.

**FR-WS-006:** The system shall broadcast turn_start event when a new team's turn begins.

**FR-WS-007:** The system shall broadcast draft_complete event when all picks are finished.

**FR-WS-008:** The system shall broadcast user_joined event when participants connect.

**FR-WS-009:** The system shall broadcast user_left event when participants disconnect.

**FR-WS-010:** The system shall broadcast error events for invalid operations.

**FR-WS-011:** The system shall accept make_pick commands from current team via WebSocket.

**FR-WS-012:** The system shall accept start_draft commands from creator via WebSocket.

**FR-WS-013:** The system shall accept join_draft commands for authentication via WebSocket.

**FR-WS-014:** The system shall broadcast bid_update events for auction drafts.

**FR-WS-015:** The system shall broadcast nomination events for auction drafts.

**FR-WS-016:** The system shall accept place_bid commands for auction drafts via WebSocket.

**FR-WS-017:** The system shall accept nominate commands for auction drafts via WebSocket.

#### 2.10.2 Trade WebSocket

**FR-WS-018:** The system shall provide WebSocket endpoint for season trade notifications.

**FR-WS-019:** The system shall broadcast trade_proposed event when new trades are created.

**FR-WS-020:** The system shall broadcast trade_accepted event when trades are accepted.

**FR-WS-021:** The system shall broadcast trade_rejected event when trades are rejected.

**FR-WS-022:** The system shall broadcast trade_cancelled event when trades are cancelled.

**FR-WS-023:** The system shall broadcast trade_approved event when trades are admin approved.

#### 2.10.3 Waiver Wire WebSocket

**FR-WS-024:** The system shall provide WebSocket endpoint for season waiver wire notifications.

**FR-WS-025:** The system shall broadcast waiver_claim_created event when new claims are submitted.

**FR-WS-026:** The system shall broadcast waiver_claim_cancelled event when claims are cancelled.

**FR-WS-027:** The system shall broadcast waiver_claim_approved event when claims are approved.

**FR-WS-028:** The system shall broadcast waiver_claim_rejected event when claims are rejected.

**FR-WS-029:** The system shall broadcast waiver_vote_cast event when votes are cast on claims.

---

### 2.11 Discord Integration (DISCORD)

**FR-DISCORD-001:** The system shall provide a Discord bot framework with slash commands.

**FR-DISCORD-002:** The system shall support /draft command to display draft information.

**FR-DISCORD-003:** The system shall support /picks command to show recent picks.

**FR-DISCORD-004:** The system shall support /available command to list available Pokemon.

**FR-DISCORD-005:** The system shall support /standings command to show season standings.

**FR-DISCORD-006:** The system shall support /schedule command to display match schedule.

**FR-DISCORD-007:** The system shall support /team command to show team roster.

**FR-DISCORD-008:** The system shall support /link command to link Discord account to PokeDraft user.

**FR-DISCORD-009:** The system shall send Discord notifications for draft events (partial implementation).

**FR-DISCORD-010:** The system shall send Discord notifications for trade events (partial implementation).

**FR-DISCORD-011:** The system shall send Discord notifications for match events (partial implementation).

---

### 2.12 User Interface (UI)

#### 2.12.1 Navigation and Layout

**FR-UI-001:** The system shall provide a responsive navigation header with logo and menu items.

**FR-UI-002:** The system shall display user authentication status in navigation.

**FR-UI-003:** The system shall provide quick access links to Dashboard, Leagues, and Create Draft.

**FR-UI-004:** The system shall display user avatar and name when authenticated.

**FR-UI-005:** The system shall provide a footer with credits and version information.

#### 2.12.2 Home Page

**FR-UI-006:** The system shall display a landing page with feature highlights.

**FR-UI-007:** The system shall provide call-to-action buttons for starting drafts and viewing leagues.

**FR-UI-008:** The system shall display key features: multiple formats, real-time drafting, league management.

#### 2.12.3 Authentication Pages

**FR-UI-009:** The system shall provide a login page with email and Discord options.

**FR-UI-010:** The system shall display development mode login options when enabled.

**FR-UI-011:** The system shall handle OAuth callback redirects.

**FR-UI-012:** The system shall display authentication errors to users.

#### 2.12.4 Dashboard

**FR-UI-013:** The system shall display a dashboard with quick action buttons.

**FR-UI-014:** The system shall list active drafts with status indicators on dashboard.

**FR-UI-015:** The system shall list recent completed drafts on dashboard.

**FR-UI-016:** The system shall display user's leagues with member counts on dashboard.

**FR-UI-017:** The system shall provide quick access to pool presets on dashboard.

**FR-UI-018:** The system shall allow deletion of pending drafts from dashboard.

#### 2.12.5 Draft Creation Page

**FR-UI-019:** The system shall provide a form to configure draft settings.

**FR-UI-020:** The system shall display draft format selection (Snake, Linear, Auction).

**FR-UI-021:** The system shall provide roster size input with validation (1-20).

**FR-UI-022:** The system shall provide timer duration input with validation (30-600 seconds).

**FR-UI-023:** The system shall provide toggle for point cap mode.

**FR-UI-024:** The system shall display auction-specific settings when auction format is selected.

**FR-UI-025:** The system shall provide Pokemon pool customization interface.

**FR-UI-026:** The system shall display template preset selection.

**FR-UI-027:** The system shall provide advanced filters for Pokemon pool (generation, type, BST, stats, abilities).

**FR-UI-028:** The system shall display Pokemon grid with sprites and names.

**FR-UI-029:** The system shall allow toggling Pokemon inclusion/exclusion in pool.

**FR-UI-030:** The system shall provide bulk point value assignment interface.

**FR-UI-031:** The system shall display pool statistics (total count, filtered count).

**FR-UI-032:** The system shall allow saving Pokemon pool as preset.

**FR-UI-033:** The system shall allow loading Pokemon pool from preset.

**FR-UI-034:** The system shall validate draft settings before creation.

**FR-UI-035:** The system shall redirect to draft room after successful creation.

#### 2.12.6 Draft Room Page

**FR-UI-036:** The system shall display draft room with real-time updates.

**FR-UI-037:** The system shall show current draft status (Pending, Live, Paused, Completed).

**FR-UI-038:** The system shall display rejoin code prominently for sharing.

**FR-UI-039:** The system shall display countdown timer for current pick.

**FR-UI-040:** The system shall highlight whose turn it is to pick.

**FR-UI-041:** The system shall display all teams with their picked Pokemon.

**FR-UI-042:** The system shall show team names and pick order.

**FR-UI-043:** The system shall display Pokemon sprites for picked Pokemon.

**FR-UI-044:** The system shall provide Pokemon browser with available Pokemon.

**FR-UI-045:** The system shall allow searching and filtering available Pokemon in draft room.

**FR-UI-046:** The system shall display Pokemon details on hover or click (stats, types, abilities).

**FR-UI-047:** The system shall enable pick button only for current team's user.

**FR-UI-048:** The system shall display pick confirmation feedback.

**FR-UI-049:** The system shall show WebSocket connection status indicator.

**FR-UI-050:** The system shall provide start draft button for creator when draft is pending.

**FR-UI-051:** The system shall provide export team button when draft is complete.

**FR-UI-052:** The system shall allow toggling sprite style (Default, Official Artwork, HOME).

**FR-UI-053:** The system shall persist sprite preference to localStorage.

**FR-UI-054:** The system shall display error messages for invalid picks.

**FR-UI-055:** The system shall auto-reconnect WebSocket on disconnection.

**FR-UI-056:** The system shall restore draft state after reconnection.

#### 2.12.7 League Pages

**FR-UI-057:** The system shall display a list of user's leagues.

**FR-UI-058:** The system shall provide a form to create new leagues.

**FR-UI-059:** The system shall display league invite code and shareable link.

**FR-UI-060:** The system shall provide a page to join leagues via invite code.

**FR-UI-061:** The system shall display league details including name, owner, and members.

**FR-UI-062:** The system shall list all seasons within a league.

**FR-UI-063:** The system shall display season status for each season.

**FR-UI-064:** The system shall provide create season button for league owners.

**FR-UI-065:** The system shall provide league settings page for owners.

**FR-UI-066:** The system shall allow owners to configure default draft settings in league settings.

**FR-UI-067:** The system shall allow owners to configure trade approval requirements in league settings.

**FR-UI-068:** The system shall display member list with option to remove members (owner only).

**FR-UI-069:** The system shall provide leave league button for non-owners.

#### 2.12.8 Season Pages

**FR-UI-070:** The system shall display season details with tabbed interface.

**FR-UI-071:** The system shall provide Standings tab showing win/loss/tie records and points.

**FR-UI-072:** The system shall provide Schedule tab with match list or bracket visualization.

**FR-UI-073:** The system shall provide Teams tab showing all teams and rosters.

**FR-UI-074:** The system shall provide Trades tab for proposing and viewing trades.

**FR-UI-075:** The system shall display season status prominently (Pre-Draft, Drafting, Active, Completed).

**FR-UI-076:** The system shall provide generate schedule button for owners when no schedule exists.

**FR-UI-077:** The system shall allow owners to select schedule format (Round Robin, Single Elimination, Double Elimination).

**FR-UI-078:** The system shall allow owners to select seeding method (Standings or Random).

**FR-UI-079:** The system shall display matches with team names, scores, and status.

**FR-UI-080:** The system shall allow owners to record match results by clicking matches.

**FR-UI-081:** The system shall provide form to enter winner, replay URL, and notes for matches.

**FR-UI-082:** The system shall display bracket visualization for elimination formats.

**FR-UI-083:** The system shall highlight bracket progression paths.

**FR-UI-084:** The system shall display team rosters with Pokemon sprites in Teams tab.

**FR-UI-085:** The system shall update standings in real-time as match results are recorded.

#### 2.12.9 Trade Interface

**FR-UI-086:** The system shall display list of all trades in season with status badges.

**FR-UI-087:** The system shall provide propose trade button in Trades tab.

**FR-UI-088:** The system shall display modal to create trade proposals.

**FR-UI-089:** The system shall allow selection of Pokemon to trade away from user's roster.

**FR-UI-090:** The system shall allow selection of recipient team.

**FR-UI-091:** The system shall allow selection of Pokemon to receive from recipient's roster.

**FR-UI-092:** The system shall provide optional message field for trade proposals.

**FR-UI-093:** The system shall display trade cards with proposer, recipient, and Pokemon involved.

**FR-UI-094:** The system shall provide accept button for trade recipients.

**FR-UI-095:** The system shall provide reject button for trade recipients.

**FR-UI-096:** The system shall provide cancel button for trade proposers.

**FR-UI-097:** The system shall provide approve button for league owners when approval is required.

**FR-UI-098:** The system shall display trade status (Pending, Accepted, Rejected, Cancelled).

**FR-UI-099:** The system shall update trade list in real-time via WebSocket.

**FR-UI-100:** The system shall display toast notifications for trade events.

#### 2.12.10 Team Export

**FR-UI-101:** The system shall provide export button in completed draft room.

**FR-UI-102:** The system shall display modal with export format options (Showdown, JSON, CSV).

**FR-UI-103:** The system shall generate exportable text for selected format.

**FR-UI-104:** The system shall provide copy to clipboard button for export.

**FR-UI-105:** The system shall display success feedback when copied.

#### 2.12.11 Preset Management

**FR-UI-106:** The system shall display modal to save current Pokemon pool as preset.

**FR-UI-107:** The system shall provide form with preset name, description, and visibility toggle.

**FR-UI-108:** The system shall display modal to load presets.

**FR-UI-109:** The system shall list user's presets and public presets in load modal.

**FR-UI-110:** The system shall allow searching/filtering presets by name.

**FR-UI-111:** The system shall display preset details (name, description, Pokemon count).

**FR-UI-112:** The system shall apply preset pool configuration when loaded.

#### 2.12.12 Responsive Design

**FR-UI-113:** The system shall provide mobile-responsive layout for all pages.

**FR-UI-114:** The system shall adapt navigation menu for small screens.

**FR-UI-115:** The system shall stack content vertically on mobile devices.

**FR-UI-116:** The system shall ensure touch-friendly button and link sizes on mobile.

**FR-UI-117:** The system shall display readable text sizes across all screen sizes.

---

## 3. Non-Functional Requirements

### 3.1 Performance (PERF)

**NFR-PERF-001:** The system shall respond to API requests within 500ms for 95% of requests under normal load.

**NFR-PERF-002:** The system shall establish WebSocket connections within 2 seconds.

**NFR-PERF-003:** The system shall broadcast draft pick events to all participants within 100ms.

**NFR-PERF-004:** The system shall load Pokemon data using optimized batch queries to minimize database calls.

**NFR-PERF-005:** The system shall cache frequently accessed data using React Query with 5-minute stale time.

**NFR-PERF-006:** The system shall use database indexes on frequently queried fields (user_id, league_id, draft_id, season_id).

**NFR-PERF-007:** The system shall load initial draft room UI within 3 seconds on standard connections.

**NFR-PERF-008:** The system shall paginate or limit large result sets to prevent performance degradation.

### 3.2 Security (SEC)

**NFR-SEC-001:** The system shall use HTTPS for all client-server communication in production.

**NFR-SEC-002:** The system shall use WSS (WebSocket Secure) for all WebSocket connections in production.

**NFR-SEC-003:** The system shall validate and verify JWT tokens on every authenticated API request.

**NFR-SEC-004:** The system shall implement CORS restrictions to prevent unauthorized cross-origin requests.

**NFR-SEC-005:** The system shall sanitize all user inputs to prevent SQL injection attacks.

**NFR-SEC-006:** The system shall sanitize all user inputs to prevent XSS (Cross-Site Scripting) attacks.

**NFR-SEC-007:** The system shall enforce authorization checks ensuring users can only access their own resources.

**NFR-SEC-008:** The system shall enforce league ownership checks for privileged operations.

**NFR-SEC-009:** The system shall generate cryptographically secure session tokens for anonymous users.

**NFR-SEC-010:** The system shall generate cryptographically secure invite codes and rejoin codes.

**NFR-SEC-011:** The system shall securely store sensitive configuration in environment variables.

**NFR-SEC-012:** The system shall not expose internal error details in production API responses.

### 3.3 Reliability (REL)

**NFR-REL-001:** The system shall persist draft state to database after each pick to prevent data loss.

**NFR-REL-002:** The system shall support automatic WebSocket reconnection on connection loss.

**NFR-REL-003:** The system shall restore full draft state when clients reconnect.

**NFR-REL-004:** The system shall handle database connection failures gracefully with retry logic.

**NFR-REL-005:** The system shall use database transactions for operations that modify multiple tables.

**NFR-REL-006:** The system shall validate all data before persisting to database.

**NFR-REL-007:** The system shall log errors for debugging and monitoring purposes.

**NFR-REL-008:** The system shall provide meaningful error messages to users when operations fail.

### 3.4 Scalability (SCALE)

**NFR-SCALE-001:** The system shall support at least 100 concurrent draft rooms.

**NFR-SCALE-002:** The system shall support at least 1000 concurrent WebSocket connections.

**NFR-SCALE-003:** The system shall support leagues with at least 50 members.

**NFR-SCALE-004:** The system shall support drafts with at least 20 teams.

**NFR-SCALE-005:** The system shall support Pokemon pools with all 1000+ Pokemon.

**NFR-SCALE-006:** The system shall use async/await patterns for non-blocking I/O operations.

**NFR-SCALE-007:** The system shall implement connection pooling for database connections.

### 3.5 Usability (USE)

**NFR-USE-001:** The system shall provide intuitive navigation with clear labels and visual hierarchy.

**NFR-USE-002:** The system shall display loading indicators during asynchronous operations.

**NFR-USE-003:** The system shall provide informative error messages that guide users to resolution.

**NFR-USE-004:** The system shall use consistent visual design patterns across all pages.

**NFR-USE-005:** The system shall provide visual feedback for user actions (button clicks, form submissions).

**NFR-USE-006:** The system shall display success notifications for completed operations.

**NFR-USE-007:** The system shall use color-coded status indicators for drafts, seasons, trades, and matches.

**NFR-USE-008:** The system shall provide keyboard accessibility for interactive elements.

**NFR-USE-009:** The system shall use descriptive alt text for Pokemon sprites and icons.

**NFR-USE-010:** The system shall maintain accessibility standards (WCAG 2.1 AA) for contrast and readability.

### 3.6 Maintainability (MAINT)

**NFR-MAINT-001:** The system shall use TypeScript for type safety in frontend code.

**NFR-MAINT-002:** The system shall use Python type hints in backend code.

**NFR-MAINT-003:** The system shall organize code into logical modules and services.

**NFR-MAINT-004:** The system shall use Alembic for database schema migrations.

**NFR-MAINT-005:** The system shall version control all source code using Git.

**NFR-MAINT-006:** The system shall use consistent code formatting (Prettier for frontend).

**NFR-MAINT-007:** The system shall document API endpoints with parameter and response schemas.

**NFR-MAINT-008:** The system shall use environment variables for configuration management.

**NFR-MAINT-009:** The system shall separate concerns using MVC-like architecture (models, services, routes).

### 3.7 Compatibility (COMPAT)

**NFR-COMPAT-001:** The system shall support modern web browsers (Chrome, Firefox, Safari, Edge) released within the last 2 years.

**NFR-COMPAT-002:** The system shall support mobile browsers on iOS 14+ and Android 10+.

**NFR-COMPAT-003:** The system shall use WebSocket protocol compatible with RFC 6455.

**NFR-COMPAT-004:** The system shall use JSON for all API request and response bodies.

**NFR-COMPAT-005:** The system shall support PostgreSQL 12+.

---

## 4. Interface Requirements

### 4.1 External API Interfaces (API)

**IR-API-001:** The system shall provide RESTful API endpoints following versioning scheme `/api/v1/`.

**IR-API-002:** The system shall accept and return JSON-formatted data for all API requests and responses.

**IR-API-003:** The system shall use standard HTTP methods: GET, POST, PUT, DELETE.

**IR-API-004:** The system shall use standard HTTP status codes (200, 201, 400, 401, 403, 404, 500).

**IR-API-005:** The system shall include authorization tokens in HTTP headers (Authorization: Bearer <token>).

**IR-API-006:** The system shall provide consistent error response format with error message and code.

**IR-API-007:** The system shall provide consistent success response format with data and metadata.

**IR-API-008:** The system shall document API endpoints using OpenAPI/Swagger specification (implicit via FastAPI).

### 4.2 WebSocket Interfaces (WS-IF)

**IR-WS-001:** The system shall use WebSocket protocol for real-time bidirectional communication.

**IR-WS-002:** The system shall send WebSocket messages in JSON format.

**IR-WS-003:** The system shall include message type field in all WebSocket messages.

**IR-WS-004:** The system shall include event-specific payload in WebSocket messages.

**IR-WS-005:** The system shall provide WebSocket endpoint at `/ws/draft/{draft_id}` for draft rooms.

**IR-WS-006:** The system shall provide WebSocket endpoint at `/ws/trade/{season_id}` for trade notifications.

**IR-WS-007:** The system shall authenticate WebSocket connections before allowing event subscription.

**IR-WS-008:** The system shall provide WebSocket endpoint at `/ws/waivers/{season_id}` for waiver wire notifications.

### 4.3 Authentication Provider Interface (AUTH-IF)

**IR-AUTH-001:** The system shall integrate with Supabase authentication service for user management.

**IR-AUTH-002:** The system shall validate JWT tokens against Supabase JWKS endpoint.

**IR-AUTH-003:** The system shall extract user metadata from JWT token claims (email, sub, user_metadata).

**IR-AUTH-004:** The system shall support Discord OAuth flow via Supabase authentication.

**IR-AUTH-005:** The system shall handle OAuth callback redirects from Supabase.

### 4.4 Database Interface (DB-IF)

**IR-DB-001:** The system shall connect to PostgreSQL database using SQLAlchemy ORM.

**IR-DB-002:** The system shall use async SQLAlchemy session for all database operations.

**IR-DB-003:** The system shall use parameterized queries to prevent SQL injection.

**IR-DB-004:** The system shall use database transactions for multi-table operations.

**IR-DB-005:** The system shall use JSONB column type for flexible schema fields.

### 4.5 Pokemon Data Interface (POKE-IF)

**IR-POKE-001:** The system shall load Pokemon data from local database populated from PokeAPI CSV files.

**IR-POKE-002:** The system shall use PokeAPI CDN for Pokemon sprite URLs.

**IR-POKE-003:** The system shall construct sprite URLs using pattern: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{style}/{id}.png`

### 4.6 Discord Bot Interface (DISCORD-IF)

**IR-DISCORD-001:** The system shall use Discord.py library for Discord bot implementation.

**IR-DISCORD-002:** The system shall authenticate with Discord using bot token.

**IR-DISCORD-003:** The system shall register slash commands using Discord application commands API.

**IR-DISCORD-004:** The system shall send messages to Discord channels via Discord REST API.

---

## 5. Data Requirements

### 5.1 Data Models (DATA)

**DR-DATA-001:** The system shall persist User records with fields: id, email, display_name, avatar_url, discord_user_id, discord_username, created_at, updated_at.

**DR-DATA-002:** The system shall persist League records with fields: id, name, owner_id, invite_code, settings (JSONB), created_at, updated_at.

**DR-DATA-003:** The system shall persist LeagueMembership records with fields: league_id, user_id, active, joined_at.

**DR-DATA-004:** The system shall persist Season records with fields: id, league_id, name, status, settings (JSONB), created_at, updated_at.

**DR-DATA-005:** The system shall persist Draft records with fields: id, season_id (nullable), format, status, roster_size, timer_seconds, budget_enabled, budget_amount, pokemon_pool (JSONB), creator_token, rejoin_code, created_at, started_at, completed_at, expires_at.

**DR-DATA-006:** The system shall persist Team records with fields: id, draft_id, season_id, user_id (nullable), session_token (nullable), name, draft_position, budget_remaining, wins, losses, ties, created_at.

**DR-DATA-007:** The system shall persist DraftPick records with fields: id, draft_id, team_id, pokemon_id, pick_number, points_spent, picked_at.

**DR-DATA-008:** The system shall persist Trade records with fields: id, season_id, proposer_team_id, recipient_team_id, proposer_pokemon_ids (array), recipient_pokemon_ids (array), status, message, created_at, updated_at.

**DR-DATA-009:** The system shall persist Match records with fields: id, season_id, team_a_id, team_b_id, winner_id, is_tie, replay_url, notes, format, bracket_round, bracket_position, seed_a, seed_b, next_match_id, loser_next_match_id, scheduled_at, played_at.

**DR-DATA-010:** The system shall persist Pokemon records with fields: id, name, generation, is_legendary, is_mythical, evolution_stage, base_stat_total, created_at.

**DR-DATA-011:** The system shall persist PokemonSpecies records with fields: id, name, generation, evolution_chain_id, is_legendary, is_mythical.

**DR-DATA-012:** The system shall persist PokemonType records with fields: id, name.

**DR-DATA-013:** The system shall persist PokemonTypeLink records with fields: pokemon_id, type_id, slot.

**DR-DATA-014:** The system shall persist PokemonStat records with fields: id, name.

**DR-DATA-015:** The system shall persist PokemonStatValue records with fields: pokemon_id, stat_id, base_stat.

**DR-DATA-016:** The system shall persist PokemonAbility records with fields: id, name, is_hidden.

**DR-DATA-017:** The system shall persist PokemonAbilityLink records with fields: pokemon_id, ability_id, is_hidden.

**DR-DATA-018:** The system shall persist PoolPreset records with fields: id, user_id, name, description, is_public, pool_data (JSONB), created_at, updated_at.

**DR-DATA-019:** The system shall persist TeamPokemon records with fields: team_id, pokemon_id, acquired_via, acquired_at (currently unused, picks stored in DraftPick).

**DR-DATA-020:** The system shall persist WaiverClaim records with fields: id, season_id, team_id, pokemon_id, drop_pokemon_id (nullable), status, priority, requires_approval, admin_approved (nullable), admin_notes (nullable), votes_for, votes_against, votes_required (nullable), processing_type, process_after (nullable), week_number (nullable), created_at, resolved_at (nullable).

**DR-DATA-021:** The system shall persist WaiverVote records with fields: id, waiver_claim_id, user_id, vote, created_at.

### 5.2 Data Integrity (INTEGRITY)

**DR-INTEGRITY-001:** The system shall enforce foreign key constraints between related tables.

**DR-INTEGRITY-002:** The system shall use CASCADE delete for dependent records (e.g., deleting draft deletes picks).

**DR-INTEGRITY-003:** The system shall enforce unique constraints on invite_code, rejoin_code, and email fields.

**DR-INTEGRITY-004:** The system shall enforce NOT NULL constraints on required fields.

**DR-INTEGRITY-005:** The system shall use database indexes on foreign keys for query performance.

**DR-INTEGRITY-006:** The system shall validate enum values (draft format, status, match format) at application level.

**DR-INTEGRITY-007:** The system shall use CHECK constraints for valid value ranges (roster_size >= 1, timer_seconds >= 0).

### 5.3 Data Retention (RETENTION)

**DR-RETENTION-001:** The system shall retain completed draft records indefinitely.

**DR-RETENTION-002:** The system shall automatically expire pending anonymous drafts after 24 hours.

**DR-RETENTION-003:** The system shall retain user accounts indefinitely unless deleted by user.

**DR-RETENTION-004:** The system shall retain league and season data indefinitely.

**DR-RETENTION-005:** The system shall retain trade history indefinitely for auditing purposes.

**DR-RETENTION-006:** The system shall retain match results indefinitely.

### 5.4 Data Privacy (PRIVACY)

**DR-PRIVACY-001:** The system shall store only essential user information (email, display name, avatar URL).

**DR-PRIVACY-002:** The system shall not expose user email addresses in public API responses.

**DR-PRIVACY-003:** The system shall allow users to view and update their own profile information.

**DR-PRIVACY-004:** The system shall not share user data with third parties except for authentication (Supabase).

**DR-PRIVACY-005:** The system shall use session tokens instead of user IDs for anonymous draft participants.

---

## 6. System Requirements

### 6.1 Development Environment (DEV)

**SR-DEV-001:** The system shall provide development mode toggle via DEV_MODE environment variable.

**SR-DEV-002:** The system shall support local development with hot-reloading for frontend and backend.

**SR-DEV-003:** The system shall provide database migration capabilities via Alembic.

**SR-DEV-004:** The system shall provide test user creation in development mode.

**SR-DEV-005:** The system shall support pytest for backend testing.

### 6.2 Deployment (DEPLOY)

**SR-DEPLOY-001:** The system shall use environment variables for all environment-specific configuration.

**SR-DEPLOY-002:** The system shall support containerized deployment via Docker.

**SR-DEPLOY-003:** The system shall use PostgreSQL as the production database.

**SR-DEPLOY-004:** The system shall run frontend build process via Vite for production optimization.

**SR-DEPLOY-005:** The system shall run backend via Uvicorn ASGI server.

**SR-DEPLOY-006:** The system shall support CORS configuration via environment variable.

**SR-DEPLOY-007:** The system shall serve frontend static files from production web server.

### 6.3 Configuration (CONFIG)

**SR-CONFIG-001:** The system shall read configuration from .env file in development.

**SR-CONFIG-002:** The system shall provide default values for optional configuration parameters.

**SR-CONFIG-003:** The system shall validate required environment variables at startup.

**SR-CONFIG-004:** The system shall support configuration of default timer seconds (DEFAULT_TIMER_SECONDS).

**SR-CONFIG-005:** The system shall support configuration of draft expiration hours (DRAFT_EXPIRE_HOURS).

**SR-CONFIG-006:** The system shall support configuration of maximum pending anonymous drafts (MAX_PENDING_ANONYMOUS_DRAFTS).

**SR-CONFIG-007:** The system shall support configuration of sprite base URL (SPRITE_BASE_URL).

---

## 7. Requirements Traceability Matrix

| Requirement ID | Priority | Status | Verification Method | Related Requirements |
|---------------|----------|---------|---------------------|---------------------|
| FR-AUTH-* | High | Implemented | Integration Testing | NFR-SEC-*, IR-AUTH-* |
| FR-LEAGUE-* | High | Implemented | Integration Testing | DR-DATA-002, DR-DATA-003 |
| FR-SEASON-* | High | Implemented | Integration Testing | DR-DATA-004 |
| FR-DRAFT-* | Critical | Implemented | Integration Testing, Manual Testing | FR-WS-*, DR-DATA-005, DR-DATA-006, DR-DATA-007 |
| FR-TEAM-* | High | Implemented | Integration Testing | DR-DATA-006 |
| FR-TRADE-* | Medium | Implemented | Integration Testing, Manual Testing | FR-WS-018 to FR-WS-023, DR-DATA-008 |
| FR-WAIVER-* | Medium | Implemented | Integration Testing, Manual Testing | FR-WS-024 to FR-WS-029, DR-DATA-020, DR-DATA-021 |
| FR-MATCH-* | High | Implemented | Integration Testing | DR-DATA-009 |
| FR-POKE-* | High | Implemented | Unit Testing | IR-POKE-*, DR-DATA-010 to DR-DATA-017 |
| FR-PRESET-* | Low | Implemented | Integration Testing | DR-DATA-018 |
| FR-WS-* | Critical | Implemented | Manual Testing, Integration Testing | NFR-PERF-002, NFR-PERF-003, NFR-REL-002, NFR-REL-003 |
| FR-DISCORD-* | Low | Partially Implemented | Manual Testing | IR-DISCORD-* |
| FR-UI-* | High | Implemented | Manual Testing, User Acceptance Testing | NFR-USE-* |
| NFR-PERF-* | High | Implemented | Performance Testing | - |
| NFR-SEC-* | Critical | Implemented | Security Testing, Code Review | - |
| NFR-REL-* | High | Implemented | Integration Testing, Failure Testing | - |
| NFR-SCALE-* | Medium | Implemented | Load Testing | - |
| NFR-USE-* | High | Implemented | User Acceptance Testing | - |
| NFR-MAINT-* | Medium | Implemented | Code Review | - |
| NFR-COMPAT-* | High | Implemented | Compatibility Testing | - |

---

## 8. Assumptions and Dependencies

### 8.1 Assumptions
1. Users have modern web browsers with JavaScript enabled
2. Users have stable internet connections for real-time features
3. PostgreSQL database is available and properly configured
4. Supabase authentication service is operational
5. PokeAPI CDN is available for Pokemon sprites
6. Discord service is operational for Discord integration features

### 8.2 Dependencies
1. **Frontend Dependencies**: React, React Router, TanStack Query, Zustand, Tailwind CSS, Supabase JS Client, Lucide React
2. **Backend Dependencies**: FastAPI, SQLAlchemy, Alembic, Uvicorn, Supabase Python, PyJWT, Discord.py
3. **Database**: PostgreSQL 12+
4. **External Services**: Supabase (authentication), PokeAPI CDN (sprites), Discord API (bot integration)
5. **Build Tools**: Vite (frontend), Python 3.9+ (backend)

### 8.3 Constraints
1. WebSocket connections require persistent connections, which may be limited by server resources
2. Anonymous drafts expire after 24 hours to prevent database bloat
3. Maximum of 3 pending anonymous drafts per user to prevent abuse
4. Pokemon data is static and loaded from CSV files, not dynamically fetched from PokeAPI
5. Discord bot integration is partially implemented and requires completion

---

## 9. Glossary

**Draft**: An event where teams take turns selecting Pokemon to build their rosters.

**Snake Draft**: A draft format where pick order reverses each round (e.g., 1-8, 8-1, 1-8).

**Linear Draft**: A draft format where pick order remains constant each round (e.g., 1-8, 1-8, 1-8).

**Auction Draft**: A draft format where teams nominate Pokemon and bid using a budget.

**League**: A persistent group of users who compete across multiple seasons.

**Season**: A competitive cycle within a league, including draft, matches, and standings.

**Team**: A roster of Pokemon owned by a user in a season or draft.

**Trade**: An exchange of Pokemon between two teams in an active season.

**Waiver Wire / Free Agent**: A system allowing teams to claim unowned Pokemon from the draft pool during an active season, with optional approval requirements.

**Waiver Claim**: A request to add a free agent Pokemon to a team's roster, optionally dropping another Pokemon.

**Match**: A scheduled or completed battle between two teams.

**Bracket**: A tournament structure with elimination format (single or double elimination).

**Pool Preset**: A saved Pokemon pool configuration for quick draft setup.

**Rejoin Code**: A memorable code (format: WORD-NNNN) used to join or rejoin anonymous drafts.

**Invite Code**: A unique code used to join a league.

**BST (Base Stat Total)**: The sum of all base stats for a Pokemon (HP + Attack + Defense + Sp. Atk + Sp. Def + Speed).

**WebSocket**: A communication protocol providing full-duplex communication over a single TCP connection for real-time updates.

**JWT (JSON Web Token)**: A compact, URL-safe token used for authentication and authorization.

**JSONB**: PostgreSQL JSON binary storage format providing efficient querying and indexing.

**Supabase**: An open-source Firebase alternative providing authentication, database, and storage services.

---

## 10. Document Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-12-31 | System Analysis | Initial requirements specification based on existing PokeDraft functionality |
| 1.1 | 2025-12-31 | System Analysis | Added Waiver Wire / Free Agent System requirements (FR-WAIVER-*) |

---

**End of Requirements Specification**
