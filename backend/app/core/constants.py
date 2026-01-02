"""
Constants used throughout the application.

Centralizes magic strings and values for type safety and maintainability.
"""


class LeagueSettings:
    """Settings keys for league configuration stored in league.settings JSON field."""

    # Trade settings
    TRADE_APPROVAL_REQUIRED = "trade_approval_required"

    # Waiver settings
    WAIVER_ENABLED = "waiver_enabled"
    WAIVER_MAX_PER_WEEK = "waiver_max_per_week"
    WAIVER_REQUIRE_DROP = "waiver_require_drop"
    WAIVER_APPROVAL_TYPE = "waiver_approval_type"
    WAIVER_PROCESSING_TYPE = "waiver_processing_type"

    # Waiver approval types
    WAIVER_APPROVAL_NONE = "none"
    WAIVER_APPROVAL_ADMIN = "admin"
    WAIVER_APPROVAL_LEAGUE_VOTE = "league_vote"

    # Waiver processing types
    WAIVER_PROCESSING_IMMEDIATE = "immediate"
    WAIVER_PROCESSING_NEXT_WEEK = "next_week"


class SeasonSettings:
    """Settings keys for season configuration stored in season.settings JSON field."""

    CURRENT_WEEK = "current_week"
