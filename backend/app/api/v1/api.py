"""
Main API router for v1
"""

from fastapi import APIRouter

# Import routers
from app.api.v1.endpoints import migrations

api_router = APIRouter()

# Include routers
api_router.include_router(migrations.router, prefix="/migrations", tags=["migrations"])

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Intelligent Store Migration Assistant API v1",
        "version": "1.0.0",
        "status": "active",
        "available_endpoints": [
            "/migrations - LangGraph multi-agent migration workflows",
            "/docs - Interactive API documentation",
            "/redoc - Alternative API documentation"
        ]
    }