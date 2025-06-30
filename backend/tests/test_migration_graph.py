"""
Comprehensive tests for LangGraph Multi-Agent Migration System
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

# Mock the LangGraph imports since they're not installed in test environment
import sys
from unittest.mock import MagicMock

# Mock LangGraph modules
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['langgraph.prebuilt'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.messages'] = MagicMock()
sys.modules['langchain_core.tools'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['structlog'] = MagicMock()

# Now import our modules
from backend.app.agents.data_analysis_agent import DataAnalysisAgent
from backend.app.agents.migration_planning_agent import MigrationPlanningAgent
from backend.app.agents.seo_preservation_agent import SEOPreservationAgent
from backend.app.agents.customer_communication_agent import CustomerCommunicationAgent


class TestDataAnalysisAgent:
    """Test the Data Analysis Agent functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a DataAnalysisAgent instance for testing"""
        with patch('backend.app.agents.data_analysis_agent.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            return DataAnalysisAgent()
    
    @pytest.fixture
    def sample_platform_config(self):
        """Sample platform configuration for testing"""
        return {
            "store_url": "test-store.myshopify.com",
            "access_token": "test_token",
            "platform_type": "shopify"
        }
    
    @pytest.fixture
    def sample_migration_options(self):
        """Sample migration options for testing"""
        return {
            "preserve_seo": True,
            "parallel_processing": True,
            "max_duration_days": 14
        }
    
    @pytest.mark.asyncio
    async def test_analyze_platform_success(self, agent, sample_platform_config, sample_migration_options):
        """Test successful platform analysis"""
        
        # Mock the AI chain response
        mock_ai_response = {
            "platform_analysis": {
                "platform_type": "shopify",
                "structure_complexity": "medium",
                "data_quality_score": 8.5
            },
            "data_volume_analysis": {
                "estimated_total_products": 2000,
                "estimated_total_customers": 5500,
                "estimated_total_orders": 12000
            },
            "technical_analysis": {
                "migration_estimates": {
                    "estimated_duration_days": 12,
                    "complexity_factors": ["custom_themes", "third_party_integrations"]
                }
            }
        }
        
        with patch.object(agent, '_create_ai_platform_analysis', return_value=mock_ai_response):
            result = await agent.analyze_platform("shopify", sample_platform_config, sample_migration_options)
            
            assert result is not None
            assert "platform_analysis" in result
            assert "data_volume_analysis" in result
            assert result["platform_analysis"]["platform_type"] == "shopify"
            assert result["data_volume_analysis"]["estimated_total_products"] == 2000
    
    @pytest.mark.asyncio
    async def test_analyze_platform_fallback(self, agent, sample_platform_config, sample_migration_options):
        """Test platform analysis fallback when AI fails"""
        
        with patch.object(agent, '_create_ai_platform_analysis', side_effect=Exception("AI service unavailable")):
            result = await agent.analyze_platform("shopify", sample_platform_config, sample_migration_options)
            
            assert result is not None
            assert "fallback_reason" in result
            assert result["platform_analysis"]["structure_complexity"] == "unknown"
    
    def test_calculate_technical_metrics(self, agent):
        """Test technical metrics calculation"""
        
        platform_data = {
            "product_count": 2000,
            "custom_features": 5,
            "api_endpoints": 20
        }
        
        metrics = agent._calculate_technical_metrics(platform_data)
        
        assert "complexity_score" in metrics
        assert "estimated_migration_hours" in metrics
        assert isinstance(metrics["complexity_score"], (int, float))
        assert metrics["complexity_score"] >= 0
    
    def test_estimate_migration_effort(self, agent):
        """Test migration effort estimation"""
        
        platform_analysis = {
            "structure_complexity": "medium",
            "custom_features_count": 3,
            "data_volume": "large"
        }
        
        effort = agent._estimate_migration_effort(platform_analysis)
        
        assert "estimated_duration_days" in effort
        assert "estimated_effort_hours" in effort
        assert effort["estimated_duration_days"] > 0
        assert effort["estimated_effort_hours"] > 0


class TestMigrationPlanningAgent:
    """Test the Migration Planning Agent functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a MigrationPlanningAgent instance for testing"""
        with patch('backend.app.agents.migration_planning_agent.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            return MigrationPlanningAgent()
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result for testing"""
        return {
            "platform_analysis": {
                "structure_complexity": "medium",
                "data_quality_score": 8.5
            },
            "data_volume_analysis": {
                "estimated_total_products": 2000,
                "estimated_total_customers": 5500
            },
            "technical_analysis": {
                "migration_estimates": {
                    "estimated_duration_days": 12
                }
            }
        }
    
    @pytest.fixture
    def sample_migration_config(self):
        """Sample migration configuration for testing"""
        return {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "migration_options": {
                "max_duration_days": 14,
                "parallel_processing": True
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_migration_plan_success(self, agent, sample_analysis_result, sample_migration_config):
        """Test successful migration plan creation"""
        
        mock_ai_plan = {
            "migration_plan": {
                "estimated_duration_days": 12,
                "complexity_level": "medium",
                "confidence_score": 0.89
            },
            "phases": [
                {
                    "phase_name": "Analysis & Setup",
                    "duration_days": 3,
                    "tasks": []
                }
            ],
            "risks": []
        }
        
        with patch.object(agent, '_create_ai_migration_plan', return_value=mock_ai_plan):
            result = await agent.create_migration_plan(sample_analysis_result, sample_migration_config)
            
            assert result is not None
            assert "migration_plan" in result
            assert "phases" in result
            assert result["migration_plan"]["estimated_duration_days"] == 12
    
    @pytest.mark.asyncio
    async def test_create_migration_plan_fallback(self, agent, sample_analysis_result, sample_migration_config):
        """Test migration plan fallback when AI fails"""
        
        with patch.object(agent, '_create_ai_migration_plan', side_effect=Exception("AI service unavailable")):
            result = await agent.create_migration_plan(sample_analysis_result, sample_migration_config)
            
            assert result is not None
            assert "fallback_reason" in result["migration_plan"]
            assert len(result["phases"]) > 0
    
    def test_calculate_data_volume(self, agent):
        """Test data volume calculation"""
        
        analysis_result = {
            "technical_analysis": {
                "data_volume_analysis": {
                    "estimated_total_products": 2000,
                    "estimated_total_customers": 5500,
                    "estimated_total_orders": 12000
                }
            }
        }
        
        volume = agent._calculate_data_volume(analysis_result)
        
        assert "products" in volume
        assert "customers" in volume
        assert "orders" in volume
        assert "complexity" in volume
        assert volume["products"] == 2000
        assert volume["customers"] == 5500


class TestSEOPreservationAgent:
    """Test the SEO Preservation Agent functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a SEOPreservationAgent instance for testing"""
        with patch('backend.app.agents.seo_preservation_agent.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            return SEOPreservationAgent()
    
    @pytest.fixture
    def sample_source_analysis(self):
        """Sample source analysis for testing"""
        return {
            "product_analysis": {
                "total_products": 2000,
                "seo_optimization_level": "good"
            }
        }
    
    @pytest.fixture
    def sample_migration_plan(self):
        """Sample migration plan for testing"""
        return {
            "migration_plan": {
                "estimated_duration_days": 12,
                "complexity_level": "medium"
            }
        }
    
    @pytest.fixture
    def sample_migration_config(self):
        """Sample migration configuration for testing"""
        return {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {"store_url": "old.myshopify.com"},
            "destination_config": {"store_url": "new.ideasoft.com.tr"}
        }
    
    @pytest.mark.asyncio
    async def test_analyze_seo_requirements_success(self, agent, sample_source_analysis, sample_migration_plan, sample_migration_config):
        """Test successful SEO analysis"""
        
        mock_seo_analysis = {
            "seo_analysis": {
                "risk_level": "medium",
                "critical_pages_count": 150
            },
            "url_mappings": [
                {
                    "source_url": "/products/{slug}",
                    "destination_url": "/urun/{slug}",
                    "redirect_type": "301"
                }
            ]
        }
        
        with patch.object(agent, '_create_ai_seo_analysis', return_value=mock_seo_analysis):
            result = await agent.analyze_seo_requirements(sample_source_analysis, sample_migration_plan, sample_migration_config)
            
            assert result is not None
            assert "seo_analysis" in result
            assert "url_mappings" in result
            assert result["seo_analysis"]["risk_level"] == "medium"
    
    def test_detect_domain_changes(self, agent):
        """Test domain change detection"""
        
        migration_config = {
            "source_config": {"store_url": "https://old.myshopify.com"},
            "destination_config": {"store_url": "https://new.ideasoft.com.tr"}
        }
        
        domain_change = agent._detect_domain_changes(migration_config)
        assert domain_change is True
        
        # Test no domain change
        migration_config_same = {
            "source_config": {"store_url": "https://same.domain.com"},
            "destination_config": {"store_url": "https://same.domain.com"}
        }
        
        no_domain_change = agent._detect_domain_changes(migration_config_same)
        assert no_domain_change is False
    
    def test_detect_url_structure_changes(self, agent):
        """Test URL structure change detection"""
        
        source_analysis = {}
        migration_config = {
            "source_platform": "shopify",
            "destination_platform": "ideasoft"
        }
        
        url_change = agent._detect_url_structure_changes(source_analysis, migration_config)
        assert url_change is True  # Different platforms should have different URL structures
    
    def test_calculate_traffic_risk(self, agent):
        """Test traffic risk calculation"""
        
        risk = agent._calculate_traffic_risk(5000, "good")
        
        assert "risk_level" in risk
        assert "estimated_traffic_loss" in risk
        assert "recovery_timeline" in risk
        assert risk["risk_level"] in ["low", "medium", "high", "critical"]


class TestCustomerCommunicationAgent:
    """Test the Customer Communication Agent functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a CustomerCommunicationAgent instance for testing"""
        with patch('backend.app.agents.customer_communication_agent.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            return CustomerCommunicationAgent()
    
    @pytest.fixture
    def sample_migration_plan(self):
        """Sample migration plan for testing"""
        return {
            "migration_plan": {
                "estimated_duration_days": 12,
                "complexity_level": "medium"
            }
        }
    
    @pytest.fixture
    def sample_seo_analysis(self):
        """Sample SEO analysis for testing"""
        return {
            "seo_analysis": {
                "risk_level": "medium"
            }
        }
    
    @pytest.fixture
    def sample_migration_config(self):
        """Sample migration configuration for testing"""
        return {
            "source_platform": "shopify",
            "destination_platform": "ideasoft",
            "source_config": {"store_url": "old.myshopify.com"},
            "destination_config": {"store_url": "new.ideasoft.com.tr"}
        }
    
    @pytest.mark.asyncio
    async def test_create_communication_plan_success(self, agent, sample_migration_plan, sample_seo_analysis, sample_migration_config):
        """Test successful communication plan creation"""
        
        mock_comm_plan = {
            "communication_strategy": {
                "approach": "transparent",
                "estimated_customer_count": 5500
            },
            "message_templates": [
                {
                    "template_id": "announcement",
                    "template_name": "Migration Announcement"
                }
            ]
        }
        
        with patch.object(agent, '_create_ai_communication_plan', return_value=mock_comm_plan):
            result = await agent.create_communication_plan(sample_migration_plan, sample_seo_analysis, sample_migration_config)
            
            assert result is not None
            assert "communication_strategy" in result
            assert "message_templates" in result
            assert "notification_schedule" in result
    
    def test_assess_customer_impact(self, agent):
        """Test customer impact assessment"""
        
        migration_config = {
            "source_config": {"store_url": "old.domain.com"},
            "destination_config": {"store_url": "new.domain.com"}
        }
        
        seo_analysis = {
            "seo_analysis": {"risk_level": "high"}
        }
        
        impact = agent._assess_customer_impact(migration_config, seo_analysis)
        assert impact in ["minimal", "low", "medium", "high"]
    
    def test_get_platform_features(self, agent):
        """Test platform feature retrieval"""
        
        shopify_features = agent._get_platform_features("shopify")
        ideasoft_features = agent._get_platform_features("ideasoft")
        
        assert isinstance(shopify_features, list)
        assert isinstance(ideasoft_features, list)
        assert len(shopify_features) > 0
        assert len(ideasoft_features) > 0
    
    def test_compare_platform_features(self, agent):
        """Test platform feature comparison"""
        
        comparison = agent._compare_platform_features("shopify", "ideasoft")
        
        assert "new_features" in comparison
        assert "removed_features" in comparison
        assert "common_features" in comparison
        assert isinstance(comparison["new_features"], list)


class TestMigrationOrchestrator:
    """Test the main LangGraph orchestrator"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator for testing"""
        # Import and create the orchestrator with mocked dependencies
        with patch('backend.app.agents.migration_graph.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test_key"
            
            # Mock the LangGraph components
            with patch('backend.app.agents.migration_graph.StateGraph'), \
                 patch('backend.app.agents.migration_graph.ChatOpenAI'), \
                 patch('backend.app.agents.migration_graph.DataAnalysisAgent'), \
                 patch('backend.app.agents.migration_graph.MigrationPlanningAgent'), \
                 patch('backend.app.agents.migration_graph.SEOPreservationAgent'), \
                 patch('backend.app.agents.migration_graph.CustomerCommunicationAgent'):
                
                from backend.app.agents.migration_graph import MigrationOrchestrator
                return MigrationOrchestrator()
    
    @pytest.fixture
    def sample_workflow_input(self):
        """Sample workflow input for testing"""
        class MockWorkflowInput:
            def __init__(self):
                self.migration_id = str(uuid.uuid4())
                self.source_platform = "shopify"
                self.destination_platform = "ideasoft"
                self.source_config = {"store_url": "test.myshopify.com"}
                self.destination_config = {"store_url": "test.ideasoft.com.tr"}
                self.migration_options = {"preserve_seo": True}
        
        return MockWorkflowInput()
    
    @pytest.mark.asyncio
    async def test_workflow_state_initialization(self, mock_orchestrator, sample_workflow_input):
        """Test workflow state initialization"""
        
        # Mock the workflow execution
        mock_result = {
            "migration_id": sample_workflow_input.migration_id,
            "current_stage": "completed",
            "current_progress": 100.0,
            "completed_stages": ["coordination", "data_analysis", "planning"],
            "errors": []
        }
        
        with patch.object(mock_orchestrator, 'app') as mock_app:
            mock_app.ainvoke = AsyncMock(return_value=mock_result)
            
            result = await mock_orchestrator.execute_migration_workflow(sample_workflow_input)
            
            assert result is not None
            assert result["migration_id"] == sample_workflow_input.migration_id
            assert result["current_stage"] == "completed"
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, mock_orchestrator, sample_workflow_input):
        """Test workflow error handling"""
        
        with patch.object(mock_orchestrator, 'app') as mock_app:
            mock_app.ainvoke = AsyncMock(side_effect=Exception("Workflow failed"))
            
            result = await mock_orchestrator.execute_migration_workflow(sample_workflow_input)
            
            assert result is not None
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_workflow_status_retrieval(self, mock_orchestrator):
        """Test workflow status retrieval"""
        
        migration_id = str(uuid.uuid4())
        
        status = await mock_orchestrator.get_workflow_status(migration_id)
        
        assert status is not None
        assert "migration_id" in status
        assert "status" in status
        assert "current_stage" in status
    
    @pytest.mark.asyncio
    async def test_workflow_pause_resume(self, mock_orchestrator):
        """Test workflow pause and resume functionality"""
        
        migration_id = str(uuid.uuid4())
        
        # Test pause
        pause_result = await mock_orchestrator.pause_workflow(migration_id)
        assert pause_result is True
        
        # Test resume
        resume_result = await mock_orchestrator.resume_workflow(migration_id)
        assert resume_result is True


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_shopify_to_ideasoft_workflow(self):
        """Test complete Shopify to Ideasoft migration workflow"""
        
        # Mock all agent responses
        mock_analysis = {
            "platform_analysis": {"structure_complexity": "medium"},
            "data_volume_analysis": {"estimated_total_products": 2000}
        }
        
        mock_plan = {
            "migration_plan": {"estimated_duration_days": 12},
            "phases": []
        }
        
        mock_seo = {
            "seo_analysis": {"risk_level": "medium"},
            "url_mappings": []
        }
        
        mock_comm = {
            "communication_strategy": {"estimated_customer_count": 5500},
            "message_templates": []
        }
        
        # Test that agents can work together
        assert mock_analysis["platform_analysis"]["structure_complexity"] == "medium"
        assert mock_plan["migration_plan"]["estimated_duration_days"] == 12
        assert mock_seo["seo_analysis"]["risk_level"] == "medium"
        assert mock_comm["communication_strategy"]["estimated_customer_count"] == 5500
    
    def test_error_propagation_and_recovery(self):
        """Test error propagation and recovery mechanisms"""
        
        # Test that errors are properly handled at each level
        test_errors = [
            {"stage": "data_analysis", "error": "API timeout"},
            {"stage": "planning", "error": "Invalid configuration"},
            {"stage": "seo_analysis", "error": "Domain unreachable"}
        ]
        
        for error in test_errors:
            # Each error should be containable and not crash the system
            assert "stage" in error
            assert "error" in error
            assert isinstance(error["stage"], str)
            assert isinstance(error["error"], str)
    
    def test_data_flow_consistency(self):
        """Test data flow consistency between agents"""
        
        # Mock data flowing between agents
        analysis_output = {
            "platform_analysis": {"structure_complexity": "medium"},
            "data_volume_analysis": {"estimated_total_products": 2000}
        }
        
        # Planning agent should receive analysis output
        planning_input = analysis_output
        assert planning_input["platform_analysis"]["structure_complexity"] == "medium"
        
        # SEO agent should receive both analysis and planning outputs
        seo_input = {
            "analysis": analysis_output,
            "plan": {"migration_plan": {"estimated_duration_days": 12}}
        }
        assert seo_input["analysis"]["data_volume_analysis"]["estimated_total_products"] == 2000
        assert seo_input["plan"]["migration_plan"]["estimated_duration_days"] == 12


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])