"""
SEO Preservation Agent - Maintains search rankings during migration
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain.chains import LLMChain
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class SEOAnalysisOutputParser(BaseOutputParser):
    """Parser for SEO analysis agent output"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the LLM output into structured SEO analysis"""
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
                    "seo_summary": text,
                    "risk_level": "medium",
                    "url_mappings": [],
                    "recommendations": []
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse SEO analysis as JSON", text=text)
            return {
                "seo_summary": text,
                "risk_level": "medium", 
                "url_mappings": [],
                "recommendations": []
            }


class SEOPreservationAgent:
    """
    Intelligent agent for preserving SEO rankings during migration
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.output_parser = SEOAnalysisOutputParser()
        
        # System prompt for SEO analysis
        self.system_prompt = SystemMessagePromptTemplate.from_template("""
You are an expert SEO specialist with extensive experience in e-commerce platform migrations.
Your role is to ensure search rankings are preserved during platform transitions.

Key responsibilities:
1. Analyze current SEO structure and identify critical elements
2. Create URL mapping strategies to preserve link equity
3. Ensure metadata and structured data continuity
4. Plan redirect strategies and canonical URL management
5. Assess SEO risks and create mitigation plans

Always provide structured JSON output with the following format:
{{
    "seo_analysis": {{
        "current_seo_score": 0.0-10.0,
        "risk_level": "low|medium|high|critical",
        "critical_pages_count": number,
        "indexed_pages_estimated": number,
        "backlinks_estimated": number
    }},
    "url_structure_analysis": {{
        "current_url_pattern": "description",
        "destination_url_pattern": "description", 
        "url_changes_required": boolean,
        "seo_friendly_urls": boolean,
        "canonical_issues": ["list of issues"]
    }},
    "critical_elements": {{
        "meta_titles": {{
            "count": number,
            "optimization_level": "poor|fair|good|excellent",
            "migration_complexity": "low|medium|high"
        }},
        "meta_descriptions": {{
            "count": number,
            "optimization_level": "poor|fair|good|excellent",
            "migration_complexity": "low|medium|high"
        }},
        "heading_structure": {{
            "h1_tags": number,
            "structure_quality": "poor|fair|good|excellent",
            "migration_complexity": "low|medium|high"
        }},
        "structured_data": {{
            "schemas_present": ["list of schema types"],
            "schema_compliance": "poor|fair|good|excellent",
            "migration_complexity": "low|medium|high"
        }}
    }},
    "url_mappings": [
        {{
            "source_url": "original URL pattern",
            "destination_url": "new URL pattern",
            "redirect_type": "301|302|canonical",
            "seo_priority": "low|medium|high|critical",
            "estimated_traffic": "percentage or description"
        }}
    ],
    "redirect_strategy": {{
        "redirect_method": "htaccess|nginx|application|cdn",
        "batch_processing": boolean,
        "testing_approach": "description",
        "monitoring_plan": "description"
    }},
    "migration_risks": [
        {{
            "risk_type": "rankings|traffic|indexing|technical",
            "risk_description": "detailed description",
            "probability": "low|medium|high",
            "impact_severity": "low|medium|high|critical",
            "affected_pages": number,
            "mitigation_strategy": "specific actions",
            "timeline_impact": "immediate|short-term|long-term"
        }}
    ],
    "preservation_plan": {{
        "pre_migration_tasks": ["list of tasks"],
        "during_migration_tasks": ["list of tasks"],
        "post_migration_tasks": ["list of tasks"],
        "monitoring_duration_days": number,
        "recovery_procedures": ["emergency procedures"]
    }},
    "success_metrics": [
        {{
            "metric_name": "specific SEO metric",
            "baseline_value": "current value",
            "target_value": "target after migration",
            "measurement_frequency": "daily|weekly|monthly",
            "alert_threshold": "when to trigger alerts"
        }}
    ]
}}

Focus on preserving organic search traffic and maintaining search engine rankings.
        """)
        
        self.human_prompt = HumanMessagePromptTemplate.from_template("""
Analyze the SEO requirements for the following migration:

Source Platform Analysis:
{source_analysis}

Migration Plan:
{migration_plan}

Migration Configuration:
- Source Platform: {source_platform}
- Destination Platform: {destination_platform}
- Domain Changes: {domain_changes}
- URL Structure Changes: {url_structure_changes}

Please provide a comprehensive SEO preservation analysis that includes:
1. Current SEO assessment and risk evaluation
2. URL mapping strategy for critical pages
3. Metadata and structured data migration plan
4. Redirect implementation strategy
5. Risk mitigation for organic traffic preservation
6. Monitoring and recovery procedures

Consider the complexity and timeline from the migration plan to ensure SEO preservation is realistic and achievable.
        """)
        
        # Create the SEO analysis chain
        self.seo_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                self.system_prompt,
                self.human_prompt
            ]),
            output_parser=self.output_parser
        )
    
    async def analyze_seo_requirements(
        self,
        source_analysis: Dict[str, Any],
        migration_plan: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze SEO requirements and create preservation strategy
        
        Args:
            source_analysis: Results from data analysis agent
            migration_plan: Migration plan from planning agent
            migration_config: Migration configuration
            
        Returns:
            Comprehensive SEO preservation plan
        """
        
        logger.info(
            "Starting SEO analysis",
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform')
        )
        
        try:
            # Determine if domain/URL structure changes are required
            domain_changes = self._detect_domain_changes(migration_config)
            url_structure_changes = self._detect_url_structure_changes(source_analysis, migration_config)
            
            # Create SEO analysis using AI
            ai_analysis = await self._create_ai_seo_analysis(
                source_analysis,
                migration_plan,
                migration_config,
                domain_changes,
                url_structure_changes
            )
            
            # Enhance with technical SEO analysis
            enhanced_analysis = await self._enhance_with_technical_analysis(ai_analysis, source_analysis)
            
            # Generate specific URL mappings
            url_mappings = await self._generate_url_mappings(enhanced_analysis, migration_config)
            
            # Create monitoring plan
            monitoring_plan = await self._create_monitoring_plan(enhanced_analysis)
            
            # Final SEO strategy
            final_analysis = {
                **enhanced_analysis,
                "url_mappings": url_mappings,
                "monitoring_plan": monitoring_plan,
                "analysis_metadata": {
                    "created_timestamp": datetime.utcnow().isoformat(),
                    "created_by_agent": "seo_preservation_agent",
                    "version": "1.0"
                }
            }
            
            logger.info(
                "SEO analysis completed successfully",
                risk_level=final_analysis.get('seo_analysis', {}).get('risk_level'),
                url_mappings_count=len(url_mappings),
                monitoring_duration=final_analysis.get('preservation_plan', {}).get('monitoring_duration_days')
            )
            
            return final_analysis
            
        except Exception as e:
            logger.error(
                "SEO analysis failed",
                error=str(e),
                exc_info=True
            )
            
            # Return fallback analysis
            return self._create_fallback_seo_analysis(migration_config, str(e))
    
    async def _create_ai_seo_analysis(
        self,
        source_analysis: Dict[str, Any],
        migration_plan: Dict[str, Any],
        migration_config: Dict[str, Any],
        domain_changes: bool,
        url_structure_changes: bool
    ) -> Dict[str, Any]:
        """Create SEO analysis using AI"""
        
        # Prepare data for AI analysis
        source_summary = json.dumps(source_analysis, indent=2)
        plan_summary = json.dumps(migration_plan, indent=2)
        
        # Run AI SEO analysis
        result = await self.seo_chain.arun(
            source_analysis=source_summary,
            migration_plan=plan_summary,
            source_platform=migration_config.get('source_platform'),
            destination_platform=migration_config.get('destination_platform'),
            domain_changes=str(domain_changes),
            url_structure_changes=str(url_structure_changes)
        )
        
        return result
    
    async def _enhance_with_technical_analysis(
        self,
        ai_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance AI analysis with technical SEO considerations"""
        
        # Add technical SEO factors
        product_analysis = source_analysis.get('product_analysis', {})
        
        if product_analysis:
            # Estimate SEO impact based on product data
            total_products = product_analysis.get('total_products', 0)
            seo_optimization = product_analysis.get('seo_optimization_level', 'fair')
            
            # Calculate potential traffic impact
            if total_products > 0:
                traffic_risk = self._calculate_traffic_risk(total_products, seo_optimization)
                ai_analysis['traffic_impact_assessment'] = traffic_risk
        
        # Add page-specific analysis
        page_analysis = self._analyze_page_types(source_analysis)
        ai_analysis['page_type_analysis'] = page_analysis
        
        return ai_analysis
    
    async def _generate_url_mappings(
        self,
        seo_analysis: Dict[str, Any],
        migration_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific URL mappings for critical pages"""
        
        url_mappings = []
        
        # Common e-commerce page patterns
        page_patterns = [
            {
                "type": "product",
                "source_pattern": "/products/{slug}",
                "destination_pattern": "/products/{slug}",
                "priority": "critical"
            },
            {
                "type": "category",
                "source_pattern": "/collections/{slug}",
                "destination_pattern": "/categories/{slug}",
                "priority": "high"
            },
            {
                "type": "page",
                "source_pattern": "/pages/{slug}",
                "destination_pattern": "/pages/{slug}",
                "priority": "medium"
            },
            {
                "type": "blog",
                "source_pattern": "/blogs/{slug}",
                "destination_pattern": "/blog/{slug}",
                "priority": "medium"
            }
        ]
        
        source_platform = migration_config.get('source_platform', '').lower()
        destination_platform = migration_config.get('destination_platform', '').lower()
        
        # Adjust patterns based on platforms
        if source_platform == 'shopify' and destination_platform == 'ideasoft':
            for pattern in page_patterns:
                if pattern['type'] == 'category':
                    pattern['destination_pattern'] = '/kategori/{slug}'
                elif pattern['type'] == 'product':
                    pattern['destination_pattern'] = '/urun/{slug}'
        
        # Create URL mappings
        for pattern in page_patterns:
            mapping = {
                "source_url": pattern["source_pattern"],
                "destination_url": pattern["destination_pattern"],
                "redirect_type": "301",
                "seo_priority": pattern["priority"],
                "page_type": pattern["type"],
                "estimated_traffic": self._estimate_page_traffic(pattern["type"])
            }
            url_mappings.append(mapping)
        
        return url_mappings
    
    async def _create_monitoring_plan(self, seo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create SEO monitoring and recovery plan"""
        
        risk_level = seo_analysis.get('seo_analysis', {}).get('risk_level', 'medium')
        
        # Adjust monitoring based on risk level
        if risk_level == 'critical':
            monitoring_duration = 90
            check_frequency = 'daily'
        elif risk_level == 'high':
            monitoring_duration = 60
            check_frequency = 'every 2 days'
        elif risk_level == 'medium':
            monitoring_duration = 30
            check_frequency = 'weekly'
        else:
            monitoring_duration = 14
            check_frequency = 'weekly'
        
        return {
            "monitoring_duration_days": monitoring_duration,
            "check_frequency": check_frequency,
            "metrics_to_monitor": [
                "organic_traffic",
                "keyword_rankings",
                "indexation_status",
                "crawl_errors",
                "page_load_speed",
                "core_web_vitals"
            ],
            "tools_required": [
                "Google Search Console",
                "Google Analytics",
                "Third-party SEO tools",
                "Server log analysis"
            ],
            "alert_thresholds": {
                "traffic_drop_percentage": 15,
                "ranking_drop_positions": 5,
                "indexation_loss_percentage": 10,
                "crawl_error_increase": 50
            },
            "recovery_procedures": [
                "Verify redirect implementation",
                "Submit updated sitemaps",
                "Request re-indexing for critical pages",
                "Check for technical SEO issues",
                "Monitor competitor activity"
            ]
        }
    
    def _detect_domain_changes(self, migration_config: Dict[str, Any]) -> bool:
        """Detect if domain changes are required during migration"""
        
        source_config = migration_config.get('source_config', {})
        destination_config = migration_config.get('destination_config', {})
        
        source_domain = source_config.get('store_url', '')
        destination_domain = destination_config.get('store_url', '')
        
        if source_domain and destination_domain:
            source_parsed = urlparse(source_domain)
            dest_parsed = urlparse(destination_domain)
            return source_parsed.netloc != dest_parsed.netloc
        
        return False  # Assume no domain change if URLs not provided
    
    def _detect_url_structure_changes(
        self, 
        source_analysis: Dict[str, Any], 
        migration_config: Dict[str, Any]
    ) -> bool:
        """Detect if URL structure changes are likely"""
        
        source_platform = migration_config.get('source_platform', '').lower()
        destination_platform = migration_config.get('destination_platform', '').lower()
        
        # Platform-specific URL structure differences
        platform_url_patterns = {
            'shopify': '/products/, /collections/, /pages/',
            'woocommerce': '/product/, /product-category/, /page/',
            'magento': '/catalog/product/, /catalog/category/',
            'ideasoft': '/urun/, /kategori/, /sayfa/',
            'ikas': '/products/, /categories/, /pages/'
        }
        
        source_pattern = platform_url_patterns.get(source_platform, '')
        dest_pattern = platform_url_patterns.get(destination_platform, '')
        
        return source_pattern != dest_pattern
    
    def _calculate_traffic_risk(self, total_products: int, seo_optimization: str) -> Dict[str, Any]:
        """Calculate potential traffic impact risk"""
        
        # Base risk calculation
        if total_products > 5000:
            base_risk = "high"
        elif total_products > 1000:
            base_risk = "medium"
        else:
            base_risk = "low"
        
        # Adjust based on current SEO optimization
        optimization_multiplier = {
            'poor': 1.5,
            'fair': 1.2,
            'good': 1.0,
            'excellent': 0.8
        }
        
        multiplier = optimization_multiplier.get(seo_optimization, 1.0)
        
        # Calculate estimated impact
        if base_risk == "high" and multiplier > 1.2:
            impact_level = "critical"
            estimated_traffic_loss = "15-30%"
        elif base_risk == "high" or multiplier > 1.2:
            impact_level = "high"
            estimated_traffic_loss = "10-20%"
        elif base_risk == "medium" or multiplier > 1.0:
            impact_level = "medium"
            estimated_traffic_loss = "5-15%"
        else:
            impact_level = "low"
            estimated_traffic_loss = "0-10%"
        
        return {
            "risk_level": impact_level,
            "estimated_traffic_loss": estimated_traffic_loss,
            "affected_products": total_products,
            "current_optimization": seo_optimization,
            "recovery_timeline": "2-8 weeks"
        }
    
    def _analyze_page_types(self, source_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different page types and their SEO importance"""
        
        product_analysis = source_analysis.get('product_analysis', {})
        
        return {
            "product_pages": {
                "count": product_analysis.get('total_products', 0),
                "seo_priority": "critical",
                "migration_complexity": "medium"
            },
            "category_pages": {
                "count": product_analysis.get('product_categories', 0),
                "seo_priority": "high",
                "migration_complexity": "medium"
            },
            "content_pages": {
                "count": 10,  # Estimated
                "seo_priority": "medium",
                "migration_complexity": "low"
            },
            "blog_pages": {
                "count": 5,  # Estimated
                "seo_priority": "medium",
                "migration_complexity": "low"
            }
        }
    
    def _estimate_page_traffic(self, page_type: str) -> str:
        """Estimate traffic distribution by page type"""
        
        traffic_estimates = {
            "product": "40-60% of organic traffic",
            "category": "20-30% of organic traffic",
            "page": "5-15% of organic traffic",
            "blog": "5-20% of organic traffic",
            "home": "10-20% of organic traffic"
        }
        
        return traffic_estimates.get(page_type, "Unknown")
    
    def _create_fallback_seo_analysis(self, migration_config: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create fallback SEO analysis when AI analysis fails"""
        
        return {
            "seo_analysis": {
                "current_seo_score": 5.0,
                "risk_level": "medium",
                "critical_pages_count": 100,
                "indexed_pages_estimated": 500,
                "backlinks_estimated": 50,
                "fallback_reason": error
            },
            "url_structure_analysis": {
                "current_url_pattern": "Standard e-commerce structure",
                "destination_url_pattern": "Standard e-commerce structure",
                "url_changes_required": True,
                "seo_friendly_urls": True,
                "canonical_issues": []
            },
            "critical_elements": {
                "meta_titles": {
                    "count": 100,
                    "optimization_level": "fair",
                    "migration_complexity": "medium"
                },
                "meta_descriptions": {
                    "count": 80,
                    "optimization_level": "fair",
                    "migration_complexity": "medium"
                },
                "heading_structure": {
                    "h1_tags": 100,
                    "structure_quality": "good",
                    "migration_complexity": "low"
                },
                "structured_data": {
                    "schemas_present": ["Product", "Organization"],
                    "schema_compliance": "fair",
                    "migration_complexity": "medium"
                }
            },
            "migration_risks": [
                {
                    "risk_type": "rankings",
                    "risk_description": "Potential temporary ranking fluctuations",
                    "probability": "medium",
                    "impact_severity": "medium",
                    "affected_pages": 100,
                    "mitigation_strategy": "Implement proper redirects and monitoring",
                    "timeline_impact": "short-term"
                }
            ],
            "preservation_plan": {
                "pre_migration_tasks": [
                    "Export current SEO data",
                    "Create redirect mapping",
                    "Set up monitoring tools"
                ],
                "during_migration_tasks": [
                    "Implement redirects",
                    "Verify metadata migration",
                    "Monitor crawl errors"
                ],
                "post_migration_tasks": [
                    "Submit updated sitemaps",
                    "Monitor rankings and traffic",
                    "Fix any identified issues"
                ],
                "monitoring_duration_days": 30,
                "recovery_procedures": [
                    "Check redirect implementation",
                    "Verify sitemap submission",
                    "Monitor search console for errors"
                ]
            },
            "success_metrics": [
                {
                    "metric_name": "Organic traffic retention",
                    "baseline_value": "100%",
                    "target_value": "95%+",
                    "measurement_frequency": "weekly",
                    "alert_threshold": "85%"
                }
            ]
        }