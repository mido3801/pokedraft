from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.errors import not_found, forbidden, bad_request
from app.schemas.preset import (
    PoolPresetCreate,
    PoolPresetUpdate,
    PoolPresetResponse,
    PoolPresetSummary,
)
from app.models.preset import PoolPreset
from app.models.user import User

router = APIRouter()


@router.get("", response_model=list[PoolPresetSummary])
async def list_presets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's presets + all public presets."""
    result = await db.execute(
        select(PoolPreset, User.display_name)
        .join(User, PoolPreset.user_id == User.id)
        .where(
            or_(
                PoolPreset.user_id == current_user.id,
                PoolPreset.is_public == True
            )
        )
        .order_by(PoolPreset.created_at.desc())
    )
    presets_with_creators = result.all()

    return [
        PoolPresetSummary(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            description=preset.description,
            pokemon_count=preset.pokemon_count,
            is_public=preset.is_public,
            created_at=preset.created_at,
            creator_name=creator_name if preset.user_id != current_user.id else None,
        )
        for preset, creator_name in presets_with_creators
    ]


@router.post("", response_model=PoolPresetResponse, status_code=status.HTTP_201_CREATED)
async def create_preset(
    preset: PoolPresetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pool preset."""
    if not preset.pokemon_pool:
        raise bad_request("Pokemon pool cannot be empty")

    db_preset = PoolPreset(
        user_id=current_user.id,
        name=preset.name,
        description=preset.description,
        pokemon_pool=preset.pokemon_pool,
        pokemon_count=len(preset.pokemon_pool),
        is_public=preset.is_public,
    )
    db.add(db_preset)
    await db.commit()
    await db.refresh(db_preset)

    return PoolPresetResponse(
        id=db_preset.id,
        user_id=db_preset.user_id,
        name=db_preset.name,
        description=db_preset.description,
        pokemon_pool=db_preset.pokemon_pool,
        pokemon_count=db_preset.pokemon_count,
        is_public=db_preset.is_public,
        created_at=db_preset.created_at,
        updated_at=db_preset.updated_at,
    )


@router.get("/{preset_id}", response_model=PoolPresetResponse)
async def get_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single preset with full pool data."""
    result = await db.execute(
        select(PoolPreset, User.display_name)
        .join(User, PoolPreset.user_id == User.id)
        .where(PoolPreset.id == preset_id)
    )
    row = result.first()

    if not row:
        raise not_found("Preset", preset_id)

    preset, creator_name = row

    # Check access
    if preset.user_id != current_user.id and not preset.is_public:
        raise forbidden("You don't have access to this preset")

    return PoolPresetResponse(
        id=preset.id,
        user_id=preset.user_id,
        name=preset.name,
        description=preset.description,
        pokemon_pool=preset.pokemon_pool,
        pokemon_count=preset.pokemon_count,
        is_public=preset.is_public,
        created_at=preset.created_at,
        updated_at=preset.updated_at,
        creator_name=creator_name if preset.user_id != current_user.id else None,
    )


@router.put("/{preset_id}", response_model=PoolPresetResponse)
async def update_preset(
    preset_id: UUID,
    preset_update: PoolPresetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a preset (owner only)."""
    result = await db.execute(
        select(PoolPreset).where(PoolPreset.id == preset_id)
    )
    preset = result.scalar_one_or_none()

    if not preset:
        raise not_found("Preset", preset_id)

    if preset.user_id != current_user.id:
        raise forbidden("You can only edit your own presets")

    # Update fields
    if preset_update.name is not None:
        preset.name = preset_update.name
    if preset_update.description is not None:
        preset.description = preset_update.description
    if preset_update.is_public is not None:
        preset.is_public = preset_update.is_public
    if preset_update.pokemon_pool is not None:
        if not preset_update.pokemon_pool:
            raise bad_request("Pokemon pool cannot be empty")
        preset.pokemon_pool = preset_update.pokemon_pool
        preset.pokemon_count = len(preset_update.pokemon_pool)

    await db.commit()
    await db.refresh(preset)

    return PoolPresetResponse(
        id=preset.id,
        user_id=preset.user_id,
        name=preset.name,
        description=preset.description,
        pokemon_pool=preset.pokemon_pool,
        pokemon_count=preset.pokemon_count,
        is_public=preset.is_public,
        created_at=preset.created_at,
        updated_at=preset.updated_at,
    )


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a preset (owner only)."""
    result = await db.execute(
        select(PoolPreset).where(PoolPreset.id == preset_id)
    )
    preset = result.scalar_one_or_none()

    if not preset:
        raise not_found("Preset", preset_id)

    if preset.user_id != current_user.id:
        raise forbidden("You can only delete your own presets")

    await db.delete(preset)
    await db.commit()
