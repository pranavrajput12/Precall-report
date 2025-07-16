from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="CrewAI Workflow API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data
AGENTS = [
    {
        "id": "1",
        "name": "LinkedIn Research Agent",
        "role": "researcher",
        "goal": "Research LinkedIn profiles and company information",
        "backstory": "Expert at gathering professional information from LinkedIn",
        "tools": ["linkedin_scraper", "company_analyzer"],
        "model": "gpt-4",
        "status": "active"
    },
    {
        "id": "2", 
        "name": "Reply Generation Agent",
        "role": "writer",
        "goal": "Generate personalized LinkedIn replies",
        "backstory": "Skilled at crafting professional, engaging LinkedIn messages",
        "tools": ["text_generator", "sentiment_analyzer"],
        "model": "gpt-4",
        "status": "active"
    },
    {
        "id": "3",
        "name": "Quality Assurance Agent", 
        "role": "reviewer",
        "goal": "Review and improve generated replies",
        "backstory": "Ensures all replies meet quality standards",
        "tools": ["quality_checker", "grammar_checker"],
        "model": "claude-3",
        "status": "active"
    }
]

WORKFLOWS = [
    {
        "id": "default_workflow",
        "name": "LinkedIn Reply Generation",
        "description": "Generate personalized LinkedIn replies",
        "status": "active",
        "steps": [
            {
                "id": "research_step",
                "name": "Research Profile",
                "agent_id": "1",
                "order": 1
            },
            {
                "id": "generate_step", 
                "name": "Generate Reply",
                "agent_id": "2",
                "order": 2
            },
            {
                "id": "review_step",
                "name": "Review Quality",
                "agent_id": "3", 
                "order": 3
            }
        ]
    }
]

MODELS = [
    {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "openai",
        "type": "chat",
        "status": "active",
        "config": {
            "temperature": 0.3,
            "max_tokens": 2048
        }
    },
    {
        "id": "claude-3",
        "name": "Claude-3",
        "provider": "anthropic",
        "type": "chat",
        "status": "active",
        "config": {
            "temperature": 0.3,
            "max_tokens": 2048
        }
    }
]

MODEL_ASSIGNMENTS = [
    {"agent_id": "1", "model_id": "gpt-4"},
    {"agent_id": "2", "model_id": "gpt-4"},
    {"agent_id": "3", "model_id": "claude-3"}
]

TOOLS = [
    {
        "id": "linkedin_scraper",
        "name": "LinkedIn Scraper",
        "description": "Extract profile information from LinkedIn",
        "status": "active"
    },
    {
        "id": "company_analyzer",
        "name": "Company Analyzer",
        "description": "Analyze company information and trends",
        "status": "active"
    },
    {
        "id": "text_generator",
        "name": "Text Generator",
        "description": "Generate personalized text content",
        "status": "active"
    }
]

PROMPTS = [
    {
        "id": "profile_enrichment_prompt",
        "name": "Profile Enrichment",
        "description": "Enhanced profile enrichment with strategic sales intelligence",
        "template": """You are an elite ProfileEnricher agent specializing in deep sales intelligence and strategic business analysis. Your goal is to provide actionable insights that enable highly personalized, value-driven outreach.

SOURCES TO ANALYZE:
Prospect LinkedIn: {prospect_profile_url}
Company LinkedIn: {prospect_company_url}
Company Website: {prospect_company_website}

PROVIDE A COMPREHENSIVE ANALYSIS WITH THESE SECTIONS:

## PROSPECT INTELLIGENCE
- Full name, current role, and professional title
- Career progression and key achievements
- Educational background and certifications
- Industry expertise and specializations
- Recent activity and engagement patterns
- Personal interests and networking behavior
- Influence level and thought leadership indicators

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

Format your response as a detailed, actionable intelligence report that enables highly personalized and strategic outreach.""",
        "variables": ["prospect_profile_url", "prospect_company_url", "prospect_company_website"],
        "agent_id": "1",
        "category": "research",
        "channel": "linkedin",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "linkedin_thread_analysis_prompt",
        "name": "LinkedIn Thread Analysis",
        "description": "Enhanced LinkedIn conversation analysis with strategic sales insights",
        "template": """You are an elite LinkedInThreadAnalyzer agent with deep expertise in sales psychology, conversation analysis, and strategic communication patterns. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

CONVERSATION THREAD TO ANALYZE:
{conversation_thread}

PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

{
    "conversation_overview": {
        "participant_count": "number of people in conversation",
        "message_count": "total messages exchanged",
        "conversation_duration": "timespan of conversation",
        "conversation_type": "cold_outreach|warm_introduction|follow_up|referral"
    },
    "qualification_analysis": {
        "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
        "buying_signals": ["list of specific buying signals observed"],
        "pain_points_mentioned": ["explicit or implicit pain points"],
        "budget_indicators": ["any budget or financial discussions"],
        "timeline_indicators": ["urgency signals or timeline mentions"],
        "authority_level": "decision_maker|influencer|user|researcher"
    },
    "conversation_intelligence": {
        "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent",
        "engagement_level": "high|medium|low",
        "response_time_pattern": "immediate|delayed|inconsistent",
        "communication_style": "direct|diplomatic|analytical|relationship_focused",
        "decision_making_signals": ["indicators of decision-making authority or process"]
    },
    "strategic_insights": {
        "key_interests": ["topics that generated most engagement"],
        "objections_raised": ["concerns or pushback mentioned"],
        "value_drivers": ["what seems to motivate the prospect"],
        "competitive_mentions": ["any competitor references"],
        "next_best_actions": ["recommended follow-up strategies"]
    },
    "personalization_data": {
        "conversation_highlights": ["key moments or quotes to reference"],
        "shared_interests": ["common ground identified"],
        "professional_context": ["role-specific insights"],
        "company_context": ["company-specific talking points"]
    },
    "competitive_intelligence": {
        "current_solutions": ["existing tools or providers mentioned"],
        "satisfaction_level": "high|medium|low|unknown",
        "switching_indicators": ["signs of willingness to change"],
        "decision_criteria": ["factors important to prospect"]
    },
    "follow_up_strategy": {
        "recommended_approach": "consultative|educational|social_proof|urgency",
        "optimal_timing": "immediate|within_24h|within_week|scheduled",
        "key_messages": ["main points to emphasize"],
        "success_probability": "high|medium|low",
        "risk_factors": ["potential obstacles or concerns"]
    },
    "explicit_questions": ["direct questions asked by prospect that need answers"]
}

Ensure all analysis is based on actual conversation content and provide specific examples where possible.""",
        "variables": ["conversation_thread"],
        "agent_id": "2",
        "category": "generation",
        "channel": "linkedin",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "email_thread_analysis_prompt",
        "name": "Email Thread Analysis",
        "description": "Enhanced email conversation analysis with strategic sales insights",
        "template": """You are an elite EmailThreadAnalyzer agent with deep expertise in email communication patterns, sales psychology, and strategic analysis. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

EMAIL THREAD TO ANALYZE:
{conversation_thread}

PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

{
    "conversation_overview": {
        "participant_count": "number of people in email thread",
        "message_count": "total emails exchanged",
        "conversation_duration": "timespan of email thread",
        "conversation_type": "cold_outreach|warm_introduction|follow_up|referral|internal_discussion"
    },
    "qualification_analysis": {
        "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
        "buying_signals": ["list of specific buying signals observed"],
        "pain_points_mentioned": ["explicit or implicit pain points"],
        "budget_indicators": ["any budget or financial discussions"],
        "timeline_indicators": ["urgency signals or timeline mentions"],
        "authority_level": "decision_maker|influencer|user|researcher|gatekeeper"
    },
    "conversation_intelligence": {
        "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent|formal",
        "engagement_level": "high|medium|low",
        "response_time_pattern": "immediate|delayed|inconsistent|business_hours",
        "communication_style": "direct|diplomatic|analytical|relationship_focused|technical",
        "email_signatures": ["insights from email signatures and titles"]
    },
    "strategic_insights": {
        "key_interests": ["topics that generated most engagement"],
        "objections_raised": ["concerns or pushback mentioned"],
        "value_drivers": ["what seems to motivate the prospect"],
        "competitive_mentions": ["any competitor references"],
        "next_best_actions": ["recommended follow-up strategies"],
        "stakeholder_involvement": ["other people mentioned or CC'd"]
    },
    "personalization_data": {
        "conversation_highlights": ["key moments or quotes to reference"],
        "shared_interests": ["common ground identified"],
        "professional_context": ["role-specific insights"],
        "company_context": ["company-specific talking points"],
        "technical_requirements": ["specific technical needs mentioned"]
    },
    "competitive_intelligence": {
        "current_solutions": ["existing tools or providers mentioned"],
        "satisfaction_level": "high|medium|low|unknown",
        "switching_indicators": ["signs of willingness to change"],
        "decision_criteria": ["factors important to prospect"],
        "evaluation_process": ["procurement or evaluation process insights"]
    },
    "follow_up_strategy": {
        "recommended_approach": "consultative|educational|social_proof|urgency|technical_demo",
        "optimal_timing": "immediate|within_24h|within_week|scheduled|after_event",
        "key_messages": ["main points to emphasize"],
        "success_probability": "high|medium|low",
        "risk_factors": ["potential obstacles or concerns"],
        "escalation_opportunities": ["chances to involve senior stakeholders"]
    },
    "explicit_questions": ["direct questions asked by prospect that need answers"]
}

Ensure all analysis is based on actual email content and provide specific examples where possible.""",
        "variables": ["conversation_thread"],
        "agent_id": "2",
        "category": "generation",
        "channel": "email",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "linkedin_reply_generation_prompt",
        "name": "LinkedIn Reply Generation",
        "description": "Generate compelling LinkedIn replies with strategic sales psychology",
        "template": """You are an elite LinkedInReplyGenerator agent with deep expertise in LinkedIn communication, sales psychology, and relationship building. Your goal is to create compelling, personalized LinkedIn messages that drive engagement and move prospects through the sales funnel.

CONTEXT AND INTELLIGENCE:
{context}

GENERATE A COMPREHENSIVE LINKEDIN RESPONSE STRATEGY WITH THESE COMPONENTS:

## IMMEDIATE RESPONSE
Craft a personalized, engaging LinkedIn message that:
- Acknowledges specific details from their profile or recent activity
- Demonstrates genuine understanding of their business challenges
- Provides immediate value (insight, resource, or connection)
- Includes a clear, compelling call-to-action
- Uses LinkedIn's conversational tone and format
- References specific details that show you've done your research

## FOLLOW-UP SEQUENCE (3-5 messages)
Design a strategic LinkedIn message sequence that:
- Builds on the initial conversation momentum
- Provides additional value at each touchpoint
- Addresses potential objections proactively
- Includes social proof and credibility indicators
- Maintains engagement without being pushy
- Escalates appropriately toward a call or meeting
- Varies content types (educational, social proof, urgency, etc.)

## PERSONALIZATION ELEMENTS
Incorporate these LinkedIn-specific personalization strategies:
- Reference their recent posts or company updates
- Mention mutual connections or shared experiences
- Use industry-specific language and terminology
- Address their specific role and responsibilities
- Connect to their company's current priorities or challenges
- Include relevant case studies from similar companies in their industry

## VALUE PROPOSITIONS
Highlight value propositions that:
- Directly address their expressed or implied pain points
- Demonstrate clear ROI and business impact
- Include specific metrics and success stories
- Position your solution as uniquely suited to their needs
- Create urgency through time-sensitive opportunities

## LINKEDIN ENGAGEMENT TACTICS
Use proven LinkedIn engagement techniques:
- Compelling opening lines that grab attention
- Scannable format with short paragraphs and bullet points
- Clear calls-to-action with specific next steps
- Professional yet conversational tone
- Strategic use of LinkedIn features (polls, documents, etc.)
- Social proof and credibility indicators

## MESSAGE SEQUENCE STRUCTURE
Structure each message with:
- Personalized greeting using their name
- Value-driven opening that references their interests
- Clear main message with specific insights
- Strong call-to-action with easy next steps
- Professional closing
- Strategic follow-up timing

FORMAT REQUIREMENTS:
- Keep messages concise (LinkedIn's character limits)
- Use professional LinkedIn messaging format
- Include specific conversation starters
- Provide optimal timing between messages
- Structure each message with clear purpose

TONE AND STYLE:
- Professional and authoritative
- Helpful and consultative
- Confident but not pushy
- Authentic and genuine
- Results-focused and data-driven

Generate a complete LinkedIn message sequence strategy that maximizes response rates, engagement, and conversion toward a business conversation.""",
        "variables": ["context"],
        "agent_id": "2",
        "category": "generation",
        "channel": "linkedin",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "email_reply_generation_prompt",
        "name": "Email Reply Generation",
        "description": "Generate compelling email sequences with strategic sales psychology",
        "template": """You are an elite EmailReplyGenerator agent with deep expertise in email marketing, sales psychology, and multi-touch communication strategies. Your goal is to create compelling, highly personalized email sequences that drive engagement and move prospects through the sales funnel.

CONTEXT AND INTELLIGENCE:
{context}

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

Generate a complete email sequence strategy that maximizes open rates, engagement, and conversion toward a business conversation.""",
        "variables": ["context"],
        "agent_id": "2",
        "category": "generation",
        "channel": "email",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "quality_assurance_prompt",
        "name": "Quality Assurance Review",
        "description": "Comprehensive quality review with strategic sales optimization",
        "template": """You are an elite QualityAssurance agent with deep expertise in sales communication, persuasion psychology, and conversion optimization. Your goal is to ensure all outreach messages meet the highest standards of professionalism, effectiveness, and strategic alignment.

MESSAGE TO REVIEW:
{message_content}

CONTEXT AND INTELLIGENCE:
{context}

PROVIDE A COMPREHENSIVE QUALITY ANALYSIS WITH THESE SECTIONS:

## QUALITY ASSESSMENT
Evaluate the message across these dimensions:
- **Clarity**: Is the message clear and easy to understand?
- **Professionalism**: Does it maintain appropriate business tone?
- **Personalization**: How well is it tailored to the specific prospect?
- **Value Proposition**: Is the value clearly articulated?
- **Call-to-Action**: Is the next step clear and compelling?
- **Grammar & Style**: Are there any errors or improvements needed?

## STRATEGIC ALIGNMENT
Assess strategic effectiveness:
- **Audience Fit**: How well does it match the prospect's profile?
- **Timing**: Is the approach appropriate for their stage?
- **Channel Optimization**: Is it optimized for the communication channel?
- **Competitive Positioning**: How does it differentiate from competitors?
- **Objection Handling**: Does it address potential concerns?

## PERSUASION PSYCHOLOGY
Evaluate psychological effectiveness:
- **Attention Grabbing**: Does it capture interest immediately?
- **Credibility Building**: Are trust signals effectively used?
- **Emotional Resonance**: Does it connect on an emotional level?
- **Social Proof**: Are credibility indicators well-placed?
- **Urgency Creation**: Is appropriate urgency conveyed?
- **Reciprocity**: Does it provide value before asking?

## CONVERSION OPTIMIZATION
Analyze conversion potential:
- **Response Likelihood**: How likely is the prospect to respond?
- **Engagement Quality**: Will it drive meaningful conversation?
- **Meeting Potential**: Does it move toward a business discussion?
- **Relationship Building**: Does it strengthen the connection?
- **Brand Representation**: Does it reflect well on the company?

## SPECIFIC IMPROVEMENTS
Provide actionable recommendations:
- **Content Enhancements**: Specific wording improvements
- **Structure Optimization**: Better organization suggestions
- **Personalization Opportunities**: Additional customization ideas
- **Value Amplification**: Ways to strengthen the value proposition
- **CTA Optimization**: Improvements to the call-to-action

## RISK ASSESSMENT
Identify potential issues:
- **Compliance Concerns**: Any legal or regulatory issues
- **Brand Risks**: Potential negative brand implications
- **Relationship Risks**: Could it damage the relationship?
- **Competitive Risks**: Does it reveal sensitive information?
- **Timing Risks**: Is the timing appropriate?

## FINAL RECOMMENDATION
Provide overall assessment:
- **Quality Score**: Rate 1-10 with justification
- **Approval Status**: Approve, Revise, or Reject
- **Key Strengths**: What works well
- **Critical Issues**: Must-fix problems
- **Optional Enhancements**: Nice-to-have improvements

## OPTIMIZED VERSION
If improvements are needed, provide a revised version that:
- Addresses all identified issues
- Incorporates suggested enhancements
- Maintains the original intent and tone
- Maximizes conversion potential
- Ensures brand consistency

Format your response with clear sections and specific, actionable feedback that enables immediate implementation.""",
        "variables": ["message_content", "context"],
        "agent_id": "3",
        "category": "quality_assurance",
        "channel": "both",
        "version": 1,
        "updated_at": "2024-01-15T10:00:00Z",
        "created_at": "2024-01-15T09:00:00Z"
    }
]

# API Endpoints
@app.get("/api/agents")
async def get_agents():
    return AGENTS

@app.get("/api/workflows")
async def get_workflows():
    return WORKFLOWS

@app.get("/api/prompts")
async def get_prompts():
    return PROMPTS

@app.get("/api/models")
async def get_models():
    return MODELS

@app.get("/api/execution-history")
async def get_execution_history():
    return [
        {
            "id": "1",
            "workflow_id": "default_workflow",
            "status": "completed",
            "started_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T10:05:00Z",
            "duration": 300,
            "result": "Successfully generated LinkedIn reply"
        }
    ]

@app.get("/api/test-results")
async def get_test_results():
    return [
        {
            "id": "1",
            "agent_id": "1",
            "test_name": "Profile Research Test",
            "status": "passed",
            "score": 0.95,
            "timestamp": "2024-01-15T09:00:00Z"
        }
    ]

# Observability endpoints
@app.get("/api/observability/traces")
async def get_traces():
    """Get system traces for observability"""
    return {
        "recent_traces": [
            {
                "id": "trace_001",
                "workflow_id": "linkedin-workflow",
                "agent_id": "linkedin-research-agent",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T10:02:30Z",
                "duration": 2.5,
                "status": "completed",
                "input": "Profile: https://linkedin.com/in/john-doe",
                "output": "Research completed successfully",
                "error": None
            },
            {
                "id": "trace_002", 
                "workflow_id": "linkedin-workflow",
                "agent_id": "reply-generation-agent",
                "start_time": "2024-01-15T10:02:30Z",
                "end_time": "2024-01-15T10:04:15Z",
                "duration": 1.75,
                "status": "completed",
                "input": "Generate LinkedIn message",
                "output": "Personalized message generated",
                "error": None
            },
            {
                "id": "trace_003",
                "workflow_id": "linkedin-workflow", 
                "agent_id": "quality-assurance-agent",
                "start_time": "2024-01-15T10:04:15Z",
                "end_time": "2024-01-15T10:05:00Z",
                "duration": 0.75,
                "status": "error",
                "input": "Review message quality",
                "output": None,
                "error": "Quality threshold not met"
            }
        ]
    }

@app.get("/api/observability/metrics")
async def get_observability_metrics():
    """Get observability metrics"""
    return {
        "traces": {
            "total_traces": 156,
            "errors": 12,
            "avg_execution_time": 2.3,
            "success_rate": 0.92
        },
        "performance": {
            "avg_response_time": 1.8,
            "throughput": 45.2,
            "error_rate": 0.08
        }
    }

@app.get("/api/system/health")
async def get_system_health():
    """Get system health status"""
    return {
        "system_metrics": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 35.1,
            "network_latency": 12.5,
            "active_connections": 23,
            "uptime": "2d 14h 32m"
        },
        "performance": {
            "monitoring_active": True,
            "last_health_check": "2024-01-15T10:05:00Z",
            "status": "healthy"
        }
    }

# Evaluation endpoints
@app.get("/api/evaluation/summary")
async def get_evaluation_summary():
    """Get evaluation summary"""
    return {
        "total_evaluations": 89,
        "average_score": 8.4,
        "average_execution_time": 3.2,
        "success_rate": 0.89,
        "recent_results": [
            {
                "id": "eval_001",
                "metric": "Response Quality",
                "score": 8.7,
                "confidence": 0.92,
                "evaluator": "GPT-4",
                "timestamp": "2024-01-15T10:00:00Z",
                "prompt_id": "profile_enrichment_prompt",
                "input": "Analyze LinkedIn profile",
                "output": "Comprehensive analysis completed",
                "feedback": "High quality response with detailed insights"
            },
            {
                "id": "eval_002",
                "metric": "Relevance",
                "score": 9.1,
                "confidence": 0.95,
                "evaluator": "Claude-3",
                "timestamp": "2024-01-15T09:45:00Z",
                "prompt_id": "linkedin_reply_generation_prompt",
                "input": "Generate LinkedIn message",
                "output": "Personalized outreach message",
                "feedback": "Highly relevant and personalized"
            },
            {
                "id": "eval_003",
                "metric": "Accuracy",
                "score": 7.8,
                "confidence": 0.88,
                "evaluator": "GPT-4",
                "timestamp": "2024-01-15T09:30:00Z",
                "prompt_id": "quality_assurance_prompt",
                "input": "Review message quality",
                "output": "Quality assessment report",
                "feedback": "Good accuracy but could be more precise"
            }
        ],
        "metric_statistics": {
            "response_quality": {"avg": 8.4, "min": 6.2, "max": 9.8},
            "relevance": {"avg": 8.7, "min": 7.1, "max": 9.9},
            "accuracy": {"avg": 8.1, "min": 6.8, "max": 9.5},
            "coherence": {"avg": 8.9, "min": 7.5, "max": 9.7}
        }
    }

@app.get("/api/evaluation/metrics")
async def get_evaluation_metrics():
    """Get evaluation metrics"""
    return {
        "overall_performance": {
            "average_score": 8.4,
            "total_evaluations": 89,
            "success_rate": 0.89,
            "improvement_trend": 0.12
        },
        "metric_breakdown": {
            "response_quality": 8.4,
            "relevance": 8.7,
            "accuracy": 8.1,
            "coherence": 8.9
        },
        "recent_trends": [
            {"date": "2024-01-15", "score": 8.4},
            {"date": "2024-01-14", "score": 8.2},
            {"date": "2024-01-13", "score": 8.1},
            {"date": "2024-01-12", "score": 7.9},
            {"date": "2024-01-11", "score": 7.8}
        ]
    }

# Config endpoints (for frontend compatibility)
@app.get("/api/config/agents")
async def get_config_agents():
    return AGENTS

@app.get("/api/config/prompts")
async def get_config_prompts():
    return PROMPTS

@app.get("/api/config/prompts/{prompt_id}")
async def get_config_prompt(prompt_id: str):
    prompt = next((p for p in PROMPTS if p["id"] == prompt_id), None)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@app.post("/api/config/prompts/{prompt_id}")
async def save_config_prompt(prompt_id: str, data: dict):
    # Find existing prompt or create new one
    prompt_index = next((i for i, p in enumerate(PROMPTS) if p["id"] == prompt_id), None)
    
    if prompt_index is not None:
        # Update existing prompt
        PROMPTS[prompt_index].update(data)
        PROMPTS[prompt_index]["version"] = PROMPTS[prompt_index].get("version", 1) + 1
        PROMPTS[prompt_index]["updated_at"] = datetime.now().isoformat()
    else:
        # Create new prompt
        new_prompt = {
            "id": prompt_id,
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **data
        }
        PROMPTS.append(new_prompt)
    
    return {"message": "Prompt saved successfully", "prompt": PROMPTS[prompt_index] if prompt_index is not None else new_prompt}

@app.delete("/api/config/prompts/{prompt_id}")
async def delete_config_prompt(prompt_id: str):
    global PROMPTS
    PROMPTS = [p for p in PROMPTS if p["id"] != prompt_id]
    return {"message": "Prompt deleted successfully"}

@app.post("/api/config/test/prompt/{prompt_id}")
async def test_config_prompt(prompt_id: str, test_data: dict):
    prompt = next((p for p in PROMPTS if p["id"] == prompt_id), None)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    try:
        # Simple template rendering
        template = prompt["template"]
        variables = test_data.get("input_data", {}).get("variables", {})
        
        rendered_prompt = template
        for var_name, var_value in variables.items():
            rendered_prompt = rendered_prompt.replace(f"{{{var_name}}}", str(var_value))
        
        return {
            "prompt_id": prompt_id,
            "result": {
                "rendered_prompt": rendered_prompt,
                "variables_used": list(variables.keys()),
                "template_length": len(template),
                "rendered_length": len(rendered_prompt)
            },
            "execution_time": 0.5,
            "status": "success",
            "error_message": ""
        }
    except Exception as e:
        return {
            "prompt_id": prompt_id,
            "result": f"Error: {str(e)}",
            "execution_time": 0.1,
            "status": "error",
            "error_message": str(e)
        }

@app.get("/api/config/test-results/prompt/{prompt_id}")
async def get_prompt_test_results(prompt_id: str):
    # Mock test results
    return [
        {
            "id": "test_1",
            "prompt_id": prompt_id,
            "test_input": "Sample test input",
            "test_output": "Sample test output",
            "execution_time": 1.2,
            "status": "success",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "id": "test_2", 
            "prompt_id": prompt_id,
            "test_input": "Another test input",
            "test_output": "Another test output",
            "execution_time": 0.8,
            "status": "success",
            "timestamp": "2024-01-15T09:30:00Z"
        }
    ]

@app.get("/api/config/version-history/prompt/{prompt_id}")
async def get_prompt_version_history(prompt_id: str):
    # Mock version history
    return [
        {
            "version": 2,
            "created_at": "2024-01-15T10:00:00Z",
            "changes": "Updated template with enhanced personalization",
            "author": "System"
        },
        {
            "version": 1,
            "created_at": "2024-01-15T09:00:00Z", 
            "changes": "Initial version",
            "author": "System"
        }
    ]

@app.post("/api/config/rollback/prompt/{prompt_id}")
async def rollback_prompt_version(prompt_id: str, data: dict):
    version = data.get("version", 1)
    return {"message": f"Rolled back prompt {prompt_id} to version {version}"}

@app.get("/api/config/workflows")
async def get_config_workflows():
    return WORKFLOWS

@app.get("/api/config/models")
async def get_config_models():
    return MODELS

@app.get("/api/config/model-assignments")
async def get_config_model_assignments():
    return MODEL_ASSIGNMENTS

@app.get("/api/config/tools")
async def get_config_tools():
    return TOOLS

@app.post("/api/workflows/execute")
async def execute_workflow(data: dict):
    """Execute a workflow"""
    try:
        workflow_id = data.get("workflow_id", "default_workflow")
        input_data = data.get("input_data", {})
        
        # Simulate workflow execution
        result = {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": "Successfully generated LinkedIn reply: 'Hi! I noticed your work in AI and would love to connect and discuss potential collaboration opportunities.'",
            "execution_time": 3.2,
            "steps_completed": 3
        }
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Additional workflow endpoints for interactive dashboard
@app.get("/api/workflows")
def get_workflows():
    return [
        {
            "id": "linkedin-workflow",
            "name": "LinkedIn Outreach Workflow",
            "description": "Automated LinkedIn outreach with research, reply generation, and quality assurance",
            "steps": [
                {
                    "id": "research-step",
                    "name": "Research Step",
                    "agent_id": "linkedin-research-agent",
                    "order": 1
                },
                {
                    "id": "reply-step", 
                    "name": "Reply Generation Step",
                    "agent_id": "reply-generation-agent",
                    "order": 2
                },
                {
                    "id": "quality-step",
                    "name": "Quality Assurance Step", 
                    "agent_id": "quality-assurance-agent",
                    "order": 3
                }
            ],
            "settings": {
                "parallel_execution": False,
                "timeout": 300
            }
        }
    ]

@app.post("/api/workflows/{workflow_id}/execute")
def execute_workflow(workflow_id: str, input_data: dict = None):
    import uuid
    execution_id = str(uuid.uuid4())
    
    return {
        "execution_id": execution_id,
        "status": "running",
        "current_step": 2,
        "total_steps": 3,
        "progress": 66,
        "started_at": "2024-01-15T12:00:00Z",
        "estimated_completion": "2024-01-15T12:05:00Z"
    }

@app.get("/api/executions/{execution_id}/status")
def get_execution_status(execution_id: str):
    return {
        "execution_id": execution_id,
        "status": "running",
        "current_step": 2,
        "total_steps": 3,
        "progress": 66,
        "started_at": "2024-01-15T12:00:00Z",
        "estimated_completion": "2024-01-15T12:05:00Z"
    }

# Additional config endpoints to fix 404 errors
@app.get("/api/config/agents/{agent_id}/model")
async def get_agent_model(agent_id: str, model_id: str = None):
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    model = next((m for m in MODELS if m["id"] == agent.get("model", "gpt-4")), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "agent_id": agent_id,
        "model": model,
        "assignment_date": "2024-01-15T10:00:00Z",
        "status": "active"
    }

@app.get("/api/config/models/{model_id}")
async def get_config_model(model_id: str):
    model = next((m for m in MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@app.get("/api/config/health")
async def get_config_health():
    return {
        "status": "healthy",
        "uptime": "2h 34m",
        "memory_usage": "45%",
        "cpu_usage": "23%",
        "active_connections": 12,
        "last_backup": "2024-01-15T10:30:00Z"
    }

# System configuration endpoints
@app.get("/api/config/system")
async def get_system_config():
    """Get system configuration"""
    return {
        "api_timeout": 30,
        "max_concurrent_executions": 5,
        "log_level": "INFO",
        "enable_monitoring": True,
        "enable_notifications": True,
        "theme": "light"
    }

@app.put("/api/config/system")
async def update_system_config(config: dict):
    """Update system configuration"""
    # In a real implementation, this would save to database or config file
    return {"message": "System configuration updated successfully", "config": config}

@app.post("/api/system/backup")
async def create_system_backup():
    """Create system backup"""
    import uuid
    backup_id = str(uuid.uuid4())
    return {
        "backup_id": backup_id,
        "filename": f"crewai_backup_{backup_id[:8]}.zip",
        "created_at": "2024-01-15T10:30:00Z",
        "size": "2.4 MB",
        "message": "Backup created successfully"
    }

@app.post("/api/system/refresh")
async def refresh_system():
    """Refresh system configuration and cache"""
    return {
        "message": "System refreshed successfully",
        "refreshed_at": "2024-01-15T10:35:00Z",
        "components_refreshed": [
            "Configuration cache",
            "Agent definitions",
            "Prompt templates",
            "Model assignments"
        ]
    }

# Performance monitoring endpoints
@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics for the dashboard"""
    import time
    import random
    
    # Generate realistic performance data
    now = time.time()
    data = []
    
    for i in range(30):  # Last 30 minutes
        timestamp = now - (i * 60)  # 1 minute intervals
        data.append({
            "time": time.strftime("%H:%M", time.localtime(timestamp)),
            "executions": random.randint(5, 15),
            "averageTime": random.randint(1500, 4000),
            "successRate": random.randint(85, 98),
            "errors": random.randint(0, 2),
        })
    
    return {"performance_data": list(reversed(data))}

@app.get("/api/performance/agents")
async def get_agent_performance():
    """Get agent performance metrics"""
    import random
    
    agent_metrics = []
    for agent in AGENTS:
        agent_metrics.append({
            "name": agent["name"],
            "executions": random.randint(20, 80),
            "avgTime": random.randint(800, 3500),
            "successRate": random.randint(88, 99),
            "status": agent["status"],
            "last_execution": "2024-01-15T10:30:00Z"
        })
    
    return {"agent_metrics": agent_metrics}

@app.get("/api/performance/system")
async def get_system_performance():
    """Get system performance metrics"""
    import random
    
    return {
        "system_health": {
            "cpu": random.randint(25, 65),
            "memory": random.randint(40, 80),
            "activeAgents": len([a for a in AGENTS if a["status"] == "active"]),
            "totalExecutions": random.randint(150, 300),
            "uptime": "2d 14h 32m",
            "last_updated": "2024-01-15T10:35:00Z"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090) 