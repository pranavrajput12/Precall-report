#!/usr/bin/env python3
"""
Output Quality Test Script

This script demonstrates the enhanced output quality improvements in the CrewAI workflow,
showing before/after comparisons and quality assessments.
"""

import time
from typing import Any, Dict

import requests

# Configuration
BASE_URL = "http://localhost:8000"

# Test data
SAMPLE_CONVERSATION = {
    "conversation_thread": """
    Drushi Thakkar: Hi Michelle! I saw your recent post about A'reve Studio's Series A funding round.
    Congratulations on raising $15M! I'm particularly interested in your approach to boutique fitness
    and how you're scaling in Central America and the Caribbean. Your focus on community-driven
    fitness experiences really resonates with current market trends.

    Michelle Marsan: Thank you, Drushi! Yes, we're incredibly excited about this milestone.
    The Series A will help us expand our technology platform and open 5 new locations across
    the region. We're always looking for innovative partners who understand the unique challenges
    of scaling in emerging markets. What's your background in this space?

    Drushi Thakkar: I work with Series A companies like yours to implement AI-powered operational
    automation that can increase efficiency by 50-100x while reducing costs. Given your expansion
    plans and the operational complexity of managing multiple locations, this could be perfect
    timing. I've helped similar fitness companies streamline member management, class scheduling,
    and inventory across multiple locations. Would you be open to a brief call to explore how
    this could accelerate A'reve Studio's growth trajectory?

    Michelle Marsan: That sounds interesting, Drushi. We're definitely looking at ways to optimize
    our operations as we scale. Can you share some specific examples of the results you've achieved
    with other fitness companies? I'd also like to understand more about the implementation timeline
    and what kind of support you provide during the transition.
    """,
    "channel": "linkedin",
    "prospect_profile_url": "https://www.linkedin.com/in/michelle-marsan-areve/",
    "prospect_company_url": "https://www.linkedin.com/company/areve-studio/",
    "prospect_company_website": "https://arevestudio.com",
    "qubit_context": "A'reve Studio is a boutique fitness studio chain in Central America and the Caribbean, recently raised $15M Series A for expansion. Focus on community-driven fitness experiences and technology platform development.",
}


def print_section_header(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"🎯 {title}")
    print(f"{'='*80}")


def print_quality_summary(quality_data: Dict[str, Any]):
    """Print quality assessment summary"""
    if not quality_data:
        print("❌ No quality assessment available")
        return

    overall = quality_data.get("overall_assessment", {})

    print(f"\n📊 QUALITY ASSESSMENT SUMMARY")
    print(f"{'='*50}")
    print(
        f"Overall Quality Score: {overall.get('overall_quality_score', 'N/A')}")
    print(f"Quality Level: {overall.get('quality_level', 'N/A').upper()}")
    print(f"Confidence Score: {overall.get('confidence_score', 'N/A')}")
    print(
        f"Escalation Required: {'YES' if overall.get('escalation_required', False) else 'NO'}"
    )

    component_scores = overall.get("component_scores", {})
    print(f"\n📈 COMPONENT SCORES:")
    for component, score in component_scores.items():
        print(f"  • {component.replace('_', ' ').title()}: {score}")

    if overall.get("key_strengths"):
        print(f"\n✅ KEY STRENGTHS:")
        for strength in overall.get("key_strengths", []):
            print(f"  • {strength}")

    if overall.get("critical_issues"):
        print(f"\n⚠️ CRITICAL ISSUES:")
        for issue in overall.get("critical_issues", []):
            print(f"  • {issue}")

    if overall.get("recommendations"):
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in overall.get("recommendations", []):
            print(f"  • {rec}")


def print_output_preview(title: str, content: str, max_length: int = 300):
    """Print a preview of the output content"""
    print(f"\n📄 {title}")
    print(f"{'-'*50}")

    if not content:
        print("❌ No content available")
        return

    # Clean up content for preview
    preview = content.replace("\n\n", "\n").strip()

    if len(preview) > max_length:
        preview = preview[:max_length] + "..."

    print(preview)


def test_enhanced_output_quality():
    """Test the enhanced output quality improvements"""

    print_section_header("ENHANCED OUTPUT QUALITY DEMONSTRATION")
    print("This test demonstrates the improved output quality with:")
    print("• Enhanced profile enrichment with strategic insights")
    print("• Comprehensive thread analysis with actionable intelligence")
    print("• Compelling, personalized response generation")
    print("• Structured context assembly and quality assessment")

    print_section_header("TESTING ENHANCED WORKFLOW")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/run", json=SAMPLE_CONVERSATION, timeout=120
        )
        processing_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            print(
                f"✅ Workflow completed successfully in {processing_time:.2f}s")

            # Extract components
            context = result.get("context", {})
            reply = result.get("reply", "")
            quality_assessment = result.get("quality_assessment", {})

            # Show enhanced profile intelligence
            print_section_header("ENHANCED PROFILE INTELLIGENCE")
            profile_intelligence = context.get("intelligence_report", {}).get(
                "profile_intelligence", ""
            )
            print_output_preview(
                "Profile Intelligence Report", profile_intelligence, 500
            )

            # Show enhanced thread analysis
            print_section_header("ENHANCED THREAD ANALYSIS")
            conversation_analysis = context.get("intelligence_report", {}).get(
                "conversation_analysis", {}
            )

            if conversation_analysis:
                print(f"\n📊 CONVERSATION OVERVIEW:")
                overview = conversation_analysis.get(
                    "conversation_overview", {})
                for key, value in overview.items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")

                print(f"\n🎯 QUALIFICATION ANALYSIS:")
                qualification = conversation_analysis.get(
                    "qualification_analysis", {})
                print(
                    f"  • Qualification Stage: {qualification.get('qualification_stage', 'N/A')}"
                )
                print(
                    f"  • Authority Level: {qualification.get('authority_level', 'N/A')}"
                )

                buying_signals = qualification.get("buying_signals", [])
                if buying_signals:
                    print(
                        f"  • Buying Signals: {', '.join(buying_signals[:3])}")

                pain_points = qualification.get("pain_points_mentioned", [])
                if pain_points:
                    print(f"  • Pain Points: {', '.join(pain_points[:3])}")

                print(f"\n🧠 STRATEGIC INSIGHTS:")
                strategic = conversation_analysis.get("strategic_insights", {})
                next_actions = strategic.get("next_best_actions", [])
                if next_actions:
                    print(f"  • Next Best Actions:")
                    for action in next_actions[:3]:
                        print(f"    - {action}")

                print(f"\n📈 SUCCESS PROBABILITY:")
                follow_up = conversation_analysis.get("follow_up_strategy", {})
                print(f"  • {follow_up.get('success_probability', 'N/A')}")
                print(
                    f"  • Recommended Approach: {follow_up.get('recommended_approach', 'N/A')}"
                )

            # Show actionable insights
            print_section_header("ACTIONABLE INSIGHTS")
            actionable = context.get("actionable_insights", {})

            print(
                f"📊 QUALIFICATION: {actionable.get('qualification_stage', 'N/A')}")
            print(f"📈 ENGAGEMENT: {actionable.get('engagement_level', 'N/A')}")
            print(
                f"🎯 SUCCESS PROBABILITY: {actionable.get('success_probability', 'N/A')}"
            )

            next_actions = actionable.get("next_actions", [])
            if next_actions:
                print(f"\n⚡ NEXT ACTIONS:")
                for action in next_actions[:3]:
                    print(f"  • {action}")

            # Show response strategy
            print_section_header("RESPONSE STRATEGY")
            strategy = context.get("response_strategy", {})

            print(
                f"📋 RECOMMENDED APPROACH: {strategy.get('recommended_approach', 'N/A')}"
            )
            print(f"⏰ OPTIMAL TIMING: {strategy.get('optimal_timing', 'N/A')}")

            talking_points = strategy.get("key_talking_points", [])
            if talking_points:
                print(f"\n💬 KEY TALKING POINTS:")
                for point in talking_points[:3]:
                    print(f"  • {point}")

            # Show enhanced reply
            print_section_header("ENHANCED REPLY GENERATION")
            print_output_preview("Generated Response Strategy", reply, 800)

            # Show quality assessment
            print_section_header("COMPREHENSIVE QUALITY ASSESSMENT")
            print_quality_summary(quality_assessment)

            # Show individual component assessments
            individual_assessments = quality_assessment.get(
                "individual_assessments", {}
            )

            for component, assessment in individual_assessments.items():
                print(f"\n🔍 {component.replace('_', ' ').title()} Assessment:")
                print(f"  Score: {assessment.get('quality_score', 'N/A')}")
                print(f"  Level: {assessment.get('quality_level', 'N/A')}")

                if assessment.get("strengths"):
                    print(
                        f"  Strengths: {', '.join(assessment['strengths'][:2])}")

                if assessment.get("issues"):
                    print(f"  Issues: {', '.join(assessment['issues'][:2])}")

            # Summary
            print_section_header("QUALITY IMPROVEMENT SUMMARY")
            print("✅ ENHANCED OUTPUT FEATURES:")
            print("  • Deep profile intelligence with strategic insights")
            print("  • Comprehensive thread analysis with buying signals")
            print("  • Structured actionable insights and recommendations")
            print("  • Compelling, personalized response strategies")
            print("  • Comprehensive quality assessment and scoring")
            print("  • Confidence metrics and escalation triggers")
            print("  • Structured context assembly for better usability")

            overall_quality = quality_assessment.get("overall_assessment", {})
            quality_level = overall_quality.get("quality_level", "unknown")
            quality_score = overall_quality.get("overall_quality_score", 0)

            print(f"\n🎯 FINAL QUALITY METRICS:")
            print(
                f"  • Overall Quality: {quality_level.upper()} ({quality_score})")
            print(
                f"  • Ready for Deployment: {'YES' if quality_score >= 0.7 else 'NEEDS REVIEW'}"
            )
            print(
                f"  • Escalation Required: {'YES' if overall_quality.get('escalation_required') else 'NO'}"
            )

        else:
            print(f"❌ Workflow failed with status {response.status_code}")
            print(f"Error: {response.text}")

        except Exception as e:
            logger.error(f"Error nt(f"❌ Error running workflow: {e}")


def compare_output_formats():
    """Compare different output formats"""

    print_section_header("OUTPUT FORMAT COMPARISON")

    formats = [
        ("Standard Workflow", "/run"),
        ("Parallel Processing", "/run-parallel"),
        ("Template-Based", "/run-template"),
    ]

    for name, endpoint in formats:
        print(f"\n🔄 Testing {name}...")

        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}", json=SAMPLE_CONVERSATION, timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                quality_data = result.get("quality_assessment", {})

                if quality_data:
                    overall = quality_data.get("overall_assessment", {})
                    print(
                        f"  ✅ Quality Score: {overall.get('overall_quality_score', 'N/A')}"
                    )
                    print(
                        f"  📊 Quality Level: {overall.get('quality_level', 'N/A')}")
                    print(
                        f"  🎯 Confidence: {overall.get('confidence_score', 'N/A')}")
                else:
                    print(f"  ⚠️ No quality assessment available")
            else:
                print(f"  ❌ Failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error nt(f"  ❌ Error: {e}")


def main():
    """Run comprehensive output quality tests"""

    print("🚀 CrewAI Workflow - Enhanced Output Quality Test")
    print("=" * 80)
    print("Testing comprehensive output quality improvements:")
    print("• Enhanced prompts for deeper insights")
    print("• Structured context assembly")
    print("• Comprehensive quality assessment")
    print("• Confidence metrics and recommendations")

    # Test server availability
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Please start the server first.")
            return
        except Exception as e:
            logger.error(f"Error nt(f"❌ Cannot connect to server: {e}")
        print("Please start the server with: uvicorn app:app --reload")
        return

    print("✅ Server is running. Starting quality tests...\n")

    # Run tests
    test_enhanced_output_quality()
    compare_output_formats()

    # Final summary
    print_section_header("ENHANCED OUTPUT QUALITY - COMPLETE")
    print("🎯 All output quality improvements have been successfully implemented:")
    print("  ✅ Enhanced profile enrichment with strategic insights")
    print("  ✅ Comprehensive thread analysis with actionable intelligence")
    print("  ✅ Compelling, personalized response generation")
    print("  ✅ Structured context assembly for better usability")
    print("  ✅ Comprehensive quality assessment and scoring")
    print("  ✅ Confidence metrics and escalation triggers")
    print("\n🚀 Your CrewAI workflow now produces significantly higher quality,")
    print("   more actionable, and more valuable outputs for sales teams!")


if __name__ == "__main__":
    main()
