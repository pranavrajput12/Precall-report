"""
Input Validation Module with Intelligent Rules and Suggestions

This module provides comprehensive validation for workflow inputs with
intelligent suggestions and auto-correction capabilities.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse
from datetime import datetime

from logging_config import log_info, log_warning, log_debug
from config_system import config_system

logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        self.suggestions: List[Dict[str, str]] = []
        self.auto_corrections: Dict[str, Any] = {}
    
    def add_error(self, field: str, message: str, suggestion: str = None):
        """Add validation error"""
        self.is_valid = False
        error = {"field": field, "message": message}
        if suggestion:
            error["suggestion"] = suggestion
        self.errors.append(error)
    
    def add_warning(self, field: str, message: str, suggestion: str = None):
        """Add validation warning"""
        warning = {"field": field, "message": message}
        if suggestion:
            warning["suggestion"] = suggestion
        self.warnings.append(warning)
    
    def add_suggestion(self, field: str, message: str, value: Any = None):
        """Add improvement suggestion"""
        suggestion = {"field": field, "message": message}
        if value:
            suggestion["suggested_value"] = value
        self.suggestions.append(suggestion)
    
    def add_auto_correction(self, field: str, corrected_value: Any):
        """Add auto-corrected value"""
        self.auto_corrections[field] = corrected_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "auto_corrections": self.auto_corrections
        }


class InputValidator:
    """Intelligent input validation with suggestions and auto-correction"""
    
    def __init__(self):
        # Load validation rules from config
        validation_config = config_system.get("validation", {})
        
        # URL validation patterns
        self.linkedin_profile_pattern = re.compile(
            r'^https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?$',
            re.IGNORECASE
        )
        self.linkedin_company_pattern = re.compile(
            r'^https?://(?:www\.)?linkedin\.com/company/[\w\-]+/?$',
            re.IGNORECASE
        )
        self.url_pattern = re.compile(
            r'^https?://(?:www\.)?[\w\-]+(\.[\w\-]+)+[^\s]*$',
            re.IGNORECASE
        )
        
        # Content quality thresholds
        self.min_thread_length = validation_config.get("min_thread_length", 20)
        self.max_thread_length = validation_config.get("max_thread_length", 10000)
        self.min_context_length = validation_config.get("min_context_length", 10)
        
        # Common company domain patterns
        self.common_tlds = {'.com', '.org', '.net', '.io', '.ai', '.co', '.dev'}
        
        # Industry keywords for context enrichment
        self.industry_keywords = {
            'tech': ['software', 'saas', 'platform', 'api', 'cloud', 'ai', 'ml'],
            'finance': ['fintech', 'banking', 'investment', 'capital', 'fund'],
            'healthcare': ['health', 'medical', 'biotech', 'pharma', 'clinical'],
            'retail': ['ecommerce', 'retail', 'shopping', 'marketplace'],
            'education': ['edtech', 'learning', 'education', 'training']
        }
    
    def validate_linkedin_url(self, url: str, url_type: str = "profile") -> Tuple[bool, str]:
        """Validate and normalize LinkedIn URL"""
        if not url:
            return False, f"{url_type} URL is required"
        
        # Auto-fix common issues
        url = url.strip()
        
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Remove trailing slashes and parameters
        url = url.split('?')[0].rstrip('/')
        
        # Check pattern
        pattern = self.linkedin_profile_pattern if url_type == "profile" else self.linkedin_company_pattern
        if pattern.match(url):
            return True, url
        
        # Try to fix common mistakes
        if 'linkedin.com' in url:
            # Extract the relevant part
            parts = url.split('/')
            if url_type == "profile" and '/in/' in url:
                idx = parts.index('in')
                if idx < len(parts) - 1:
                    username = parts[idx + 1]
                    fixed_url = f"https://www.linkedin.com/in/{username}"
                    return True, fixed_url
            elif url_type == "company" and '/company/' in url:
                idx = parts.index('company')
                if idx < len(parts) - 1:
                    company = parts[idx + 1]
                    fixed_url = f"https://www.linkedin.com/company/{company}"
                    return True, fixed_url
        
        return False, f"Invalid LinkedIn {url_type} URL format"
    
    def validate_website_url(self, url: str) -> Tuple[bool, str]:
        """Validate and normalize website URL"""
        if not url:
            return True, ""  # Website is optional
        
        url = url.strip()
        
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        if self.url_pattern.match(url):
            return True, url
        
        # Try to fix common issues
        if '.' in url and not url.startswith('http'):
            # Might be just domain
            fixed_url = f"https://{url}"
            if self.url_pattern.match(fixed_url):
                return True, fixed_url
        
        return False, "Invalid website URL format"
    
    def suggest_company_website(self, company_name: str, company_linkedin: str) -> Optional[str]:
        """Suggest company website based on name or LinkedIn"""
        if not company_name and company_linkedin:
            # Extract company name from LinkedIn URL
            match = self.linkedin_company_pattern.match(company_linkedin)
            if match:
                parts = company_linkedin.split('/')
                if 'company' in parts:
                    idx = parts.index('company')
                    if idx < len(parts) - 1:
                        company_name = parts[idx + 1]
        
        if company_name:
            # Clean company name
            clean_name = company_name.lower().replace(' ', '').replace('-', '')
            
            # Try common patterns
            suggestions = [
                f"https://www.{clean_name}.com",
                f"https://{clean_name}.com",
                f"https://www.{clean_name}.io",
                f"https://{clean_name}.ai"
            ]
            
            return suggestions[0]  # Return most likely
        
        return None
    
    def analyze_conversation_thread(self, thread: str) -> Dict[str, Any]:
        """Analyze conversation thread for quality and extract insights"""
        analysis = {
            "length": len(thread),
            "word_count": len(thread.split()),
            "has_greeting": any(greeting in thread.lower() for greeting in ['hi', 'hello', 'hey']),
            "has_question": '?' in thread,
            "detected_topics": [],
            "sentiment": "neutral"
        }
        
        # Detect industry/topics
        thread_lower = thread.lower()
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in thread_lower for keyword in keywords):
                analysis["detected_topics"].append(industry)
        
        # Simple sentiment detection
        positive_words = ['excited', 'interested', 'love', 'great', 'amazing']
        negative_words = ['not interested', 'busy', 'maybe later', 'no thanks']
        
        if any(word in thread_lower for word in positive_words):
            analysis["sentiment"] = "positive"
        elif any(word in thread_lower for word in negative_words):
            analysis["sentiment"] = "negative"
        
        return analysis
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResult:
        """Comprehensive input validation with intelligent suggestions"""
        result = ValidationResult()
        
        # 1. Validate conversation thread
        thread = inputs.get('conversation_thread', '').strip()
        if not thread:
            result.add_error(
                'conversation_thread',
                'Conversation thread is required',
                'Provide the conversation history or initial message'
            )
        else:
            thread_analysis = self.analyze_conversation_thread(thread)
            
            if thread_analysis['length'] < self.min_thread_length:
                result.add_warning(
                    'conversation_thread',
                    f'Thread is very short ({thread_analysis["length"]} chars)',
                    'Consider providing more context for better personalization'
                )
            elif thread_analysis['length'] > self.max_thread_length:
                result.add_warning(
                    'conversation_thread',
                    f'Thread is very long ({thread_analysis["length"]} chars)',
                    'Consider summarizing to key points'
                )
            
            # Add insights as suggestions
            if thread_analysis['detected_topics']:
                result.add_suggestion(
                    'message_context',
                    f"Detected topics: {', '.join(thread_analysis['detected_topics'])}. Consider adding this context."
                )
        
        # 2. Validate channel
        channel = inputs.get('channel', '').strip().lower()
        if channel not in ['linkedin', 'email']:
            result.add_error(
                'channel',
                f'Invalid channel: {channel}',
                'Use "linkedin" or "email"'
            )
            # Auto-correct common mistakes
            if channel in ['linked in', 'li']:
                result.add_auto_correction('channel', 'linkedin')
            elif channel in ['mail', 'e-mail']:
                result.add_auto_correction('channel', 'email')
        
        # 3. Validate LinkedIn URLs
        profile_url = inputs.get('prospect_profile_url', '')
        is_valid, corrected_url = self.validate_linkedin_url(profile_url, 'profile')
        if not is_valid:
            result.add_error('prospect_profile_url', corrected_url)
        elif corrected_url != profile_url:
            result.add_auto_correction('prospect_profile_url', corrected_url)
        
        company_url = inputs.get('prospect_company_url', '')
        is_valid, corrected_url = self.validate_linkedin_url(company_url, 'company')
        if not is_valid:
            result.add_error('prospect_company_url', corrected_url)
        elif corrected_url != company_url:
            result.add_auto_correction('prospect_company_url', corrected_url)
        
        # 4. Validate website URL
        website_url = inputs.get('prospect_company_website', '')
        is_valid, corrected_url = self.validate_website_url(website_url)
        if not is_valid:
            result.add_error('prospect_company_website', corrected_url)
        elif corrected_url != website_url:
            result.add_auto_correction('prospect_company_website', corrected_url)
        
        # Suggest website if missing
        if not website_url and company_url:
            suggested_website = self.suggest_company_website('', company_url)
            if suggested_website:
                result.add_suggestion(
                    'prospect_company_website',
                    'Consider adding company website for better context',
                    suggested_website
                )
        
        # 5. Validate context fields
        message_context = inputs.get('message_context', '').strip()
        if not message_context:
            result.add_warning(
                'message_context',
                'No message context provided',
                'Add context about your outreach goal for better personalization'
            )
        elif len(message_context) < self.min_context_length:
            result.add_warning(
                'message_context',
                'Message context is very brief',
                'Provide more details about your value proposition'
            )
        
        your_company = inputs.get('your_company', '').strip()
        if not your_company:
            result.add_error(
                'your_company',
                'Your company name is required',
                'Provide your company name for proper introduction'
            )
        
        your_role = inputs.get('your_role', '').strip()
        if not your_role:
            result.add_error(
                'your_role',
                'Your role/title is required',
                'Provide your role for credibility'
            )
        
        # 6. Cross-field validation
        if channel == 'linkedin' and not profile_url:
            result.add_error(
                'prospect_profile_url',
                'LinkedIn profile URL is required for LinkedIn channel'
            )
        
        # 7. Add quality score
        quality_score = 100
        quality_score -= len(result.errors) * 20
        quality_score -= len(result.warnings) * 5
        
        if quality_score < 50:
            result.add_warning(
                'overall',
                f'Input quality score: {quality_score}/100',
                'Address errors and warnings for better results'
            )
        
        log_info(logger, f"Validation complete: {len(result.errors)} errors, {len(result.warnings)} warnings")
        
        return result


# Create singleton instance
input_validator = InputValidator()


def validate_workflow_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main validation function for workflow inputs
    
    Args:
        inputs: Dictionary of workflow inputs
    
    Returns:
        Validation result dictionary
    """
    result = input_validator.validate_inputs(inputs)
    return result.to_dict()