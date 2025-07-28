"""
Context Enrichment Module

This module automatically fetches and enriches missing context data
from various sources to improve workflow quality.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
from urllib.parse import urlparse, quote

from agents import llm
from cache import cache_result
from logging_config import log_info, log_warning, log_debug, log_error
from config_system import config_system

logger = logging.getLogger(__name__)


class ContextEnricher:
    """Intelligent context enrichment for workflow inputs"""
    
    def __init__(self):
        # Load enrichment configuration
        enrichment_config = config_system.get("enrichment", {})
        
        self.enable_auto_enrichment = enrichment_config.get("enable_auto_enrichment", True)
        self.enrichment_timeout = enrichment_config.get("timeout", 30)
        self.max_retries = enrichment_config.get("max_retries", 2)
        
        # Industry detection patterns
        self.industry_patterns = {
            'technology': [
                r'\b(software|saas|platform|api|cloud|ai|ml|tech|digital|data|cyber)\b',
                r'\b(developer|engineer|architect|devops|fullstack)\b'
            ],
            'finance': [
                r'\b(finance|fintech|banking|investment|capital|fund|trading|wealth)\b',
                r'\b(cfo|analyst|advisor|portfolio|equity)\b'
            ],
            'healthcare': [
                r'\b(health|medical|biotech|pharma|clinical|patient|care|wellness)\b',
                r'\b(doctor|physician|nurse|therapist|researcher)\b'
            ],
            'education': [
                r'\b(education|edtech|learning|training|academic|university|school)\b',
                r'\b(teacher|professor|instructor|educator|dean)\b'
            ],
            'marketing': [
                r'\b(marketing|advertising|brand|content|social|digital|growth)\b',
                r'\b(cmo|marketer|copywriter|strategist)\b'
            ],
            'sales': [
                r'\b(sales|revenue|business development|account|customer success)\b',
                r'\b(sales rep|account executive|bdr|sdr)\b'
            ]
        }
        
        # Company size indicators
        self.company_size_patterns = {
            'startup': [r'\b(startup|early stage|seed|series [a-c])\b', r'\b(1-50|small team)\b'],
            'mid-market': [r'\b(mid-market|growing|scale|series [d-f])\b', r'\b(50-500|medium)\b'],
            'enterprise': [r'\b(enterprise|fortune|global|multinational)\b', r'\b(500\+|large)\b']
        }
        
        # Common talking points by industry
        self.industry_talking_points = {
            'technology': [
                'digital transformation initiatives',
                'scalability challenges',
                'technical debt management',
                'innovation roadmap',
                'API integration capabilities'
            ],
            'finance': [
                'regulatory compliance',
                'risk management strategies',
                'ROI optimization',
                'financial automation',
                'data security concerns'
            ],
            'healthcare': [
                'patient outcome improvement',
                'HIPAA compliance',
                'clinical efficiency',
                'telemedicine adoption',
                'healthcare costs reduction'
            ],
            'sales': [
                'pipeline acceleration',
                'conversion rate optimization',
                'sales enablement tools',
                'quota attainment',
                'customer acquisition costs'
            ]
        }
    
    @cache_result(key_prefix="company_extract", ttl=86400)
    def extract_company_from_profile(self, profile_url: str) -> Optional[str]:
        """Extract company name from LinkedIn profile URL"""
        try:
            # Use LLM to intelligently extract company info
            prompt = f"""Given this LinkedIn profile URL: {profile_url}
            
            Extract the company name from the URL path or make an intelligent guess based on common patterns.
            For example:
            - /in/john-doe-acme-corp/ might indicate "Acme Corp"
            - /in/sarah-tech-founder/ might indicate she's a founder at a tech company
            
            Return ONLY the company name or 'Unknown' if you cannot determine it.
            """
            
            response = llm.invoke(prompt)
            company = response.content.strip()
            
            if company and company.lower() != 'unknown':
                log_info(logger, f"Extracted company '{company}' from profile URL")
                return company
                
        except Exception as e:
            log_warning(logger, f"Failed to extract company from profile: {e}")
        
        return None
    
    @cache_result(key_prefix="industry_detect", ttl=86400)
    def detect_industry(self, company_name: str = None, profile_data: str = None, 
                       conversation: str = None) -> Tuple[str, float]:
        """Detect industry from available data with confidence score"""
        combined_text = ' '.join(filter(None, [company_name, profile_data, conversation])).lower()
        
        if not combined_text:
            return 'general', 0.0
        
        industry_scores = {}
        
        # Check patterns
        for industry, patterns in self.industry_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            # Get industry with highest score
            best_industry = max(industry_scores, key=industry_scores.get)
            max_score = industry_scores[best_industry]
            confidence = min(max_score / 10.0, 1.0)  # Normalize confidence
            
            log_info(logger, f"Detected industry: {best_industry} (confidence: {confidence:.2f})")
            return best_industry, confidence
        
        return 'general', 0.0
    
    def detect_company_size(self, company_data: str) -> str:
        """Detect company size from available data"""
        if not company_data:
            return 'unknown'
        
        company_lower = company_data.lower()
        
        for size, patterns in self.company_size_patterns.items():
            for pattern in patterns:
                if re.search(pattern, company_lower, re.IGNORECASE):
                    return size
        
        return 'unknown'
    
    def generate_talking_points(self, industry: str, company_size: str, 
                              context: str = None) -> List[str]:
        """Generate relevant talking points based on context"""
        points = []
        
        # Add industry-specific points
        if industry in self.industry_talking_points:
            points.extend(self.industry_talking_points[industry][:3])
        
        # Add size-specific points
        if company_size == 'startup':
            points.extend(['rapid growth challenges', 'resource optimization', 'market positioning'])
        elif company_size == 'enterprise':
            points.extend(['enterprise scalability', 'change management', 'digital transformation'])
        
        # Add context-specific points if provided
        if context:
            # Use LLM to generate contextual talking points
            try:
                prompt = f"""Based on this context: {context}
                
                Generate 2-3 specific talking points for a business conversation.
                Focus on pain points, opportunities, or mutual interests.
                
                Return as a simple list, one point per line.
                """
                
                response = llm.invoke(prompt)
                custom_points = [p.strip() for p in response.content.strip().split('\n') if p.strip()]
                points.extend(custom_points[:2])
                
            except Exception as e:
                log_warning(logger, f"Failed to generate custom talking points: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for point in points:
            if point not in seen:
                seen.add(point)
                unique_points.append(point)
        
        return unique_points[:5]  # Return top 5 points
    
    def suggest_message_context(self, industry: str, role: str = None, 
                               company_size: str = None) -> str:
        """Suggest message context based on enriched data"""
        contexts = {
            'technology': {
                'startup': 'Helping fast-growing tech startups scale their infrastructure efficiently',
                'enterprise': 'Enabling digital transformation for enterprise technology leaders',
                'default': 'Accelerating technology innovation and operational excellence'
            },
            'finance': {
                'startup': 'Empowering fintech innovators with scalable solutions',
                'enterprise': 'Optimizing financial operations for enterprise organizations',
                'default': 'Driving financial efficiency and compliance'
            },
            'healthcare': {
                'default': 'Improving patient outcomes through innovative healthcare solutions'
            },
            'sales': {
                'default': 'Accelerating sales performance and revenue growth'
            }
        }
        
        # Get industry-specific context
        industry_contexts = contexts.get(industry, contexts.get('general', {}))
        
        # Get size-specific or default
        if company_size and company_size in industry_contexts:
            return industry_contexts[company_size]
        
        return industry_contexts.get('default', 
            'Helping organizations achieve their business objectives through innovative solutions')
    
    @cache_result(key_prefix="enrich_context", ttl=3600)
    async def enrich_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich workflow inputs with additional context"""
        enriched = inputs.copy()
        enrichments = {}
        
        try:
            # 1. Extract company from profile if not provided
            if not inputs.get('prospect_company_url') and inputs.get('prospect_profile_url'):
                company = self.extract_company_from_profile(inputs['prospect_profile_url'])
                if company:
                    enrichments['detected_company'] = company
            
            # 2. Detect industry
            industry, confidence = self.detect_industry(
                company_name=enrichments.get('detected_company'),
                conversation=inputs.get('conversation_thread')
            )
            
            if confidence > 0.3:  # Only use if confident
                enrichments['detected_industry'] = industry
                enrichments['industry_confidence'] = confidence
            
            # 3. Detect company size if possible
            company_size = 'unknown'
            if inputs.get('prospect_company_url') or enrichments.get('detected_company'):
                # In a real implementation, this would fetch data from the URL
                company_size = self.detect_company_size(
                    inputs.get('prospect_company_url', '') + ' ' + 
                    enrichments.get('detected_company', '')
                )
            enrichments['company_size'] = company_size
            
            # 4. Generate talking points
            talking_points = self.generate_talking_points(
                industry=enrichments.get('detected_industry', 'general'),
                company_size=company_size,
                context=inputs.get('message_context')
            )
            
            if talking_points:
                enrichments['suggested_talking_points'] = talking_points
            
            # 5. Suggest message context if not provided
            if not inputs.get('message_context'):
                suggested_context = self.suggest_message_context(
                    industry=enrichments.get('detected_industry', 'general'),
                    company_size=company_size
                )
                enrichments['suggested_message_context'] = suggested_context
            
            # 6. Extract key topics from conversation
            if inputs.get('conversation_thread'):
                topics = self.extract_conversation_topics(inputs['conversation_thread'])
                if topics:
                    enrichments['conversation_topics'] = topics
            
            # 7. Suggest optimal timing
            enrichments['suggested_timing'] = self.suggest_optimal_timing(
                industry=enrichments.get('detected_industry', 'general'),
                channel=inputs.get('channel', 'linkedin')
            )
            
            # Add enrichments to result
            enriched['enrichments'] = enrichments
            
            log_info(logger, f"Context enriched with {len(enrichments)} additional fields")
            
        except Exception as e:
            log_error(logger, f"Error during context enrichment: {e}")
            enriched['enrichment_error'] = str(e)
        
        return enriched
    
    def extract_conversation_topics(self, conversation: str) -> List[str]:
        """Extract key topics from conversation"""
        # Common business topics to look for
        topic_keywords = {
            'growth': ['growth', 'scale', 'expand', 'increase'],
            'efficiency': ['efficient', 'optimize', 'streamline', 'automate'],
            'innovation': ['innovate', 'transform', 'disrupt', 'cutting-edge'],
            'challenges': ['challenge', 'struggle', 'issue', 'problem'],
            'success': ['success', 'achieve', 'accomplish', 'win']
        }
        
        found_topics = []
        conversation_lower = conversation.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in conversation_lower for keyword in keywords):
                found_topics.append(topic)
        
        return found_topics
    
    def suggest_optimal_timing(self, industry: str, channel: str) -> Dict[str, Any]:
        """Suggest optimal timing for outreach"""
        # Industry-specific optimal times (simplified)
        timing_suggestions = {
            'technology': {
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'best_hours': '10AM-12PM, 2PM-4PM',
                'avoid': 'Monday mornings, Friday afternoons'
            },
            'finance': {
                'best_days': ['Tuesday', 'Wednesday'],
                'best_hours': '9AM-11AM, 2PM-3PM',
                'avoid': 'Market open/close times'
            },
            'general': {
                'best_days': ['Tuesday', 'Wednesday', 'Thursday'],
                'best_hours': '10AM-11AM, 2PM-3PM',
                'avoid': 'Monday mornings, Friday afternoons'
            }
        }
        
        timing = timing_suggestions.get(industry, timing_suggestions['general'])
        
        # Adjust for channel
        if channel == 'email':
            timing['response_time'] = 'Typically within 24-48 hours'
        else:  # LinkedIn
            timing['response_time'] = 'Typically within 2-5 days'
        
        return timing


# Create singleton instance
context_enricher = ContextEnricher()


async def enrich_workflow_context(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main enrichment function for workflow inputs
    
    Args:
        inputs: Dictionary of workflow inputs
    
    Returns:
        Enriched inputs with additional context
    """
    if not context_enricher.enable_auto_enrichment:
        return inputs
    
    return await context_enricher.enrich_context(inputs)