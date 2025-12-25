from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.core.security import get_current_user
from app.schemas.match import Match, MatchResult, Standings, ScheduleGenerateRequest

router = APIRouter()


@router.get("/schedule", response_model=list[Match])
async def get_schedule(
    season_id: UUID = Query(..., description="Season to get schedule for"),
    week: int = Query(None, description="Filter by week"),
    current_user=Depends(get_current_user),
):
    """Get the schedule for a season."""
    # TODO: Implement schedule retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/schedule", response_model=list[Match], status_code=status.HTTP_201_CREATED)
async def generate_schedule(
    season_id: UUID = Query(..., description="Season to generate schedule for"),
    request: ScheduleGenerateRequest = ScheduleGenerateRequest(),
    current_user=Depends(get_current_user),
):
    """Generate a schedule for a season (league owner only)."""
    # TODO: Implement schedule generation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/standings", response_model=Standings)
async def get_standings(
    season_id: UUID = Query(..., description="Season to get standings for"),
    current_user=Depends(get_current_user),
):
    """Get current standings for a season."""
    # TODO: Implement standings calculation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{match_id}", response_model=Match)
async def get_match(
    match_id: UUID,
    current_user=Depends(get_current_user),
):
    """Get match details."""
    # TODO: Implement match retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{match_id}/result", response_model=Match)
async def record_result(
    match_id: UUID,
    result: MatchResult,
    current_user=Depends(get_current_user),
):
    """Record a match result."""
    # TODO: Implement result recording
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
