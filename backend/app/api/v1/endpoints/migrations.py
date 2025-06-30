"""
Migration API endpoints using LangGraph multi-agent system
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import structlog

from app.agents.migration_graph import MigrationOrchestrator, MigrationWorkflowInput
from app.core.database import get_database_session
from app.models.migration import Migration, MigrationStatus
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter()

# Global orchestrator instance
migration_orchestrator = MigrationOrchestrator()


# Pydantic models for API
class PlatformConfig(BaseModel):
    """Platform configuration model"""
    store_url: str = Field(..., description="Store URL or domain")
    access_token: Optional[str] = Field(None, description="API access token")
    api_key: Optional[str] = Field(None, description="API key")
    additional_config: Dict[str, Any] = Field(default_factory=dict, description="Additional platform-specific configuration")


class MigrationRequest(BaseModel):
    """Request model for creating a new migration"""
    name: str = Field(..., description="Migration name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Migration description")
    source_platform: str = Field(..., description="Source platform type")
    destination_platform: str = Field(..., description="Destination platform type")
    source_config: PlatformConfig = Field(..., description="Source platform configuration")
    destination_config: PlatformConfig = Field(..., description="Destination platform configuration")
    migration_options: Dict[str, Any] = Field(default_factory=dict, description="Migration preferences and options")
    
    @validator('source_platform', 'destination_platform')
    def validate_platform(cls, v):
        supported_platforms = ['shopify', 'woocommerce', 'magento', 'bigcommerce', 'ideasoft', 'ikas']
        if v.lower() not in supported_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(supported_platforms)}')
        return v.lower()


class MigrationResponse(BaseModel):
    """Response model for migration operations"""
    migration_id: str
    name: str
    status: str
    source_platform: str
    destination_platform: str
    progress_percentage: float
    current_stage: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    estimated_completion: Optional[str] = None


class MigrationDetailResponse(MigrationResponse):
    """Detailed migration response with agent results"""
    agent_analysis: Optional[Dict[str, Any]] = None
    migration_plan: Optional[Dict[str, Any]] = None
    seo_analysis: Optional[Dict[str, Any]] = None
    communication_plan: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""
    migration_id: str
    workflow_status: str
    current_stage: str
    progress_percentage: float
    completed_stages: List[str]
    active_agents: List[str]
    next_stage: Optional[str] = None
    estimated_completion_time: Optional[str] = None


@router.post("/", response_model=MigrationResponse, status_code=status.HTTP_201_CREATED)
async def create_migration(
    migration_request: MigrationRequest,
    background_tasks: BackgroundTasks,
    db_session = Depends(get_database_session)
):
    """
    Create a new migration using the LangGraph multi-agent system
    """
    logger.info(
        "Creating new migration",
        name=migration_request.name,
        source_platform=migration_request.source_platform,
        destination_platform=migration_request.destination_platform
    )
    
    try:
        # Generate migration ID
        migration_id = str(uuid.uuid4())
        
        # Create migration record in database
        migration = Migration(
            id=migration_id,
            name=migration_request.name,
            description=migration_request.description,
            status=MigrationStatus.PENDING,
            source_platform=migration_request.source_platform,
            destination_platform=migration_request.destination_platform,
            source_config=migration_request.source_config.dict(),
            destination_config=migration_request.destination_config.dict(),
            migration_options=migration_request.migration_options
        )
        
        db_session.add(migration)
        await db_session.commit()
        
        # Start LangGraph workflow in background
        background_tasks.add_task(
            execute_migration_workflow,
            migration_id,
            migration_request,
            db_session
        )
        
        # Return immediate response
        return MigrationResponse(
            migration_id=migration_id,
            name=migration.name,
            status=migration.status.value,
            source_platform=migration.source_platform,
            destination_platform=migration.destination_platform,
            progress_percentage=0.0,
            current_stage="initializing",
            created_at=migration.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(
            "Failed to create migration",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create migration: {str(e)}"
        )


@router.get("/{migration_id}", response_model=MigrationDetailResponse)
async def get_migration(
    migration_id: str,
    db_session = Depends(get_database_session)
):
    """
    Get detailed migration information including agent results
    """
    try:
        # Query migration from database
        migration = await db_session.get(Migration, migration_id)
        
        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        # Get workflow status from orchestrator
        workflow_status = await migration_orchestrator.get_workflow_status(migration_id)
        
        return MigrationDetailResponse(
            migration_id=migration.id,
            name=migration.name,
            status=migration.status.value,
            source_platform=migration.source_platform,
            destination_platform=migration.destination_platform,
            progress_percentage=migration.progress_percentage,
            current_stage=migration.current_step,
            created_at=migration.created_at.isoformat(),
            updated_at=migration.updated_at.isoformat() if migration.updated_at else None,
            agent_analysis=migration.agent_analysis,
            migration_plan=migration.migration_plan,
            seo_analysis=migration.seo_analysis,
            communication_plan=migration.communication_plan,
            errors=migration.errors or [],
            warnings=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get migration",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve migration: {str(e)}"
        )


@router.get("/{migration_id}/workflow-status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    migration_id: str,
    db_session = Depends(get_database_session)
):
    """
    Get current workflow status from LangGraph orchestrator
    """
    try:
        # Verify migration exists
        migration = await db_session.get(Migration, migration_id)
        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        # Get workflow status
        workflow_status = await migration_orchestrator.get_workflow_status(migration_id)
        
        return WorkflowStatusResponse(
            migration_id=migration_id,
            workflow_status=workflow_status.get("status", "unknown"),
            current_stage=workflow_status.get("current_stage", "unknown"),
            progress_percentage=workflow_status.get("progress", 0.0),
            completed_stages=workflow_status.get("completed_stages", []),
            active_agents=workflow_status.get("active_agents", []),
            next_stage=workflow_status.get("next_stage"),
            estimated_completion_time=workflow_status.get("estimated_completion")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workflow status",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.post("/{migration_id}/pause")
async def pause_migration(
    migration_id: str,
    db_session = Depends(get_database_session)
):
    """
    Pause a running migration workflow
    """
    try:
        # Verify migration exists and is pausable
        migration = await db_session.get(Migration, migration_id)
        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        if migration.status not in [MigrationStatus.IN_PROGRESS, MigrationStatus.ANALYZING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Migration cannot be paused in status: {migration.status.value}"
            )
        
        # Pause workflow
        success = await migration_orchestrator.pause_workflow(migration_id)
        
        if success:
            # Update database
            migration.status = MigrationStatus.PAUSED
            await db_session.commit()
            
            return JSONResponse(
                content={
                    "message": f"Migration {migration_id} paused successfully",
                    "migration_id": migration_id,
                    "status": "paused"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause migration workflow"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to pause migration",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause migration: {str(e)}"
        )


@router.post("/{migration_id}/resume")
async def resume_migration(
    migration_id: str,
    background_tasks: BackgroundTasks,
    db_session = Depends(get_database_session)
):
    """
    Resume a paused migration workflow
    """
    try:
        # Verify migration exists and is resumable
        migration = await db_session.get(Migration, migration_id)
        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        if migration.status != MigrationStatus.PAUSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Migration cannot be resumed in status: {migration.status.value}"
            )
        
        # Resume workflow
        success = await migration_orchestrator.resume_workflow(migration_id)
        
        if success:
            # Update database
            migration.status = MigrationStatus.IN_PROGRESS
            await db_session.commit()
            
            return JSONResponse(
                content={
                    "message": f"Migration {migration_id} resumed successfully",
                    "migration_id": migration_id,
                    "status": "in_progress"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resume migration workflow"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to resume migration",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume migration: {str(e)}"
        )


@router.delete("/{migration_id}")
async def cancel_migration(
    migration_id: str,
    db_session = Depends(get_database_session)
):
    """
    Cancel a migration and cleanup resources
    """
    try:
        # Verify migration exists
        migration = await db_session.get(Migration, migration_id)
        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        if migration.status in [MigrationStatus.COMPLETED, MigrationStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Migration cannot be cancelled in status: {migration.status.value}"
            )
        
        # Cancel workflow (if running)
        if migration.status in [MigrationStatus.IN_PROGRESS, MigrationStatus.ANALYZING, MigrationStatus.PAUSED]:
            await migration_orchestrator.pause_workflow(migration_id)
        
        # Update database
        migration.status = MigrationStatus.CANCELLED
        await db_session.commit()
        
        logger.info("Migration cancelled", migration_id=migration_id)
        
        return JSONResponse(
            content={
                "message": f"Migration {migration_id} cancelled successfully",
                "migration_id": migration_id,
                "status": "cancelled"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cancel migration",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel migration: {str(e)}"
        )


@router.get("/", response_model=List[MigrationResponse])
async def list_migrations(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db_session = Depends(get_database_session)
):
    """
    List migrations with optional filtering
    """
    try:
        # Build query
        query = db_session.query(Migration)
        
        if status_filter:
            try:
                status_enum = MigrationStatus(status_filter.lower())
                query = query.filter(Migration.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Apply pagination
        migrations = query.offset(skip).limit(limit).all()
        
        # Convert to response model
        response = []
        for migration in migrations:
            response.append(MigrationResponse(
                migration_id=migration.id,
                name=migration.name,
                status=migration.status.value,
                source_platform=migration.source_platform,
                destination_platform=migration.destination_platform,
                progress_percentage=migration.progress_percentage,
                current_stage=migration.current_step,
                created_at=migration.created_at.isoformat(),
                updated_at=migration.updated_at.isoformat() if migration.updated_at else None
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list migrations",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list migrations: {str(e)}"
        )


async def execute_migration_workflow(
    migration_id: str,
    migration_request: MigrationRequest,
    db_session
):
    """
    Background task to execute the LangGraph migration workflow
    """
    logger.info("Starting LangGraph migration workflow", migration_id=migration_id)
    
    try:
        # Update status to analyzing
        migration = await db_session.get(Migration, migration_id)
        migration.status = MigrationStatus.ANALYZING
        await db_session.commit()
        
        # Create workflow input
        workflow_input = MigrationWorkflowInput(
            migration_id=migration_id,
            source_platform=migration_request.source_platform,
            destination_platform=migration_request.destination_platform,
            source_config=migration_request.source_config.dict(),
            destination_config=migration_request.destination_config.dict(),
            migration_options=migration_request.migration_options
        )
        
        # Execute the LangGraph workflow
        workflow_result = await migration_orchestrator.execute_migration_workflow(workflow_input)
        
        # Update migration with results
        migration.status = MigrationStatus.COMPLETED if workflow_result.get("current_stage") == "completed" else MigrationStatus.FAILED
        migration.progress_percentage = workflow_result.get("current_progress", 0.0)
        migration.current_step = workflow_result.get("current_stage")
        migration.agent_analysis = workflow_result.get("analysis_result")
        migration.migration_plan = workflow_result.get("migration_plan")
        migration.seo_analysis = workflow_result.get("seo_analysis")
        migration.communication_plan = workflow_result.get("communication_plan")
        migration.errors = workflow_result.get("errors", [])
        
        await db_session.commit()
        
        logger.info(
            "Migration workflow completed",
            migration_id=migration_id,
            status=migration.status.value,
            progress=migration.progress_percentage
        )
        
    except Exception as e:
        logger.error(
            "Migration workflow failed",
            migration_id=migration_id,
            error=str(e),
            exc_info=True
        )
        
        # Update migration status to failed
        try:
            migration = await db_session.get(Migration, migration_id)
            migration.status = MigrationStatus.FAILED
            migration.errors = [{"error": str(e), "timestamp": datetime.utcnow().isoformat()}]
            await db_session.commit()
        except Exception as update_error:
            logger.error("Failed to update migration status after error", error=str(update_error))