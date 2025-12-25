from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.core.security import get_current_user
from app.schemas.trade import Trade, TradeCreate, TradeResponse

router = APIRouter()


@router.post("", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def propose_trade(
    trade: TradeCreate,
    season_id: UUID = Query(..., description="Season for the trade"),
    current_user=Depends(get_current_user),
):
    """Propose a trade to another team."""
    # TODO: Implement trade proposal
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("", response_model=list[Trade])
async def list_trades(
    season_id: UUID = Query(..., description="Season to list trades for"),
    status_filter: str = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user),
):
    """List trades in a season."""
    # TODO: Implement trade listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.get("/{trade_id}", response_model=Trade)
async def get_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
):
    """Get trade details."""
    # TODO: Implement trade retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{trade_id}/accept", response_model=Trade)
async def accept_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
):
    """Accept a trade proposal."""
    # TODO: Implement trade acceptance
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{trade_id}/reject", response_model=Trade)
async def reject_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
):
    """Reject a trade proposal."""
    # TODO: Implement trade rejection
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{trade_id}/cancel", response_model=Trade)
async def cancel_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
):
    """Cancel a trade proposal (proposer only)."""
    # TODO: Implement trade cancellation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )


@router.post("/{trade_id}/approve", response_model=Trade)
async def approve_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
):
    """Approve a trade (league owner only, if approval required)."""
    # TODO: Implement trade approval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )
