"""
Main API router for v1
"""

from fastapi import APIRouter

# Import routers when they're created
# from app.api.v1.endpoints import migrations, agents, platforms

api_router = APIRouter()

# Include routers when ready
# api_router.include_router(migrations.router, prefix="/migrations", tags=["migrations"])
# api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
# api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Intelligent Store Migration Assistant API v1",
        "version": "1.0.0",
        "status": "active"
    }