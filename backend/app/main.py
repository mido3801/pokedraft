from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.websocket.draft_handler import router as ws_router
from app.websocket.trade_handler import router as trade_ws_router

# Startup debug info
print(f"[STARTUP] DEV_MODE: {settings.DEV_MODE}")
print(f"[STARTUP] SUPABASE_JWT_SECRET configured: {bool(settings.SUPABASE_JWT_SECRET)}")
print(f"[STARTUP] SUPABASE_JWT_SECRET length: {len(settings.SUPABASE_JWT_SECRET)}")

app = FastAPI(
    title="Pokemon Draft League API",
    description="API for managing Pokemon draft leagues",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include WebSocket routes
app.include_router(ws_router)
app.include_router(trade_ws_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
