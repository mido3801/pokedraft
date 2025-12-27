"""
Standardized error handling for the API.

Provides consistent error responses across all endpoints.
"""

from typing import Any, Optional
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} not found"
        if identifier is not None:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(HTTPException):
    """Access forbidden error."""

    def __init__(self, message: str = "You don't have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class BadRequestError(HTTPException):
    """Bad request error."""

    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class UnauthorizedError(HTTPException):
    """Unauthorized error."""

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


class ConflictError(HTTPException):
    """Conflict error (e.g., duplicate resource)."""

    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class NotImplementedError(HTTPException):
    """Not implemented error."""

    def __init__(self, message: str = "This feature is not yet implemented"):
        super().__init__(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=message)


# Convenience factory functions for common patterns
def not_found(resource: str, identifier: Any = None) -> NotFoundError:
    """Create a not found error."""
    return NotFoundError(resource, identifier)


def forbidden(message: str = "You don't have permission to perform this action") -> ForbiddenError:
    """Create a forbidden error."""
    return ForbiddenError(message)


def bad_request(message: str) -> BadRequestError:
    """Create a bad request error."""
    return BadRequestError(message)


def unauthorized(message: str = "Not authenticated") -> UnauthorizedError:
    """Create an unauthorized error."""
    return UnauthorizedError(message)


def conflict(message: str) -> ConflictError:
    """Create a conflict error."""
    return ConflictError(message)


def not_implemented(message: str = "This feature is not yet implemented") -> NotImplementedError:
    """Create a not implemented error."""
    return NotImplementedError(message)


# Domain-specific error helpers
def league_not_found(league_id: Any = None) -> NotFoundError:
    """League not found error."""
    return NotFoundError("League", league_id)


def season_not_found(season_id: Any = None) -> NotFoundError:
    """Season not found error."""
    return NotFoundError("Season", season_id)


def team_not_found(team_id: Any = None) -> NotFoundError:
    """Team not found error."""
    return NotFoundError("Team", team_id)


def match_not_found(match_id: Any = None) -> NotFoundError:
    """Match not found error."""
    return NotFoundError("Match", match_id)


def trade_not_found(trade_id: Any = None) -> NotFoundError:
    """Trade not found error."""
    return NotFoundError("Trade", trade_id)


def draft_not_found(draft_id: Any = None) -> NotFoundError:
    """Draft not found error."""
    return NotFoundError("Draft", draft_id)


def user_not_found(user_id: Any = None) -> NotFoundError:
    """User not found error."""
    return NotFoundError("User", user_id)


def pokemon_not_found(pokemon_id: Any = None) -> NotFoundError:
    """Pokemon not found error."""
    return NotFoundError("Pokemon", pokemon_id)


# Authorization error helpers
def not_league_member() -> ForbiddenError:
    """User is not a league member error."""
    return ForbiddenError("You are not a member of this league")


def not_league_owner() -> ForbiddenError:
    """User is not the league owner error."""
    return ForbiddenError("Only the league owner can perform this action")


def not_team_owner() -> ForbiddenError:
    """User is not the team owner error."""
    return ForbiddenError("You are not authorized to manage this team")
