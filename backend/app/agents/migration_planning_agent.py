"""
Migration Planning Agent - Creates detailed migration roadmaps and timelines
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain.chains import LLMChain
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class MigrationPlanOutputParser(BaseOutputParser):
    """Parser for migration planning agent output"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the LLM output into structured migration plan"""
        try:
            # Extract JSON from the response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    "plan_summary": text,
                    "estimated_duration_days": 7,
                    "phases": [],
                    "risks": []
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse migration plan as JSON", text=text)
            return {
                "plan_summary": text,
                "estimated_duration_days": 7,
                "phases": [],
                "risks": []
            }


class MigrationPlanningAgent:
    """
    Intelligent agent for creating detailed migration plans and timelines
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.2,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.output_parser = MigrationPlanOutputParser()
        
        # System prompt for migration planning
        self.system_prompt = SystemMessagePromptTemplate.from_template("""
You are an expert e-commerce migration planner with extensive experience in platform transitions.
Your role is to create comprehensive, realistic migration plans based on technical analysis results.

Key responsibilities:
1. Create detailed phase-by-phase migration timelines
2. Identify dependencies and prerequisites
3. Assess risks and create mitigation strategies
4. Estimate resource requirements and effort
5. Plan rollback procedures for safety

Always provide structured JSON output with the following format:
{{
    "migration_plan": {{
        "plan_id": "unique identifier",
        "estimated_duration_days": number,
        "estimated_effort_hours": number,
        "complexity_level": "low|medium|high|critical",
        "confidence_score": 0.0-1.0
    }},
    "phases": [
        {{
            "phase_name": "descriptive name",
            "phase_number": number,
            "duration_days": number,
            "prerequisites": ["list of requirements"],
            "tasks": [
                {{
                    "task_name": "specific task",
                    "estimated_hours": number,
                    "assignee_type": "developer|analyst|qa|admin",
                    "dependencies": ["task dependencies"],
                    "critical_path": boolean
                }}
            ],
            "deliverables": ["expected outputs"],
            "success_criteria": ["measurable criteria"]
        }}
    ],
    "resource_requirements": {{
        "developers": number,
        "analysts": number,
        "qa_engineers": number,
        "system_admins": number,
        "estimated_cost_range": "low|medium|high"
    }},
    "risks": [
        {{
            "risk_category": "technical|business|timeline|data",
            "risk_description": "detailed description",
            "probability": "low|medium|high",
            "impact": "low|medium|high",
            "mitigation_strategy": "specific actions",
            "contingency_plan": "backup approach"
        }}
    ],
    "rollback_plan": {{
        "rollback_triggers": ["conditions for rollback"],
        "rollback_procedures": ["step-by-step rollback"],
        "data_recovery_time": "estimated time",
        "business_impact": "impact assessment"
    }},
    "success_metrics": [
        {{
            "metric_name": "specific metric",
            "target_value": "measurable target",
            "measurement_method": "how to measure"
        }}
    ]
}}

Focus on practical, actionable plans that minimize business disruption.
        """)
        
        self.human_prompt = HumanMessagePromptTemplate.from_template("""
Create a comprehensive migration plan based on the following analysis:

Platform Analysis Results:
{analysis_result}

Migration Configuration:
- Source Platform: {source_platform}
- Destination Platform: {destination_platform}
- Data Volume: {data_volume}
- Business Requirements: {business_requirements}

Please create a detailed migration plan that includes:
1. Phase-by-phase breakdown with realistic timelines
2. Resource requirements and role assignments
3. Risk assessment with mitigation strategies
4. Dependencies and critical path analysis
5. Rollback procedures for safety
6. Success metrics and validation criteria

Consider the complexity level from the analysis and ensure the plan is achievable within business constraints.
        """)
        
        # Create the planning chain
        self.planning_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                self.system_prompt,
                self.human_prompt
            ]),
            output_parser=self.output_parser
        )
    
    async def create_migration_plan(
        self,
        analysis_result: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a comprehensive migration plan based on analysis results
        
        Args:
            analysis_result: Results from data analysis agent
            migration_config: Migration configuration and preferences
            
        Returns:
            Detailed migration plan with timelines and resources
        """
        
        logger.info(
            "Creating migration plan",
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform')
        )
        
        try:
            # Extract key information from analysis
            platform_complexity = analysis_result.get('platform_analysis', {}).get('structure_complexity', 'medium')
            data_volume = self._calculate_data_volume(analysis_result)
            business_requirements = migration_config.get('migration_options', {})
            
            # Create migration plan using AI
            ai_plan = await self._create_ai_migration_plan(
                analysis_result,
                migration_config,
                platform_complexity,
                data_volume,
                business_requirements
            )
            
            # Enhance with technical calculations
            enhanced_plan = await self._enhance_plan_with_calculations(ai_plan, analysis_result)
            
            # Add timeline optimization
            optimized_plan = await self._optimize_timeline(enhanced_plan)
            
            # Final validation and adjustments
            final_plan = await self._validate_and_adjust_plan(optimized_plan, migration_config)
            
            logger.info(
                "Migration plan created successfully",
                estimated_days=final_plan.get('migration_plan', {}).get('estimated_duration_days'),
                phases_count=len(final_plan.get('phases', [])),
                risks_identified=len(final_plan.get('risks', []))
            )
            
            return final_plan
            
        except Exception as e:
            logger.error(
                "Migration planning failed",
                error=str(e),
                exc_info=True
            )
            
            # Return fallback plan
            return self._create_fallback_plan(migration_config, str(e))
    
    async def _create_ai_migration_plan(
        self,
        analysis_result: Dict[str, Any],
        migration_config: Dict[str, Any],
        platform_complexity: str,
        data_volume: Dict[str, Any],
        business_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create migration plan using AI analysis"""
        
        # Prepare data for AI analysis
        analysis_summary = json.dumps(analysis_result, indent=2)
        
        # Run AI planning
        result = await self.planning_chain.arun(
            analysis_result=analysis_summary,
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform'),
            data_volume=json.dumps(data_volume, indent=2),
            business_requirements=json.dumps(business_requirements, indent=2)
        )
        
        return result
    
    async def _enhance_plan_with_calculations(
        self,
        ai_plan: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance AI plan with technical calculations"""
        
        # Calculate more accurate time estimates
        technical_analysis = analysis_result.get('technical_analysis', {})
        migration_estimates = technical_analysis.get('migration_estimates', {})
        
        if migration_estimates:
            # Update duration based on technical analysis
            technical_duration = migration_estimates.get('estimated_duration_days', 0)
            ai_duration = ai_plan.get('migration_plan', {}).get('estimated_duration_days', 0)
            
            # Use the more conservative estimate
            final_duration = max(technical_duration, ai_duration)
            
            if 'migration_plan' not in ai_plan:
                ai_plan['migration_plan'] = {}
            
            ai_plan['migration_plan']['estimated_duration_days'] = final_duration
            ai_plan['migration_plan']['technical_estimate_days'] = technical_duration
            ai_plan['migration_plan']['ai_estimate_days'] = ai_duration
        
        # Add data-specific considerations
        data_volume = analysis_result.get('technical_analysis', {}).get('data_volume_analysis', {})
        if data_volume:
            ai_plan['data_considerations'] = {
                'estimated_products': data_volume.get('estimated_total_products', 0),
                'estimated_customers': data_volume.get('estimated_total_customers', 0),
                'estimated_orders': data_volume.get('estimated_total_orders', 0),
                'parallel_processing_recommended': data_volume.get('estimated_total_products', 0) > 1000
            }
        
        return ai_plan
    
    async def _optimize_timeline(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize timeline based on dependencies and critical path"""
        
        phases = plan.get('phases', [])
        
        for i, phase in enumerate(phases):
            # Add buffer time for complex phases
            if phase.get('phase_name', '').lower() in ['data_migration', 'testing', 'go_live']:
                current_duration = phase.get('duration_days', 1)
                phase['duration_days'] = int(current_duration * 1.2)  # Add 20% buffer
                phase['buffer_added'] = True
            
            # Calculate critical path
            phase['critical_path'] = i in [0, len(phases)-1]  # First and last phases are critical
            
            # Add recommended start date
            if i == 0:
                phase['recommended_start_date'] = datetime.utcnow().strftime('%Y-%m-%d')
            else:
                prev_phase = phases[i-1]
                prev_duration = prev_phase.get('duration_days', 1)
                start_date = datetime.utcnow() + timedelta(days=sum(p.get('duration_days', 1) for p in phases[:i]))
                phase['recommended_start_date'] = start_date.strftime('%Y-%m-%d')
        
        return plan
    
    async def _validate_and_adjust_plan(
        self,
        plan: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and make final adjustments to the plan"""
        
        # Check for business constraints
        options = migration_config.get('migration_options', {})
        max_duration = options.get('max_duration_days')
        
        if max_duration and plan.get('migration_plan', {}).get('estimated_duration_days', 0) > max_duration:
            # Suggest parallel processing or phased approach
            plan['optimization_suggestions'] = [
                f"Original plan exceeds maximum duration of {max_duration} days",
                "Consider parallel processing of data migration",
                "Evaluate phased migration approach",
                "Increase resource allocation to compress timeline"
            ]
        
        # Add final metadata
        plan['plan_metadata'] = {
            'created_timestamp': datetime.utcnow().isoformat(),
            'created_by_agent': 'migration_planning_agent',
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return plan
    
    def _calculate_data_volume(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data volume metrics from analysis"""
        
        technical_analysis = analysis_result.get('technical_analysis', {})
        data_volume = technical_analysis.get('data_volume_analysis', {})
        
        if not data_volume:
            return {
                "products": 0,
                "customers": 0,
                "orders": 0,
                "complexity": "unknown"
            }
        
        total_items = (
            data_volume.get('estimated_total_products', 0) +
            data_volume.get('estimated_total_customers', 0) +
            data_volume.get('estimated_total_orders', 0)
        )
        
        if total_items < 1000:
            complexity = "low"
        elif total_items < 10000:
            complexity = "medium"
        else:
            complexity = "high"
        
        return {
            "products": data_volume.get('estimated_total_products', 0),
            "customers": data_volume.get('estimated_total_customers', 0),
            "orders": data_volume.get('estimated_total_orders', 0),
            "total_items": total_items,
            "complexity": complexity
        }
    
    def _create_fallback_plan(self, migration_config: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create a basic fallback plan when AI planning fails"""
        
        return {
            "migration_plan": {
                "plan_id": f"fallback_{int(datetime.utcnow().timestamp())}",
                "estimated_duration_days": 14,
                "estimated_effort_hours": 200,
                "complexity_level": "medium",
                "confidence_score": 0.3,
                "fallback_reason": error
            },
            "phases": [
                {
                    "phase_name": "Analysis & Planning",
                    "phase_number": 1,
                    "duration_days": 3,
                    "prerequisites": ["API access", "backup creation"],
                    "tasks": [
                        {
                            "task_name": "Detailed data analysis",
                            "estimated_hours": 16,
                            "assignee_type": "analyst",
                            "dependencies": [],
                            "critical_path": True
                        }
                    ],
                    "deliverables": ["Migration plan", "Risk assessment"],
                    "success_criteria": ["Plan approved", "Risks identified"]
                },
                {
                    "phase_name": "Data Migration",
                    "phase_number": 2,
                    "duration_days": 7,
                    "prerequisites": ["Testing environment", "Data mapping"],
                    "tasks": [
                        {
                            "task_name": "Extract and migrate data",
                            "estimated_hours": 80,
                            "assignee_type": "developer",
                            "dependencies": ["Detailed data analysis"],
                            "critical_path": True
                        }
                    ],
                    "deliverables": ["Migrated data", "Validation report"],
                    "success_criteria": ["Data integrity verified", "No data loss"]
                },
                {
                    "phase_name": "Testing & Go-Live",
                    "phase_number": 3,
                    "duration_days": 4,
                    "prerequisites": ["Migrated data", "UAT environment"],
                    "tasks": [
                        {
                            "task_name": "User acceptance testing",
                            "estimated_hours": 40,
                            "assignee_type": "qa",
                            "dependencies": ["Extract and migrate data"],
                            "critical_path": True
                        }
                    ],
                    "deliverables": ["Test results", "Go-live checklist"],
                    "success_criteria": ["All tests passed", "Go-live approved"]
                }
            ],
            "resource_requirements": {
                "developers": 2,
                "analysts": 1,
                "qa_engineers": 1,
                "system_admins": 1,
                "estimated_cost_range": "medium"
            },
            "risks": [
                {
                    "risk_category": "technical",
                    "risk_description": "AI planning failed - using fallback plan",
                    "probability": "high",
                    "impact": "medium",
                    "mitigation_strategy": "Manual planning review required",
                    "contingency_plan": "Engage external consultant"
                }
            ],
            "rollback_plan": {
                "rollback_triggers": ["Critical data loss", "System failure"],
                "rollback_procedures": ["Restore from backup", "DNS rollback"],
                "data_recovery_time": "4 hours",
                "business_impact": "Temporary service interruption"
            },
            "success_metrics": [
                {
                    "metric_name": "Data integrity",
                    "target_value": "100% accuracy",
                    "measurement_method": "Automated validation scripts"
                }
            ]
        }