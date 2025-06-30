"""
Pytest Configuration and Fixtures

Provides test fixtures and configuration for the enhanced system tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


@pytest.fixture
def test_client():
    """Mock test client for API testing"""
    mock_client = Mock()
    
    # Mock response object
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Setup async methods
    async def async_get(*args, **kwargs):
        return mock_response
    
    async def async_post(*args, **kwargs):
        mock_response.status_code = 201
        return mock_response
    
    async def async_put(*args, **kwargs):
        return mock_response
    
    async def async_delete(*args, **kwargs):
        mock_response.status_code = 204
        return mock_response
    
    async def async_options(*args, **kwargs):
        return mock_response
    
    mock_client.get = async_get
    mock_client.post = async_post
    mock_client.put = async_put
    mock_client.delete = async_delete
    mock_client.options = async_options
    
    return mock_client


@pytest.fixture
def test_db():
    """Mock database for testing"""
    mock_db = Mock()
    
    # Mock database operations
    async def async_query(*args, **kwargs):
        return [{"id": 1, "name": "test"}]
    
    async def async_execute(*args, **kwargs):
        return True
    
    mock_db.query = async_query
    mock_db.execute = async_execute
    
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    
    # Mock Redis operations
    mock_redis.get.return_value = '{"cached": "data"}'
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = True
    
    return mock_redis


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing"""
    mock_openai = Mock()
    
    # Mock completion response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="Mocked AI response"))
    ]
    mock_response.usage = Mock(total_tokens=100)
    
    mock_openai.chat.completions.create.return_value = mock_response
    
    return mock_openai


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    return Mock(
        ENVIRONMENT="test",
        DEBUG=True,
        OPENAI_API_KEY="test-key",
        DATABASE_URL="postgresql://test:test@localhost/test",
        REDIS_URL="redis://localhost:6379/0"
    )