"""
Migration model for tracking migration processes
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class MigrationStatus(str, Enum):
    """Migration status enumeration"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Migration(Base):
    """Migration model"""
    
    __tablename__ = "migrations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default=MigrationStatus.PENDING)
    
    # Source platform
    source_platform = Column(String(100), nullable=False)
    source_config = Column(JSONB)
    
    # Destination platform
    destination_platform = Column(String(100), nullable=False)
    destination_config = Column(JSONB)
    
    # Migration options
    migration_options = Column(JSONB, default=dict)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(255))
    total_steps = Column(Integer)
    completed_steps = Column(Integer, default=0)
    
    # Data counters
    total_products = Column(Integer, default=0)
    migrated_products = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    migrated_customers = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    migrated_orders = Column(Integer, default=0)
    
    # Error tracking
    error_count = Column(Integer, default=0)
    errors = Column(JSONB, default=list)
    
    # Metadata
    metadata_info = Column(JSONB, default=dict)
    
    # Agent data
    agent_analysis = Column(JSONB)
    migration_plan = Column(JSONB)
    seo_analysis = Column(JSONB)
    communication_plan = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # User tracking
    created_by = Column(UUID(as_uuid=True))
    
    def __repr__(self):
        return f"<Migration(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "source_platform": self.source_platform,
            "destination_platform": self.destination_platform,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "total_products": self.total_products,
            "migrated_products": self.migrated_products,
            "total_customers": self.total_customers,
            "migrated_customers": self.migrated_customers,
            "total_orders": self.total_orders,
            "migrated_orders": self.migrated_orders,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }