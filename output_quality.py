"""
Output Quality Assessment and Scoring Module

This module provides comprehensive quality scoring and confidence metrics for
CrewAI workflow outputs, enabling better decision-making and continuous improvement.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class OutputQualityAssessor:
    """Comprehensive quality assessment for workflow outputs"""

    def __init__(self):
        self.quality_thresholds = {
            "excellent": 0.85,
            "good": 0.70,
            "acceptable": 0.55,
            "poor": 0.40,
        }

    def assess_profile_quality(self, profile_summary: str) -> Dict[str, Any]:
        """Assess the quality of profile enrichment output"""
        if not profile_summary or len(profile_summary.strip()) < 100:
            return {
                "quality_score": 0.0,
                "quality_level": "poor",
                "issues": ["Profile summary too short or empty"],
                "strengths": [],
                "recommendations": ["Gather more comprehensive profile data"],
            }

        score = 0.0
        issues = []
        strengths = []

        # Content depth assessment
        sections = [
            "PROSPECT INTELLIGENCE",
            "COMPANY INTELLIGENCE",
            "STRATEGIC INSIGHTS",
            "PERSONALIZATION OPPORTUNITIES",
            "RISK ASSESSMENT",
        ]
        sections_found = sum(
            1 for section in sections if section in profile_summary)

        if sections_found >= 4:
            score += 0.25
            strengths.append("Comprehensive section coverage")
        elif sections_found >= 2:
            score += 0.15
        else:
            issues.append("Missing key analysis sections")

        # Specific details assessment
        detail_indicators = [
            r"linkedin\.com/in/",  # LinkedIn profile
            r"linkedin\.com/company/",  # Company LinkedIn
            r"\$\d+[MK]",  # Funding amounts
            r"\d{4}",  # Years/dates
            r"[A-Z][a-z]+ [A-Z][a-z]+",  # Names
            r"CEO|CTO|VP|Director|Manager",  # Titles
        ]

        details_found = sum(
            1 for pattern in detail_indicators if re.search(
                pattern, profile_summary))

        if details_found >= 4:
            score += 0.25
            strengths.append("Rich specific details")
        elif details_found >= 2:
            score += 0.15
        else:
            issues.append("Lacks specific details and personalization data")

        # Actionability assessment
        actionable_keywords = [
            "opportunity",
            "challenge",
            "pain point",
            "growth",
            "expansion",
            "funding",
            "hiring",
            "technology",
            "competitive",
            "market",
        ]

        actionable_found = sum(
            1
            for keyword in actionable_keywords
            if keyword.lower() in profile_summary.lower()
        )

        if actionable_found >= 5:
            score += 0.25
            strengths.append("Highly actionable insights")
        elif actionable_found >= 3:
            score += 0.15
        else:
            issues.append("Limited actionable insights")

        # Structure and readability
        if "##" in profile_summary and len(profile_summary.split("\n")) > 10:
            score += 0.25
            strengths.append("Well-structured and readable")
        else:
            issues.append("Poor structure or formatting")

        quality_level = self._get_quality_level(score)

        return {
            "quality_score": round(
                score,
                2),
            "quality_level": quality_level,
            "issues": issues,
            "strengths": strengths,
            "recommendations": self._get_profile_recommendations(
                score,
                issues),
        }

    def assess_thread_analysis_quality(
            self, thread_analysis: str) -> Dict[str, Any]:
        """Assess the quality of thread analysis output"""
        if not thread_analysis:
            return {
                "quality_score": 0.0,
                "quality_level": "poor",
                "issues": ["Thread analysis is empty"],
                "strengths": [],
                "recommendations": ["Ensure thread analysis is properly generated"],
            }

        score = 0.0
        issues = []
        strengths = []

        # JSON structure assessment
        try:
            parsed = json.loads(thread_analysis)
            score += 0.2
            strengths.append("Valid JSON structure")
        except Exception:
            issues.append("Invalid JSON format")
            return {
                "quality_score": 0.0,
                "quality_level": "poor",
                "issues": issues,
                "strengths": strengths,
                "recommendations": ["Fix JSON formatting issues"],
            }

        # Required sections assessment
        required_sections = [
            "conversation_overview",
            "qualification_analysis",
            "conversation_intelligence",
            "strategic_insights",
            "personalization_data",
            "follow_up_strategy",
        ]

        sections_present = sum(
            1 for section in required_sections if section in parsed)

        if sections_present >= 5:
            score += 0.25
            strengths.append("Comprehensive analysis sections")
        elif sections_present >= 3:
            score += 0.15
        else:
            issues.append("Missing critical analysis sections")

        # Data richness assessment
        qualification = parsed.get("qualification_analysis", {})
        if qualification.get("buying_signals") and qualification.get(
            "pain_points_mentioned"
        ):
            score += 0.2
            strengths.append("Rich qualification insights")
        else:
            issues.append("Limited qualification intelligence")

        # Strategic insights assessment
        strategic = parsed.get("strategic_insights", {})
        if (
            strategic.get("next_best_actions")
            and strategic.get("key_talking_points")
            and strategic.get("value_propositions")
        ):
            score += 0.2
            strengths.append("Actionable strategic insights")
        else:
            issues.append("Weak strategic recommendations")

        # Personalization data assessment
        personalization = parsed.get("personalization_data", {})
        if personalization.get("explicit_questions") and personalization.get(
            "professional_priorities"
        ):
            score += 0.15
            strengths.append("Strong personalization data")
        else:
            issues.append("Limited personalization opportunities")

        quality_level = self._get_quality_level(score)

        return {
            "quality_score": round(score, 2),
            "quality_level": quality_level,
            "issues": issues,
            "strengths": strengths,
            "recommendations": self._get_thread_recommendations(score, issues),
        }

    def assess_reply_quality(
        self, reply: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality of generated reply"""
        if not reply or len(reply.strip()) < 50:
            return {
                "quality_score": 0.0,
                "quality_level": "poor",
                "issues": ["Reply too short or empty"],
                "strengths": [],
                "recommendations": ["Generate more comprehensive response"],
            }

        score = 0.0
        issues = []
        strengths = []

        # Structure assessment
        if "##" in reply and "IMMEDIATE RESPONSE" in reply:
            score += 0.2
            strengths.append("Well-structured response strategy")
        else:
            issues.append("Poor structure or missing strategy sections")

        # Personalization assessment
        personalization_indicators = [
            r"[A-Z][a-z]+ [A-Z][a-z]+",  # Names
            r"[A-Z][a-z]+ (Inc|LLC|Corp|Company|Studio)",  # Company names
            r"congratulations|exciting|interesting|impressive",  # Engagement words
            r"your (recent|latest|current)",  # Personal references
        ]

        personalization_found = sum(
            1
            for pattern in personalization_indicators
            if re.search(pattern, reply, re.IGNORECASE)
        )

        if personalization_found >= 3:
            score += 0.25
            strengths.append("Highly personalized content")
        elif personalization_found >= 1:
            score += 0.15
        else:
            issues.append("Lacks personalization")

        # Value proposition assessment
        value_keywords = [
            "efficiency",
            "growth",
            "ROI",
            "results",
            "improvement",
            "solution",
            "benefit",
            "advantage",
            "opportunity",
            "success",
            "impact",
        ]

        value_found = sum(
            1 for keyword in value_keywords if keyword.lower() in reply.lower()
        )

        if value_found >= 4:
            score += 0.2
            strengths.append("Strong value propositions")
        elif value_found >= 2:
            score += 0.1
        else:
            issues.append("Weak value propositions")

        # Call-to-action assessment
        cta_patterns = [
            r"would you be (open|interested|available)",
            r"shall we schedule",
            r"let's discuss",
            r"I'd love to (share|show|discuss)",
            r"would you like to (see|learn|explore)",
        ]

        cta_found = any(re.search(pattern, reply, re.IGNORECASE)
                        for pattern in cta_patterns)

        if cta_found:
            score += 0.15
            strengths.append("Clear call-to-action")
        else:
            issues.append("Missing or weak call-to-action")

        # Follow-up sequence assessment
        if "FOLLOW-UP" in reply and "Follow-up" in reply:
            score += 0.2
            strengths.append("Comprehensive follow-up strategy")
        else:
            issues.append("Missing follow-up sequence")

        quality_level = self._get_quality_level(score)

        return {
            "quality_score": round(score, 2),
            "quality_level": quality_level,
            "issues": issues,
            "strengths": strengths,
            "recommendations": self._get_reply_recommendations(score, issues),
        }

    def assess_overall_workflow_quality(
        self, profile_quality: Dict, thread_quality: Dict, reply_quality: Dict
    ) -> Dict[str, Any]:
        """Assess overall workflow output quality"""

        # Weighted average based on importance
        weights = {"profile": 0.3, "thread": 0.4, "reply": 0.3}

        overall_score = (
            profile_quality["quality_score"] * weights["profile"]
            + thread_quality["quality_score"] * weights["thread"]
            + reply_quality["quality_score"] * weights["reply"]
        )

        all_issues = (
            profile_quality["issues"]
            + thread_quality["issues"]
            + reply_quality["issues"]
        )

        all_strengths = (
            profile_quality["strengths"]
            + thread_quality["strengths"]
            + reply_quality["strengths"]
        )

        quality_level = self._get_quality_level(overall_score)

        # Confidence assessment
        confidence_score = self._calculate_confidence(
            overall_score, all_issues)

        return {
            "overall_quality_score": round(overall_score, 2),
            "quality_level": quality_level,
            "confidence_score": round(confidence_score, 2),
            "component_scores": {
                "profile_enrichment": profile_quality["quality_score"],
                "thread_analysis": thread_quality["quality_score"],
                "reply_generation": reply_quality["quality_score"],
            },
            "critical_issues": [
                issue
                for issue in all_issues
                if any(
                    word in issue.lower()
                    for word in ["empty", "missing", "invalid", "poor"]
                )
            ],
            "key_strengths": list(set(all_strengths)),
            "recommendations": self._get_overall_recommendations(
                overall_score, all_issues
            ),
            "escalation_required": overall_score < 0.4 or confidence_score < 0.5,
        }

    def _get_quality_level(self, score: float) -> str:
        """Convert numeric score to quality level"""
        if score >= self.quality_thresholds["excellent"]:
            return "excellent"
        elif score >= self.quality_thresholds["good"]:
            return "good"
        elif score >= self.quality_thresholds["acceptable"]:
            return "acceptable"
        else:
            return "poor"

    def _calculate_confidence(self, score: float, issues: List[str]) -> float:
        """Calculate confidence score based on quality and issues"""
        base_confidence = score

        # Reduce confidence for critical issues
        critical_issues = sum(
            1
            for issue in issues
            if any(
                word in issue.lower()
                for word in ["empty", "missing", "invalid", "error"]
            )
        )

        confidence_penalty = critical_issues * 0.1

        return max(0.0, base_confidence - confidence_penalty)

    def _get_profile_recommendations(
        self, score: float, issues: List[str]
    ) -> List[str]:
        """Get specific recommendations for profile improvement"""
        recommendations = []

        if score < 0.4:
            recommendations.append(
                "Enhance data collection from LinkedIn and company sources"
            )
            recommendations.append(
                "Implement more comprehensive profile analysis")

        if "Missing key analysis sections" in issues:
            recommendations.append(
                "Ensure all required sections are included in profile analysis"
            )

        if "Lacks specific details" in issues:
            recommendations.append(
                "Extract more specific details like names, titles, and dates"
            )

        return recommendations

    def _get_thread_recommendations(
            self,
            score: float,
            issues: List[str]) -> List[str]:
        """Get specific recommendations for thread analysis improvement"""
        recommendations = []

        if score < 0.4:
            recommendations.append(
                "Improve conversation parsing and analysis depth")

        if "Invalid JSON format" in issues:
            recommendations.append(
                "Fix JSON formatting in thread analysis output")

        if "Limited qualification intelligence" in issues:
            recommendations.append(
                "Enhance qualification and buying signal detection")

        return recommendations

    def _get_reply_recommendations(
            self,
            score: float,
            issues: List[str]) -> List[str]:
        """Get specific recommendations for reply improvement"""
        recommendations = []

        if score < 0.4:
            recommendations.append(
                "Improve reply personalization and value proposition"
            )

        if "Lacks personalization" in issues:
            recommendations.append(
                "Include more specific personal and company references"
            )

        if "Missing or weak call-to-action" in issues:
            recommendations.append("Add clear, compelling call-to-action")

        return recommendations

    def _get_overall_recommendations(
        self, score: float, issues: List[str]
    ) -> List[str]:
        """Get overall workflow improvement recommendations"""
        recommendations = []

        if score < 0.4:
            recommendations.append("Consider escalating to human review")
            recommendations.append("Implement additional quality checks")

        if len(issues) > 5:
            recommendations.append(
                "Address multiple quality issues before sending")

        recommendations.append("Monitor response rates and engagement metrics")

        return recommendations


# Global instance
quality_assessor = OutputQualityAssessor()


def assess_workflow_output_quality(
    profile_summary: str, thread_analysis: str, reply: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Comprehensive quality assessment for complete workflow output

    Args:
        profile_summary: Profile enrichment output
        thread_analysis: Thread analysis output
        reply: Generated reply
        context: Workflow context

    Returns:
        Dictionary with quality scores, issues, and recommendations
    """

    # Assess individual components
    profile_quality = quality_assessor.assess_profile_quality(profile_summary)
    thread_quality = quality_assessor.assess_thread_analysis_quality(
        thread_analysis)
    reply_quality = quality_assessor.assess_reply_quality(reply, context)

    # Assess overall quality
    overall_quality = quality_assessor.assess_overall_workflow_quality(
        profile_quality, thread_quality, reply_quality
    )

    # Add timestamp and metadata
    assessment = {
        "timestamp": datetime.now().isoformat(),
        "assessment_version": "1.0",
        "individual_assessments": {
            "profile_enrichment": profile_quality,
            "thread_analysis": thread_quality,
            "reply_generation": reply_quality,
        },
        "overall_assessment": overall_quality,
    }

    return assessment
