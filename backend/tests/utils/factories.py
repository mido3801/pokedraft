"""
Factory utilities for creating test data.

This module provides factory functions for creating test instances of models
with sensible defaults and easy customization via parametrization.

Usage:
    from tests.utils.factories import UserFactory, LeagueFactory

    async def test_something(db_session):
        user = await UserFactory.create(db_session, email="custom@test.com")
        league = await LeagueFactory.create(db_session, owner=user)
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    League,
    LeagueMembership,
    Season,
    Draft,
    DraftPick,
    Team,
    Trade,
    Match,
    Pokemon,
    PokemonType,
    PokemonAbility,
    PoolPreset,
    WaiverClaim,
)
from app.models.waiver import WaiverClaimStatus, WaiverProcessingType

fake = Faker()


# ============================================================================
# Base Factory Class
# ============================================================================


class BaseFactory:
    """Base factory class with common utilities."""

    @classmethod
    async def create(cls, db_session: AsyncSession, **kwargs):
        """
        Create and persist an instance to the database.

        Args:
            db_session: Database session
            **kwargs: Field overrides

        Returns:
            Created model instance
        """
        instance = await cls.build(**kwargs)
        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)
        return instance

    @classmethod
    async def build(cls, **kwargs):
        """
        Build an instance without persisting to database.

        Args:
            **kwargs: Field overrides

        Returns:
            Model instance (not persisted)
        """
        raise NotImplementedError("Subclasses must implement build()")

    @classmethod
    async def create_batch(cls, db_session: AsyncSession, count: int, **kwargs):
        """
        Create multiple instances.

        Args:
            db_session: Database session
            count: Number of instances to create
            **kwargs: Field overrides applied to all instances

        Returns:
            List of created instances
        """
        instances = []
        for _ in range(count):
            instance = await cls.create(db_session, **kwargs)
            instances.append(instance)
        return instances


# ============================================================================
# User Factory
# ============================================================================


class UserFactory(BaseFactory):
    """Factory for creating User instances."""

    @classmethod
    async def build(
        cls,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        discord_id: Optional[str] = None,
        discord_username: Optional[str] = None,
    ) -> User:
        """Build a User instance."""
        return User(
            email=email or fake.email(),
            display_name=display_name or fake.user_name(),
            avatar_url=avatar_url or fake.image_url(),
            discord_id=discord_id,
            discord_username=discord_username,
        )


# ============================================================================
# League Factory
# ============================================================================


class LeagueFactory(BaseFactory):
    """Factory for creating League instances."""

    @classmethod
    async def build(
        cls,
        name: Optional[str] = None,
        owner_id: Optional[int] = None,
        invite_code: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> League:
        """Build a League instance."""
        return League(
            name=name or f"Test League {fake.word().title()}",
            owner_id=owner_id,
            invite_code=invite_code or fake.lexify(text="??????").upper(),
            settings=settings or {},
        )

    @classmethod
    async def create_with_owner(
        cls,
        db_session: AsyncSession,
        owner: Optional[User] = None,
        **kwargs,
    ) -> League:
        """Create a league with an owner."""
        if owner is None:
            owner = await UserFactory.create(db_session)

        league = await cls.create(db_session, owner_id=owner.id, **kwargs)
        return league

    @classmethod
    async def create_with_members(
        cls,
        db_session: AsyncSession,
        member_count: int = 3,
        **kwargs,
    ) -> tuple[League, List[User]]:
        """
        Create a league with multiple members including owner.

        Returns:
            Tuple of (league, list of members including owner)
        """
        owner = await UserFactory.create(db_session)
        league = await cls.create(db_session, owner_id=owner.id, **kwargs)

        members = [owner]
        for _ in range(member_count - 1):
            member = await UserFactory.create(db_session)
            membership = LeagueMembership(
                league_id=league.id,
                user_id=member.id,
                is_active=True,
            )
            db_session.add(membership)
            members.append(member)

        await db_session.flush()
        return league, members


# ============================================================================
# Season Factory
# ============================================================================


class SeasonFactory(BaseFactory):
    """Factory for creating Season instances."""

    @classmethod
    async def build(
        cls,
        league_id: Optional[int] = None,
        season_number: Optional[int] = None,
        status: str = "pre_draft",
        settings: Optional[dict] = None,
    ) -> Season:
        """Build a Season instance."""
        return Season(
            league_id=league_id,
            season_number=season_number or fake.random_int(1, 10),
            status=status,
            settings=settings or {},
        )

    @classmethod
    async def create_with_league(
        cls,
        db_session: AsyncSession,
        league: Optional[League] = None,
        **kwargs,
    ) -> Season:
        """Create a season with a league."""
        if league is None:
            league, _ = await LeagueFactory.create_with_members(db_session)

        season = await cls.create(db_session, league_id=league.id, **kwargs)
        return season


# ============================================================================
# Draft Factory
# ============================================================================


class DraftFactory(BaseFactory):
    """Factory for creating Draft instances."""

    @classmethod
    async def build(
        cls,
        season_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        format: str = "snake",
        status: str = "pending",
        roster_size: int = 6,
        timer_seconds: int = 90,
        budget_enabled: bool = False,
        budget_per_team: Optional[int] = None,
        pokemon_pool: Optional[dict] = None,
        session_token: Optional[str] = None,
        rejoin_code: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Draft:
        """Build a Draft instance."""
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(hours=24)

        return Draft(
            season_id=season_id,
            creator_id=creator_id,
            format=format,
            status=status,
            roster_size=roster_size,
            timer_seconds=timer_seconds,
            budget_enabled=budget_enabled,
            budget_per_team=budget_per_team or (100 if budget_enabled else None),
            pokemon_pool=pokemon_pool or {"pool": []},
            session_token=session_token or str(uuid4()),
            rejoin_code=rejoin_code or f"{fake.word().upper()}-{fake.random_int(1000, 9999)}",
            expires_at=expires_at,
            started_at=started_at,
            completed_at=completed_at,
        )

    @classmethod
    async def create_with_season(
        cls,
        db_session: AsyncSession,
        season: Optional[Season] = None,
        **kwargs,
    ) -> Draft:
        """Create a draft with a season."""
        if season is None:
            season = await SeasonFactory.create_with_league(db_session)

        draft = await cls.create(db_session, season_id=season.id, **kwargs)
        return draft


# ============================================================================
# Team Factory
# ============================================================================


class TeamFactory(BaseFactory):
    """Factory for creating Team instances."""

    @classmethod
    async def build(
        cls,
        draft_id: Optional[int] = None,
        season_id: Optional[int] = None,
        user_id: Optional[int] = None,
        session_token: Optional[str] = None,
        display_name: Optional[str] = None,
        draft_position: int = 1,
        budget_remaining: Optional[int] = None,
        wins: int = 0,
        losses: int = 0,
        ties: int = 0,
    ) -> Team:
        """Build a Team instance."""
        return Team(
            draft_id=draft_id,
            season_id=season_id,
            user_id=user_id,
            session_token=session_token,
            display_name=display_name or f"Team {fake.last_name()}",
            draft_position=draft_position,
            budget_remaining=budget_remaining,
            wins=wins,
            losses=losses,
            ties=ties,
        )

    @classmethod
    async def create_for_draft(
        cls,
        db_session: AsyncSession,
        draft: Draft,
        user: Optional[User] = None,
        **kwargs,
    ) -> Team:
        """Create a team for a draft."""
        if user is None:
            user = await UserFactory.create(db_session)

        team = await cls.create(
            db_session,
            draft_id=draft.id,
            season_id=draft.season_id,
            user_id=user.id,
            **kwargs,
        )
        return team


# ============================================================================
# Pokemon Factory
# ============================================================================


class PokemonFactory(BaseFactory):
    """Factory for creating Pokemon instances."""

    @classmethod
    async def build(
        cls,
        identifier: Optional[str] = None,
        species_id: int = 1,
        height: int = 10,
        weight: int = 100,
        base_experience: Optional[int] = 100,
        is_default: bool = True,
        generation: int = 1,
        base_stat_total: int = 400,
        evolution_stage: str = "unevolved",
        is_legendary: bool = False,
        is_mythical: bool = False,
    ) -> Pokemon:
        """Build a Pokemon instance."""
        return Pokemon(
            identifier=identifier or fake.first_name().lower(),
            species_id=species_id,
            height=height,
            weight=weight,
            base_experience=base_experience,
            is_default=is_default,
            generation=generation,
            base_stat_total=base_stat_total,
            evolution_stage=evolution_stage,
            is_legendary=is_legendary,
            is_mythical=is_mythical,
        )

    @classmethod
    async def create(cls, db_session: AsyncSession, **kwargs):
        """
        Create and persist a Pokemon with its species.
        This override creates the species first if needed.
        """
        from app.models import PokemonSpecies

        # Extract custom parameters
        identifier = kwargs.get('identifier', fake.first_name().lower())
        generation = kwargs.get('generation', kwargs.get('generation_id', 1))
        is_legendary = kwargs.get('is_legendary', False)
        is_mythical = kwargs.get('is_mythical', False)

        # Create species first
        species = PokemonSpecies(
            identifier=f"{identifier}-species",
            generation_id=generation,
            is_legendary=is_legendary,
            is_mythical=is_mythical,
        )
        db_session.add(species)
        await db_session.flush()

        # Create pokemon with the species
        kwargs['species_id'] = species.id
        kwargs['identifier'] = identifier
        # Ensure generation is set
        if 'generation' not in kwargs and 'generation_id' in kwargs:
            kwargs['generation'] = kwargs.pop('generation_id')
        elif 'generation' not in kwargs:
            kwargs['generation'] = generation

        instance = await cls.build(**kwargs)
        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)
        return instance

    @classmethod
    async def create_batch_with_variety(
        cls,
        db_session: AsyncSession,
        count: int = 10,
    ) -> List[Pokemon]:
        """
        Create a batch of Pokemon with variety in their attributes.
        Useful for testing filters and queries.
        """
        from app.models import PokemonSpecies

        pokemon_list = []
        evolution_stages = ["unevolved", "middle", "fully_evolved"]

        for i in range(count):
            generation = (i % 9) + 1
            is_legendary = (i % 5 == 0)
            is_mythical = (i % 7 == 0)
            base_stat_total = 300 + (i * 40)  # Range from 300 to ~700
            evolution_stage = evolution_stages[i % 3]

            # First create the species
            species = PokemonSpecies(
                identifier=f"testmon-species-{i+1}",
                generation_id=generation,
                is_legendary=is_legendary,
                is_mythical=is_mythical,
            )
            db_session.add(species)
            await db_session.flush()

            # Then create the pokemon
            pokemon = await cls.create(
                db_session,
                identifier=f"testmon{i+1}",
                species_id=species.id,
                height=10 + i,
                weight=100 + (i * 10),
                base_experience=100 + (i * 10),
                generation=generation,
                base_stat_total=base_stat_total,
                evolution_stage=evolution_stage,
                is_legendary=is_legendary,
                is_mythical=is_mythical,
            )
            pokemon_list.append(pokemon)
        return pokemon_list


# ============================================================================
# Trade Factory
# ============================================================================


class TradeFactory(BaseFactory):
    """Factory for creating Trade instances."""

    @classmethod
    async def build(
        cls,
        season_id: Optional[int] = None,
        proposer_team_id: Optional[int] = None,
        recipient_team_id: Optional[int] = None,
        proposer_pokemon_ids: Optional[List[int]] = None,
        recipient_pokemon_ids: Optional[List[int]] = None,
        status: str = "pending",
        message: Optional[str] = None,
    ) -> Trade:
        """Build a Trade instance."""
        return Trade(
            season_id=season_id,
            proposer_team_id=proposer_team_id,
            recipient_team_id=recipient_team_id,
            proposer_pokemon_ids=proposer_pokemon_ids or [],
            recipient_pokemon_ids=recipient_pokemon_ids or [],
            status=status,
            message=message or fake.sentence(),
        )


# ============================================================================
# Match Factory
# ============================================================================


class MatchFactory(BaseFactory):
    """Factory for creating Match instances."""

    @classmethod
    async def build(
        cls,
        season_id: Optional[int] = None,
        team_a_id: Optional[int] = None,
        team_b_id: Optional[int] = None,
        winner_id: Optional[int] = None,
        is_tie: bool = False,
        replay_url: Optional[str] = None,
        notes: Optional[str] = None,
        format: str = "round_robin",
    ) -> Match:
        """Build a Match instance."""
        return Match(
            season_id=season_id,
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            winner_id=winner_id,
            is_tie=is_tie,
            replay_url=replay_url or fake.url(),
            notes=notes,
            format=format,
        )


# ============================================================================
# Pool Preset Factory
# ============================================================================


class PoolPresetFactory(BaseFactory):
    """Factory for creating PoolPreset instances."""

    @classmethod
    async def build(
        cls,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        pool_data: Optional[dict] = None,
    ) -> PoolPreset:
        """Build a PoolPreset instance."""
        return PoolPreset(
            user_id=user_id,
            name=name or f"Preset {fake.word().title()}",
            description=description or fake.sentence(),
            is_public=is_public,
            pool_data=pool_data or {"pool": []},
        )


# ============================================================================
# Waiver Claim Factory
# ============================================================================


class WaiverClaimFactory(BaseFactory):
    """Factory for creating WaiverClaim instances."""

    @classmethod
    async def build(
        cls,
        season_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pokemon_id: int = 25,  # Pikachu by default
        drop_pokemon_id: Optional[int] = None,
        status: WaiverClaimStatus = WaiverClaimStatus.PENDING,
        priority: int = 0,
        requires_approval: bool = False,
        admin_approved: Optional[bool] = None,
        admin_notes: Optional[str] = None,
        votes_for: int = 0,
        votes_against: int = 0,
        votes_required: Optional[int] = None,
        processing_type: WaiverProcessingType = WaiverProcessingType.IMMEDIATE,
        process_after: Optional[datetime] = None,
        week_number: Optional[int] = None,
    ) -> WaiverClaim:
        """Build a WaiverClaim instance."""
        return WaiverClaim(
            season_id=season_id,
            team_id=team_id,
            pokemon_id=pokemon_id,
            drop_pokemon_id=drop_pokemon_id,
            status=status,
            priority=priority,
            requires_approval=requires_approval,
            admin_approved=admin_approved,
            admin_notes=admin_notes,
            votes_for=votes_for,
            votes_against=votes_against,
            votes_required=votes_required,
            processing_type=processing_type,
            process_after=process_after,
            week_number=week_number,
        )

    @classmethod
    async def create_for_season(
        cls,
        db_session: AsyncSession,
        season: Season,
        team: Team,
        pokemon_id: int = 25,
        **kwargs,
    ) -> WaiverClaim:
        """Create a waiver claim for a season and team."""
        claim = await cls.create(
            db_session,
            season_id=season.id,
            team_id=team.id,
            pokemon_id=pokemon_id,
            **kwargs,
        )
        return claim

    @classmethod
    async def create_with_approval(
        cls,
        db_session: AsyncSession,
        season: Season,
        team: Team,
        pokemon_id: int = 25,
        approval_type: str = "admin",
        **kwargs,
    ) -> WaiverClaim:
        """Create a waiver claim that requires approval."""
        votes_required = None
        if approval_type == "league_vote":
            votes_required = kwargs.pop("votes_required", 3)

        claim = await cls.create(
            db_session,
            season_id=season.id,
            team_id=team.id,
            pokemon_id=pokemon_id,
            requires_approval=True,
            votes_required=votes_required,
            **kwargs,
        )
        return claim
