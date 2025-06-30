"""
Test Factories for Enhanced Migration System

Mock factories for testing without external dependencies.
"""

import uuid
from datetime import datetime
from typing import Dict, Any


class MigrationFactory:
    """Factory for creating mock migration objects"""
    
    @staticmethod
    def create(**kwargs):
        """Create a mock migration"""
        defaults = {
            "id": str(uuid.uuid4()),
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "status": "pending",
            "created_at": datetime.now(),
            "progress": 0.0
        }
        defaults.update(kwargs)
        return defaults


class UserFactory:
    """Factory for creating mock user objects"""
    
    @staticmethod
    def create(**kwargs):
        """Create a mock user"""
        defaults = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "created_at": datetime.now()
        }
        defaults.update(kwargs)
        return defaults


class PlatformConfigFactory:
    """Factory for creating mock platform configurations"""
    
    @staticmethod
    def create(**kwargs):
        """Create a mock platform config"""
        defaults = {
            "platform": "shopify",
            "api_endpoint": "https://api.shopify.com",
            "api_key": "test_key",
            "settings": {
                "rate_limit": 100,
                "timeout": 30
            }
        }
        defaults.update(kwargs)
        return defaults


class WorkflowStateFactory:
    """Factory for creating mock workflow states"""
    
    @staticmethod
    def create(**kwargs):
        """Create a mock workflow state"""
        defaults = {
            "migration_id": str(uuid.uuid4()),
            "current_stage": "coordinator",
            "progress_percentage": 0.0,
            "workflow_status": "running",
            "agents_completed": [],
            "error_count": 0,
            "created_at": datetime.now()
        }
        defaults.update(kwargs)
        return defaults