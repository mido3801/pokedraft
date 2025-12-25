# Pokemon Draft League Platform

**Design Document v1.0**

*DRAFT — December 2024*

---

## 1. Overview & Goals

### 1.1 Project Summary

A web application for managing Pokemon draft leagues. The platform handles team management, draft execution, scheduling, and league administration—everything except the actual Pokemon battles, which occur on external platforms like Pokemon Showdown.

### 1.2 Core Goals

1. **Polished Draft Experience:** A visually impressive, real-time draft interface that works seamlessly across desktop and mobile.

2. **High Customization:** Support for multiple draft formats, configurable rules, custom Pokemon pools, and flexible league settings.

3. **Low Barrier to Entry:** Anonymous users can create and participate in drafts without accounts; accounts unlock persistent features.

4. **Discord Integration:** Optional notifications for draft turns, match reminders, and league events via a centralized Discord bot.

5. **Complete League Management:** Schedules, match results, standings, trades, and multi-season support.

### 1.3 Out of Scope

- Actual Pokemon battling (handled by Pokemon Showdown or similar)
- Team building tools (movesets, EVs, IVs, etc.)
- Starter/bench roster management (handled by battle platform)

---

## 2. User Types & Authentication

### 2.1 User Types

The platform supports two primary user types with different capability sets.

| Capability | Anonymous User | Authenticated User |
|------------|----------------|-------------------|
| Create draft | ✓ (temporary session) | ✓ (persistent league) |
| Join live draft | ✓ (via link) | ✓ |
| Join async draft | ✗ | ✓ |
| Join league | ✗ | ✓ (via invite) |
| Save teams | ✗ (download only) | ✓ |
| Download team file | ✓ | ✓ |
| Trade Pokemon | ✗ | ✓ |
| Discord notifications | ✗ | ✓ (if linked) |

### 2.2 Anonymous User Session Management

Anonymous users need reliable ways to rejoin a draft session if disconnected. The platform implements a layered approach:

1. **Unique Session URL:** Each draft generates a unique URL with an embedded token (e.g., `draft.site/d/abc123xyz`). This is the primary rejoin mechanism.

2. **Rejoin Code:** A short, memorable code displayed prominently in the UI (e.g., `PIKA-7842`) that users can enter on the homepage to rejoin.

3. **LocalStorage Backup:** The session token is stored in browser localStorage. If a user returns to the site, they receive an auto-prompt to rejoin their active draft.

4. **Optional Email:** Users may optionally provide an email to receive a rejoin link, reducing friction for those who want extra security.

Draft sessions persist for 7 days after completion, allowing users to return and download their team file if they forgot during the draft.

### 2.3 Authentication

Authenticated users sign in via standard OAuth providers (Google, Discord) or email/password. Discord OAuth is recommended for seamless Discord notification integration. Authentication is handled by Supabase Auth.

---

## 3. Core Concepts & Data Model

### 3.1 Entity Relationships

```
User → League (many-to-many via Membership)
League → Season (one-to-many)
Season → Draft (one-to-one)
Season → Team (one-to-many)
Team → Pokemon (one-to-many)
Season → Match (one-to-many)
Season → Trade (one-to-many)
```

### 3.2 Core Entities

#### League

A league is the top-level container for competitive play. It persists across multiple seasons and contains configuration that applies to all seasons unless overridden.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | League display name |
| owner_id | UUID (FK) | User who created the league |
| invite_code | String | Unique code for joining |
| is_public | Boolean | Whether league is discoverable |
| settings | JSONB | Default league configuration |
| created_at | Timestamp | Creation timestamp |

#### Season

A season represents one competitive cycle within a league, including a draft, schedule, and standings.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| league_id | UUID (FK) | Parent league |
| season_number | Integer | Sequential season number |
| status | Enum | pre_draft, drafting, active, completed |
| keep_teams | Boolean | Whether teams carry over from previous season |
| settings | JSONB | Season-specific configuration overrides |
| started_at | Timestamp | When the season began |

#### Draft

A draft is the event where teams select Pokemon. Each season has exactly one draft.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| season_id | UUID (FK) | Parent season |
| format | Enum | snake, linear, auction |
| timer_seconds | Integer | Time per pick (null for async) |
| budget_enabled | Boolean | Whether salary cap is active |
| budget_per_team | Integer | Total points each team can spend |
| roster_size | Integer | Number of Pokemon per team |
| status | Enum | pending, live, paused, completed |
| current_pick | Integer | Current pick number |
| pokemon_pool | JSONB | Available Pokemon with optional point values |

#### Team

A team represents one participant's roster within a season.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| season_id | UUID (FK) | Parent season |
| user_id | UUID (FK) | Owner (null for anonymous) |
| display_name | String | Team/player name |
| draft_position | Integer | Position in draft order |
| budget_remaining | Integer | Remaining points (if budget enabled) |
| wins | Integer | Season win count |
| losses | Integer | Season loss count |
| ties | Integer | Season tie count |

#### TeamPokemon

A join table linking teams to their drafted Pokemon.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| team_id | UUID (FK) | Parent team |
| pokemon_id | Integer | PokeAPI Pokemon ID |
| pick_number | Integer | Overall pick number in draft |
| acquisition_type | Enum | drafted, traded, free_agent |
| points_spent | Integer | Cost paid (auction/salary cap) |

#### Match

A scheduled or completed match between two teams.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| season_id | UUID (FK) | Parent season |
| week | Integer | Week/round number |
| team_a_id | UUID (FK) | First team |
| team_b_id | UUID (FK) | Second team |
| scheduled_at | Timestamp | When match should occur |
| winner_id | UUID (FK) | Winning team (null if tie/pending) |
| result_data | JSONB | Detailed results (future: parsed replay) |

#### Trade

A trade of Pokemon between two teams.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| season_id | UUID (FK) | Parent season |
| proposer_team_id | UUID (FK) | Team proposing trade |
| recipient_team_id | UUID (FK) | Team receiving proposal |
| proposer_pokemon | UUID[] | Pokemon offered by proposer |
| recipient_pokemon | UUID[] | Pokemon requested from recipient |
| status | Enum | pending, accepted, rejected, cancelled |
| requires_approval | Boolean | Whether admin must approve |
| admin_approved | Boolean | Admin approval status |

---

## 4. Feature Specifications

### 4.1 League Management

#### Creating a League

Authenticated users can create leagues with the following options:

- **League name** (required)
- **Visibility** (public or private)
- **Default settings** (draft format, roster size, timer, etc.)
- **Template** (optional preset for common formats like OU, UU, etc.)

Upon creation, a unique invite link and invite code are generated.

#### League Templates

The platform provides preset templates for common competitive formats:

- **OU (OverUsed):** Standard competitive tier
- **UU (UnderUsed):** Second-tier competitive
- **Monotype:** Single-type team restrictions
- **Little Cup:** First-evolution Pokemon only
- **Custom:** Start from scratch

Templates pre-configure the Pokemon pool, point values (if applicable), and suggested roster sizes.

#### Joining a League

Users can join leagues via:

- **Invite link:** Direct URL shared by the league owner
- **Invite code:** Short code entered on the join page
- **Public discovery:** Browsing public leagues (if visibility is public)

#### League Administration

The league owner has exclusive access to administrative functions:

- Start new seasons
- Modify league settings
- Remove members
- Regenerate invite codes
- Configure trade approval requirements
- Approve/reject trades (if approval required)

### 4.2 Draft System

#### Draft Formats

The platform supports four draft formats:

| Format | Description |
|--------|-------------|
| Snake | Pick order reverses each round (1→8, 8→1, 1→8...). The fairest format for equal talent distribution. |
| Linear | Same pick order every round (1→8, 1→8...). Simpler but favors early picks. |
| Auction | Pokemon are nominated and teams bid. Highest bidder wins. Most complex but allows precise valuation. |
| Salary Cap | Combined with snake/linear. Each Pokemon has a fixed cost; teams must stay under budget. |

#### Snake/Linear Draft Flow

- Draft order is randomized or set by the league owner
- On their turn, users select an available Pokemon from the pool
- If salary cap is enabled, the Pokemon's cost is deducted from budget
- If the timer expires, a random available Pokemon (within budget if applicable) is assigned
- Draft continues until all teams have filled their rosters

#### Auction Draft Flow

- Nomination order follows snake or linear pattern (configurable)
- Nominating team puts up a Pokemon they can afford for bidding
- Minimum bid increment and bid timer are configurable
- When no new bids arrive within the timer, highest bidder wins
- Users cannot bid more than their remaining budget
- If a team runs out of budget before filling their roster, they cannot acquire more Pokemon

#### Pokemon Pool Configuration

League owners can define the available Pokemon in several ways:

- **Generation filter:** Select which generations to include
- **CSV upload:** Upload a custom list with optional point values
- **Exclusion list:** Ban specific Pokemon (e.g., legendaries)
- **Template:** Use a preset pool (OU, UU, etc.)

Pokemon data is sourced from PokeAPI. Regional forms (Alolan, Galarian, Hisuian, etc.) are treated as separate Pokemon. Mega evolutions and Gigantamax forms are not draftable; the base Pokemon is drafted and form changes occur in battle.

CSV uploads are validated against PokeAPI to ensure all Pokemon names/IDs are valid. Invalid entries generate clear error messages.

#### Live vs. Asynchronous Drafts

| Aspect | Live Draft | Async Draft |
|--------|-----------|-------------|
| User requirement | Anonymous or authenticated | Authenticated only |
| Timer | Seconds to minutes | Hours to days |
| Notifications | Real-time WebSocket | Discord DM/channel |
| Timeout behavior | Random pick | Random pick (after grace period) |

Note: Anonymous users can only participate in live drafts, not async.

#### Draft UI Features

- **Draft board:** Real-time view of all teams' picks
- **Available Pokemon list:** Searchable, filterable by type, generation, points
- **Pokemon details:** Full stats, types, abilities, sprite, tier information
- **Queue/favorites:** Users can pre-select Pokemon they're interested in
- **Budget tracker:** Visible remaining points (if salary cap enabled)
- **Pick timer:** Countdown display for current pick
- **Pick history:** Scrollable log of all picks
- **Mobile responsive:** Full functionality on mobile devices

### 4.3 Team Management & Trades

#### Team Export

Teams can be exported in multiple formats:

- **Pokemon Showdown paste:** Standard format for importing into Showdown
- **JSON:** Structured data for programmatic use
- **CSV:** Spreadsheet-compatible format

#### Trading

Trades can only occur during an active season. There is no trade deadline—trades are permitted throughout the entire season. The flow is:

1. Team A proposes a trade to Team B
2. Trade can be any number of Pokemon (not necessarily 1-for-1)
3. Team B accepts, rejects, or counters
4. If league requires admin approval, trade goes to owner for review
5. Upon final approval, Pokemon are swapped between teams

Note: Draft pick trading is not supported. Only Pokemon-for-Pokemon trades are allowed.

### 4.4 Scheduling & Match Results

#### Schedule Generation

When a season begins, the league owner generates a schedule using one of these formats:

| Format | Description |
|--------|-------------|
| Round Robin | Every team plays every other team once |
| Double Round Robin | Every team plays every other team twice |
| Swiss | Teams with similar records are paired each round |
| Single Elimination | Bracket format; one loss eliminates |
| Double Elimination | Bracket with losers bracket |
| Random Weekly | Random pairings generated each week |
| Custom | Admin manually sets all matchups |

Schedule format is set at season start and cannot change mid-season.

#### Recording Results

Match results can be recorded manually by either participant or the league owner. Required fields:

- Winner (or tie)
- Optional: Notes, replay link

#### Standings

The league summary page displays current standings, calculated from match results. Tiebreakers are configurable (head-to-head, point differential, etc.).

#### Future: Pokemon Showdown Replay Parsing

*[PLACEHOLDER] A future enhancement will allow users to paste a Pokemon Showdown replay URL or upload a replay file. The system will automatically extract match results and optionally track individual Pokemon statistics (KOs, usage, etc.).*

#### Future: Playoff Seeding

*[PLACEHOLDER] When transitioning from a regular season format (e.g., round robin) to a playoff bracket, the system will support configurable seeding rules. Details to be determined.*

### 4.5 Discord Integration

#### Architecture

The platform uses a centralized Discord bot hosted by the application. Users add the bot to their server via OAuth and configure notification preferences.

#### Account Linking

1. User authenticates with Discord OAuth on the platform
2. Discord user ID is linked to their platform account
3. User can now receive DM notifications and be identified in channels

#### League Bot Setup

- League owner adds bot to their Discord server
- Owner selects a channel for league notifications
- Owner configures which events trigger channel notifications

#### Notification Types

| Event | User Config (DM) | Admin Config (Channel) |
|-------|------------------|------------------------|
| Draft starting soon | ✓ | ✓ |
| It's your turn to pick | ✓ | — |
| A pick was made | ✓ | ✓ |
| Draft completed | ✓ | ✓ |
| Trade proposed to you | ✓ | — |
| Trade completed | ✓ | ✓ |
| Match scheduled (reminder) | ✓ | ✓ |
| Match result recorded | ✓ | ✓ |

---

## 5. Key User Flows

### 5.1 Anonymous Draft Session

1. Anonymous user visits homepage
2. Clicks "Start a Draft"
3. Configures draft settings (format, roster size, Pokemon pool, timer)
4. Optionally selects a template (OU, UU, etc.)
5. Enters display name
6. Receives unique draft URL and rejoin code
7. Shares link with friends
8. Other users (anonymous or authenticated) join via link
9. Creator starts the draft when ready
10. Live draft proceeds
11. At completion, all users can download team files
12. Draft session persists for 7 days for re-download

### 5.2 League Season Lifecycle

1. Owner creates league (optionally from template)
2. Users join via invite
3. Owner starts Season 1
4. Draft is conducted (live or async)
5. Schedule is generated
6. Matches occur (off-platform), results recorded
7. Trades can occur throughout
8. Season ends, final standings recorded
9. Owner can start Season 2 (new draft or keep teams)

---

## 6. Technical Architecture

### 6.1 Stack Overview

| Layer | Technology |
|-------|------------|
| Frontend | React (hosted on Netlify) |
| Backend API | FastAPI (Python) — REST endpoints |
| Real-time | FastAPI WebSocket — draft events |
| Database | PostgreSQL (Supabase) |
| Authentication | Supabase Auth (OAuth: Google, Discord) |
| Backend Hosting | Fly.io |
| Discord Bot | Python (discord.py), hosted on Fly.io |
| Pokemon Data | PokeAPI (cached locally) |

### 6.2 Real-time Draft Architecture

The live draft experience requires low-latency updates. The architecture:

1. Client connects to WebSocket endpoint with draft ID
2. Server maintains in-memory draft room state
3. Picks are validated server-side and broadcast to all connected clients
4. State is persisted to PostgreSQL on each pick for recovery
5. Disconnected clients can rejoin and receive current state

#### Draft Room State (In-Memory)

```json
{
  "draft_id": "uuid",
  "status": "live",
  "current_pick": 12,
  "pick_order": ["team1", "team2", "..."],
  "timer_end": "2024-12-15T10:30:00Z",
  "connected_users": ["user1", "user2"],
  "picks": [],
  "available_pokemon": []
}
```

#### WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| join_draft | Client → Server | `{ draft_id, user_token }` |
| draft_state | Server → Client | Full current state |
| make_pick | Client → Server | `{ pokemon_id }` |
| pick_made | Server → Clients | `{ team_id, pokemon_id, pick_number }` |
| turn_start | Server → Clients | `{ team_id, timer_end }` |
| timer_tick | Server → Clients | `{ seconds_remaining }` |
| place_bid | Client → Server | `{ pokemon_id, amount }` |
| bid_update | Server → Clients | `{ pokemon_id, bidder_id, amount }` |
| draft_complete | Server → Clients | `{ final_teams }` |
| error | Server → Client | `{ message, code }` |

### 6.3 Data Flow

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ React   │◄───►│ FastAPI │◄───►│ Postgres │
│(Netlify)│     │ (Fly.io)│     │(Supabase)│
└─────────┘     └────┬────┘     └──────────┘
                     │
                     ▼
              ┌────────────┐
              │ Discord Bot│
              └────────────┘
```

---

## 7. API Design

### 7.1 REST Endpoints

Base URL: `/api/v1`

#### Authentication

```
POST /auth/login          — OAuth callback
POST /auth/logout         — End session
GET  /auth/me             — Current user info
```

#### Leagues

```
POST /leagues             — Create league
GET  /leagues             — List user's leagues
GET  /leagues/public      — List public leagues
GET  /leagues/:id         — Get league details
PUT  /leagues/:id         — Update league settings
POST /leagues/:id/join    — Join league
POST /leagues/:id/seasons — Start new season
```

#### Drafts

```
POST /drafts              — Create draft (anonymous or league)
GET  /drafts/:id          — Get draft state
POST /drafts/:id/start    — Start draft
GET  /drafts/:id/export   — Export team (format param)
```

#### Teams

```
GET  /seasons/:id/teams   — List teams in season
GET  /teams/:id           — Get team details
GET  /teams/:id/pokemon   — List team's Pokemon
```

#### Trades

```
POST /trades              — Propose trade
GET  /trades/:id          — Get trade details
POST /trades/:id/accept   — Accept trade
POST /trades/:id/reject   — Reject trade
POST /trades/:id/approve  — Admin approve trade
```

#### Matches

```
GET  /seasons/:id/schedule   — Get schedule
POST /seasons/:id/schedule   — Generate schedule
GET  /seasons/:id/standings  — Get standings
POST /matches/:id/result     — Record result
```

#### Templates

```
GET  /templates              — List available templates
GET  /templates/:id          — Get template details
```

### 7.2 WebSocket Endpoint

```
ws://api.domain.com/ws/draft/:draft_id
```

---

## 8. Open Questions & Future Considerations

### 8.1 Resolved Decisions

| Question | Decision |
|----------|----------|
| Trade deadline? | No — trades allowed throughout the entire season |
| Async drafts for anonymous users? | No — anonymous users can only do live drafts |
| Pokemon data in draft UI? | All available data — stats, types, abilities, sprites, tier info |
| League templates? | Yes — presets for OU, UU, Monotype, Little Cup, etc. |

### 8.2 Future Features

- **Pokemon Showdown replay parsing:** Automatic result extraction and Pokemon statistics tracking
- **Advanced statistics:** Per-Pokemon win rates, usage rates, KO counts across seasons
- **Playoff seeding:** Configurable rules for transitioning from regular season to playoffs
- **Draft pick trading:** Trading future draft picks between teams
- **Co-admin support:** Allow league owners to designate additional administrators
- **Keeper/retention drafts:** Keep a subset of Pokemon between seasons

---

*— End of Document —*
