"""
Bracket generation service for single and double elimination tournaments.
"""
import math
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.match import Match as MatchModel
from app.models.team import Team


def next_power_of_2(n: int) -> int:
    """Return the smallest power of 2 >= n."""
    return 1 << (n - 1).bit_length()


def generate_bracket_positions(bracket_size: int) -> list[int]:
    """
    Generate standard bracket seeding positions.
    For 8 teams: [1, 8, 4, 5, 2, 7, 3, 6]
    This ensures that 1 and 2 meet in the finals if they both keep winning.
    """
    if bracket_size == 2:
        return [1, 2]

    half = bracket_size // 2
    positions = generate_bracket_positions(half)

    result = []
    for pos in positions:
        result.append(pos)
        result.append(bracket_size + 1 - pos)

    return result


def get_round_name(bracket_round: int, total_rounds: int, is_losers: bool = False) -> str:
    """Get display name for bracket round."""
    if bracket_round == 0:
        return "Grand Finals"

    prefix = "Losers " if is_losers else ""
    rounds_from_final = total_rounds - abs(bracket_round)

    names = {
        0: "Finals",
        1: "Semifinals",
        2: "Quarterfinals",
        3: "Round of 16",
        4: "Round of 32",
        5: "Round of 64",
    }

    return prefix + names.get(rounds_from_final, f"Round {abs(bracket_round)}")


def generate_single_elimination_bracket(
    season_id: UUID,
    team_ids: list[UUID],
    seeds: list[UUID],
) -> list[MatchModel]:
    """
    Generate single elimination bracket matches.

    Seeding follows standard bracket seeding:
    - 8 teams: 1v8, 4v5, 3v6, 2v7 (so 1 and 2 meet in finals if both win)
    - Byes go to top seeds if team count isn't power of 2

    Args:
        season_id: The season ID
        team_ids: List of team IDs participating
        seeds: Ordered list of team IDs by seed (index 0 = #1 seed)

    Returns:
        List of Match models (not yet committed to DB)
    """
    num_teams = len(team_ids)
    bracket_size = next_power_of_2(num_teams)
    total_rounds = int(math.log2(bracket_size))
    num_byes = bracket_size - num_teams

    # Generate standard bracket seeding positions
    seed_positions = generate_bracket_positions(bracket_size)

    # Create seed position to team ID mapping
    # Seeds list has top seed at index 0
    seed_to_team = {i + 1: seeds[i] for i in range(len(seeds))}

    matches: list[MatchModel] = []
    match_lookup: dict[tuple[int, int], MatchModel] = {}  # (round, position) -> match

    # Round 1: Create all first-round matches
    for position in range(bracket_size // 2):
        seed_a_num = seed_positions[position * 2]
        seed_b_num = seed_positions[position * 2 + 1]

        team_a = seed_to_team.get(seed_a_num)
        team_b = seed_to_team.get(seed_b_num)

        is_bye = team_a is None or team_b is None

        match = MatchModel(
            id=uuid.uuid4(),
            season_id=season_id,
            week=1,
            bracket_round=1,
            bracket_position=position,
            team_a_id=team_a if team_a else team_b,  # Bye: the present team is team_a
            team_b_id=team_b if not is_bye else None,
            seed_a=seed_a_num if team_a else seed_b_num,
            seed_b=seed_b_num if team_b and not is_bye else None,
            is_bye=is_bye,
            schedule_format='single_elimination',
        )
        matches.append(match)
        match_lookup[(1, position)] = match

    # Create subsequent rounds (empty, to be filled by progression)
    for round_num in range(2, total_rounds + 1):
        matches_in_round = bracket_size // (2 ** round_num)
        for position in range(matches_in_round):
            match = MatchModel(
                id=uuid.uuid4(),
                season_id=season_id,
                week=round_num,
                bracket_round=round_num,
                bracket_position=position,
                team_a_id=None,  # TBD
                team_b_id=None,  # TBD
                schedule_format='single_elimination',
            )
            matches.append(match)
            match_lookup[(round_num, position)] = match

    # Link matches: set next_match_id
    # Round N position P feeds into Round N+1 position P//2
    for match in matches:
        if match.bracket_round < total_rounds:
            next_position = match.bracket_position // 2
            next_round = match.bracket_round + 1
            next_match = match_lookup.get((next_round, next_position))
            if next_match:
                match.next_match_id = next_match.id

    return matches


def generate_double_elimination_bracket(
    season_id: UUID,
    team_ids: list[UUID],
    seeds: list[UUID],
    include_bracket_reset: bool = True,
) -> list[MatchModel]:
    """
    Generate double elimination bracket.

    Structure:
    - Winners bracket: Standard single-elim structure
    - Losers bracket: Receives losers from winners bracket
    - Grand finals: Winners bracket champion vs Losers bracket champion
    - Optional bracket reset if losers bracket champion wins grand finals

    Losers bracket rounds are numbered with negative integers:
    - -1: First losers round
    - -2: Second losers round, etc.
    """
    num_teams = len(team_ids)
    bracket_size = next_power_of_2(num_teams)
    total_winners_rounds = int(math.log2(bracket_size))

    matches: list[MatchModel] = []
    winners_lookup: dict[tuple[int, int], MatchModel] = {}
    losers_lookup: dict[tuple[int, int], MatchModel] = {}

    # Create seed position to team ID mapping
    seed_positions = generate_bracket_positions(bracket_size)
    seed_to_team = {i + 1: seeds[i] for i in range(len(seeds))}

    # ===== WINNERS BRACKET =====
    # Round 1
    for position in range(bracket_size // 2):
        seed_a_num = seed_positions[position * 2]
        seed_b_num = seed_positions[position * 2 + 1]

        team_a = seed_to_team.get(seed_a_num)
        team_b = seed_to_team.get(seed_b_num)

        is_bye = team_a is None or team_b is None

        match = MatchModel(
            id=uuid.uuid4(),
            season_id=season_id,
            week=1,
            bracket_round=1,
            bracket_position=position,
            team_a_id=team_a if team_a else team_b,
            team_b_id=team_b if not is_bye else None,
            seed_a=seed_a_num if team_a else seed_b_num,
            seed_b=seed_b_num if team_b and not is_bye else None,
            is_bye=is_bye,
            schedule_format='double_elimination',
        )
        matches.append(match)
        winners_lookup[(1, position)] = match

    # Winners bracket rounds 2+
    for round_num in range(2, total_winners_rounds + 1):
        matches_in_round = bracket_size // (2 ** round_num)
        for position in range(matches_in_round):
            match = MatchModel(
                id=uuid.uuid4(),
                season_id=season_id,
                week=round_num,
                bracket_round=round_num,
                bracket_position=position,
                team_a_id=None,
                team_b_id=None,
                schedule_format='double_elimination',
            )
            matches.append(match)
            winners_lookup[(round_num, position)] = match

    # Link winners bracket
    for match in matches:
        if match.bracket_round and match.bracket_round > 0 and match.bracket_round < total_winners_rounds:
            next_position = match.bracket_position // 2
            next_round = match.bracket_round + 1
            next_match = winners_lookup.get((next_round, next_position))
            if next_match:
                match.next_match_id = next_match.id

    # ===== LOSERS BRACKET =====
    # The losers bracket has a more complex structure:
    # - After WR1: Losers from WR1 play each other
    # - After WR2: Losers from WR2 join, play winners from LR1
    # - Pattern continues...

    # For a bracket_size of 8 (3 winners rounds), losers bracket has:
    # LR1: 4 matches (WR1 losers face off)
    # LR2: 2 matches (LR1 winners vs WR2 losers)
    # LR3: 1 match (LR2 winners face off)
    # LR4: 1 match (LR3 winner vs WR3 loser)

    # Calculate losers bracket structure
    # Each winners round creates losers, losers bracket alternates between:
    # - "Minor" round: losers from winners bracket drop in
    # - "Major" round: purely losers bracket progression

    current_losers_count = bracket_size // 2  # Losers from round 1
    losers_round = 1
    week_offset = total_winners_rounds + 1  # Losers bracket starts after winners finals

    # First losers round: R1 losers play each other
    if current_losers_count > 0:
        matches_in_round = current_losers_count // 2
        for position in range(matches_in_round):
            match = MatchModel(
                id=uuid.uuid4(),
                season_id=season_id,
                week=week_offset,
                bracket_round=-losers_round,  # Negative for losers bracket
                bracket_position=position,
                team_a_id=None,
                team_b_id=None,
                schedule_format='double_elimination',
            )
            matches.append(match)
            losers_lookup[(-losers_round, position)] = match

        current_losers_count = matches_in_round
        losers_round += 1
        week_offset += 1

    # Remaining losers rounds
    for winners_round in range(2, total_winners_rounds + 1):
        # Minor round: current losers bracket survivors vs losers dropping from winners
        losers_from_winners = bracket_size // (2 ** winners_round)

        # Match count is the current losers bracket size (they absorb the new losers)
        matches_in_round = current_losers_count
        for position in range(matches_in_round):
            match = MatchModel(
                id=uuid.uuid4(),
                season_id=season_id,
                week=week_offset,
                bracket_round=-losers_round,
                bracket_position=position,
                team_a_id=None,  # From previous losers round
                team_b_id=None,  # Drops from winners bracket
                schedule_format='double_elimination',
            )
            matches.append(match)
            losers_lookup[(-losers_round, position)] = match

        losers_round += 1
        week_offset += 1

        # Major round: losers bracket internal matchups (if there are enough)
        if matches_in_round > 1:
            matches_in_major = matches_in_round // 2
            for position in range(matches_in_major):
                match = MatchModel(
                    id=uuid.uuid4(),
                    season_id=season_id,
                    week=week_offset,
                    bracket_round=-losers_round,
                    bracket_position=position,
                    team_a_id=None,
                    team_b_id=None,
                    schedule_format='double_elimination',
                )
                matches.append(match)
                losers_lookup[(-losers_round, position)] = match

            current_losers_count = matches_in_major
            losers_round += 1
            week_offset += 1
        else:
            current_losers_count = matches_in_round

    # Link losers bracket internally
    for (round_num, position), match in losers_lookup.items():
        if round_num < -1:  # Not the final losers round
            next_round = round_num + 1
            next_position = position // 2 if round_num % 2 == 0 else position
            next_match = losers_lookup.get((next_round, next_position))
            if next_match:
                match.next_match_id = next_match.id

    # Link winners bracket losers to losers bracket
    for (winners_round, position), match in winners_lookup.items():
        if winners_round == 1:
            # R1 losers go to first losers round
            # Position mapping: pairs go to same losers match
            loser_position = position // 2
            loser_match = losers_lookup.get((-1, loser_position))
            if loser_match:
                match.loser_next_match_id = loser_match.id
        elif winners_round < total_winners_rounds:
            # Later rounds: losers drop into alternating losers rounds
            # Find the appropriate minor round
            losers_minor_round = -(2 * (winners_round - 1))
            loser_match = losers_lookup.get((losers_minor_round, position))
            if loser_match:
                match.loser_next_match_id = loser_match.id

    # ===== GRAND FINALS =====
    losers_final_round = min(losers_lookup.keys(), key=lambda x: x[0])[0] if losers_lookup else -1

    grand_finals = MatchModel(
        id=uuid.uuid4(),
        season_id=season_id,
        week=week_offset,
        bracket_round=0,  # 0 = Grand Finals
        bracket_position=0,
        team_a_id=None,  # Winners bracket champion
        team_b_id=None,  # Losers bracket champion
        schedule_format='double_elimination',
    )
    matches.append(grand_finals)

    # Link winners finals to grand finals
    winners_final = winners_lookup.get((total_winners_rounds, 0))
    if winners_final:
        winners_final.next_match_id = grand_finals.id

    # Link losers finals to grand finals
    losers_final = losers_lookup.get((losers_final_round, 0))
    if losers_final:
        losers_final.next_match_id = grand_finals.id

    # ===== BRACKET RESET =====
    if include_bracket_reset:
        bracket_reset = MatchModel(
            id=uuid.uuid4(),
            season_id=season_id,
            week=week_offset + 1,
            bracket_round=0,
            bracket_position=1,
            team_a_id=None,
            team_b_id=None,
            is_bracket_reset=True,
            schedule_format='double_elimination',
        )
        grand_finals.next_match_id = bracket_reset.id
        matches.append(bracket_reset)

    return matches


async def process_bracket_progression(
    match: MatchModel,
    winner_id: UUID,
    loser_id: Optional[UUID],
    db,  # AsyncSession
) -> None:
    """
    After a bracket match result is recorded, advance teams to next matches.

    Args:
        match: The match that was just completed
        winner_id: ID of the winning team
        loser_id: ID of the losing team (None for byes)
        db: Database session
    """
    from sqlalchemy import select

    if not match.schedule_format or match.schedule_format == 'round_robin':
        return  # No progression for round robin

    # Determine winner's seed
    winner_seed = match.seed_a if winner_id == match.team_a_id else match.seed_b
    loser_seed = match.seed_b if winner_id == match.team_a_id else match.seed_a

    # 1. Advance winner to next match
    if match.next_match_id:
        next_result = await db.execute(
            select(MatchModel).where(MatchModel.id == match.next_match_id)
        )
        next_match = next_result.scalar_one_or_none()

        if next_match:
            # Handle grand finals bracket reset specially
            if match.bracket_round == 0 and not match.is_bracket_reset:
                # Grand finals: check if losers bracket champion won
                if match.schedule_format == 'double_elimination':
                    # In grand finals, team_b is from losers bracket
                    if winner_id == match.team_b_id:
                        # Losers bracket winner won, activate bracket reset
                        next_match.team_a_id = match.team_a_id  # Winners bracket champ
                        next_match.team_b_id = match.team_b_id  # Losers bracket champ
                        next_match.seed_a = match.seed_a
                        next_match.seed_b = match.seed_b
                    # else: Winners bracket champion won, bracket reset not needed
            else:
                # Standard progression: even positions go to team_a, odd to team_b
                if match.bracket_position is not None and match.bracket_position % 2 == 0:
                    next_match.team_a_id = winner_id
                    next_match.seed_a = winner_seed
                else:
                    next_match.team_b_id = winner_id
                    next_match.seed_b = winner_seed

    # 2. For double elim: send loser to losers bracket
    if match.loser_next_match_id and loser_id:
        loser_result = await db.execute(
            select(MatchModel).where(MatchModel.id == match.loser_next_match_id)
        )
        loser_match = loser_result.scalar_one_or_none()

        if loser_match:
            # Assign loser to losers bracket match
            # Losers typically fill team_b slot (team_a is from previous losers round)
            if loser_match.team_a_id is None:
                loser_match.team_a_id = loser_id
                loser_match.seed_a = loser_seed
            else:
                loser_match.team_b_id = loser_id
                loser_match.seed_b = loser_seed

    await db.flush()


def process_bye_matches(matches: list[MatchModel]) -> list[tuple[MatchModel, UUID]]:
    """
    Find bye matches and auto-complete them.
    Returns list of (match, winner_id) tuples for bye matches.
    """
    bye_results = []
    for match in matches:
        if match.is_bye and match.team_a_id and not match.winner_id:
            match.winner_id = match.team_a_id
            match.recorded_at = datetime.utcnow()
            bye_results.append((match, match.team_a_id))
    return bye_results
