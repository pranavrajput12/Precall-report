import os
from typing import Any, Dict, List, cast

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr

from config_system import config_system

load_dotenv()

# Get LLM configuration from config system
llm_config = config_system.get("llm")

# Azure OpenAI credentials - still using env vars for sensitive credentials
# but with config system fallbacks
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT",
                                   config_system.get("llm.azure_deployment"))
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION",
                                    config_system.get("llm.azure_api_version"))

# Enhanced LLM configuration with streaming support and explicit Azure credentials
# Note: Disable streaming for CrewAI compatibility
# Set environment variables for litellm
# IMPORTANT: Set these as environment variables, not in code!
# export AZURE_API_KEY="your-api-key"
# export AZURE_API_BASE="https://your-endpoint.openai.azure.com"
# export AZURE_API_VERSION="2025-01-01-preview"

# Get Azure credentials from environment variables
azure_api_key = os.environ.get('AZURE_API_KEY')
if not azure_api_key:
    raise ValueError("AZURE_API_KEY environment variable is required")

azure_endpoint = os.environ.get('AZURE_API_BASE', 'https://airops.openai.azure.com')
azure_api_version = os.environ.get('AZURE_API_VERSION', '2025-01-01-preview')

llm = AzureChatOpenAI(
    api_key=SecretStr(azure_api_key),
    azure_endpoint=azure_endpoint,
    azure_deployment="gpt-4.1",
    api_version="2025-01-01-preview",
    temperature=llm_config.get("temperature", 0.7),
    max_tokens=llm_config.get("max_tokens", 1500),
    streaming=False,  # Disable streaming for CrewAI compatibility
    model="azure/gpt-4.1",  # Specify model name for litellm routing
    model_kwargs={
        "top_p": llm_config.get("top_p", 1.0),
        "frequency_penalty": llm_config.get("frequency_penalty", 0.0),
        "presence_penalty": llm_config.get("presence_penalty", 0.0)
    },
)

# Enhanced agents with improved configurations
profile_enrichment_agent = Agent(
    role="ProfileEnricher",
    goal="Given LinkedIn and company URLs, return a concise, insight-rich summary of the prospect and their company, including founder details, industry, fundraising, and social proof.",
    backstory="""You are a senior sales intelligence researcher with expertise in:
    - LinkedIn profile analysis and social selling
    - Company research and competitive intelligence
    - Industry trend analysis and market insights
    - Identifying decision makers and influencers
    - Extracting actionable sales intelligence from public data

    You excel at synthesizing complex information into clear, actionable insights that help sales teams connect with prospects effectively.""",
    llm=llm,
    verbose=True,
    max_iter=3,
    allow_delegation=False,
    step_callback=None,  # Can be used for streaming updates
)

linkedin_thread_analyzer = Agent(
    role="LinkedInThreadAnalyzer",
    goal="Analyze LinkedIn conversation threads to extract key sales insights, qualification stage, message summary, tone, and explicit questions from prospects.",
    backstory="""You are a conversation analysis expert specializing in LinkedIn communications with deep understanding of:
    - Professional networking communication patterns
    - Sales qualification methodologies (BANT, MEDDIC, etc.)
    - Emotional intelligence and tone analysis
    - Intent recognition in professional conversations
    - LinkedIn-specific communication nuances

    You can quickly identify buying signals, objections, and engagement opportunities in LinkedIn conversations.""",
    llm=llm,
    verbose=True,
    max_iter=2,
    allow_delegation=False,
)

email_thread_analyzer = Agent(
    role="EmailThreadAnalyzer",
    goal="Analyze email threads to extract intent, qualification stage, message summary, tone, and explicit questions from prospects.",
    backstory="""You are an email communication specialist with expertise in:
    - B2B email communication patterns
    - Sales funnel progression analysis
    - Professional email etiquette and tone
    - Multi-threaded conversation analysis
    - Intent classification and urgency detection

    You excel at parsing complex email threads and extracting actionable insights for sales teams.""",
    llm=llm,
    verbose=True,
    max_iter=2,
    allow_delegation=False,
)

faq_answer_agent = Agent(
    role="FAQAnswerer",
    goal="Given a client question and access to the internal FAQ, return a concise, accurate, and contextually relevant answer.",
    backstory="""You are a customer success specialist with deep knowledge of:
    - Product features and capabilities
    - Common customer pain points and solutions
    - Technical documentation and FAQs
    - Customer communication best practices
    - Escalation procedures and support workflows

    You provide accurate, helpful answers while maintaining a professional and supportive tone.""",
    llm=llm,
    verbose=True,
    max_iter=2,
    allow_delegation=False,
)

linkedin_reply_agent = Agent(
    role="LinkedInReplyGenerator",
    goal="Produce polished, multi-step LinkedIn reply sequences (initial + follow-ups) using conversation context, FAQ answers, and tone analysis. Format all links as raw URLs.",
    backstory="""You are a LinkedIn social selling expert with mastery of:
    - Professional LinkedIn communication styles
    - Multi-touch engagement sequences
    - Personalization at scale
    - LinkedIn algorithm optimization
    - Professional relationship building
    - CTA optimization for LinkedIn

    You craft messages that feel personal, valuable, and action-oriented while maintaining professional standards.""",
    llm=llm,
    verbose=True,
    max_iter=3,
    allow_delegation=False,
)

email_reply_agent = Agent(
    role="EmailReplyGenerator",
    goal="Produce complete email-cadence sequences (initial + up to 7 follow-ups) using conversation context, FAQ answers, and tone analysis. Format all links as anchor text.",
    backstory="""You are an email marketing and sales communication expert with deep knowledge of:
    - Email deliverability best practices
    - Multi-touch email sequences
    - Personalization techniques
    - A/B testing and optimization
    - Professional email formatting
    - CRM integration considerations

    You create email sequences that drive engagement while respecting recipient preferences and maintaining professional standards.""",
    llm=llm,
    verbose=True,
    max_iter=3,
    allow_delegation=False,
)

escalation_agent = Agent(
    role="EscalationAgent",
    goal="Monitor workflow confidence and data completeness, escalating to a human manager when required data is missing or confidence is low (<0.25).",
    backstory="""You are a quality assurance and process management specialist with expertise in:
    - Workflow monitoring and optimization
    - Quality control and confidence scoring
    - Escalation procedures and protocols
    - Risk assessment and mitigation
    - Human-AI collaboration workflows

    You ensure high-quality outputs by identifying when human intervention is needed and providing clear escalation guidance.""",
    llm=llm,
    verbose=True,
    max_iter=1,
    allow_delegation=False,
)


def create_enhanced_crew(agents: List[Agent], tasks: List[Task]) -> Crew:
    """
    Create an enhanced crew with improved configuration for CrewAI v0.141.0
    """
    # Get workflow configuration from config system
    workflow_config = config_system.get("workflow")
    
    return Crew(
        agents=cast(List[Any], agents),  # Type cast to avoid type error
        tasks=tasks,
        verbose=True,
        process="sequential",  # Can be "sequential" or "hierarchical"  # type: ignore
        max_rpm=config_system.get("agents.max_rpm", 10),  # Rate limiting
        step_callback=None,  # Can be used for streaming updates
        task_callback=None,  # Can be used for task completion updates
        share_crew=False,
        embedder={
            "provider": "azure_openai",
            "config": {
                "model": config_system.get("faq.embedding_model", "text-embedding-ada-002"),
                "deployment_name": os.getenv(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
                    config_system.get("llm.azure_embedding_deployment", "text-embedding-ada-002")
                ),
            },
        },
    )


def create_profile_enrichment_task(
        prospect_profile_url: str,
        prospect_company_url: str,
        prospect_company_website: str) -> Task:
    """Create a profile enrichment task with enhanced configuration"""
    return Task(
        description=f"""
        Analyze and enrich the prospect and company profile using the provided URLs:

        Prospect LinkedIn: {prospect_profile_url}
        Company LinkedIn: {prospect_company_url}
        Company Website: {prospect_company_website}

        Provide a comprehensive summary including:
        1. Prospect's professional background and role
        2. Company overview and industry positioning
        3. Recent company news and developments
        4. Founder/leadership team details
        5. Fundraising history and financial status
        6. Social proof and testimonials
        7. Potential pain points and opportunities

        Format the output as a structured summary that can be used for personalized outreach.
        """,
        agent=profile_enrichment_agent,
        expected_output="A structured profile summary with key insights for sales outreach",
        async_execution=False,
        context=None,
        callback=None,
        human_input=False,
    )


def create_thread_analysis_task(
        conversation_thread: str,
        channel: str) -> Task:
    """Create a thread analysis task with enhanced configuration"""
    analyzer_agent = (linkedin_thread_analyzer if channel ==
                      "linkedin" else email_thread_analyzer)

    return Task(
        description=f"""
        Analyze the following {channel} conversation thread:

        {conversation_thread}

        Extract and analyze:
        1. Qualification stage (Cold, Warm, Hot, Qualified)
        2. Comprehensive message summary
        3. Tone and sentiment analysis
        4. Explicit questions from the prospect
        5. Buying signals and intent indicators
        6. Objections or concerns raised
        7. Next best actions

        Return the analysis in JSON format for easy processing.
        """,
        agent=analyzer_agent,
        expected_output="JSON formatted analysis with qualification stage, summary, tone, and questions",
        async_execution=False,
        context=None,
        callback=None,
        human_input=False,
    )


def create_reply_generation_task(
        context: Dict[str, Any], channel: str) -> Task:
    """Create a reply generation task with enhanced configuration"""
    reply_agent = linkedin_reply_agent if channel == "linkedin" else email_reply_agent

    return Task(
        description=f"""
        Generate a personalized {channel} reply sequence using the provided context:

        Context: {context}

        Create:
        1. Initial response addressing specific questions/concerns
        2. Follow-up sequence (2-3 for LinkedIn, up to 7 for email)
        3. Personalized elements based on profile data
        4. Clear call-to-action in each message
        5. Professional tone matching the conversation

        {"Format links as raw URLs for LinkedIn" if channel == "linkedin" else "Format links as anchor text for email"}

        Ensure the sequence feels natural and provides value at each touchpoint.
        """,
        agent=reply_agent,
        expected_output=f"Complete {channel} reply sequence with personalized messaging",
        async_execution=False,
        context=None,
        callback=None,
        human_input=False,
    )


# Tool configurations from config system
tools_config = config_system.get("tools", {})

# Tool configurations for enhanced functionality
AVAILABLE_TOOLS = {
    "web_search": {
        "enabled": tools_config.get("web_search.enabled", True),
        "provider": tools_config.get("web_search.provider", "serp_api"),
        "config": {
            "api_key": os.getenv("SERP_API_KEY", ""),
            "engine": tools_config.get("web_search.engine", "google"),
            "num_results": tools_config.get("web_search.num_results", 10),
        },
    },
    "linkedin_scraper": {
        "enabled": tools_config.get("linkedin_scraper.enabled", False),  # Requires additional setup
        "provider": tools_config.get("linkedin_scraper.provider", "custom"),
        "config": tools_config.get("linkedin_scraper.config", {}),
    },
    "company_enrichment": {
        "enabled": tools_config.get("company_enrichment.enabled", False),  # Requires additional setup
        "provider": tools_config.get("company_enrichment.provider", "clearbit"),
        "config": {"api_key": os.getenv("CLEARBIT_API_KEY", "")},
    },
}
