from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import asyncio


@dataclass
class DraftParticipant:
    """A participant in a draft."""
    team_id: UUID
    user_id: Optional[UUID]
    display_name: str
    session_token: Optional[str]
    draft_position: int
    budget_remaining: Optional[int]
    pokemon: List[int] = field(default_factory=list)


@dataclass
class DraftPick:
    """A pick made in the draft."""
    pick_number: int
    team_id: UUID
    pokemon_id: int
    points_spent: Optional[int]
    picked_at: datetime


class DraftRoom:
    """
    In-memory state for a live draft.

    Maintains the current state of a draft and handles pick logic.
    State is persisted to database on each pick for recovery.
    """

    def __init__(self, draft_id: UUID):
        self.draft_id = draft_id
        self.status: str = "pending"  # pending, live, paused, completed
        self.format: str = "snake"  # snake, linear, auction
        self.is_loading: bool = False  # Track if room is being loaded
        self.load_lock = asyncio.Lock()  # Lock to prevent concurrent loading

        self.roster_size: int = 6
        self.timer_seconds: Optional[int] = 90
        self.budget_enabled: bool = False
        self.budget_per_team: Optional[int] = None
        self.rejoin_code: Optional[str] = None

        self.current_pick: int = 0
        self.timer_end: Optional[datetime] = None
        self.timer_task: Optional[asyncio.Task] = None

        self.participants: Dict[UUID, DraftParticipant] = {}
        self.pick_order: List[UUID] = []
        self.picks: List[DraftPick] = []
        self.available_pokemon: List[dict] = []

        # Auction-specific settings
        self.nomination_timer_seconds: Optional[int] = None
        self.bid_timer_seconds: int = 15
        self.min_bid: int = 1
        self.bid_increment: int = 1

        # Auction-specific state
        self.auction_phase: str = "nominating"  # "nominating" | "bidding" | "idle"
        self.current_nomination: Optional[dict] = None  # {pokemon_id, pokemon_name, nominator_id, nominator_name}
        self.current_highest_bid: Optional[dict] = None  # {team_id, team_name, amount}
        self.bid_history: List[dict] = []
        self.nominating_team_index: int = 0  # Index in pick_order for nomination rotation
        self.bid_timer_task: Optional[asyncio.Task] = None

    def get_state(self) -> dict:
        """Get the current state as a JSON-serializable dict."""
        # Build a map of pokemon_id -> name for pick lookups
        pokemon_names = {p.get("id") or p.get("pokemon_id"): p.get("name", "") for p in self.available_pokemon}
        # Also include picked pokemon names
        for pick in self.picks:
            if pick.pokemon_id not in pokemon_names:
                pokemon_names[pick.pokemon_id] = f"Pokemon #{pick.pokemon_id}"

        return {
            "draft_id": str(self.draft_id),
            "rejoin_code": self.rejoin_code,
            "status": self.status,
            "format": self.format,
            "current_pick": self.current_pick,
            "roster_size": self.roster_size,
            "timer_seconds": self.timer_seconds,
            "timer_end": self.timer_end.isoformat() if self.timer_end else None,
            "pick_order": [str(pid) for pid in self.pick_order],
            "teams": [
                {
                    "team_id": str(p.team_id),
                    "display_name": p.display_name,
                    "draft_position": p.draft_position,
                    "budget_remaining": p.budget_remaining,
                    "pokemon": p.pokemon,
                }
                for p in self.participants.values()
            ],
            "picks": [
                {
                    "pick_number": pick.pick_number,
                    "team_id": str(pick.team_id),
                    "team_name": self.participants[pick.team_id].display_name if pick.team_id in self.participants else "Unknown",
                    "pokemon_id": pick.pokemon_id,
                    "pokemon_name": pokemon_names.get(pick.pokemon_id, f"Pokemon #{pick.pokemon_id}"),
                    "points_spent": pick.points_spent,
                    "picked_at": pick.picked_at.isoformat(),
                }
                for pick in self.picks
            ],
            "available_pokemon": [
                {
                    "id": p.get("id") or p.get("pokemon_id"),
                    "name": p.get("name", ""),
                    "types": p.get("types", []),
                    "sprite": p.get("sprite", f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p.get('id') or p.get('pokemon_id')}.png"),
                    "points": p.get("points"),
                    "stats": p.get("stats"),
                    "generation": p.get("generation"),
                    "is_legendary": p.get("is_legendary", False),
                    "is_mythical": p.get("is_mythical", False),
                    "abilities": p.get("abilities", []),
                }
                for p in self.available_pokemon
            ],
            "budget_enabled": self.budget_enabled,
            "budget_per_team": self.budget_per_team,
            # Auction-specific settings
            "nomination_timer_seconds": self.nomination_timer_seconds,
            "bid_timer_seconds": self.bid_timer_seconds,
            "min_bid": self.min_bid,
            "bid_increment": self.bid_increment,
            # Auction state
            "auction_phase": self.auction_phase if self.format == "auction" else None,
            "current_nomination": self.current_nomination,
            "current_highest_bid": self.current_highest_bid,
            "bid_timer_end": self.timer_end.isoformat() if self.timer_end and self.format == "auction" and self.auction_phase == "bidding" else None,
        }

    def get_current_team(self) -> Optional[UUID]:
        """Get the team ID whose turn it is to pick."""
        if not self.pick_order or self.current_pick >= len(self.pick_order) * self.roster_size:
            return None

        if self.format == "auction":
            # For auction: return nominating team during nominating phase, None during bidding
            if self.auction_phase == "nominating":
                return self.get_nominating_team()
            return None  # During bidding, all teams can bid
        elif self.format == "snake":
            round_num = self.current_pick // len(self.pick_order)
            position_in_round = self.current_pick % len(self.pick_order)
            if round_num % 2 == 1:
                position_in_round = len(self.pick_order) - 1 - position_in_round
            return self.pick_order[position_in_round]
        else:  # linear
            return self.pick_order[self.current_pick % len(self.pick_order)]

    def get_nominating_team(self) -> Optional[UUID]:
        """Get the team ID whose turn it is to nominate (auction only)."""
        if not self.pick_order:
            return None
        # Rotation through teams for nominations
        return self.pick_order[self.nominating_team_index % len(self.pick_order)]

    def get_teams_needing_pokemon(self) -> List[UUID]:
        """Get list of teams that still need Pokemon (haven't filled roster)."""
        teams_needing = []
        for team_id, participant in self.participants.items():
            if len(participant.pokemon) < self.roster_size:
                teams_needing.append(team_id)
        return teams_needing

    def advance_nominating_team(self):
        """Advance to the next team that needs Pokemon for nomination."""
        if not self.pick_order:
            return

        teams_needing = self.get_teams_needing_pokemon()
        if not teams_needing:
            return

        # Find next team in rotation that still needs Pokemon
        start_index = self.nominating_team_index
        for _ in range(len(self.pick_order)):
            self.nominating_team_index = (self.nominating_team_index + 1) % len(self.pick_order)
            next_team = self.pick_order[self.nominating_team_index]
            if next_team in teams_needing:
                return

        # Fallback: reset to start if somehow no valid team found
        self.nominating_team_index = start_index

    def is_pokemon_available(self, pokemon_id: int) -> bool:
        """Check if a Pokemon is still available."""
        picked_ids = {pick.pokemon_id for pick in self.picks}
        return pokemon_id not in picked_ids

    def can_afford(self, team_id: UUID, points: int) -> bool:
        """Check if a team can afford a Pokemon (budget mode only)."""
        if not self.budget_enabled:
            return True
        participant = self.participants.get(team_id)
        if not participant or participant.budget_remaining is None:
            return False
        return participant.budget_remaining >= points

    def has_roster_space(self, team_id: UUID) -> bool:
        """Check if a team has roster space for another Pokemon."""
        participant = self.participants.get(team_id)
        if not participant:
            return False
        return len(participant.pokemon) < self.roster_size

    def clear_auction_state(self):
        """Clear current auction state after a pick is made."""
        self.current_nomination = None
        self.current_highest_bid = None
        self.bid_history = []
        self.auction_phase = "nominating"
        if self.bid_timer_task:
            self.bid_timer_task.cancel()
            self.bid_timer_task = None
        self.timer_end = None

    def start_nomination(self, pokemon_id: int, pokemon_name: str, nominator_id: UUID):
        """Start a new nomination and auto-bid at min_bid."""
        nominator = self.participants.get(nominator_id)
        nominator_name = nominator.display_name if nominator else "Unknown"

        self.current_nomination = {
            "pokemon_id": pokemon_id,
            "pokemon_name": pokemon_name,
            "nominator_id": str(nominator_id),
            "nominator_name": nominator_name,
        }

        # Auto-bid at min_bid
        self.current_highest_bid = {
            "team_id": str(nominator_id),
            "team_name": nominator_name,
            "amount": self.min_bid,
        }

        self.bid_history = [{
            "team_id": str(nominator_id),
            "team_name": nominator_name,
            "amount": self.min_bid,
        }]

        self.auction_phase = "bidding"

    def place_auction_bid(self, team_id: UUID, amount: int) -> bool:
        """Place a bid in the current auction. Returns True if valid."""
        if not self.current_nomination or self.auction_phase != "bidding":
            return False

        participant = self.participants.get(team_id)
        if not participant:
            return False

        # Record the bid
        self.current_highest_bid = {
            "team_id": str(team_id),
            "team_name": participant.display_name,
            "amount": amount,
        }

        self.bid_history.append({
            "team_id": str(team_id),
            "team_name": participant.display_name,
            "amount": amount,
        })

        return True

    def make_pick(self, team_id: UUID, pokemon_id: int, points: Optional[int] = None) -> DraftPick:
        """
        Record a pick. Returns the pick or raises ValueError if invalid.
        For auction format, turn check is skipped (winner determined by bidding).
        """
        if self.status != "live":
            raise ValueError("Draft is not live")

        # For non-auction formats, verify turn order
        if self.format != "auction":
            current_team = self.get_current_team()
            if current_team != team_id:
                raise ValueError("Not your turn")

        if not self.is_pokemon_available(pokemon_id):
            raise ValueError("Pokemon not available")

        if self.budget_enabled and points is not None:
            if not self.can_afford(team_id, points):
                raise ValueError("Cannot afford this Pokemon")
            self.participants[team_id].budget_remaining -= points

        pick = DraftPick(
            pick_number=self.current_pick,
            team_id=team_id,
            pokemon_id=pokemon_id,
            points_spent=points,
            picked_at=datetime.utcnow(),
        )
        self.picks.append(pick)
        self.participants[team_id].pokemon.append(pokemon_id)
        self.current_pick += 1

        # Check if draft is complete
        total_picks_needed = len(self.pick_order) * self.roster_size
        if self.current_pick >= total_picks_needed:
            self.status = "completed"
        elif self.format != "auction":
            # Reset timer for next pick (non-auction only; auction handles its own timers)
            self.start_timer()

        return pick

    def start_timer(self):
        """Start the pick timer."""
        if self.timer_seconds:
            self.timer_end = datetime.utcnow() + timedelta(seconds=self.timer_seconds)

    def start_draft(self):
        """Start the draft."""
        if self.status != "pending":
            raise ValueError("Draft already started")
        self.status = "live"
        self.start_timer()

    def pause_draft(self):
        """Pause the draft."""
        if self.status != "live":
            raise ValueError("Draft is not live")
        self.status = "paused"
        self.timer_end = None

    def resume_draft(self):
        """Resume a paused draft."""
        if self.status != "paused":
            raise ValueError("Draft is not paused")
        self.status = "live"
        self.start_timer()
