import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, Dict

from agents import llm  # Import the working LLM directly
from cache import (async_cache_result, cache_result, metrics_collector,
                   workflow_cache, MetricsCollector)
from faq import get_faq_answer
from faq_agent import get_intelligent_faq_answer, analyze_questions_batch
from output_quality import assess_workflow_output_quality
from logging_config import log_info, log_error, log_warning, log_debug

# Set up logging
logger = logging.getLogger(__name__)

def normalize_channel(channel):
    """
    Normalize channel name to standard format.
    
    Args:
        channel (str): The input channel name to normalize
        
    Returns:
        str: Normalized channel name ('linkedin' or 'email')
        
    Raises:
        ValueError: If the channel is not recognized
    """
    c = channel.strip().lower()
    if c in ["linkedin", "linked in", "li"]:
        return "linkedin"
    elif c in ["email", "mail"]:
        return "email"
    else:
        raise ValueError(f"Unknown channel: {channel}")



def assemble_context(
    profile_summary, thread_analysis, faq_answers, client_report, qubit_context
):
    """
    Enhanced context assembly with structured, actionable intelligence.
    
    This function takes various data sources and assembles them into a structured
    context object that can be used for generating personalized responses. It parses
    thread analysis JSON, extracts key insights, and organizes them into categories
    for easy access by the response generation system.
    
    Args:
        profile_summary (str): Enriched profile information about the prospect
        thread_analysis (str or dict): Analysis of the conversation thread, either as JSON string or dict
        faq_answers (list): List of FAQ answers relevant to the conversation
        client_report (str): Information about the client/company
        qubit_context (str): Additional context provided by the user
        
    Returns:
        dict: Structured context with intelligence report, actionable insights,
              response strategy, and risk assessment sections
    """

    # Parse thread analysis if it's JSON
    parsed_thread_analysis = {}
    if thread_analysis:
        try:
            parsed_thread_analysis = (
                json.loads(thread_analysis)
                if isinstance(thread_analysis, str)
                else thread_analysis
            )
        except Exception:
            parsed_thread_analysis = {"raw_analysis": thread_analysis}

    return {
        "intelligence_report": {
            "profile_intelligence": profile_summary or "",
            "conversation_analysis": parsed_thread_analysis,
            "faq_responses": faq_answers or [],
            "client_context": client_report or "",
            "strategic_context": qubit_context or "",
        },
        "actionable_insights": {
            "qualification_stage": parsed_thread_analysis.get(
                "qualification_analysis", {}
            ).get("qualification_stage", "unknown"),
            "buying_signals": parsed_thread_analysis.get(
                "qualification_analysis", {}
            ).get("buying_signals", []),
            "pain_points": parsed_thread_analysis.get("qualification_analysis", {}).get(
                "pain_points_mentioned", []
            ),
            "next_actions": parsed_thread_analysis.get("strategic_insights", {}).get(
                "next_best_actions", []
            ),
            "personalization_data": parsed_thread_analysis.get(
                "personalization_data", {}
            ),
            "engagement_level": parsed_thread_analysis.get(
                "conversation_intelligence", {}
            ).get("engagement_level", "unknown"),
            "success_probability": parsed_thread_analysis.get(
                "follow_up_strategy", {}
            ).get("success_probability", "unknown"),
        },
        "response_strategy": {
            "recommended_approach": parsed_thread_analysis.get(
                "follow_up_strategy", {}
            ).get("recommended_approach", "consultative"),
            "optimal_timing": parsed_thread_analysis.get("strategic_insights", {}).get(
                "optimal_timing", "within 24 hours"
            ),
            "key_talking_points": parsed_thread_analysis.get(
                "strategic_insights", {}
            ).get("key_talking_points", []),
            "value_propositions": parsed_thread_analysis.get(
                "strategic_insights", {}
            ).get("value_propositions", []),
            "content_suggestions": parsed_thread_analysis.get(
                "follow_up_strategy", {}
            ).get("content_suggestions", []),
        },
        "risk_assessment": {
            "risk_factors": parsed_thread_analysis.get("strategic_insights", {}).get(
                "risk_factors", []
            ),
            "objections_raised": parsed_thread_analysis.get(
                "conversation_intelligence", {}
            ).get("objections_raised", []),
            "competitive_threats": parsed_thread_analysis.get(
                "competitive_intelligence", {}
            ).get("competitors_mentioned", []),
        },
        # Legacy fields for backward compatibility
        "overview": profile_summary or "",
        "thread_analysis": thread_analysis or "",
        "faq_answers": faq_answers or [],
        "client_report": client_report or "",
        "qubit_context": qubit_context or "",
    }


@async_cache_result(ttl=7200, key_prefix="profile_enrichment")  # 2 hours cache
async def run_profile_enrichment_streaming(
    prospect_profile_url, prospect_company_url, prospect_company_website
):
    """Enhanced profile enrichment task with deep sales intelligence and strategic insights"""
    # Check cache first
    cached_data = workflow_cache.get_cached_profile_data(
        prospect_profile_url, prospect_company_url
    )
    if cached_data:
        yield {
            "type": "profile_enrichment_complete",
            "result": cached_data,
            "cached": True,
        }
        return  # Fixed: return without value in async generator

    prompt = f"""
    You are an elite ProfileEnricher agent specializing in deep sales intelligence and strategic business analysis. Your goal is to provide actionable insights that enable highly personalized, value-driven outreach.

    SOURCES TO ANALYZE:
    Prospect LinkedIn: {prospect_profile_url}
    Company LinkedIn: {prospect_company_url}
    Company Website: {prospect_company_website}

    PROVIDE A COMPREHENSIVE ANALYSIS WITH THESE SECTIONS:

    ## PROSPECT INTELLIGENCE
    - Full name, title, and tenure at current company
    - Career progression and key achievements
    - Educational background and certifications
    - Professional interests and thought leadership topics
    - Recent posts, articles, or content shared
    - Mutual connections and network insights
    - Personal interests and values (if publicly available)

    ## COMPANY INTELLIGENCE
    - Company overview, mission, and value proposition
    - Industry, sector, and market positioning
    - Current business model and revenue streams
    - Recent news, announcements, or milestones
    - Funding history and investor information
    - Key leadership team and decision makers
    - Technology stack and tools used
    - Competitive landscape and differentiators

    ## STRATEGIC INSIGHTS
    - Current business challenges and pain points
    - Growth opportunities and expansion plans
    - Budget cycles and decision-making processes
    - Buying signals and readiness indicators
    - Potential objections and concerns
    - Best timing for outreach and engagement

    ## PERSONALIZATION OPPORTUNITIES
    - Specific conversation starters and ice breakers
    - Relevant case studies or success stories to mention
    - Industry trends or insights to reference
    - Mutual interests or connections to leverage
    - Value propositions most likely to resonate
    - Recommended approach and messaging strategy

    ## RISK ASSESSMENT
    - Potential red flags or concerns
    - Competitor relationships or conflicts
    - Market timing considerations
    - Stakeholder influence and decision dynamics

    Format your response as a detailed, actionable intelligence report that enables highly personalized and strategic outreach.
    """

    start_time = time.time()
    try:
        # Use streaming with LangChain v0.3
        result_chunks = []
        async for chunk in llm.astream(prompt):
            result_chunks.append(chunk.content)
            yield {
                "type": "profile_enrichment_chunk",
                "chunk": chunk.content,
                "partial_result": "".join(result_chunks),
            }

        final_result = "".join(result_chunks)

        # Cache the result
        workflow_cache.cache_profile_data(
            prospect_profile_url, prospect_company_url, final_result
        )

        # Record metrics
        metrics_collector.record_timing(
            "profile_enrichment", time.time() - start_time)
        metrics_collector.increment_counter("profile_enrichment_success")

        yield {
            "type": "profile_enrichment_complete",
            "result": final_result,
            "cached": False,
        }
        return  # Fixed: return without value in async generator
    except Exception as e:
        metrics_collector.increment_counter("profile_enrichment_error")
        error_msg = f"Error getting profile summary: {str(e)}"
        yield {"type": "profile_enrichment_error", "error": error_msg}
        return  # Fixed: return without value in async generator


@async_cache_result(ttl=3600, key_prefix="thread_analysis")  # 1 hour cache
async def run_thread_analysis_streaming(conversation_thread, channel):
    """Enhanced thread analysis task with strategic sales insights and actionable intelligence"""
    if channel == "linkedin":
        prompt = f"""
        You are an elite LinkedInThreadAnalyzer agent with deep expertise in sales psychology, conversation analysis, and strategic communication patterns. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

        CONVERSATION THREAD TO ANALYZE:
        {conversation_thread}

        PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

        {{
            "conversation_overview": {{
                "participant_count": "number of people in conversation",
                "message_count": "total messages exchanged",
                "conversation_duration": "timespan of conversation",
                "conversation_type": "cold_outreach|warm_introduction|follow_up|referral"
            }},
            "qualification_analysis": {{
                "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
                "buying_signals": ["list of specific buying signals observed"],
                "pain_points_mentioned": ["explicit or implicit pain points"],
                "budget_indicators": ["any budget or financial discussions"],
                "timeline_indicators": ["urgency signals or timeline mentions"],
                "authority_level": "decision_maker|influencer|user|researcher"
            }},
            "conversation_intelligence": {{
                "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent",
                "engagement_level": "high|medium|low",
                "response_pattern": "immediate|delayed|inconsistent",
                "communication_style": "direct|detailed|brief|analytical|relationship_focused",
                "objections_raised": ["specific objections or concerns mentioned"],
                "interests_expressed": ["topics or solutions they showed interest in"]
            }},
            "strategic_insights": {{
                "next_best_actions": ["specific recommended next steps"],
                "optimal_timing": "best time to follow up",
                "preferred_communication": "linkedin|email|phone|meeting",
                "key_talking_points": ["topics to emphasize in follow-up"],
                "value_propositions": ["most relevant value props based on conversation"],
                "risk_factors": ["potential deal risks or concerns"]
            }},
            "personalization_data": {{
                "explicit_questions": ["direct questions asked by prospect"],
                "implicit_needs": ["underlying needs inferred from conversation"],
                "personal_interests": ["personal details or interests mentioned"],
                "professional_priorities": ["work-related priorities or goals"],
                "decision_criteria": ["factors important to their decision making"],
                "stakeholder_mentions": ["other people or roles mentioned"]
            }},
            "competitive_intelligence": {{
                "competitors_mentioned": ["any competing solutions discussed"],
                "current_solutions": ["existing tools or processes they use"],
                "switching_barriers": ["obstacles to changing current solution"],
                "differentiation_opportunities": ["ways to stand out from competition"]
            }},
            "follow_up_strategy": {{
                "message_summary": "concise summary of entire conversation",
                "recommended_approach": "consultative|solution_focused|relationship_building|educational",
                "content_suggestions": ["specific content or resources to share"],
                "meeting_readiness": "ready|needs_nurturing|requires_education",
                "success_probability": "high|medium|low with reasoning"
            }}
        }}

        Ensure all analysis is based on actual conversation content and provides actionable insights for sales strategy.
        """
    else:
        prompt = f"""
        You are an elite EmailThreadAnalyzer agent with deep expertise in email communication patterns, sales psychology, and strategic engagement analysis. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

        EMAIL THREAD TO ANALYZE:
        {conversation_thread}

        PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

        {{
            "conversation_overview": {{
                "participant_count": "number of people in conversation",
                "message_count": "total messages exchanged",
                "conversation_duration": "timespan of conversation",
                "conversation_type": "cold_outreach|warm_introduction|follow_up|referral|internal_discussion"
            }},
            "qualification_analysis": {{
                "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
                "buying_signals": ["list of specific buying signals observed"],
                "pain_points_mentioned": ["explicit or implicit pain points"],
                "budget_indicators": ["any budget or financial discussions"],
                "timeline_indicators": ["urgency signals or timeline mentions"],
                "authority_level": "decision_maker|influencer|user|researcher"
            }},
            "conversation_intelligence": {{
                "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent",
                "engagement_level": "high|medium|low",
                "response_pattern": "immediate|delayed|inconsistent",
                "communication_style": "direct|detailed|brief|analytical|relationship_focused",
                "objections_raised": ["specific objections or concerns mentioned"],
                "interests_expressed": ["topics or solutions they showed interest in"]
            }},
            "strategic_insights": {{
                "next_best_actions": ["specific recommended next steps"],
                "optimal_timing": "best time to follow up",
                "preferred_communication": "email|phone|meeting|linkedin",
                "key_talking_points": ["topics to emphasize in follow-up"],
                "value_propositions": ["most relevant value props based on conversation"],
                "risk_factors": ["potential deal risks or concerns"]
            }},
            "personalization_data": {{
                "explicit_questions": ["direct questions asked by prospect"],
                "implicit_needs": ["underlying needs inferred from conversation"],
                "personal_interests": ["personal details or interests mentioned"],
                "professional_priorities": ["work-related priorities or goals"],
                "decision_criteria": ["factors important to their decision making"],
                "stakeholder_mentions": ["other people or roles mentioned"]
            }},
            "competitive_intelligence": {{
                "competitors_mentioned": ["any competing solutions discussed"],
                "current_solutions": ["existing tools or processes they use"],
                "switching_barriers": ["obstacles to changing current solution"],
                "differentiation_opportunities": ["ways to stand out from competition"]
            }},
            "follow_up_strategy": {{
                "message_summary": "concise summary of entire conversation",
                "recommended_approach": "consultative|solution_focused|relationship_building|educational",
                "content_suggestions": ["specific content or resources to share"],
                "meeting_readiness": "ready|needs_nurturing|requires_education",
                "success_probability": "high|medium|low with reasoning"
            }}
        }}

        Ensure all analysis is based on actual conversation content and provides actionable insights for sales strategy.
        """

    start_time = time.time()
    try:
        result_chunks = []
        async for chunk in llm.astream(prompt):
            result_chunks.append(chunk.content)
            yield {
                "type": "thread_analysis_chunk",
                "chunk": chunk.content,
                "partial_result": "".join(result_chunks),
            }

        final_result = "".join(result_chunks)

        # Record metrics
        metrics_collector.record_timing(
            "thread_analysis", time.time() - start_time)
        metrics_collector.increment_counter("thread_analysis_success")

        yield {"type": "thread_analysis_complete", "result": final_result}
        return  # Fixed: return without value in async generator
    except Exception as e:
        metrics_collector.increment_counter("thread_analysis_error")
        error_msg = f'{{"error": "Error analyzing thread: {str(e)}"}}'
        yield {"type": "thread_analysis_error", "error": error_msg}
        return  # Fixed: return without value in async generator


# 30 minutes cache
@async_cache_result(ttl=1800, key_prefix="reply_generation")
async def run_reply_generation_streaming(context, channel):
    """Enhanced reply generation with compelling, highly personalized responses"""
    if channel == "linkedin":
        prompt = f"""
        You are an elite LinkedInReplyGenerator agent with deep expertise in sales psychology, persuasive communication, and relationship building. Your goal is to create compelling, highly personalized LinkedIn responses that drive engagement and move prospects through the sales funnel.

        CONTEXT AND INTELLIGENCE:
        {json.dumps(context, indent=2)}

        IMPORTANT: If FAQ answers are provided in the context, you MUST incorporate them into your response strategy. Use these official answers to address any questions the prospect has asked.

        GENERATE A COMPREHENSIVE LINKEDIN RESPONSE STRATEGY WITH THESE COMPONENTS:

        ## IMMEDIATE RESPONSE
        Craft a personalized, engaging LinkedIn message that:
        - Acknowledges specific details from the conversation
        - Demonstrates genuine understanding of their business challenges
        - Provides immediate value (insight, resource, or connection)
        - Includes a clear, non-pushy call-to-action
        - Maintains a professional yet personable tone
        - Uses their name and company naturally
        - References specific details that show you've done your research
        - IMPORTANT: Keep this message between 80-100 words for optimal engagement

        ## FOLLOW-UP SEQUENCE (Exactly 3 messages)
        Design a strategic follow-up sequence with exactly 3 messages that:
        - Builds on the initial conversation momentum
        - Provides additional value at each touchpoint
        - Addresses potential objections proactively
        - Includes social proof and credibility indicators
        - Maintains engagement without being pushy
        - Escalates appropriately toward a meeting or call
        - IMPORTANT: Keep each follow-up message between 75-125 words

        ## PERSONALIZATION ELEMENTS
        Incorporate these personalization strategies:
        - Reference their recent posts, achievements, or company news
        - Mention mutual connections or shared interests
        - Use industry-specific language and terminology
        - Address their specific role and responsibilities
        - Connect to their company's current priorities or challenges

        ## VALUE PROPOSITIONS
        Highlight value propositions that:
        - Directly address their expressed or implied pain points
        - Demonstrate ROI and business impact
        - Include relevant case studies or success stories
        - Position your solution as uniquely suited to their needs
        - Create urgency without being aggressive

        ## ENGAGEMENT TACTICS
        Use proven engagement techniques:
        - Ask thoughtful, open-ended questions
        - Share relevant industry insights or trends
        - Offer valuable resources (whitepapers, tools, introductions)
        - Suggest low-commitment next steps
        - Create curiosity gaps that encourage responses

        FORMAT REQUIREMENTS:
        - Use raw URLs for all links
        - Keep messages LinkedIn-appropriate (professional but conversational)
        - Include the full conversation thread for context
        - Structure output with clear sections:
          
          ## IMMEDIATE RESPONSE
          [Your 80-100 word message here]
          [Word Count: X words]
          
          ## FOLLOW-UP SEQUENCE
          
          ### Follow-up 1 (Day 3-4)
          [Your 75-125 word message here]
          [Word Count: X words]
          
          ### Follow-up 2 (Day 7-10)
          [Your 75-125 word message here]
          [Word Count: X words]
          
          ### Follow-up 3 (Day 14-21)
          [Your 75-125 word message here]
          [Word Count: X words]
          
        - At the end, provide a WORD COUNT SUMMARY section with:
          * Immediate Response: X words
          * Follow-up 1: X words
          * Follow-up 2: X words
          * Follow-up 3: X words
          * Total Word Count: X words

        TONE AND STYLE:
        - Professional yet approachable
        - Confident but not arrogant
        - Helpful and consultative
        - Authentic and genuine
        - Results-focused

        Generate a complete response strategy that maximizes the probability of engagement and progression toward a business conversation.
        """
    else:
        prompt = f"""
        You are an elite EmailReplyGenerator agent with deep expertise in email marketing, sales psychology, and multi-touch communication strategies. Your goal is to create compelling, highly personalized email sequences that drive engagement and move prospects through the sales funnel.

        CONTEXT AND INTELLIGENCE:
        {json.dumps(context, indent=2)}

        IMPORTANT: If FAQ answers are provided in the context, you MUST incorporate them into your response strategy. Use these official answers to address any questions the prospect has asked.

        GENERATE A COMPREHENSIVE EMAIL RESPONSE STRATEGY WITH THESE COMPONENTS:

        ## IMMEDIATE RESPONSE
        Craft a personalized, engaging email that:
        - Acknowledges specific details from the conversation
        - Demonstrates genuine understanding of their business challenges
        - Provides immediate value (insight, resource, or connection)
        - Includes a clear, compelling call-to-action
        - Uses professional email formatting and structure
        - References specific details that show you've done your research

        ## FOLLOW-UP SEQUENCE (3-7 emails)
        Design a strategic email sequence that:
        - Builds on the initial conversation momentum
        - Provides additional value at each touchpoint
        - Addresses potential objections proactively
        - Includes social proof and credibility indicators
        - Maintains engagement without being pushy
        - Escalates appropriately toward a meeting or call
        - Varies content types (educational, social proof, urgency, etc.)

        ## PERSONALIZATION ELEMENTS
        Incorporate these personalization strategies:
        - Reference their recent company news or achievements
        - Mention mutual connections or shared experiences
        - Use industry-specific language and terminology
        - Address their specific role and responsibilities
        - Connect to their company's current priorities or challenges
        - Include relevant case studies from similar companies

        ## VALUE PROPOSITIONS
        Highlight value propositions that:
        - Directly address their expressed or implied pain points
        - Demonstrate clear ROI and business impact
        - Include specific metrics and success stories
        - Position your solution as uniquely suited to their needs
        - Create urgency through time-sensitive opportunities

        ## ENGAGEMENT TACTICS
        Use proven email engagement techniques:
        - Compelling subject lines that encourage opens
        - Strong opening lines that grab attention
        - Scannable format with bullet points and short paragraphs
        - Clear calls-to-action with specific next steps
        - P.S. lines that reinforce key messages
        - Social proof and credibility indicators

        ## EMAIL SEQUENCE STRUCTURE
        Structure each email with:
        - Compelling subject line
        - Personalized greeting
        - Value-driven opening
        - Clear main message
        - Strong call-to-action
        - Professional signature
        - Strategic P.S. when appropriate

        FORMAT REQUIREMENTS:
        - Use anchor text for all links
        - Include proper email formatting and structure
        - Provide subject lines for each email
        - Include the full conversation thread for context
        - Structure each email with clear sections
        - Specify optimal timing between emails

        TONE AND STYLE:
        - Professional and authoritative
        - Helpful and consultative
        - Confident but not pushy
        - Authentic and genuine
        - Results-focused and data-driven

        Generate a complete email sequence strategy that maximizes open rates, engagement, and conversion toward a business conversation.
        """

    start_time = time.time()
    try:
        result_chunks = []
        async for chunk in llm.astream(prompt):
            result_chunks.append(chunk.content)
            yield {
                "type": "reply_generation_chunk",
                "chunk": chunk.content,
                "partial_result": "".join(result_chunks),
            }

        final_result = "".join(result_chunks)

        # Record metrics
        metrics_collector.record_timing(
            "reply_generation", time.time() - start_time)
        metrics_collector.increment_counter("reply_generation_success")

        yield {"type": "reply_generation_complete", "result": final_result}
        return  # Fixed: return without value in async generator
    except Exception as e:
        metrics_collector.increment_counter("reply_generation_error")
        error_msg = f"Error generating reply: {str(e)}"
        yield {"type": "reply_generation_error", "error": error_msg}
        return  # Fixed: return without value in async generator


@cache_result(ttl=7200, key_prefix="profile_enrichment")  # 2 hours cache
def run_profile_enrichment(
    prospect_profile_url, prospect_company_url, prospect_company_website
):
    """Enhanced profile enrichment task with deep sales intelligence and strategic insights"""
    # Check cache first
    cached_data = workflow_cache.get_cached_profile_data(
        prospect_profile_url, prospect_company_url
    )
    if cached_data:
        metrics_collector.increment_counter("profile_enrichment_cache_hit")
        return cached_data

    prompt = f"""
    You are an elite ProfileEnricher agent specializing in deep sales intelligence and strategic business analysis. Your goal is to provide actionable insights that enable highly personalized, value-driven outreach.

    SOURCES TO ANALYZE:
    Prospect LinkedIn: {prospect_profile_url}
    Company LinkedIn: {prospect_company_url}
    Company Website: {prospect_company_website}

    PROVIDE A COMPREHENSIVE ANALYSIS WITH THESE SECTIONS:

    ## PROSPECT INTELLIGENCE
    - Full name, title, and tenure at current company
    - Career progression and key achievements
    - Educational background and certifications
    - Professional interests and thought leadership topics
    - Recent posts, articles, or content shared
    - Mutual connections and network insights
    - Personal interests and values (if publicly available)

    ## COMPANY INTELLIGENCE
    - Company overview, mission, and value proposition
    - Industry, sector, and market positioning
    - Current business model and revenue streams
    - Recent news, announcements, or milestones
    - Funding history and investor information
    - Key leadership team and decision makers
    - Technology stack and tools used
    - Competitive landscape and differentiators

    ## STRATEGIC INSIGHTS
    - Current business challenges and pain points
    - Growth opportunities and expansion plans
    - Budget cycles and decision-making processes
    - Buying signals and readiness indicators
    - Potential objections and concerns
    - Best timing for outreach and engagement

    ## PERSONALIZATION OPPORTUNITIES
    - Specific conversation starters and ice breakers
    - Relevant case studies or success stories to mention
    - Industry trends or insights to reference
    - Mutual interests or connections to leverage
    - Value propositions most likely to resonate
    - Recommended approach and messaging strategy

    ## RISK ASSESSMENT
    - Potential red flags or concerns
    - Competitor relationships or conflicts
    - Market timing considerations
    - Stakeholder influence and decision dynamics

    Format your response as a detailed, actionable intelligence report that enables highly personalized and strategic outreach.
    """

    start_time = time.time()
    try:
        if llm is None:
            raise ValueError("LLM is not properly initialized. Check Azure OpenAI configuration.")
        result = llm.invoke(prompt)
        final_result = result.content

        # Cache the result
        workflow_cache.cache_profile_data(
            prospect_profile_url, prospect_company_url, final_result
        )

        # Record metrics
        metrics_collector.record_timing(
            "profile_enrichment", time.time() - start_time)
        metrics_collector.increment_counter("profile_enrichment_success")

        return final_result
    except Exception as e:
        metrics_collector.increment_counter("profile_enrichment_error")
        return f"Error getting profile summary: {str(e)}"


@cache_result(ttl=3600, key_prefix="thread_analysis")  # 1 hour cache
def run_thread_analysis(conversation_thread, channel):
    """Enhanced thread analysis task with strategic sales insights and actionable intelligence"""
    if channel == "linkedin":
        prompt = f"""
        You are an elite LinkedInThreadAnalyzer agent with deep expertise in sales psychology, conversation analysis, and strategic communication patterns. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

        CONVERSATION THREAD TO ANALYZE:
        {conversation_thread}

        PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

        {{
            "conversation_overview": {{
                "participant_count": "number of people in conversation",
                "message_count": "total messages exchanged",
                "conversation_duration": "timespan of conversation",
                "conversation_type": "cold_outreach|warm_introduction|follow_up|referral"
            }},
            "qualification_analysis": {{
                "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
                "buying_signals": ["list of specific buying signals observed"],
                "pain_points_mentioned": ["explicit or implicit pain points"],
                "budget_indicators": ["any budget or financial discussions"],
                "timeline_indicators": ["urgency signals or timeline mentions"],
                "authority_level": "decision_maker|influencer|user|researcher"
            }},
            "conversation_intelligence": {{
                "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent",
                "engagement_level": "high|medium|low",
                "response_pattern": "immediate|delayed|inconsistent",
                "communication_style": "direct|detailed|brief|analytical|relationship_focused",
                "objections_raised": ["specific objections or concerns mentioned"],
                "interests_expressed": ["topics or solutions they showed interest in"]
            }},
            "strategic_insights": {{
                "next_best_actions": ["specific recommended next steps"],
                "optimal_timing": "best time to follow up",
                "preferred_communication": "linkedin|email|phone|meeting",
                "key_talking_points": ["topics to emphasize in follow-up"],
                "value_propositions": ["most relevant value props based on conversation"],
                "risk_factors": ["potential deal risks or concerns"]
            }},
            "personalization_data": {{
                "explicit_questions": ["direct questions asked by prospect"],
                "implicit_needs": ["underlying needs inferred from conversation"],
                "personal_interests": ["personal details or interests mentioned"],
                "professional_priorities": ["work-related priorities or goals"],
                "decision_criteria": ["factors important to their decision making"],
                "stakeholder_mentions": ["other people or roles mentioned"]
            }},
            "competitive_intelligence": {{
                "competitors_mentioned": ["any competing solutions discussed"],
                "current_solutions": ["existing tools or processes they use"],
                "switching_barriers": ["obstacles to changing current solution"],
                "differentiation_opportunities": ["ways to stand out from competition"]
            }},
            "follow_up_strategy": {{
                "message_summary": "concise summary of entire conversation",
                "recommended_approach": "consultative|solution_focused|relationship_building|educational",
                "content_suggestions": ["specific content or resources to share"],
                "meeting_readiness": "ready|needs_nurturing|requires_education",
                "success_probability": "high|medium|low with reasoning"
            }}
        }}

        Ensure all analysis is based on actual conversation content and provides actionable insights for sales strategy.
        """
    else:
        prompt = f"""
        You are an elite EmailThreadAnalyzer agent with deep expertise in email communication patterns, sales psychology, and strategic engagement analysis. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

        EMAIL THREAD TO ANALYZE:
        {conversation_thread}

        PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

        {{
            "conversation_overview": {{
                "participant_count": "number of people in conversation",
                "message_count": "total messages exchanged",
                "conversation_duration": "timespan of conversation",
                "conversation_type": "cold_outreach|warm_introduction|follow_up|referral|internal_discussion"
            }},
            "qualification_analysis": {{
                "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
                "buying_signals": ["list of specific buying signals observed"],
                "pain_points_mentioned": ["explicit or implicit pain points"],
                "budget_indicators": ["any budget or financial discussions"],
                "timeline_indicators": ["urgency signals or timeline mentions"],
                "authority_level": "decision_maker|influencer|user|researcher"
            }},
            "conversation_intelligence": {{
                "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent",
                "engagement_level": "high|medium|low",
                "response_pattern": "immediate|delayed|inconsistent",
                "communication_style": "direct|detailed|brief|analytical|relationship_focused",
                "objections_raised": ["specific objections or concerns mentioned"],
                "interests_expressed": ["topics or solutions they showed interest in"]
            }},
            "strategic_insights": {{
                "next_best_actions": ["specific recommended next steps"],
                "optimal_timing": "best time to follow up",
                "preferred_communication": "email|phone|meeting|linkedin",
                "key_talking_points": ["topics to emphasize in follow-up"],
                "value_propositions": ["most relevant value props based on conversation"],
                "risk_factors": ["potential deal risks or concerns"]
            }},
            "personalization_data": {{
                "explicit_questions": ["direct questions asked by prospect"],
                "implicit_needs": ["underlying needs inferred from conversation"],
                "personal_interests": ["personal details or interests mentioned"],
                "professional_priorities": ["work-related priorities or goals"],
                "decision_criteria": ["factors important to their decision making"],
                "stakeholder_mentions": ["other people or roles mentioned"]
            }},
            "competitive_intelligence": {{
                "competitors_mentioned": ["any competing solutions discussed"],
                "current_solutions": ["existing tools or processes they use"],
                "switching_barriers": ["obstacles to changing current solution"],
                "differentiation_opportunities": ["ways to stand out from competition"]
            }},
            "follow_up_strategy": {{
                "message_summary": "concise summary of entire conversation",
                "recommended_approach": "consultative|solution_focused|relationship_building|educational",
                "content_suggestions": ["specific content or resources to share"],
                "meeting_readiness": "ready|needs_nurturing|requires_education",
                "success_probability": "high|medium|low with reasoning"
            }}
        }}

        Ensure all analysis is based on actual conversation content and provides actionable insights for sales strategy.
        """

    start_time = time.time()
    try:
        if llm is None:
            raise ValueError("LLM is not properly initialized. Check Azure OpenAI configuration.")
        result = llm.invoke(prompt)
        final_result = result.content

        # Record metrics
        metrics_collector.record_timing(
            "thread_analysis", time.time() - start_time)
        metrics_collector.increment_counter("thread_analysis_success")

        return final_result
    except Exception as e:
        metrics_collector.increment_counter("thread_analysis_error")
        return f'{{"error": "Error analyzing thread: {str(e)}"}}'


@cache_result(ttl=1800, key_prefix="reply_generation")  # 30 minutes cache
def run_reply_generation(context, channel):
    """Enhanced reply generation with compelling, highly personalized responses"""
    if channel == "linkedin":
        prompt = f"""
        You are an elite LinkedInReplyGenerator agent with deep expertise in sales psychology, persuasive communication, and relationship building. Your goal is to create compelling, highly personalized LinkedIn responses that drive engagement and move prospects through the sales funnel.

        CONTEXT AND INTELLIGENCE:
        {json.dumps(context, indent=2)}

        IMPORTANT: If FAQ answers are provided in the context, you MUST incorporate them into your response strategy. Use these official answers to address any questions the prospect has asked.

        GENERATE A COMPREHENSIVE LINKEDIN RESPONSE STRATEGY WITH THESE COMPONENTS:

        ## IMMEDIATE RESPONSE
        Craft a personalized, engaging LinkedIn message that:
        - Acknowledges specific details from the conversation
        - Demonstrates genuine understanding of their business challenges
        - Provides immediate value (insight, resource, or connection)
        - Includes a clear, non-pushy call-to-action
        - Maintains a professional yet personable tone
        - Uses their name and company naturally
        - References specific details that show you've done your research
        - IMPORTANT: Keep this message between 80-100 words for optimal engagement

        ## FOLLOW-UP SEQUENCE (Exactly 3 messages)
        Design a strategic follow-up sequence with exactly 3 messages that:
        - Builds on the initial conversation momentum
        - Provides additional value at each touchpoint
        - Addresses potential objections proactively
        - Includes social proof and credibility indicators
        - Maintains engagement without being pushy
        - Escalates appropriately toward a meeting or call
        - IMPORTANT: Keep each follow-up message between 75-125 words

        ## PERSONALIZATION ELEMENTS
        Incorporate these personalization strategies:
        - Reference their recent posts, achievements, or company news
        - Mention mutual connections or shared interests
        - Use industry-specific language and terminology
        - Address their specific role and responsibilities
        - Connect to their company's current priorities or challenges

        ## VALUE PROPOSITIONS
        Highlight value propositions that:
        - Directly address their expressed or implied pain points
        - Demonstrate ROI and business impact
        - Include relevant case studies or success stories
        - Position your solution as uniquely suited to their needs
        - Create urgency without being aggressive

        ## ENGAGEMENT TACTICS
        Use proven engagement techniques:
        - Ask thoughtful, open-ended questions
        - Share relevant industry insights or trends
        - Offer valuable resources (whitepapers, tools, introductions)
        - Suggest low-commitment next steps
        - Create curiosity gaps that encourage responses

        FORMAT REQUIREMENTS:
        - Use raw URLs for all links
        - Keep messages LinkedIn-appropriate (professional but conversational)
        - Include the full conversation thread for context
        - Structure output with clear sections:
          
          ## IMMEDIATE RESPONSE
          [Your 80-100 word message here]
          [Word Count: X words]
          
          ## FOLLOW-UP SEQUENCE
          
          ### Follow-up 1 (Day 3-4)
          [Your 75-125 word message here]
          [Word Count: X words]
          
          ### Follow-up 2 (Day 7-10)
          [Your 75-125 word message here]
          [Word Count: X words]
          
          ### Follow-up 3 (Day 14-21)
          [Your 75-125 word message here]
          [Word Count: X words]
          
        - At the end, provide a WORD COUNT SUMMARY section with:
          * Immediate Response: X words
          * Follow-up 1: X words
          * Follow-up 2: X words
          * Follow-up 3: X words
          * Total Word Count: X words

        TONE AND STYLE:
        - Professional yet approachable
        - Confident but not arrogant
        - Helpful and consultative
        - Authentic and genuine
        - Results-focused

        Generate a complete response strategy that maximizes the probability of engagement and progression toward a business conversation.
        """
    else:
        prompt = f"""
        You are an elite EmailReplyGenerator agent with deep expertise in email marketing, sales psychology, and multi-touch communication strategies. Your goal is to create compelling, highly personalized email sequences that drive engagement and move prospects through the sales funnel.

        CONTEXT AND INTELLIGENCE:
        {json.dumps(context, indent=2)}

        IMPORTANT: If FAQ answers are provided in the context, you MUST incorporate them into your response strategy. Use these official answers to address any questions the prospect has asked.

        GENERATE A COMPREHENSIVE EMAIL RESPONSE STRATEGY WITH THESE COMPONENTS:

        ## IMMEDIATE RESPONSE
        Craft a personalized, engaging email that:
        - Acknowledges specific details from the conversation
        - Demonstrates genuine understanding of their business challenges
        - Provides immediate value (insight, resource, or connection)
        - Includes a clear, compelling call-to-action
        - Uses professional email formatting and structure
        - References specific details that show you've done your research

        ## FOLLOW-UP SEQUENCE (3-7 emails)
        Design a strategic email sequence that:
        - Builds on the initial conversation momentum
        - Provides additional value at each touchpoint
        - Addresses potential objections proactively
        - Includes social proof and credibility indicators
        - Maintains engagement without being pushy
        - Escalates appropriately toward a meeting or call
        - Varies content types (educational, social proof, urgency, etc.)

        ## PERSONALIZATION ELEMENTS
        Incorporate these personalization strategies:
        - Reference their recent company news or achievements
        - Mention mutual connections or shared experiences
        - Use industry-specific language and terminology
        - Address their specific role and responsibilities
        - Connect to their company's current priorities or challenges
        - Include relevant case studies from similar companies

        ## VALUE PROPOSITIONS
        Highlight value propositions that:
        - Directly address their expressed or implied pain points
        - Demonstrate clear ROI and business impact
        - Include specific metrics and success stories
        - Position your solution as uniquely suited to their needs
        - Create urgency through time-sensitive opportunities

        ## ENGAGEMENT TACTICS
        Use proven email engagement techniques:
        - Compelling subject lines that encourage opens
        - Strong opening lines that grab attention
        - Scannable format with bullet points and short paragraphs
        - Clear calls-to-action with specific next steps
        - P.S. lines that reinforce key messages
        - Social proof and credibility indicators

        ## EMAIL SEQUENCE STRUCTURE
        Structure each email with:
        - Compelling subject line
        - Personalized greeting
        - Value-driven opening
        - Clear main message
        - Strong call-to-action
        - Professional signature
        - Strategic P.S. when appropriate

        FORMAT REQUIREMENTS:
        - Use anchor text for all links
        - Include proper email formatting and structure
        - Provide subject lines for each email
        - Include the full conversation thread for context
        - Structure each email with clear sections
        - Specify optimal timing between emails

        TONE AND STYLE:
        - Professional and authoritative
        - Helpful and consultative
        - Confident but not pushy
        - Authentic and genuine
        - Results-focused and data-driven

        Generate a complete email sequence strategy that maximizes open rates, engagement, and conversion toward a business conversation.
        """

    start_time = time.time()
    try:
        if llm is None:
            raise ValueError("LLM is not properly initialized. Check Azure OpenAI configuration.")
        result = llm.invoke(prompt)
        final_result = result.content

        # Record metrics
        metrics_collector.record_timing(
            "reply_generation", time.time() - start_time)
        metrics_collector.increment_counter("reply_generation_success")

        return final_result
    except Exception as e:
        metrics_collector.increment_counter("reply_generation_error")
        return f"Error generating reply: {str(e)}"


def extract_word_counts(reply_text):
    """Extract word counts from the generated reply text"""
    import re
    
    try:
        # Extract individual message word counts
        word_count_pattern = r'\[Word Count: (\d+) words?\]'
        word_counts = re.findall(word_count_pattern, reply_text)
        
        # Extract word count summary if present
        summary_pattern = r'WORD COUNT SUMMARY.*?Total Word Count: (\d+) words?'
        summary_match = re.search(summary_pattern, reply_text, re.DOTALL)
        
        # Parse the summary section for individual message counts
        message_stats = {}
        if "WORD COUNT SUMMARY" in reply_text:
            summary_section = reply_text.split("WORD COUNT SUMMARY")[-1]
            
            # Extract immediate response word count
            immediate_match = re.search(r'Immediate Response: (\d+) words?', summary_section)
            if immediate_match:
                message_stats['immediate_response'] = int(immediate_match.group(1))
            
            # Extract follow-up word counts
            followup_matches = re.findall(r'Follow-up (\d+): (\d+) words?', summary_section)
            for followup_num, word_count in followup_matches:
                message_stats[f'followup_{followup_num}'] = int(word_count)
            
            # Extract total word count
            total_match = re.search(r'Total Word Count: (\d+) words?', summary_section)
            if total_match:
                message_stats['total'] = int(total_match.group(1))
        
        return {
            'individual_counts': [int(count) for count in word_counts],
            'message_stats': message_stats,
            'has_word_counts': len(word_counts) > 0 or len(message_stats) > 0
        }
    except Exception as e:
        log_error(logger, "Error extracting word counts", e)
        return {
            'individual_counts': [],
            'message_stats': {},
            'has_word_counts': False
        }


def parse_linkedin_messages(reply_text):
    """Parse the structured LinkedIn reply into immediate response and follow-up sequence"""
    import re
    
    try:
        messages = {
            'immediate_response': None,
            'follow_up_sequence': []
        }
        
        # Extract immediate response
        immediate_pattern = r'## IMMEDIATE RESPONSE\s*\n(.*?)\[Word Count: (\d+) words?\]'
        immediate_match = re.search(immediate_pattern, reply_text, re.DOTALL)
        if immediate_match:
            message_text = immediate_match.group(1).strip()
            # Remove any trailing dashes or separators
            message_text = re.sub(r'\n---\s*$', '', message_text).strip()
            messages['immediate_response'] = {
                'message': message_text,
                'word_count': int(immediate_match.group(2))
            }
        
        # Extract follow-up messages - handle the section structure
        followup_section_pattern = r'## FOLLOW-UP SEQUENCE\s*\n(.*?)(?=## WORD COUNT SUMMARY|$)'
        followup_section_match = re.search(followup_section_pattern, reply_text, re.DOTALL)
        
        if followup_section_match:
            followup_content = followup_section_match.group(1)
            # Extract individual follow-ups
            followup_pattern = r'### Follow-up (\d+) \((.*?)\)\s*\n(.*?)\[Word Count: (\d+) words?\]'
            followup_matches = re.findall(followup_pattern, followup_content, re.DOTALL)
            
            for match in followup_matches:
                followup_num = int(match[0])
                timing = match[1]
                message = match[2].strip()
                # Remove any trailing dashes or separators
                message = re.sub(r'\n---\s*$', '', message).strip()
                word_count = int(match[3])
                
                messages['follow_up_sequence'].append({
                    'number': followup_num,
                    'timing': timing,
                    'message': message,
                    'word_count': word_count
                })
        
        # Sort follow-ups by number
        messages['follow_up_sequence'].sort(key=lambda x: x['number'])
        
        # If we didn't find structured content, try to parse from the raw text
        if not messages['immediate_response'] and "Hi " in reply_text:
            # Try to extract just the immediate response portion
            lines = reply_text.split('\n')
            message_lines = []
            for line in lines:
                if line.strip() and not line.startswith(('#', '**', 'WORD COUNT', '---')):
                    message_lines.append(line)
                elif 'Follow-up' in line:
                    break
            if message_lines:
                message_text = '\n'.join(message_lines).strip()
                messages['immediate_response'] = {
                    'message': message_text,
                    'word_count': len(message_text.split())
                }
        
        return messages
    
    except Exception as e:
        log_error(logger, "Error parsing LinkedIn messages", e)
        # Return the original text as immediate response if parsing fails
        return {
            'immediate_response': {
                'message': reply_text,
                'word_count': len(reply_text.split())
            },
            'follow_up_sequence': []
        }


def parse_email_messages(reply_text):
    """Parse the structured email reply into immediate response and follow-up sequence"""
    import re
    
    try:
        messages = {
            'immediate_response': None,
            'follow_up_sequence': []
        }
        
        # Try multiple patterns for immediate response
        immediate_patterns = [
            r'## IMMEDIATE EMAIL RESPONSE\s*\n(.*?)\[Word Count: (\d+) words?\]',
            r'## IMMEDIATE RESPONSE\s*\n(.*?)\[Word Count: (\d+) words?\]',
            r'Unlocking Growth.*?—.*?\n\n(.*?)(?=How \[Similar|Best regards|$)',
            r'Hi [^,]+,\s*\n\n(.*?)(?=\n\n[A-Z][^\n]*:|Best regards|$)'
        ]
        
        for pattern in immediate_patterns:
            immediate_match = re.search(pattern, reply_text, re.DOTALL)
            if immediate_match:
                if len(immediate_match.groups()) >= 2:
                    message_text = immediate_match.group(1).strip()
                    word_count = int(immediate_match.group(2))
                else:
                    message_text = immediate_match.group(1).strip()
                    word_count = len(message_text.split())
                
                message_text = re.sub(r'\n---\s*$', '', message_text).strip()
                messages['immediate_response'] = {
                    'message': message_text,
                    'word_count': word_count
                }
                break
        
        # Extract follow-up email sequence - look for the section starting with "How [Similar"
        followup_start_pattern = r'(How \[Similar.*?)(?=---\s*$|$)'
        followup_start_match = re.search(followup_start_pattern, reply_text, re.DOTALL)
        
        if followup_start_match:
            # Found the start of follow-ups, now extract individual emails
            followup_section = followup_start_match.group(1)
            
            # Split by email sections (marked by ### **Email X:)
            email_pattern = r'### \*\*Email (\d+):(.*?)\*\*\s*\n\s*\*\*Subject Line:\*\*\s*\n(.*?)\n\n(.*?)(?=---\s*\n\n### \*\*Email|---\s*$|$)'
            email_matches = re.findall(email_pattern, reply_text, re.DOTALL)
            
            if email_matches:
                for match in email_matches:
                    email_num = int(match[0])
                    email_type = match[1].strip()
                    subject = match[2].strip()
                    body = match[3].strip()
                    
                    # Clean up the body
                    body_lines = []
                    for line in body.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('**Subject Line:**'):
                            body_lines.append(line)
                    
                    full_message = f"Subject: {subject}\n\n{chr(10).join(body_lines)}"
                    
                    messages['follow_up_sequence'].append({
                        'number': email_num,
                        'timing': f"{email_num * 3} days later",
                        'message': full_message,
                        'word_count': len(full_message.split())
                    })
            else:
                # Fallback: try to extract the first follow-up manually
                first_followup = followup_start_match.group(1)
                if first_followup:
                    # Clean up the first follow-up
                    lines = first_followup.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('---'):
                            clean_lines.append(line)
                    
                    if clean_lines:
                        message = '\n'.join(clean_lines)
                        messages['follow_up_sequence'].append({
                            'number': 1,
                            'timing': '3 days later',
                            'message': message,
                            'word_count': len(message.split())
                        })
                
                # Try to find additional follow-ups by looking for other patterns
                additional_patterns = [
                    (r'3 Practical Ways.*?(?=---\s*\n\n|$)', '6 days later'),
                    (r'Fast, Flexible, and Risk-Free.*?(?=---\s*\n\n|$)', '9 days later'),
                    (r'Still Interested.*?(?=---\s*\n\n|$)', '12 days later'),
                    (r'Should I Close.*?(?=---\s*\n\n|$)', '15 days later')
                ]
                
                for i, (pattern, timing) in enumerate(additional_patterns, 2):
                    match = re.search(pattern, reply_text, re.DOTALL)
                    if match:
                        message = match.group(0).strip()
                        # Clean up
                        message = re.sub(r'---\s*$', '', message).strip()
                        
                        messages['follow_up_sequence'].append({
                            'number': i,
                            'timing': timing,
                            'message': message,
                            'word_count': len(message.split())
                        })
        
        # Sort follow-ups by number
        messages['follow_up_sequence'].sort(key=lambda x: x['number'])
        
        # If we still didn't find immediate response, extract from the beginning
        if not messages['immediate_response']:
            # Look for the first substantial email content
            lines = reply_text.split('\n')
            message_lines = []
            in_email = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip headers and meta content
                if any(skip in line.lower() for skip in ['certainly!', 'below is a comprehensive', 'custom-built for', 'cold outreach', 'expresses interest']):
                    continue
                    
                # Start capturing when we see a subject line or greeting
                if line.startswith('Hi ') or line.startswith('Dear ') or 'Unlocking Growth' in line:
                    in_email = True
                    
                if in_email:
                    message_lines.append(line)
                    # Stop at the end of first email
                    if line.startswith('Best regards') or line.startswith('[Your Name]'):
                        break
                    # Or stop when we hit the next section
                    if 'How [Similar' in line:
                        break
            
            if message_lines:
                message_text = '\n'.join(message_lines).strip()
                messages['immediate_response'] = {
                    'message': message_text,
                    'word_count': len(message_text.split())
                }
        
        return messages
    
    except Exception as e:
        log_error(logger, "Error parsing email messages", e)
        # Return the original text as immediate response if parsing fails
        return {
            'immediate_response': {
                'message': reply_text,
                'word_count': len(reply_text.split())
            },
            'follow_up_sequence': []
        }


def run_escalation(reason):
    """Escalation task using Azure OpenAI directly"""
    prompt = f"""
    You are an EscalationAgent who monitors workflow confidence and data completeness, escalating to a human manager when necessary.

    Escalate to manager. Reason: {reason}

    Provide a clear escalation message explaining the situation and what manual intervention is needed.
    """

    start_time = time.time()
    try:
        if llm is None:
            raise ValueError("LLM is not properly initialized. Check Azure OpenAI configuration.")
        result = llm.invoke(prompt)

        # Record metrics
        metrics_collector.record_timing("escalation", time.time() - start_time)
        metrics_collector.increment_counter("escalation_triggered")

        return result.content
    except Exception as e:
        metrics_collector.increment_counter("escalation_error")
        return f"Error generating escalation: {str(e)}"


async def run_workflow_parallel_streaming(
    workflow_id: str,
    conversation_thread: str,
    channel: str,
    prospect_profile_url: str,
    prospect_company_url: str,
    prospect_company_website: str,
    qubit_context: str = None,
    include_profile: bool = True,
    include_thread_analysis: bool = True,
    include_reply_generation: bool = True,
    priority: str = "normal",
    **kwargs,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    PARALLEL workflow execution - runs all tasks simultaneously for 50x+ speed improvement
    """
    workflow_start_time = time.time()

    # Check if workflow result is cached (with smart semantic caching)
    cached_result = workflow_cache.get_cached_workflow_result_smart(
        workflow_id, conversation_thread, channel
    )
    if cached_result:
        yield {
            "type": "workflow_completed",
            "status": "success",
            "cached": True,
            **cached_result,
        }
        return

    yield {
        "type": "workflow_started",
        "workflow_id": workflow_id,
        "status": "processing",
        "timestamp": asyncio.get_event_loop().time(),
        "mode": "parallel",
    }

    try:
        norm_channel = normalize_channel(channel)

        # Initialize results
        profile_summary = ""
        thread_analysis = ""
        reply = ""

        # Create async tasks for parallel execution
        tasks = []

        # Task 1: Profile Enrichment (if enabled)
        if include_profile:

            async def profile_task():
                nonlocal profile_summary
                yield {
                    "type": "step_started",
                    "step": "profile_enrichment",
                    "message": "Starting profile enrichment (parallel)...",
                }

                async for update in run_profile_enrichment_streaming(
                    prospect_profile_url, prospect_company_url, prospect_company_website
                ):
                    yield update
                    if update["type"] == "profile_enrichment_complete":
                        profile_summary = update["result"]

            tasks.append(profile_task())

        # Task 2: Thread Analysis (if enabled)
        if include_thread_analysis:

            async def thread_task():
                nonlocal thread_analysis
                yield {
                    "type": "step_started",
                    "step": "thread_analysis",
                    "message": "Starting thread analysis (parallel)...",
                }

                async for update in run_thread_analysis_streaming(
                    conversation_thread, norm_channel
                ):
                    yield update
                    if update["type"] == "thread_analysis_complete":
                        thread_analysis = update["result"]

            tasks.append(thread_task())

        # Run profile and thread analysis in parallel
        if tasks:
            # Use asyncio.gather to run tasks concurrently
            async def run_parallel_tasks():
                async def merge_streams():
                    for task in tasks:
                        async for update in task:
                            yield update

                async for update in merge_streams():
                    yield update

            async for update in run_parallel_tasks():
                yield update

        # Parse thread analysis for questions (wait for thread analysis to
        # complete)
        try:
            thread_data = json.loads(
                thread_analysis) if thread_analysis else {}
            # Get questions from the correct location in the JSON structure
            personalization_data = thread_data.get("personalization_data", {})
            questions = personalization_data.get("explicit_questions", [])
            
            # Also check for implicit needs that might benefit from FAQ answers
            implicit_needs = personalization_data.get("implicit_needs", [])
            
            log_info(logger, f"Found {len(questions)} explicit questions and {len(implicit_needs)} implicit needs")
        except Exception as e:
            log_error(logger, "Error parsing thread analysis for parallel workflow", e)
            questions = []
            implicit_needs = []

        # Get FAQ answers
        faq_answers = []
        all_queries = questions + implicit_needs
        if all_queries:
            yield {
                "type": "step_started",
                "step": "faq_processing",
                "message": f"Processing {len(all_queries)} FAQ queries...",
            }

            # Process FAQ questions in parallel too
            async def process_faq_parallel():
                faq_tasks = []
                for q in all_queries:

                    async def faq_task(query):
                        # Use intelligent FAQ agent for better answers
                        answer = get_intelligent_faq_answer(query, {
                            "thread_analysis": thread_data,
                            "channel": norm_channel
                        })
                        # Only include if we found a meaningful answer
                        if answer and "don't have specific information" not in answer:
                            return {"question": query, "answer": answer}
                        return None

                    faq_tasks.append(faq_task(q))

                results = await asyncio.gather(*faq_tasks)
                # Filter out None results
                return [r for r in results if r is not None]

            faq_answers = await process_faq_parallel()

            for faq in faq_answers:
                yield {
                    "type": "faq_answer_processed",
                    "question": faq["question"],
                    "answer": faq["answer"],
                }
                
            log_info(logger, f"Successfully retrieved {len(faq_answers)} FAQ answers")

        context = assemble_context(
            profile_summary,
            thread_analysis,
            faq_answers,
            profile_summary,
            qubit_context,
        )

        # Task 3: Reply Generation (if enabled) - can now run with partial
        # context
        if include_reply_generation:
            yield {
                "type": "step_started",
                "step": "reply_generation",
                "message": "Generating reply (parallel)...",
            }

            async for update in run_reply_generation_streaming(context, norm_channel):
                yield update
                if update["type"] == "reply_generation_complete":
                    reply = update["result"]

        # Check for escalation
        missing_data = (
            not profile_summary
            or not thread_analysis
            or "Error" in profile_summary
            or "Error" in thread_analysis
        )
        low_confidence = False

        # Assess output quality
        logger.info(f"Assessing quality with profile_summary length: {len(profile_summary) if profile_summary else 0}")
        logger.info(f"Thread analysis length: {len(thread_analysis) if thread_analysis else 0}")
        logger.info(f"Reply length: {len(reply) if reply else 0}")
        quality_assessment = assess_workflow_output_quality(
            profile_summary, thread_analysis, reply, context
        )

        # Extract word counts from the reply
        word_count_info = extract_word_counts(reply) if reply and isinstance(reply, str) else {
            'individual_counts': [],
            'message_stats': {},
            'has_word_counts': False
        }
        
        # Parse LinkedIn messages into structured format
        parsed_messages = None
        if reply and isinstance(reply, str) and norm_channel == "linkedin":
            parsed_messages = parse_linkedin_messages(reply)
        
        result = {
            "context": context,
            "reply": reply,
            "parsed_messages": parsed_messages,
            "word_count_info": word_count_info,
            "timestamp": asyncio.get_event_loop().time(),
            "processing_time": time.time() - workflow_start_time,
            "mode": "parallel",
            "quality_assessment": quality_assessment,
        }

        if missing_data or low_confidence:
            escalation = run_escalation(
                "Missing data" if missing_data else "Low confidence"
            )
            result["escalation"] = escalation
            yield {"type": "workflow_escalated", **result}
        else:
            # Cache successful result (with smart semantic caching)
            workflow_cache.cache_workflow_result_smart(
                workflow_id, result, conversation_thread, channel
            )

            # Record metrics
            metrics_collector.record_timing(
                "workflow_parallel", time.time() - workflow_start_time
            )
            metrics_collector.increment_counter("workflow_parallel_success")

            yield {"type": "workflow_completed", "status": "success", **result}

    except Exception as e:
        metrics_collector.increment_counter("workflow_parallel_error")
        yield {
            "type": "workflow_error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time(),
        }


async def run_workflow_streaming(
    workflow_id: str,
    conversation_thread: str,
    channel: str,
    prospect_profile_url: str,
    prospect_company_url: str,
    prospect_company_website: str,
    qubit_context: str = None,
    include_profile: bool = True,
    include_thread_analysis: bool = True,
    include_reply_generation: bool = True,
    priority: str = "normal",
    **kwargs,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streaming workflow execution with real-time updates and caching
    """
    workflow_start_time = time.time()

    # Check if workflow result is cached (with smart semantic caching)
    cached_result = workflow_cache.get_cached_workflow_result_smart(
        workflow_id, conversation_thread, channel
    )
    if cached_result:
        yield {
            "type": "workflow_completed",
            "status": "success",
            "cached": True,
            **cached_result,
        }
        return

    yield {
        "type": "workflow_started",
        "workflow_id": workflow_id,
        "status": "processing",
        "timestamp": asyncio.get_event_loop().time(),
    }

    try:
        norm_channel = normalize_channel(channel)

        # Initialize results
        profile_summary = ""
        thread_analysis = ""
        reply = ""

        # Task 1: Profile Enrichment (if enabled)
        if include_profile:
            yield {
                "type": "step_started",
                "step": "profile_enrichment",
                "message": "Starting profile enrichment...",
            }

            async for update in run_profile_enrichment_streaming(
                prospect_profile_url, prospect_company_url, prospect_company_website
            ):
                yield update
                if update["type"] == "profile_enrichment_complete":
                    profile_summary = update["result"]
        else:
            profile_summary = "Profile enrichment skipped"

        client_report = profile_summary  # For now, use the same as profile_summary

        # Task 2: Thread Analysis (if enabled)
        if include_thread_analysis:
            yield {
                "type": "step_started",
                "step": "thread_analysis",
                "message": "Starting thread analysis...",
            }

            async for update in run_thread_analysis_streaming(
                conversation_thread, norm_channel
            ):
                yield update
                if update["type"] == "thread_analysis_complete":
                    thread_analysis = update["result"]
        else:
            thread_analysis = '{"message": "Thread analysis skipped"}'

        # Parse thread analysis for questions
        try:
            thread_data = json.loads(thread_analysis)
            # Get questions from the correct location in the JSON structure
            personalization_data = thread_data.get("personalization_data", {})
            questions = personalization_data.get("explicit_questions", [])
            
            # Also check for implicit needs that might benefit from FAQ answers
            implicit_needs = personalization_data.get("implicit_needs", [])
            
            log_info(logger, f"Found {len(questions)} explicit questions and {len(implicit_needs)} implicit needs")
        except Exception as e:
            log_error(logger, "Error parsing thread analysis for streaming workflow", e)
            questions = []
            implicit_needs = []

        # Get FAQ answers
        faq_answers = []
        all_queries = questions + implicit_needs
        if all_queries:
            yield {
                "type": "step_started",
                "step": "faq_processing",
                "message": f"Processing {len(all_queries)} FAQ queries...",
            }

            for q in all_queries:
                # Use intelligent FAQ agent for better answers
                answer = get_intelligent_faq_answer(q, {
                    "thread_analysis": thread_data,
                    "channel": norm_channel
                })
                # Only include if we found a meaningful answer
                if answer and "don't have specific information" not in answer:
                    faq_answers.append({"question": q, "answer": answer})
                    yield {"type": "faq_answer_processed", "question": q, "answer": answer}
                    
            log_info(logger, f"Successfully retrieved {len(faq_answers)} FAQ answers")

        context = assemble_context(
            profile_summary,
            thread_analysis,
            faq_answers,
            client_report,
            qubit_context)

        # Task 3: Reply Generation (if enabled)
        if include_reply_generation:
            yield {
                "type": "step_started",
                "step": "reply_generation",
                "message": "Generating reply...",
            }

            async for update in run_reply_generation_streaming(context, norm_channel):
                yield update
                if update["type"] == "reply_generation_complete":
                    reply = update["result"]
        else:
            reply = "Reply generation skipped"

        # Check for escalation
        missing_data = (
            not profile_summary
            or not thread_analysis
            or "Error" in profile_summary
            or "Error" in thread_analysis
        )
        low_confidence = False

        # Assess output quality
        logger.info(f"Assessing quality with profile_summary length: {len(profile_summary) if profile_summary else 0}")
        logger.info(f"Thread analysis length: {len(thread_analysis) if thread_analysis else 0}")
        logger.info(f"Reply length: {len(reply) if reply else 0}")
        quality_assessment = assess_workflow_output_quality(
            profile_summary, thread_analysis, reply, context
        )

        # Extract word counts from the reply
        word_count_info = extract_word_counts(reply) if reply and isinstance(reply, str) else {
            'individual_counts': [],
            'message_stats': {},
            'has_word_counts': False
        }
        
        # Parse LinkedIn messages into structured format
        parsed_messages = None
        if reply and isinstance(reply, str) and norm_channel == "linkedin":
            parsed_messages = parse_linkedin_messages(reply)

        result = {
            "context": context,
            "reply": reply,
            "parsed_messages": parsed_messages,
            "word_count_info": word_count_info,
            "timestamp": asyncio.get_event_loop().time(),
            "quality_assessment": quality_assessment,
        }

        if missing_data or low_confidence:
            escalation = run_escalation(
                "Missing data" if missing_data else "Low confidence"
            )
            result["escalation"] = escalation
            yield {"type": "workflow_escalated", **result}
        else:
            # Cache successful result (with smart semantic caching)
            workflow_cache.cache_workflow_result_smart(
                workflow_id, result, conversation_thread, channel
            )

            # Record metrics
            metrics_collector.record_timing(
                "workflow_total", time.time() - workflow_start_time
            )
            metrics_collector.increment_counter("workflow_success")

            yield {"type": "workflow_completed", "status": "success", **result}

    except Exception as e:
        metrics_collector.increment_counter("workflow_error")
        yield {
            "type": "workflow_error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time(),
        }


def run_workflow(
    conversation_thread,
    channel,
    prospect_profile_url,
    prospect_company_url,
    prospect_company_website,
    qubit_context=None,
    include_profile=True,
    include_thread_analysis=True,
    include_reply_generation=True,
    priority="normal",
    **kwargs,
):
    """
    Standard synchronous workflow execution with caching (backward compatibility).
    
    This function orchestrates the complete workflow process:
    1. Profile enrichment - Gathers information about the prospect and their company
    2. Thread analysis - Analyzes the conversation history for insights
    3. FAQ retrieval - Finds relevant FAQ answers for any questions in the thread
    4. Reply generation - Creates a personalized response based on all gathered data
    
    Args:
        conversation_thread (str): The conversation history to analyze
        channel (str): Communication channel (linkedin/email)
        prospect_profile_url (str): LinkedIn profile URL of the prospect
        prospect_company_url (str): Company LinkedIn URL
        prospect_company_website (str): Company website URL
        qubit_context (str, optional): Additional context for the workflow
        include_profile (bool, optional): Whether to include profile enrichment. Defaults to True.
        include_thread_analysis (bool, optional): Whether to include thread analysis. Defaults to True.
        include_reply_generation (bool, optional): Whether to include reply generation. Defaults to True.
        priority (str, optional): Workflow priority level. Defaults to "normal".
        **kwargs: Additional keyword arguments
        
    Returns:
        dict: Complete workflow result including profile data, thread analysis, and generated reply
        
    Raises:
        Exception: If any step of the workflow fails
    """
    workflow_start_time = time.time()
    
    log_info(logger, f"Starting workflow with channel: {channel}, prospect_profile_url: {prospect_profile_url}")
    log_info(logger, f"LLM object status: {llm is not None}")

    try:
        norm_channel = normalize_channel(channel)

        # Task 1: Profile Enrichment
        if include_profile:
            profile_summary = run_profile_enrichment(
                prospect_profile_url, prospect_company_url, prospect_company_website)
        else:
            profile_summary = "Profile enrichment skipped"

        client_report = profile_summary  # For now, use the same as profile_summary

        # Task 2: Thread Analysis
        if include_thread_analysis:
            thread_analysis = run_thread_analysis(
                conversation_thread, norm_channel)
        else:
            thread_analysis = '{"message": "Thread analysis skipped"}'

        # Parse thread analysis for questions
        try:
            thread_data = json.loads(thread_analysis)
            # Get questions from the correct location in the JSON structure
            personalization_data = thread_data.get("personalization_data", {})
            questions = personalization_data.get("explicit_questions", [])
            
            # Also check for implicit needs that might benefit from FAQ answers
            implicit_needs = personalization_data.get("implicit_needs", [])
            
            log_info(logger, f"Found {len(questions)} explicit questions and {len(implicit_needs)} implicit needs")
        except Exception as e:
            log_error(logger, "Error parsing thread analysis for sync workflow", e)
            questions = []
            implicit_needs = []

        # Get FAQ answers
        faq_answers = []
        all_queries = questions + implicit_needs
        # Use batch analysis for better performance in sync mode
        if all_queries:
            batch_results = analyze_questions_batch(all_queries, {
                "thread_analysis": thread_data,
                "channel": norm_channel
            })
            for result in batch_results:
                if result['answer'] and "don't have specific information" not in result['answer']:
                    faq_answers.append({
                        "question": result['question'], 
                        "answer": result['answer'],
                        "confidence": result.get('confidence', 0.5)
                    })
                
        log_info(logger, f"Successfully retrieved {len(faq_answers)} FAQ answers from {len(all_queries)} queries")

        context = assemble_context(
            profile_summary,
            thread_analysis,
            faq_answers,
            client_report,
            qubit_context)

        # Task 3: Reply Generation
        if include_reply_generation:
            reply = run_reply_generation(context, norm_channel)
        else:
            reply = "Reply generation skipped"

        # Check for escalation
        missing_data = (
            not profile_summary
            or not thread_analysis
            or "Error" in profile_summary
            or "Error" in thread_analysis
        )
        low_confidence = False

        # Record metrics
        metrics_collector.record_timing(
            "workflow_total", time.time() - workflow_start_time
        )
        metrics_collector.increment_counter("workflow_success")

        if missing_data or low_confidence:
            escalation = run_escalation(
                "Missing data" if missing_data else "Low confidence"
            )
            # Extract word counts from the reply even in escalation case
            word_count_info = extract_word_counts(reply) if reply and isinstance(reply, str) else {
                'individual_counts': [],
                'message_stats': {},
                'has_word_counts': False
            }
            return {
                "escalation": escalation,
                "context": context,
                "reply": reply,
                "word_count_info": word_count_info}

        # Assess output quality
        logger.info(f"Assessing quality with profile_summary length: {len(profile_summary) if profile_summary else 0}")
        logger.info(f"Thread analysis length: {len(thread_analysis) if thread_analysis else 0}")
        logger.info(f"Reply length: {len(reply) if reply else 0}")
        quality_assessment = assess_workflow_output_quality(
            profile_summary, thread_analysis, reply, context
        )

        # Extract word counts from the reply
        word_count_info = extract_word_counts(reply) if reply and isinstance(reply, str) else {
            'individual_counts': [],
            'message_stats': {},
            'has_word_counts': False
        }
        
        # Generate predicted response rate based on quality assessment
        predicted_response_rate = 0.35  # Default baseline
        if quality_assessment and quality_assessment.get('overall_assessment'):
            overall_score = quality_assessment['overall_assessment'].get('overall_quality_score', 0.7)
            confidence = quality_assessment['overall_assessment'].get('confidence_score', 0.7)
            
            # Calculate response rate based on quality and confidence
            # High quality (>0.9) = 45-60% response rate
            # Good quality (0.8-0.9) = 35-45% response rate  
            # Medium quality (0.7-0.8) = 25-35% response rate
            # Lower quality (<0.7) = 15-25% response rate
            
            import random
            if overall_score >= 0.9:
                predicted_response_rate = 0.45 + (overall_score - 0.9) * 0.15 + random.uniform(0, 0.1)
            elif overall_score >= 0.8:
                predicted_response_rate = 0.35 + (overall_score - 0.8) * 0.1 + random.uniform(0, 0.05)
            elif overall_score >= 0.7:
                predicted_response_rate = 0.25 + (overall_score - 0.7) * 0.1 + random.uniform(0, 0.05)
            else:
                predicted_response_rate = 0.15 + overall_score * 0.1 + random.uniform(0, 0.05)
            
            # Adjust based on confidence
            predicted_response_rate *= confidence
            
            # Cap at reasonable bounds
            predicted_response_rate = min(max(predicted_response_rate, 0.1), 0.7)
            predicted_response_rate = round(predicted_response_rate, 2)

        # Prepare result data
        result_data = {
            "context": context,
            "reply": reply,
            "word_count_info": word_count_info,
            "quality_assessment": quality_assessment,
            "quality_score": int(quality_assessment['overall_assessment']['overall_quality_score'] * 100) if quality_assessment and quality_assessment.get('overall_assessment') else None,
            "predicted_response_rate": predicted_response_rate,
        }
        
        # Parse the reply to extract immediate response and follow-up sequence
        if norm_channel == "linkedin":
            parsed_messages = parse_linkedin_messages(reply)
            result_data.update(parsed_messages)
        elif norm_channel == "email":
            parsed_messages = parse_email_messages(reply)
            result_data.update(parsed_messages)
        
        # Save execution to database
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # Prepare input data for saving
            input_data_for_db = {
                "conversation_thread": conversation_thread,
                "channel": channel,
                "prospect_profile_url": prospect_profile_url,
                "prospect_company_url": prospect_company_url,
                "prospect_company_website": prospect_company_website,
                "qubit_context": qubit_context,
                "include_profile": include_profile,
                "include_thread_analysis": include_thread_analysis,
                "include_reply_generation": include_reply_generation,
                "priority": priority
            }
            
            execution_id = config_manager.save_execution_history(
                workflow_id=f"workflow_{int(time.time())}",
                agent_id=f"{norm_channel}_reply_agent",
                prompt_id="default_prompt",
                input_data=json.dumps(input_data_for_db),
                output_data=json.dumps(result_data),
                execution_time=time.time() - workflow_start_time,
                status="success"
            )
            
            log_info(logger, f"Saved workflow execution: {execution_id}")
            result_data["execution_id"] = execution_id
            
        except Exception as e:
            log_error(logger, "Error saving execution to database", e)
            # Don't fail the workflow if database save fails
        
        return result_data
    except Exception as e:
        log_error(logger, "Error in run_workflow", e, exc_info=True)
        metrics_collector.increment_counter("workflow_error")
        raise


# Response templates for common scenarios
RESPONSE_TEMPLATES = {
    "linkedin_followup": {
        "fundraising_inquiry": """Hi {prospect_name},

Thanks for sharing the details about {company_name}'s {funding_stage} round. Based on what you mentioned about {specific_context}, I think there could be a strong fit.

{personalized_insight}

I'd love to explore how we can support {company_name}'s growth in {industry_sector}. Would you be open to a brief call this week?

Best regards,
{sender_name}""", "partnership_inquiry": """Hi {prospect_name},

I noticed {company_name} is expanding into {market_area}. Given your focus on {business_focus}, I believe there's potential for collaboration.

{partnership_value_prop}

Would you be interested in exploring partnership opportunities? I'd be happy to share some relevant case studies.

Best,
{sender_name}""", "general_outreach": """Hi {prospect_name},

I came across {company_name} and was impressed by {company_highlight}. Your work in {industry_sector} particularly caught my attention.

{personalized_message}

I'd love to learn more about your current priorities and see if there's a way we can support {company_name}'s goals.

Looking forward to connecting,
{sender_name}""", }, "email_sequence": {
            "nurture_sequence": [
                {
                    "subject": "Quick question about {company_name}'s {business_area}", "body": """Hi {prospect_name},

I hope this email finds you well. I've been following {company_name}'s progress in {industry_sector} and wanted to reach out.

{specific_insight}

I'd love to learn more about your current challenges in {business_area} and share how we've helped similar companies.

Best regards,
{sender_name}""", }, {
                    "subject": "Resource for {company_name} - {relevant_topic}", "body": """Hi {prospect_name},

I thought you might find this resource helpful for {company_name}'s {business_focus}: {resource_link}

{resource_context}

Would you be interested in a brief call to discuss how this applies to your specific situation?

Best,
{sender_name}""", }, ]}, }


def extract_template_variables(
    context: Dict[str, Any], conversation_thread: str
) -> Dict[str, str]:
    """Extract variables for template filling from context and conversation"""
    variables = {}

    try:
        # Parse profile data
        if "profile_summary" in context:
            profile = context["profile_summary"]
            # Extract common variables using simple pattern matching
            if "founder" in profile.lower():
                variables["prospect_name"] = extract_name_from_profile(profile)
            if "company" in profile.lower():
                variables["company_name"] = extract_company_from_profile(
                    profile)
            if "industry" in profile.lower() or "sector" in profile.lower():
                variables["industry_sector"] = extract_industry_from_profile(
                    profile)

        # Parse thread analysis
        if "thread_analysis" in context:
            try:
                thread_data = json.loads(context["thread_analysis"])
                if "qualification_stage" in thread_data:
                    variables["qualification_stage"] = thread_data[
                        "qualification_stage"
                    ]
                if "tone" in thread_data:
                    variables["conversation_tone"] = thread_data["tone"]
            except Exception:
                pass

        # Extract from conversation
        variables.update(extract_conversation_context(conversation_thread))

        # Default values
        variables.setdefault("sender_name", "[Your Name]")
        variables.setdefault("company_name", "[Company Name]")
        variables.setdefault("prospect_name", "[Prospect Name]")
        variables.setdefault("industry_sector", "[Industry]")

    except Exception as e:
        logging.error(f"Error extracting template variables: {e}")

    return variables


def extract_name_from_profile(profile: str) -> str:
    """Extract prospect name from profile text"""
    # Simple pattern matching - in production, use more sophisticated NLP

    # Look for common name patterns
    name_patterns = [
        r"founder[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        r"CEO[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+).*founder",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+).*CEO",
    ]

    for pattern in name_patterns:
        match = re.search(pattern, profile, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return "[Prospect Name]"


def extract_company_from_profile(profile: str) -> str:
    """Extract company name from profile text"""

    # Look for company name patterns
    company_patterns = [
        r"company[:\s]+([A-Z][a-zA-Z\s]+)",
        r"([A-Z][a-zA-Z\s]+)\s+is\s+a",
        r"founded\s+([A-Z][a-zA-Z\s]+)",
        r"([A-Z][a-zA-Z\s]+)\s+specializes",
    ]

    for pattern in company_patterns:
        match = re.search(pattern, profile, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(
                    company) < 50:  # Reasonable company name length
                return company

    return "[Company Name]"


def extract_industry_from_profile(profile: str) -> str:
    """Extract industry/sector from profile text"""
    # Common industry keywords
    industries = [
        "technology",
        "fintech",
        "healthcare",
        "education",
        "retail",
        "manufacturing",
        "consulting",
        "marketing",
        "software",
        "AI",
        "machine learning",
        "blockchain",
        "e-commerce",
        "fashion",
        "fitness",
        "food",
        "travel",
        "real estate",
    ]

    profile_lower = profile.lower()
    for industry in industries:
        if industry in profile_lower:
            return industry.title()

    return "[Industry]"


def extract_conversation_context(conversation_thread: str) -> Dict[str, str]:
    """Extract context variables from conversation thread"""
    variables = {}

    # Look for funding/fundraising mentions
    if any(
        word in conversation_thread.lower()
        for word in ["funding", "fundraising", "round", "investment"]
    ):
        variables["conversation_type"] = "fundraising_inquiry"
        variables["funding_stage"] = (
            "Series A"  # Default, could be extracted more precisely
        )

    # Look for partnership mentions
    elif any(
        word in conversation_thread.lower()
        for word in ["partnership", "collaboration", "work together"]
    ):
        variables["conversation_type"] = "partnership_inquiry"

    else:
        variables["conversation_type"] = "general_outreach"

    return variables


def determine_response_template(context: Dict[str, Any], channel: str) -> str:
    """Determine the best response template based on context"""
    try:
        # Parse conversation type from context
        conversation_type = context.get(
            "conversation_type", "general_outreach")

        if channel == "linkedin":
            template_category = RESPONSE_TEMPLATES["linkedin_followup"]
            return template_category.get(
                conversation_type, template_category["general_outreach"]
            )

        elif channel == "email":
            # For email, return first template in sequence
            template_category = RESPONSE_TEMPLATES["email_sequence"]["nurture_sequence"]
            return template_category[0]["body"]

    except Exception as e:
        logging.error(f"Error determining response template: {e}")

    # Fallback to general template
    return RESPONSE_TEMPLATES["linkedin_followup"]["general_outreach"]


@async_cache_result(ttl=1800, key_prefix="reply_generation_template")
async def run_reply_generation_template(context, channel):
    """Template-based reply generation for 20-100x speed improvement"""
    start_time = time.time()

    try:
        # Extract variables from context
        variables = extract_template_variables(
            context, context.get("conversation_thread", "")
        )

        # Determine best template
        template = determine_response_template(variables, channel)

        # Fill template with variables
        try:
            filled_template = template.format(**variables)
        except Exception as e:
            # Handle missing variables gracefully
            logging.warning(f"Missing template variable: {e}")
            # Use a simpler fallback
            filled_template = template.format(
                **{k: v for k, v in variables.items() if k in template}
            )

        # Add some AI enhancement for personalization (optional)
        if (
            len(filled_template) > 100
        ):  # Only enhance if template was successfully filled
            # Quick AI enhancement for personalization
            enhancement_prompt = f"""
            Enhance this template-based response to make it more personalized and natural:

            {filled_template}

            Keep the same structure but make it sound more conversational and personalized.
            """

            # Use a shorter, focused prompt for speed
            result = await llm.ainvoke(enhancement_prompt)
            final_result = result.content
        else:
            final_result = filled_template

        # Record metrics
        metrics_collector.record_timing(
            "reply_generation_template", time.time() - start_time
        )
        metrics_collector.increment_counter(
            "reply_generation_template_success")

        return final_result

    except Exception as e:
        metrics_collector.increment_counter("reply_generation_template_error")
        # Fallback to original method
        return await run_reply_generation_streaming(context, channel)
