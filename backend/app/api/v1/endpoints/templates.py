from fastapi import APIRouter, HTTPException, status

router = APIRouter()


# Predefined templates for common competitive formats
TEMPLATES = {
    "ou": {
        "id": "ou",
        "name": "OU (OverUsed)",
        "description": "Standard competitive tier with the most commonly used Pokemon",
        "roster_size": 6,
        "budget_enabled": False,
        "excluded_pokemon": [],  # Would contain legendary IDs, etc.
    },
    "uu": {
        "id": "uu",
        "name": "UU (UnderUsed)",
        "description": "Second-tier competitive format",
        "roster_size": 6,
        "budget_enabled": False,
        "excluded_pokemon": [],
    },
    "monotype": {
        "id": "monotype",
        "name": "Monotype",
        "description": "Teams must consist of Pokemon sharing a single type",
        "roster_size": 6,
        "budget_enabled": False,
        "excluded_pokemon": [],
    },
    "little_cup": {
        "id": "little_cup",
        "name": "Little Cup",
        "description": "Only first-evolution Pokemon at level 5",
        "roster_size": 6,
        "budget_enabled": False,
        "excluded_pokemon": [],
    },
    "draft_league": {
        "id": "draft_league",
        "name": "Draft League",
        "description": "Standard draft league format with point values",
        "roster_size": 11,
        "budget_enabled": True,
        "budget_per_team": 100,
        "excluded_pokemon": [],
    },
}


@router.get("")
async def list_templates():
    """List all available draft templates."""
    return list(TEMPLATES.values())


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get template details including Pokemon pool configuration."""
    if template_id not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )
    return TEMPLATES[template_id]
