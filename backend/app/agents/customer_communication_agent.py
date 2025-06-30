"""
Customer Communication Agent - Manages customer notifications and communications during migration
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


class CommunicationPlanOutputParser(BaseOutputParser):
    """Parser for communication planning agent output"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the LLM output into structured communication plan"""
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
                    "communication_summary": text,
                    "notification_count": 3,
                    "notifications": [],
                    "channels": []
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse communication plan as JSON", text=text)
            return {
                "communication_summary": text,
                "notification_count": 3,
                "notifications": [],
                "channels": []
            }


class CustomerCommunicationAgent:
    """
    Intelligent agent for managing customer communications during migration
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.output_parser = CommunicationPlanOutputParser()
        
        # System prompt for communication planning
        self.system_prompt = SystemMessagePromptTemplate.from_template("""
You are an expert customer communication specialist with extensive experience in e-commerce platform migrations.
Your role is to create comprehensive communication plans that keep customers informed and maintain trust during migrations.

Key responsibilities:
1. Create customer-friendly migration announcements
2. Plan timeline-based communication sequences
3. Draft notifications for different migration phases
4. Ensure transparency while maintaining confidence
5. Prepare FAQ and support documentation

Always provide structured JSON output with the following format:
{{
    "communication_strategy": {{
        "approach": "transparent|minimal|detailed",
        "tone": "professional|friendly|reassuring",
        "target_audience": ["customer segments"],
        "communication_timeline_days": number,
        "estimated_customer_count": number
    }},
    "notification_schedule": [
        {{
            "phase": "pre_migration|during_migration|post_migration",
            "timing": "days before/after migration",
            "notification_type": "announcement|update|completion",
            "channels": ["email|sms|website|app"],
            "priority": "low|medium|high|critical"
        }}
    ],
    "message_templates": [
        {{
            "template_id": "unique identifier",
            "template_name": "descriptive name",
            "phase": "pre_migration|during_migration|post_migration",
            "channel": "email|sms|website|app|blog",
            "subject_line": "email subject or title",
            "message_content": "full message content",
            "call_to_action": "specific action for customers",
            "personalization_fields": ["list of dynamic fields"]
        }}
    ],
    "customer_segments": [
        {{
            "segment_name": "segment identifier",
            "description": "segment description",
            "estimated_size": number,
            "communication_preferences": ["preferred channels"],
            "special_considerations": ["any special needs"]
        }}
    ],
    "support_documentation": {{
        "faq_topics": ["list of expected questions"],
        "help_articles": ["list of article topics"],
        "video_tutorials": ["list of tutorial topics"],
        "support_channel_preparation": ["required preparations"]
    }},
    "crisis_communication": {{
        "escalation_triggers": ["conditions requiring immediate communication"],
        "emergency_templates": ["template names for crisis situations"],
        "stakeholder_notifications": ["internal team notifications"],
        "recovery_messaging": ["post-crisis communication plan"]
    }},
    "success_metrics": [
        {{
            "metric_name": "specific communication metric",
            "measurement_method": "how to measure",
            "target_value": "desired outcome",
            "monitoring_frequency": "daily|weekly|monthly"
        }}
    ]
}}

Focus on maintaining customer trust and minimizing confusion during the migration process.
        """)
        
        self.human_prompt = HumanMessagePromptTemplate.from_template("""
Create a comprehensive customer communication plan for the following migration:

Migration Plan Details:
{migration_plan}

SEO Analysis Results:
{seo_analysis}

Migration Configuration:
- Source Platform: {source_platform}
- Destination Platform: {destination_platform}
- Estimated Duration: {estimated_duration_days} days
- Migration Complexity: {complexity_level}
- Customer Impact Level: {customer_impact_level}

Please create a detailed communication plan that includes:
1. Customer notification strategy and timeline
2. Message templates for different phases and channels
3. Customer segmentation and targeting approach
4. Support documentation and FAQ preparation
5. Crisis communication procedures
6. Success metrics for communication effectiveness

Consider the migration timeline and complexity to ensure communications are timely and appropriate.
        """)
        
        # Create the communication planning chain
        self.communication_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                self.system_prompt,
                self.human_prompt
            ]),
            output_parser=self.output_parser
        )
    
    async def create_communication_plan(
        self,
        migration_plan: Dict[str, Any],
        seo_analysis: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a comprehensive customer communication plan
        
        Args:
            migration_plan: Migration plan from planning agent
            seo_analysis: SEO analysis from SEO agent
            migration_config: Migration configuration
            
        Returns:
            Detailed communication plan with templates and schedules
        """
        
        logger.info(
            "Creating customer communication plan",
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform')
        )
        
        try:
            # Extract key information
            estimated_duration = migration_plan.get('migration_plan', {}).get('estimated_duration_days', 7)
            complexity_level = migration_plan.get('migration_plan', {}).get('complexity_level', 'medium')
            customer_impact_level = self._assess_customer_impact(migration_config, seo_analysis)
            
            # Create communication plan using AI
            ai_plan = await self._create_ai_communication_plan(
                migration_plan,
                seo_analysis,
                migration_config,
                estimated_duration,
                complexity_level,
                customer_impact_level
            )
            
            # Enhance with platform-specific templates
            enhanced_plan = await self._enhance_with_platform_templates(ai_plan, migration_config)
            
            # Add timeline optimization
            optimized_plan = await self._optimize_communication_timeline(enhanced_plan, estimated_duration)
            
            # Generate specific notification schedules
            notification_schedule = await self._generate_notification_schedule(optimized_plan, estimated_duration)
            
            # Final communication strategy
            final_plan = {
                **optimized_plan,
                "notification_schedule": notification_schedule,
                "implementation_guidelines": self._create_implementation_guidelines(),
                "plan_metadata": {
                    "created_timestamp": datetime.utcnow().isoformat(),
                    "created_by_agent": "customer_communication_agent",
                    "version": "1.0"
                }
            }
            
            logger.info(
                "Communication plan created successfully",
                notification_count=len(final_plan.get('message_templates', [])),
                timeline_days=final_plan.get('communication_strategy', {}).get('communication_timeline_days'),
                customer_segments=len(final_plan.get('customer_segments', []))
            )
            
            return final_plan
            
        except Exception as e:
            logger.error(
                "Communication planning failed",
                error=str(e),
                exc_info=True
            )
            
            # Return fallback plan
            return self._create_fallback_communication_plan(migration_config, str(e))
    
    async def _create_ai_communication_plan(
        self,
        migration_plan: Dict[str, Any],
        seo_analysis: Dict[str, Any],
        migration_config: Dict[str, Any],
        estimated_duration: int,
        complexity_level: str,
        customer_impact_level: str
    ) -> Dict[str, Any]:
        """Create communication plan using AI"""
        
        # Prepare data for AI analysis
        plan_summary = json.dumps(migration_plan, indent=2)
        seo_summary = json.dumps(seo_analysis, indent=2)
        
        # Run AI communication planning
        result = await self.communication_chain.arun(
            migration_plan=plan_summary,
            seo_analysis=seo_summary,
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform'),
            estimated_duration_days=estimated_duration,
            complexity_level=complexity_level,
            customer_impact_level=customer_impact_level
        )
        
        return result
    
    async def _enhance_with_platform_templates(
        self,
        ai_plan: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance AI plan with platform-specific message templates"""
        
        source_platform = migration_config.get('source_platform', '').lower()
        destination_platform = migration_config.get('destination_platform', '').lower()
        
        # Add platform-specific templates
        platform_templates = self._get_platform_specific_templates(source_platform, destination_platform)
        
        # Merge with existing templates
        existing_templates = ai_plan.get('message_templates', [])
        ai_plan['message_templates'] = existing_templates + platform_templates
        
        # Add platform-specific considerations
        ai_plan['platform_considerations'] = {
            'source_platform_features': self._get_platform_features(source_platform),
            'destination_platform_features': self._get_platform_features(destination_platform),
            'feature_differences': self._compare_platform_features(source_platform, destination_platform)
        }
        
        return ai_plan
    
    async def _optimize_communication_timeline(
        self,
        plan: Dict[str, Any],
        estimated_duration: int
    ) -> Dict[str, Any]:
        """Optimize communication timeline based on migration duration"""
        
        # Calculate optimal notification timing
        timeline_days = max(estimated_duration + 14, 21)  # Add buffer for preparation and monitoring
        
        # Update communication strategy
        if 'communication_strategy' not in plan:
            plan['communication_strategy'] = {}
        
        plan['communication_strategy']['communication_timeline_days'] = timeline_days
        plan['communication_strategy']['pre_migration_days'] = max(7, estimated_duration // 2)
        plan['communication_strategy']['post_migration_monitoring_days'] = 7
        
        return plan
    
    async def _generate_notification_schedule(
        self,
        plan: Dict[str, Any],
        estimated_duration: int
    ) -> List[Dict[str, Any]]:
        """Generate specific notification schedule with dates"""
        
        schedule = []
        migration_start_date = datetime.utcnow() + timedelta(days=7)  # Assume 7 days preparation
        
        # Pre-migration notifications
        notifications = [
            {
                "phase": "pre_migration",
                "timing_days": -7,
                "notification_type": "announcement",
                "title": "Important: Store Migration Scheduled",
                "priority": "high"
            },
            {
                "phase": "pre_migration", 
                "timing_days": -3,
                "notification_type": "reminder",
                "title": "Migration Reminder: 3 Days to Go",
                "priority": "medium"
            },
            {
                "phase": "pre_migration",
                "timing_days": -1,
                "notification_type": "final_notice",
                "title": "Final Notice: Migration Tomorrow",
                "priority": "high"
            }
        ]
        
        # During migration notifications
        if estimated_duration > 3:
            notifications.append({
                "phase": "during_migration",
                "timing_days": estimated_duration // 2,
                "notification_type": "progress_update",
                "title": "Migration Progress Update",
                "priority": "medium"
            })
        
        # Post-migration notifications
        notifications.extend([
            {
                "phase": "post_migration",
                "timing_days": 0,
                "notification_type": "completion",
                "title": "Migration Complete - Welcome to Your New Store!",
                "priority": "high"
            },
            {
                "phase": "post_migration",
                "timing_days": 3,
                "notification_type": "follow_up",
                "title": "How Is Your New Store Experience?",
                "priority": "low"
            }
        ])
        
        # Add specific dates and channels
        for notification in notifications:
            notification_date = migration_start_date + timedelta(days=notification["timing_days"])
            
            schedule_item = {
                **notification,
                "scheduled_date": notification_date.strftime('%Y-%m-%d'),
                "scheduled_time": "09:00",  # Default to 9 AM
                "channels": self._get_channels_for_priority(notification["priority"]),
                "estimated_reach": "All active customers"
            }
            schedule.append(schedule_item)
        
        return schedule
    
    def _assess_customer_impact(
        self,
        migration_config: Dict[str, Any],
        seo_analysis: Dict[str, Any]
    ) -> str:
        """Assess the level of customer impact during migration"""
        
        # Check for domain changes
        source_config = migration_config.get('source_config', {})
        destination_config = migration_config.get('destination_config', {})
        
        domain_change = (
            source_config.get('store_url', '') != 
            destination_config.get('store_url', '')
        )
        
        # Check SEO risk level
        seo_risk = seo_analysis.get('seo_analysis', {}).get('risk_level', 'medium')
        
        # Determine customer impact level
        if domain_change and seo_risk in ['high', 'critical']:
            return "high"
        elif domain_change or seo_risk == 'high':
            return "medium"
        elif seo_risk == 'medium':
            return "low"
        else:
            return "minimal"
    
    def _get_platform_specific_templates(self, source_platform: str, destination_platform: str) -> List[Dict[str, Any]]:
        """Get platform-specific message templates"""
        
        templates = []
        
        # Shopify to Ideasoft specific template
        if source_platform == 'shopify' and destination_platform == 'ideasoft':
            templates.append({
                "template_id": "shopify_to_ideasoft_announcement",
                "template_name": "Shopify to Ideasoft Migration Announcement",
                "phase": "pre_migration",
                "channel": "email",
                "subject_line": "Exciting Store Upgrade Coming Soon!",
                "message_content": """
Dear Valued Customer,

We're excited to announce that we're upgrading our store to provide you with an even better shopping experience! 

What's happening:
• We're migrating from Shopify to a new, more powerful platform (Ideasoft)
• Your account information and order history will be preserved
• All your favorite products will still be available
• You'll enjoy improved performance and new features

When: The migration is scheduled for [DATE]
Duration: Approximately [DURATION] days

What you need to do: Nothing! We'll handle everything for you.

Thank you for your patience as we make these improvements.

Best regards,
[STORE_NAME] Team
                """,
                "call_to_action": "Continue shopping as usual",
                "personalization_fields": ["customer_name", "migration_date", "duration", "store_name"]
            })
        
        return templates
    
    def _get_platform_features(self, platform: str) -> List[str]:
        """Get key features of a platform"""
        
        features = {
            'shopify': [
                'Easy checkout process',
                'Mobile-optimized design',
                'App integrations',
                'Multi-currency support'
            ],
            'ideasoft': [
                'Advanced Turkish market features',
                'Local payment integrations',
                'Enhanced SEO capabilities',
                'Improved performance'
            ],
            'woocommerce': [
                'WordPress integration',
                'Flexible customization',
                'Plugin ecosystem',
                'Content management'
            ],
            'magento': [
                'Enterprise features',
                'Advanced B2B capabilities',
                'Multi-store management',
                'Complex product catalogs'
            ]
        }
        
        return features.get(platform.lower(), ['Standard e-commerce features'])
    
    def _compare_platform_features(self, source_platform: str, destination_platform: str) -> Dict[str, Any]:
        """Compare features between platforms"""
        
        source_features = set(self._get_platform_features(source_platform))
        dest_features = set(self._get_platform_features(destination_platform))
        
        return {
            'new_features': list(dest_features - source_features),
            'removed_features': list(source_features - dest_features),
            'common_features': list(source_features & dest_features)
        }
    
    def _get_channels_for_priority(self, priority: str) -> List[str]:
        """Get communication channels based on priority"""
        
        channel_map = {
            'critical': ['email', 'sms', 'website_banner', 'app_notification'],
            'high': ['email', 'website_banner'],
            'medium': ['email'],
            'low': ['email', 'blog_post']
        }
        
        return channel_map.get(priority, ['email'])
    
    def _create_implementation_guidelines(self) -> Dict[str, Any]:
        """Create guidelines for implementing the communication plan"""
        
        return {
            "preparation_checklist": [
                "Review and approve all message templates",
                "Set up communication channels and tools",
                "Prepare customer service team with FAQs",
                "Schedule notifications in advance",
                "Test all communication systems"
            ],
            "best_practices": [
                "Send notifications during business hours",
                "Use clear, non-technical language",
                "Provide specific dates and times",
                "Include contact information for questions",
                "Monitor customer feedback and respond promptly"
            ],
            "monitoring_requirements": [
                "Track email open and click rates",
                "Monitor customer service inquiries",
                "Measure social media sentiment",
                "Collect customer feedback surveys",
                "Analyze website traffic patterns"
            ],
            "contingency_procedures": [
                "Prepare additional FAQ content",
                "Have backup communication channels ready",
                "Plan for increased customer service capacity",
                "Create escalation procedures for issues",
                "Prepare crisis communication templates"
            ]
        }
    
    def _create_fallback_communication_plan(self, migration_config: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create fallback communication plan when AI planning fails"""
        
        return {
            "communication_strategy": {
                "approach": "transparent",
                "tone": "professional",
                "target_audience": ["all_customers"],
                "communication_timeline_days": 14,
                "estimated_customer_count": 1000,
                "fallback_reason": error
            },
            "message_templates": [
                {
                    "template_id": "fallback_announcement",
                    "template_name": "Migration Announcement",
                    "phase": "pre_migration",
                    "channel": "email",
                    "subject_line": "Important Store Update Scheduled",
                    "message_content": "We're upgrading our store to serve you better. The migration is scheduled for [DATE] and will take approximately [DURATION]. Your account and order history will be preserved.",
                    "call_to_action": "Continue shopping as usual",
                    "personalization_fields": ["migration_date", "duration"]
                },
                {
                    "template_id": "fallback_completion",
                    "template_name": "Migration Complete",
                    "phase": "post_migration",
                    "channel": "email",
                    "subject_line": "Store Upgrade Complete!",
                    "message_content": "Our store upgrade is now complete! You can continue shopping with improved performance and features. Thank you for your patience.",
                    "call_to_action": "Start shopping now",
                    "personalization_fields": []
                }
            ],
            "customer_segments": [
                {
                    "segment_name": "all_customers",
                    "description": "All registered customers",
                    "estimated_size": 1000,
                    "communication_preferences": ["email"],
                    "special_considerations": ["Basic migration notifications only"]
                }
            ],
            "support_documentation": {
                "faq_topics": [
                    "What is happening to the store?",
                    "Will my account be affected?",
                    "How long will the migration take?",
                    "What if I have issues?"
                ],
                "help_articles": ["Migration FAQ", "Account Access Guide"],
                "video_tutorials": [],
                "support_channel_preparation": ["Prepare standard migration FAQ"]
            },
            "success_metrics": [
                {
                    "metric_name": "Customer inquiry volume",
                    "measurement_method": "Support ticket count",
                    "target_value": "< 5% increase",
                    "monitoring_frequency": "daily"
                }
            ]
        }