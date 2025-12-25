from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.core.security import get_current_user, get_current_user_optional
from app.schemas.draft import (
    Draft,
    DraftCreate,
    DraftState,
    AnonymousDraftCreate,
    AnonymousDraftResponse,
)
from app.schemas.team import TeamExport, ShowdownExport

router = APIRouter()


@router.post("", response_model=Draft, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft: DraftCreate,
    season_id: UUID = Query(..., description="Season to create draft for"),
    current_user=Depends(get_current_user),
):
    """Create a draft for a season (league owner only)."""
    # TODO: Implement draft creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/anonymous", response_model=AnonymousDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_anonymous_draft(draft: AnonymousDraftCreate):
    """Create an anonymous draft session (no auth required)."""
    # TODO: Implement anonymous draft creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/anonymous/join")
async def join_anonymous_draft(
    rejoin_code: str = Query(..., description="Rejoin code (e.g., PIKA-7842)"),
    display_name: str = Query(..., description="Display name for this session"),
):
    """Join an anonymous draft via rejoin code."""
    # TODO: Implement anonymous draft joining
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{draft_id}", response_model=Draft)
async def get_draft(
    draft_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Get draft details."""
    # TODO: Implement draft retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{draft_id}/state", response_model=DraftState)
async def get_draft_state(
    draft_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Get current draft state (for reconnection)."""
    # TODO: Implement draft state retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{draft_id}/start")
async def start_draft(
    draft_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Start the draft (creator/owner only)."""
    # TODO: Implement draft start
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{draft_id}/pause")
async def pause_draft(
    draft_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Pause the draft (creator/owner only)."""
    # TODO: Implement draft pause
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{draft_id}/resume")
async def resume_draft(
    draft_id: UUID,
    current_user=Depends(get_current_user_optional),
):
    """Resume a paused draft (creator/owner only)."""
    # TODO: Implement draft resume
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{draft_id}/export", response_model=ShowdownExport)
async def export_team(
    draft_id: UUID,
    team_id: UUID = Query(..., description="Team to export"),
    format: str = Query("showdown", description="Export format: showdown, json, csv"),
    current_user=Depends(get_current_user_optional),
):
    """Export a team from the draft."""
    # TODO: Implement team export
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
