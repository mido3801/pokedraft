from fastapi import APIRouter

from app.api.v1.endpoints import auth, leagues, drafts, teams, trades, matches, templates, seasons, pokemon, presets, waivers

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(leagues.router, prefix="/leagues", tags=["Leagues"])
api_router.include_router(seasons.router, prefix="/seasons", tags=["Seasons"])
api_router.include_router(drafts.router, prefix="/drafts", tags=["Drafts"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(waivers.router, prefix="/waivers", tags=["Waivers"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(pokemon.router, prefix="/pokemon", tags=["Pokemon"])
api_router.include_router(presets.router, prefix="/presets", tags=["Presets"])
