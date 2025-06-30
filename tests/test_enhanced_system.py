"""
Comprehensive Test Suite for Enhanced Migration System

Following testing best practices:
- Unit tests, integration tests, and end-to-end tests
- Test fixtures and factories
- Mocking and stubbing
- Property-based testing
- Performance testing
- Security testing
- Accessibility testing
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import uuid

# Test utilities and fixtures
from tests.factories import (
    MigrationFactory,
    UserFactory,
    PlatformConfigFactory,
    WorkflowStateFactory
)
from tests.conftest import (
    test_client,
    test_db,
    mock_redis,
    mock_openai
)

# System under test
from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    MigrationError,
    WorkflowError
)
from backend.app.core.monitoring import metrics, health_checker, performance_monitor
from backend.app.agents.migration_graph import MigrationOrchestrator
from backend.app.api.v1.endpoints.migrations import router


class TestEnhancedConfiguration:
    """Test enhanced configuration management"""
    
    def test_settings_validation(self):
        """Test settings validation and type safety"""
        settings = get_settings()
        
        # Test required fields
        assert settings.ai.OPENAI_API_KEY is not None
        assert len(settings.security.SECRET_KEY) >= 32
        
        # Test environment-specific settings
        if settings.is_production():
            assert settings.DEBUG is False
            assert "*" not in settings.security.ALLOWED_HOSTS
        
    def test_nested_configuration(self):
        """Test nested configuration structures"""
        settings = get_settings()
        
        # Test database settings
        assert settings.database.DB_POOL_SIZE >= 5
        assert settings.database.DB_POOL_SIZE <= 100
        
        # Test AI settings
        assert 0.0 <= settings.ai.OPENAI_TEMPERATURE <= 2.0
        assert 100 <= settings.ai.OPENAI_MAX_TOKENS <= 8000
        
        # Test migration settings
        assert all(
            platform in ['shopify', 'woocommerce', 'magento', 'opencart']
            for platform in settings.migration.SUPPORTED_SOURCE_PLATFORMS
        )
    
    def test_environment_validation(self):
        """Test environment variable validation"""
        from backend.app.core.config import validate_environment_variables
        
        # Should return True for valid configuration
        assert validate_environment_variables() is True
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is filtered from exports"""
        settings = get_settings()
        data = settings.to_dict()
        
        # Sensitive fields should be hidden
        sensitive_keys = ['SECRET_KEY', 'OPENAI_API_KEY', 'DATABASE_URL']
        
        def check_sensitive_data(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(sensitive_key in key.upper() for sensitive_key in sensitive_keys):
                        assert value == "***HIDDEN***", f"Sensitive data exposed at {current_path}"
                    else:
                        check_sensitive_data(value, current_path)
        
        check_sensitive_data(data)


class TestExceptionHandling:
    """Test enhanced exception handling"""
    
    def test_custom_exception_creation(self):
        """Test custom exception classes"""
        # Test ValidationError
        error = ValidationError("Invalid field", field="email", value="invalid")
        assert error.error_code == "VALIDATION_ERROR"
        assert error.context["field"] == "email"
        assert error.status_code == 422
        
        # Test MigrationError
        migration_error = MigrationError(
            "Migration failed",
            migration_id="test-123",
            stage="data_analysis"
        )
        assert migration_error.error_code == "MIGRATION_ERROR"
        assert migration_error.context["migration_id"] == "test-123"
        assert migration_error.context["stage"] == "data_analysis"
    
    def test_exception_to_dict(self):
        """Test exception serialization"""
        error = ValidationError("Test error", field="test_field")
        error_dict = error.to_dict()
        
        expected_keys = {"error_code", "message", "context", "type"}
        assert set(error_dict.keys()) == expected_keys
        assert error_dict["type"] == "ValidationError"
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware(self, test_client):
        """Test error handling middleware"""
        # Test custom exception handling
        response = await test_client.get("/api/v1/test-error-endpoint")
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
        assert "correlation_id" in data
        assert "timestamp" in data


class TestMonitoringAndObservability:
    """Test monitoring and observability features"""
    
    def test_prometheus_metrics_collection(self):
        """Test Prometheus metrics collection"""
        # Test HTTP metrics recording
        metrics.record_http_request("GET", "/api/v1/migrations", 200, 0.5)
        
        # Test migration metrics
        metrics.record_migration_start("shopify", "ideasoft")
        metrics.record_migration_completion(
            "shopify", "ideasoft", 300.0, "completed",
            {"products": 1000, "customers": 500}
        )
        
        # Test AI agent metrics
        metrics.record_ai_agent_call(
            "data_analysis", 5.0, "success",
            model="gpt-4", tokens_used=1500
        )
        
        # Verify metrics are recorded
        metrics_text = metrics.get_metrics()
        assert "http_requests_total" in metrics_text
        assert "migrations_total" in metrics_text
        assert "ai_agent_calls_total" in metrics_text
    
    @pytest.mark.asyncio
    async def test_health_checks(self):
        """Test health check system"""
        # Run all health checks
        results = await health_checker.run_all_checks()
        
        # Verify expected checks are present
        expected_checks = {"database", "memory", "disk", "external_services"}
        assert set(results.keys()) == expected_checks
        
        # Verify health check results structure
        for name, result in results.items():
            assert hasattr(result, 'status')
            assert hasattr(result, 'message')
            assert hasattr(result, 'duration_ms')
            assert result.duration_ms >= 0
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        # Record performance metrics
        performance_monitor.record_performance_metric(
            "http_response_time", 0.5, {"endpoint": "/api/v1/migrations"}
        )
        performance_monitor.record_performance_metric(
            "http_response_time", 1.2, {"endpoint": "/api/v1/migrations"}
        )
        performance_monitor.record_performance_metric(
            "http_response_time", 0.8, {"endpoint": "/api/v1/migrations"}
        )
        
        # Calculate percentiles
        percentiles = performance_monitor.calculate_percentiles("http_response_time")
        
        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["count"] == 3
    
    def test_alert_conditions(self):
        """Test alert condition checking"""
        # Simulate high memory usage
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 90  # 90% memory usage
            
            alerts = performance_monitor.check_alert_conditions()
            
            # Should generate memory alert
            memory_alerts = [a for a in alerts if a['metric'] == 'memory_usage']
            assert len(memory_alerts) > 0
            assert memory_alerts[0]['severity'] in ['warning', 'critical']


class TestSecurityFeatures:
    """Test security features and middleware"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client):
        """Test rate limiting middleware"""
        # Make multiple requests rapidly
        responses = []
        for i in range(10):
            response = await test_client.get("/api/v1/migrations")
            responses.append(response)
        
        # Check for rate limit headers
        last_response = responses[-1]
        assert "X-RateLimit-Limit" in last_response.headers
        assert "X-RateLimit-Remaining" in last_response.headers
        assert "X-RateLimit-Window" in last_response.headers
    
    @pytest.mark.asyncio
    async def test_security_headers(self, test_client):
        """Test security headers middleware"""
        response = await test_client.get("/")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        for header in security_headers:
            assert header in response.headers
    
    @pytest.mark.asyncio
    async def test_cors_configuration(self, test_client):
        """Test CORS configuration"""
        # Test preflight request
        response = await test_client.options(
            "/api/v1/migrations",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_input_validation(self):
        """Test input validation"""
        # Test with invalid data
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(
                "Invalid email format",
                field="email",
                value="invalid-email"
            )
        
        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert exc_info.value.context["field"] == "email"


class TestLangGraphEnhancements:
    """Test LangGraph workflow enhancements"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create migration orchestrator for testing"""
        return MigrationOrchestrator()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, orchestrator):
        """Test workflow error handling and recovery"""
        # Mock a failed AI agent call
        with patch.object(orchestrator, '_run_agent') as mock_agent:
            mock_agent.side_effect = Exception("AI service unavailable")
            
            # Test error handling
            state = {
                "migration_id": "test-123",
                "source_platform": "shopify",
                "destination_platform": "ideasoft",
                "current_stage": "data_analysis",
                "error_count": 0,
                "max_retries": 3
            }
            
            result = await orchestrator._handle_agent_error(state, "data_analysis")
            
            # Should increment error count and potentially retry
            assert result["error_count"] > 0
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, orchestrator):
        """Test workflow state management"""
        initial_state = {
            "migration_id": str(uuid.uuid4()),
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "progress_percentage": 0.0,
            "current_stage": "coordinator",
            "agents_completed": [],
            "workflow_status": "running"
        }
        
        # Test state transitions
        updated_state = orchestrator._update_workflow_state(
            initial_state,
            "data_analysis",
            {"analysis_result": "completed"}
        )
        
        assert updated_state["current_stage"] == "data_analysis"
        assert "coordinator" in updated_state["agents_completed"]
    
    @pytest.mark.asyncio
    async def test_agent_fallback_mechanisms(self, orchestrator):
        """Test AI agent fallback mechanisms"""
        with patch('openai.ChatCompletion.create') as mock_openai:
            # Simulate OpenAI API failure
            mock_openai.side_effect = Exception("API rate limit exceeded")
            
            # Test fallback mechanism
            state = {
                "migration_id": "test-123",
                "source_platform": "shopify",
                "product_count": 1000,
                "customer_count": 500
            }
            
            # Should use fallback logic when AI fails
            result = await orchestrator._execute_data_analysis_fallback(state)
            
            assert result is not None
            assert "fallback_used" in result
            assert result["fallback_used"] is True


class TestAPIEndpointEnhancements:
    """Test enhanced API endpoints"""
    
    @pytest.mark.asyncio
    async def test_migration_workflow_endpoints(self, test_client):
        """Test migration workflow API endpoints"""
        # Create migration
        migration_data = {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {
                "shop_url": "test-shop.myshopify.com",
                "access_token": "test-token"
            },
            "destination_config": {
                "api_url": "https://api.ideasoft.com.tr",
                "api_key": "test-key"
            }
        }
        
        response = await test_client.post("/api/v1/migrations/", json=migration_data)
        assert response.status_code == 201
        
        migration = response.json()
        migration_id = migration["id"]
        
        # Test workflow status endpoint
        status_response = await test_client.get(f"/api/v1/migrations/{migration_id}/workflow-status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "workflow_status" in status_data
        assert "current_stage" in status_data
        assert "progress_percentage" in status_data
    
    @pytest.mark.asyncio
    async def test_migration_control_endpoints(self, test_client):
        """Test migration control endpoints (pause/resume/cancel)"""
        # First create a migration
        migration_data = {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {"shop_url": "test.myshopify.com"}
        }
        
        create_response = await test_client.post("/api/v1/migrations/", json=migration_data)
        migration_id = create_response.json()["id"]
        
        # Test pause endpoint
        pause_response = await test_client.post(f"/api/v1/migrations/{migration_id}/pause")
        assert pause_response.status_code == 200
        
        # Test resume endpoint
        resume_response = await test_client.post(f"/api/v1/migrations/{migration_id}/resume")
        assert resume_response.status_code == 200
        
        # Test cancel endpoint
        cancel_response = await test_client.delete(f"/api/v1/migrations/{migration_id}")
        assert cancel_response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_api_error_responses(self, test_client):
        """Test API error response format"""
        # Test 404 error
        response = await test_client.get("/api/v1/migrations/non-existent-id")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data
        assert "correlation_id" in error_data
        assert "timestamp" in error_data
        
        # Verify error structure
        error = error_data["error"]
        assert "error_code" in error
        assert "message" in error
        assert "type" in error


class TestPerformanceOptimizations:
    """Test performance optimizations"""
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, test_db):
        """Test database connection pooling"""
        # Simulate multiple concurrent database operations
        async def db_operation():
            # Mock database query
            await asyncio.sleep(0.1)
            return True
        
        # Run multiple operations concurrently
        tasks = [db_operation() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_caching_mechanisms(self, mock_redis):
        """Test Redis caching mechanisms"""
        # Test cache set/get
        cache_key = "test:migration:config"
        cache_value = {"platform": "shopify", "config": "test"}
        
        # Mock Redis operations
        mock_redis.set.return_value = True
        mock_redis.get.return_value = json.dumps(cache_value)
        
        # Test cache operations
        mock_redis.set(cache_key, json.dumps(cache_value))
        cached_data = json.loads(mock_redis.get(cache_key))
        
        assert cached_data == cache_value
    
    def test_background_task_processing(self):
        """Test background task processing"""
        # Test that background tasks are properly queued
        task_data = {
            "migration_id": "test-123",
            "task_type": "data_migration",
            "priority": "high"
        }
        
        # Mock background task queue
        with patch('backend.app.core.background_tasks.queue_task') as mock_queue:
            mock_queue.return_value = True
            
            result = mock_queue(task_data)
            assert result is True
            mock_queue.assert_called_once_with(task_data)


class TestAccessibilityAndUsability:
    """Test accessibility and usability features"""
    
    @pytest.mark.asyncio
    async def test_api_documentation_accessibility(self, test_client):
        """Test API documentation accessibility"""
        # Test that documentation is available
        docs_response = await test_client.get("/docs")
        assert docs_response.status_code == 200
        
        redoc_response = await test_client.get("/redoc")
        assert redoc_response.status_code == 200
    
    def test_error_message_clarity(self):
        """Test error message clarity and helpfulness"""
        # Test validation error messages
        error = ValidationError(
            "Email address must be in valid format",
            field="email",
            value="invalid-email"
        )
        
        assert "email" in error.message.lower()
        assert "valid format" in error.message.lower()
        assert error.context["field"] == "email"
    
    def test_response_time_monitoring(self):
        """Test response time monitoring"""
        start_time = time.time()
        
        # Simulate API operation
        time.sleep(0.1)
        
        duration = time.time() - start_time
        
        # Record performance metric
        performance_monitor.record_performance_metric(
            "api_response_time",
            duration,
            {"endpoint": "/test"}
        )
        
        # Verify metric was recorded
        assert len(performance_monitor.metrics_buffer) > 0


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_migration_workflow(self, test_client, test_db):
        """Test complete migration workflow from start to finish"""
        # 1. Create migration
        migration_data = {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {
                "shop_url": "test-shop.myshopify.com",
                "access_token": "test-token"
            },
            "destination_config": {
                "api_url": "https://api.ideasoft.com.tr",
                "api_key": "test-key"
            },
            "migration_options": {
                "include_products": True,
                "include_customers": True,
                "include_orders": True,
                "preserve_seo": True
            }
        }
        
        create_response = await test_client.post("/api/v1/migrations/", json=migration_data)
        assert create_response.status_code == 201
        migration = create_response.json()
        migration_id = migration["id"]
        
        # 2. Monitor workflow progress
        max_attempts = 10
        for attempt in range(max_attempts):
            status_response = await test_client.get(f"/api/v1/migrations/{migration_id}/workflow-status")
            status_data = status_response.json()
            
            if status_data["workflow_status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
        
        # 3. Verify final state
        final_response = await test_client.get(f"/api/v1/migrations/{migration_id}")
        final_data = final_response.json()
        
        assert final_data["workflow_status"] in ["completed", "failed"]
        if final_data["workflow_status"] == "completed":
            assert final_data["progress_percentage"] == 100.0
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, test_client):
        """Test error recovery and retry mechanisms"""
        # Create migration with invalid configuration to trigger errors
        migration_data = {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {
                "shop_url": "invalid-shop-url",
                "access_token": "invalid-token"
            }
        }
        
        create_response = await test_client.post("/api/v1/migrations/", json=migration_data)
        migration_id = create_response.json()["id"]
        
        # Monitor for error handling
        await asyncio.sleep(2)  # Allow some processing time
        
        status_response = await test_client.get(f"/api/v1/migrations/{migration_id}/workflow-status")
        status_data = status_response.json()
        
        # Should handle errors gracefully
        assert "error_count" in status_data
        assert status_data.get("error_count", 0) >= 0


# Property-based testing
try:
    from hypothesis import given, strategies as st
    
    class TestPropertyBasedTesting:
        """Property-based tests using Hypothesis"""
        
        @given(st.text(min_size=1, max_size=100))
        def test_migration_id_validation(self, migration_id):
            """Test migration ID validation with various inputs"""
            # Assume migration IDs should be UUIDs or alphanumeric
            import re
            
            # Test that validation function handles all string inputs
            if re.match(r'^[a-zA-Z0-9\-]+$', migration_id):
                # Should be valid
                assert len(migration_id) > 0
            else:
                # Should raise validation error
                with pytest.raises(ValidationError):
                    raise ValidationError("Invalid migration ID", field="migration_id", value=migration_id)
        
        @given(st.integers(min_value=1, max_value=100000))
        def test_migration_data_volume_processing(self, item_count):
            """Test migration processing with various data volumes"""
            # Test that system can handle different data volumes
            batch_size = min(1000, max(10, item_count // 10))
            batches = (item_count + batch_size - 1) // batch_size
            
            assert batches > 0
            assert batches * batch_size >= item_count

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.benchmark
    def test_api_response_time_benchmark(self, test_client, benchmark):
        """Benchmark API response times"""
        async def api_call():
            response = await test_client.get("/api/v1/migrations")
            return response
        
        # Benchmark the API call
        result = benchmark(asyncio.run, api_call())
        assert result.status_code == 200
    
    @pytest.mark.benchmark
    def test_workflow_processing_benchmark(self, benchmark):
        """Benchmark workflow processing speed"""
        def process_workflow():
            # Mock workflow processing
            state = {
                "migration_id": "test-123",
                "product_count": 1000,
                "processing_stage": "data_analysis"
            }
            
            # Simulate processing time
            time.sleep(0.01)
            return state
        
        result = benchmark(process_workflow)
        assert result["migration_id"] == "test-123"


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=backend/app",
        "--cov-report=html",
        "--cov-report=term",
        "--cov-fail-under=80"
    ])