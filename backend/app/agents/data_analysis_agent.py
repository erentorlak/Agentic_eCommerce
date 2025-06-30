"""
Data Analysis Agent - Intelligent platform scanning and analysis
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain.chains import LLMChain
import structlog

from app.core.config import get_settings
from app.services.platform_connector import PlatformConnectorService

logger = structlog.get_logger(__name__)
settings = get_settings()


class DataAnalysisOutputParser(BaseOutputParser):
    """Parser for data analysis agent output"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the LLM output into structured data"""
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
                    "analysis_summary": text,
                    "confidence_score": 0.5,
                    "recommendations": []
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM output as JSON", text=text)
            return {
                "analysis_summary": text,
                "confidence_score": 0.3,
                "recommendations": []
            }


class DataAnalysisAgent:
    """
    Intelligent agent for analyzing e-commerce platform data structures
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.platform_connector = PlatformConnectorService()
        self.output_parser = DataAnalysisOutputParser()
        
        # System prompt for data analysis
        self.system_prompt = SystemMessagePromptTemplate.from_template("""
You are an expert e-commerce data analyst specializing in platform migrations. Your role is to analyze 
source platform data structures and provide intelligent insights for migration planning.

Key responsibilities:
1. Analyze product catalog structure and complexity
2. Assess data quality and completeness
3. Identify potential migration challenges
4. Recommend optimization strategies
5. Estimate migration effort and timeline

Always provide structured JSON output with the following format:
{{
    "platform_analysis": {{
        "platform_type": "detected platform",
        "version": "platform version if available",
        "structure_complexity": "low|medium|high",
        "data_quality_score": 0.0-1.0
    }},
    "product_analysis": {{
        "total_products": number,
        "product_categories": number,
        "variants_per_product": number,
        "custom_fields": number,
        "images_per_product": number,
        "seo_optimization_level": "poor|fair|good|excellent"
    }},
    "migration_challenges": [
        {{
            "challenge": "description",
            "severity": "low|medium|high",
            "solution": "recommended approach"
        }}
    ],
    "recommendations": [
        {{
            "category": "data_optimization|structure|seo|performance",
            "recommendation": "specific action",
            "priority": "low|medium|high",
            "estimated_effort": "hours or days"
        }}
    ],
    "confidence_score": 0.0-1.0,
    "analysis_summary": "human-readable summary"
}}

Be thorough but concise. Focus on actionable insights.
        """)
        
        self.human_prompt = HumanMessagePromptTemplate.from_template("""
Analyze the following e-commerce platform data for migration planning:

Source Platform: {platform_type}
Store URL: {store_url}

Product Data Sample:
{product_data}

Customer Data Sample:
{customer_data}

Order Data Sample:
{order_data}

Platform Configuration:
{platform_config}

Please provide a comprehensive analysis focusing on:
1. Data structure complexity and quality
2. Potential migration challenges
3. Optimization recommendations
4. Estimated effort for migration

Consider the destination platform requirements for Ideasoft/Ikas platforms.
        """)
        
        # Create the analysis chain
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=ChatPromptTemplate.from_messages([
                self.system_prompt,
                self.human_prompt
            ]),
            output_parser=self.output_parser
        )
    
    async def analyze_platform(
        self, 
        platform_type: str, 
        store_config: Dict[str, Any],
        migration_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive platform analysis
        
        Args:
            platform_type: Source platform type (shopify, woocommerce, etc.)
            store_config: Platform connection configuration
            migration_options: Optional migration preferences
            
        Returns:
            Comprehensive analysis results
        """
        logger.info(
            "Starting platform analysis",
            platform_type=platform_type,
            store_url=store_config.get('store_url')
        )
        
        try:
            # Connect to source platform
            connector = await self.platform_connector.get_connector(
                platform_type, 
                store_config
            )
            
            # Gather sample data
            analysis_data = await self._gather_analysis_data(connector)
            
            # Perform AI analysis
            ai_analysis = await self._perform_ai_analysis(
                platform_type, 
                store_config, 
                analysis_data
            )
            
            # Add technical analysis
            technical_analysis = await self._perform_technical_analysis(
                analysis_data
            )
            
            # Combine results
            final_analysis = {
                **ai_analysis,
                "technical_analysis": technical_analysis,
                "data_samples": {
                    "products_count": len(analysis_data.get('products', [])),
                    "customers_count": len(analysis_data.get('customers', [])),
                    "orders_count": len(analysis_data.get('orders', []))
                },
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_version": "1.0.0"
            }
            
            logger.info(
                "Platform analysis completed",
                confidence_score=final_analysis.get('confidence_score'),
                challenges_found=len(final_analysis.get('migration_challenges', []))
            )
            
            return final_analysis
            
        except Exception as e:
            logger.error(
                "Platform analysis failed",
                platform_type=platform_type,
                error=str(e),
                exc_info=True
            )
            
            # Return error analysis
            return {
                "error": str(e),
                "platform_analysis": {
                    "platform_type": platform_type,
                    "structure_complexity": "unknown",
                    "data_quality_score": 0.0
                },
                "migration_challenges": [{
                    "challenge": f"Failed to connect to source platform: {str(e)}",
                    "severity": "high",
                    "solution": "Verify API credentials and platform accessibility"
                }],
                "confidence_score": 0.0,
                "analysis_summary": f"Analysis failed due to connection error: {str(e)}"
            }
    
    async def _gather_analysis_data(self, connector) -> Dict[str, Any]:
        """Gather sample data from the platform for analysis"""
        
        # Gather data concurrently for efficiency
        tasks = [
            self._safe_fetch(connector.get_products, limit=50),
            self._safe_fetch(connector.get_customers, limit=20),
            self._safe_fetch(connector.get_orders, limit=20),
            self._safe_fetch(connector.get_categories, limit=20),
            self._safe_fetch(connector.get_platform_info),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "products": results[0] if not isinstance(results[0], Exception) else [],
            "customers": results[1] if not isinstance(results[1], Exception) else [],
            "orders": results[2] if not isinstance(results[2], Exception) else [],
            "categories": results[3] if not isinstance(results[3], Exception) else [],
            "platform_info": results[4] if not isinstance(results[4], Exception) else {},
        }
    
    async def _safe_fetch(self, fetch_func, **kwargs):
        """Safely execute a fetch function with error handling"""
        try:
            return await fetch_func(**kwargs)
        except Exception as e:
            logger.warning(f"Failed to fetch data: {str(e)}")
            return []
    
    async def _perform_ai_analysis(
        self, 
        platform_type: str, 
        store_config: Dict[str, Any], 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform AI-powered analysis of the platform data"""
        
        # Prepare data for LLM analysis
        product_sample = json.dumps(analysis_data.get('products', [])[:3], indent=2)
        customer_sample = json.dumps(analysis_data.get('customers', [])[:2], indent=2)
        order_sample = json.dumps(analysis_data.get('orders', [])[:2], indent=2)
        platform_config = json.dumps(analysis_data.get('platform_info', {}), indent=2)
        
        # Run AI analysis
        result = await self.analysis_chain.arun(
            platform_type=platform_type,
            store_url=store_config.get('store_url', 'Unknown'),
            product_data=product_sample,
            customer_data=customer_sample,
            order_data=order_sample,
            platform_config=platform_config
        )
        
        return result
    
    async def _perform_technical_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis of the data structure"""
        
        products = analysis_data.get('products', [])
        customers = analysis_data.get('customers', [])
        orders = analysis_data.get('orders', [])
        
        # Analyze product complexity
        product_complexity = self._analyze_product_complexity(products)
        
        # Analyze data relationships
        relationship_analysis = self._analyze_data_relationships(products, customers, orders)
        
        # Calculate migration estimates
        migration_estimates = self._calculate_migration_estimates(analysis_data)
        
        return {
            "product_complexity": product_complexity,
            "relationship_analysis": relationship_analysis,
            "migration_estimates": migration_estimates,
            "data_volume_analysis": {
                "products": len(products),
                "customers": len(customers),
                "orders": len(orders),
                "estimated_total_products": self._estimate_total_count(products),
                "estimated_total_customers": self._estimate_total_count(customers),
                "estimated_total_orders": self._estimate_total_count(orders)
            }
        }
    
    def _analyze_product_complexity(self, products: List[Dict]) -> Dict[str, Any]:
        """Analyze complexity of product data structure"""
        if not products:
            return {"complexity_score": 0, "factors": []}
        
        complexity_factors = []
        complexity_score = 0
        
        # Check for variants
        has_variants = any(len(p.get('variants', [])) > 1 for p in products)
        if has_variants:
            complexity_score += 2
            complexity_factors.append("Product variants detected")
        
        # Check for custom fields
        custom_fields = set()
        for product in products:
            for key in product.keys():
                if key not in ['id', 'title', 'description', 'price', 'images', 'variants']:
                    custom_fields.add(key)
        
        if custom_fields:
            complexity_score += len(custom_fields) * 0.5
            complexity_factors.append(f"Custom fields: {', '.join(list(custom_fields)[:5])}")
        
        # Check for multiple images
        avg_images = sum(len(p.get('images', [])) for p in products) / len(products)
        if avg_images > 3:
            complexity_score += 1
            complexity_factors.append(f"Average {avg_images:.1f} images per product")
        
        return {
            "complexity_score": min(complexity_score, 10),
            "factors": complexity_factors,
            "has_variants": has_variants,
            "custom_fields_count": len(custom_fields),
            "average_images_per_product": avg_images
        }
    
    def _analyze_data_relationships(
        self, 
        products: List[Dict], 
        customers: List[Dict], 
        orders: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze relationships between different data types"""
        
        relationships = {
            "product_customer_links": 0,
            "order_dependencies": 0,
            "referential_integrity": "good"
        }
        
        # Analyze order-product relationships
        if orders and products:
            product_ids = {str(p.get('id')) for p in products}
            order_product_refs = 0
            
            for order in orders:
                line_items = order.get('line_items', [])
                for item in line_items:
                    if str(item.get('product_id')) in product_ids:
                        order_product_refs += 1
            
            relationships["order_product_references"] = order_product_refs
        
        return relationships
    
    def _calculate_migration_estimates(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate time and effort estimates for migration"""
        
        products_count = self._estimate_total_count(analysis_data.get('products', []))
        customers_count = self._estimate_total_count(analysis_data.get('customers', []))
        orders_count = self._estimate_total_count(analysis_data.get('orders', []))
        
        # Base processing rates (items per hour)
        base_rates = {
            "products": 500,  # products per hour
            "customers": 1000,  # customers per hour
            "orders": 800  # orders per hour
        }
        
        # Calculate estimated time
        estimated_hours = {
            "products": max(1, products_count / base_rates["products"]),
            "customers": max(0.5, customers_count / base_rates["customers"]),
            "orders": max(0.5, orders_count / base_rates["orders"])
        }
        
        total_hours = sum(estimated_hours.values())
        
        return {
            "estimated_duration_hours": total_hours,
            "estimated_duration_days": max(1, total_hours / 8),
            "breakdown": estimated_hours,
            "recommended_workers": min(4, max(1, int(total_hours / 24))),
            "complexity_multiplier": 1.0  # Could be adjusted based on complexity
        }
    
    def _estimate_total_count(self, sample_data: List[Dict]) -> int:
        """Estimate total count from sample data"""
        if not sample_data:
            return 0
        
        # Simple estimation - assumes sample is representative
        # In real implementation, this would use pagination info from APIs
        sample_size = len(sample_data)
        
        # Estimate based on common e-commerce store sizes
        if sample_size < 10:
            return sample_size * 10  # Small store
        elif sample_size < 50:
            return sample_size * 20  # Medium store
        else:
            return sample_size * 40  # Large store
    
    async def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        
        if analysis_result.get('error'):
            return f"Analysis failed: {analysis_result['error']}"
        
        platform_info = analysis_result.get('platform_analysis', {})
        technical_info = analysis_result.get('technical_analysis', {})
        
        summary_parts = [
            f"Platform: {platform_info.get('platform_type', 'Unknown')}",
            f"Complexity: {platform_info.get('structure_complexity', 'Unknown')}",
            f"Data Quality: {platform_info.get('data_quality_score', 0):.1f}/1.0",
        ]
        
        if technical_info.get('migration_estimates'):
            estimates = technical_info['migration_estimates']
            summary_parts.append(
                f"Estimated Duration: {estimates.get('estimated_duration_days', 0):.1f} days"
            )
        
        challenges = analysis_result.get('migration_challenges', [])
        if challenges:
            high_severity = sum(1 for c in challenges if c.get('severity') == 'high')
            if high_severity:
                summary_parts.append(f"{high_severity} high-priority challenges identified")
        
        return " | ".join(summary_parts)