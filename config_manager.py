import hashlib
import json
import logging
import os
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for an LLM or embedding model"""

    id: str
    name: str
    provider: str  # e.g., 'openai', 'azure', 'anthropic', etc.
    type: str  # e.g., 'chat', 'completion', 'embedding'
    config: Dict[str, Any]
    status: str = "active"
    created_at: str = None
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class AgentConfig:
    """Configuration for a CrewAI agent"""

    id: str
    name: str = ""
    role: str = ""
    goal: str = ""
    backstory: str = ""
    model_id: str = "default"
    verbose: bool = True
    memory: bool = True
    max_iter: int = 3
    allow_delegation: bool = False
    temperature: float = 0.3
    max_tokens: int = 2048
    created_at: str = None
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class PromptTemplate:
    """Configuration for workflow prompts"""

    id: str
    name: str
    description: str
    template: str
    variables: List[str]
    category: str  # 'profile_enrichment', 'thread_analysis', 'reply_generation'
    channel: Optional[str] = None  # 'linkedin', 'email', or None for both
    created_at: str = None
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""

    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    settings: Dict[str, Any]
    created_at: str = None
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class ToolConfig:
    """Configuration for workflow tools"""

    id: str
    name: str
    description: str
    enabled: bool
    provider: str
    config: Dict[str, Any]
    created_at: str = None
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class VersionHistory:
    """Version history entry"""

    id: str
    entity_type: str  # 'prompt', 'workflow', 'agent', 'tool'
    entity_id: str
    version: int
    content: str
    content_hash: str
    created_at: str
    created_by: str = "system"
    change_description: str = ""


class ConfigManager:
    """Centralized configuration management for CrewAI workflow system"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.config_dir / "agents").mkdir(exist_ok=True)
        (self.config_dir / "prompts").mkdir(exist_ok=True)
        (self.config_dir / "workflows").mkdir(exist_ok=True)
        (self.config_dir / "tools").mkdir(exist_ok=True)
        (self.config_dir / "models").mkdir(exist_ok=True)
        (self.config_dir / "versions").mkdir(exist_ok=True)

        # Initialize database
        self.db_path = self.config_dir / "config.db"
        self._init_database()

        # Initialize with default configurations
        self._initialize_default_configs()

    def _init_database(self):
        """Initialize SQLite database for version control and history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create version history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS version_history (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT DEFAULT 'system',
                change_description TEXT DEFAULT '',
                UNIQUE(entity_type, entity_id, version)
            )
        """
        )

        # Create execution history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_history (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                agent_id TEXT,
                prompt_id TEXT,
                input_data TEXT,
                output_data TEXT,
                execution_time REAL,
                status TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        # Create test results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                test_input TEXT,
                test_output TEXT,
                execution_time REAL,
                status TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _save_version_history(
        self,
        entity_type: str,
        entity_id: str,
        content: str,
        version: int,
        change_description: str = "",
    ):
        """Save version history to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        history_id = (
            f"{entity_type}_{entity_id}_v{version}_{datetime.now().isoformat()}"
        )
        content_hash = self._generate_content_hash(content)

        cursor.execute(
            """
            INSERT OR REPLACE INTO version_history
            (id, entity_type, entity_id, version, content, content_hash, created_at, change_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                history_id,
                entity_type,
                entity_id,
                version,
                content,
                content_hash,
                datetime.now().isoformat(),
                change_description,
            ),
        )

        conn.commit()
        conn.close()

    def get_version_history(
        self, entity_type: str, entity_id: str
    ) -> List[VersionHistory]:
        """Get version history for an entity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, entity_type, entity_id, version, content, content_hash,
                   created_at, created_by, change_description
            FROM version_history
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY version DESC
        """,
            (entity_type, entity_id),
        )

        history = []
        for row in cursor.fetchall():
            history.append(
                VersionHistory(
                    id=row[0],
                    entity_type=row[1],
                    entity_id=row[2],
                    version=row[3],
                    content=row[4],
                    content_hash=row[5],
                    created_at=row[6],
                    created_by=row[7],
                    change_description=row[8],
                )
            )

        conn.close()
        return history

    def rollback_to_version(
        self, entity_type: str, entity_id: str, version: int
    ) -> bool:
        """Rollback an entity to a specific version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT content FROM version_history
            WHERE entity_type = ? AND entity_id = ? AND version = ?
        """,
            (entity_type, entity_id, version),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        content = row[0]

        try:
            # Restore the content
            if entity_type == "prompt":
                data = json.loads(content)
                prompt = PromptTemplate(**data)
                prompt.version = self._get_next_version(entity_type, entity_id)
                self.save_prompt_template(
                    prompt, f"Rollback to version {version}")
            elif entity_type == "workflow":
                data = json.loads(content)
                workflow = WorkflowConfig(**data)
                workflow.version = self._get_next_version(
                    entity_type, entity_id)
                self.save_workflow_config(
                    workflow, f"Rollback to version {version}")
            elif entity_type == "agent":
                data = json.loads(content)
                agent = AgentConfig(**data)
                agent.version = self._get_next_version(entity_type, entity_id)
                self.save_agent_config(agent, f"Rollback to version {version}")

            conn.close()
            return True
        except Exception as e:
            logger.error(
                f"Error rolling back {entity_type} {entity_id} to version {version}: {e}"
            )
            conn.close()
            return False

    def _get_next_version(self, entity_type: str, entity_id: str) -> int:
        """Get the next version number for an entity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT MAX(version) FROM version_history
            WHERE entity_type = ? AND entity_id = ?
        """,
            (entity_type, entity_id),
        )

        row = cursor.fetchone()
        conn.close()

        return (row[0] or 0) + 1

    def save_test_result(
        self,
        entity_type: str,
        entity_id: str,
        test_input: str,
        test_output: str,
        execution_time: float,
        status: str,
        error_message: str = "",
    ):
        """Save test result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        test_id = f"{entity_type}_{entity_id}_test_{datetime.now().isoformat()}"

        cursor.execute(
            """
            INSERT INTO test_results
            (id, entity_type, entity_id, test_input, test_output, execution_time, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                test_id,
                entity_type,
                entity_id,
                test_input,
                test_output,
                execution_time,
                status,
                error_message,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def get_test_results(
        self, entity_type: str, entity_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get test results for an entity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, test_input, test_output, execution_time, status, error_message, created_at
            FROM test_results
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (entity_type, entity_id, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "test_input": row[1],
                    "test_output": row[2],
                    "execution_time": row[3],
                    "status": row[4],
                    "error_message": row[5],
                    "created_at": row[6],
                }
            )

        conn.close()
        return results

    def save_execution_history(
        self,
        workflow_id: str,
        agent_id: str,
        prompt_id: str,
        input_data: str,
        output_data: str,
        execution_time: float,
        status: str,
        error_message: str = "",
    ):
        """Save execution history to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        execution_id = f"{workflow_id}_{agent_id}_{datetime.now().isoformat()}"

        cursor.execute(
            """
            INSERT INTO execution_history
            (id, workflow_id, agent_id, prompt_id, input_data, output_data, execution_time, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                execution_id,
                workflow_id,
                agent_id,
                prompt_id,
                input_data,
                output_data,
                execution_time,
                status,
                error_message,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def _config_exists(self) -> bool:
        """Check if configuration files exist"""
        return (self.config_dir / "agents").exists() and len(
            list((self.config_dir / "agents").glob("*.json"))
        ) > 0

    def _initialize_default_configs(self):
        """Initialize with current system configurations"""
        if not self._config_exists():
            self._create_default_agents()
            self._create_default_prompts()
            self._create_default_workflows()
            self._create_default_tools()

    def _create_default_agents(self):
        """Create default agent configurations based on current system"""
        agents = [
            AgentConfig(
                id="profile_enrichment_agent",
                role="ProfileEnricher",
                goal="Given LinkedIn and company URLs, return a concise, insight-rich summary of the prospect and their company, including founder details, industry, fundraising, and social proof.",
                backstory="""You are a senior sales intelligence researcher with expertise in:
- LinkedIn profile analysis and social selling
- Company research and competitive intelligence
- Industry trend analysis and market insights
- Identifying decision makers and influencers
- Extracting actionable sales intelligence from public data

You excel at synthesizing complex information into clear, actionable insights that help sales teams connect with prospects effectively.""",
                max_iter=3,
            ),
            AgentConfig(
                id="linkedin_thread_analyzer",
                role="LinkedInThreadAnalyzer",
                goal="Analyze LinkedIn conversation threads to extract key sales insights, qualification stage, message summary, tone, and explicit questions from prospects.",
                backstory="""You are a conversation analysis expert specializing in LinkedIn communications with deep understanding of:
- Professional networking communication patterns
- Sales qualification methodologies (BANT, MEDDIC, etc.)
- Emotional intelligence and tone analysis
- Intent recognition in professional conversations
- LinkedIn-specific communication nuances

You can quickly identify buying signals, objections, and engagement opportunities in LinkedIn conversations.""",
                max_iter=2,
            ),
            AgentConfig(
                id="email_thread_analyzer",
                role="EmailThreadAnalyzer",
                goal="Analyze email threads to extract intent, qualification stage, message summary, tone, and explicit questions from prospects.",
                backstory="""You are an email communication specialist with expertise in:
- B2B email communication patterns
- Sales funnel progression analysis
- Professional email etiquette and tone
- Multi-threaded conversation analysis
- Intent classification and urgency detection

You excel at parsing complex email threads and extracting actionable insights for sales teams.""",
                max_iter=2,
            ),
            AgentConfig(
                id="faq_answer_agent",
                role="FAQAnswerer",
                goal="Given a client question and access to the internal FAQ, return a concise, accurate, and contextually relevant answer.",
                backstory="""You are a customer success specialist with deep knowledge of:
- Product features and capabilities
- Common customer pain points and solutions
- Technical documentation and FAQs
- Customer communication best practices
- Escalation procedures and support workflows

You provide accurate, helpful answers while maintaining a professional and supportive tone.""",
                max_iter=2,
            ),
            AgentConfig(
                id="linkedin_reply_agent",
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
                max_iter=3,
            ),
            AgentConfig(
                id="email_reply_agent",
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
                max_iter=3,
            ),
            AgentConfig(
                id="escalation_agent",
                role="EscalationAgent",
                goal="Monitor workflow confidence and data completeness, escalating to a human manager when required data is missing or confidence is low (<0.25).",
                backstory="""You are a quality assurance and process management specialist with expertise in:
- Workflow monitoring and optimization
- Quality control and confidence scoring
- Escalation procedures and protocols
- Risk assessment and mitigation
- Human-AI collaboration workflows

You ensure high-quality outputs by identifying when human intervention is needed and providing clear escalation guidance.""",
                max_iter=1,
            ),
        ]

        for agent in agents:
            self.save_agent_config(agent)

    def _create_default_prompts(self):
        """Create default prompt templates based on current system"""
        prompts = [
            PromptTemplate(
                id="profile_enrichment_prompt",
                name="Profile Enrichment",
                description="Enhanced profile enrichment with strategic sales intelligence",
                template="""You are an elite ProfileEnricher agent specializing in deep sales intelligence and strategic business analysis. Your goal is to provide actionable insights that enable highly personalized, value-driven outreach.

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
                variables=[
                    "prospect_profile_url",
                    "prospect_company_url",
                    "prospect_company_website",
                ],
                category="profile_enrichment",
            ),
            PromptTemplate(
                id="linkedin_thread_analysis_prompt",
                name="LinkedIn Thread Analysis",
                description="Enhanced LinkedIn conversation analysis with strategic sales insights",
                template="""You are an elite LinkedInThreadAnalyzer agent with deep expertise in sales psychology, conversation analysis, and strategic communication patterns. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

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
        "response_time_pattern": "immediate|delayed|inconsistent",
        "communication_style": "direct|diplomatic|analytical|relationship_focused",
        "decision_making_signals": ["indicators of decision-making authority or process"]
    }},
    "strategic_insights": {{
        "key_interests": ["topics that generated most engagement"],
        "objections_raised": ["concerns or pushback mentioned"],
        "value_drivers": ["what seems to motivate the prospect"],
        "competitive_mentions": ["any competitor references"],
        "next_best_actions": ["recommended follow-up strategies"]
    }},
    "personalization_data": {{
        "conversation_highlights": ["key moments or quotes to reference"],
        "shared_interests": ["common ground identified"],
        "professional_context": ["role-specific insights"],
        "company_context": ["company-specific talking points"]
    }},
    "competitive_intelligence": {{
        "current_solutions": ["existing tools or providers mentioned"],
        "satisfaction_level": "high|medium|low|unknown",
        "switching_indicators": ["signs of willingness to change"],
        "decision_criteria": ["factors important to prospect"]
    }},
    "follow_up_strategy": {{
        "recommended_approach": "consultative|educational|social_proof|urgency",
        "optimal_timing": "immediate|within_24h|within_week|scheduled",
        "key_messages": ["main points to emphasize"],
        "success_probability": "high|medium|low",
        "risk_factors": ["potential obstacles or concerns"]
    }},
    "explicit_questions": ["direct questions asked by prospect that need answers"]
}}

Ensure all analysis is based on actual conversation content and provide specific examples where possible.""",
                variables=["conversation_thread"],
                category="thread_analysis",
                channel="linkedin",
            ),
            PromptTemplate(
                id="email_thread_analysis_prompt",
                name="Email Thread Analysis",
                description="Enhanced email conversation analysis with strategic sales insights",
                template="""You are an elite EmailThreadAnalyzer agent with deep expertise in email communication patterns, sales psychology, and strategic analysis. Your goal is to provide actionable insights that enable highly effective follow-up engagement.

EMAIL THREAD TO ANALYZE:
{conversation_thread}

PROVIDE A COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH THESE SECTIONS:

{{
    "conversation_overview": {{
        "participant_count": "number of people in email thread",
        "message_count": "total emails exchanged",
        "conversation_duration": "timespan of email thread",
        "conversation_type": "cold_outreach|warm_introduction|follow_up|referral|internal_discussion"
    }},
    "qualification_analysis": {{
        "qualification_stage": "cold|warm|hot|qualified|champion|decision_maker",
        "buying_signals": ["list of specific buying signals observed"],
        "pain_points_mentioned": ["explicit or implicit pain points"],
        "budget_indicators": ["any budget or financial discussions"],
        "timeline_indicators": ["urgency signals or timeline mentions"],
        "authority_level": "decision_maker|influencer|user|researcher|gatekeeper"
    }},
    "conversation_intelligence": {{
        "prospect_tone": "professional|casual|enthusiastic|skeptical|neutral|urgent|formal",
        "engagement_level": "high|medium|low",
        "response_time_pattern": "immediate|delayed|inconsistent|business_hours",
        "communication_style": "direct|diplomatic|analytical|relationship_focused|technical",
        "email_signatures": ["insights from email signatures and titles"]
    }},
    "strategic_insights": {{
        "key_interests": ["topics that generated most engagement"],
        "objections_raised": ["concerns or pushback mentioned"],
        "value_drivers": ["what seems to motivate the prospect"],
        "competitive_mentions": ["any competitor references"],
        "next_best_actions": ["recommended follow-up strategies"],
        "stakeholder_involvement": ["other people mentioned or CC'd"]
    }},
    "personalization_data": {{
        "conversation_highlights": ["key moments or quotes to reference"],
        "shared_interests": ["common ground identified"],
        "professional_context": ["role-specific insights"],
        "company_context": ["company-specific talking points"],
        "technical_requirements": ["specific technical needs mentioned"]
    }},
    "competitive_intelligence": {{
        "current_solutions": ["existing tools or providers mentioned"],
        "satisfaction_level": "high|medium|low|unknown",
        "switching_indicators": ["signs of willingness to change"],
        "decision_criteria": ["factors important to prospect"],
        "evaluation_process": ["procurement or evaluation process insights"]
    }},
    "follow_up_strategy": {{
        "recommended_approach": "consultative|educational|social_proof|urgency|technical_demo",
        "optimal_timing": "immediate|within_24h|within_week|scheduled|after_event",
        "key_messages": ["main points to emphasize"],
        "success_probability": "high|medium|low",
        "risk_factors": ["potential obstacles or concerns"],
        "escalation_opportunities": ["chances to involve senior stakeholders"]
    }},
    "explicit_questions": ["direct questions asked by prospect that need answers"]
}}

Ensure all analysis is based on actual email content and provide specific examples where possible.""",
                variables=["conversation_thread"],
                category="thread_analysis",
                channel="email",
            ),
        ]

        for prompt in prompts:
            self.save_prompt_template(prompt)

    def _create_default_workflows(self):
        """Create default workflow configurations"""
        workflow = WorkflowConfig(id="default_workflow",
                                  name="Default Sales Workflow",
                                  description="Standard workflow for processing inbound LinkedIn/Email inquiries",
                                  steps=[{"id": "normalize_channel",
                                          "name": "Channel Normalization",
                                          "description": "Normalize the input channel (LinkedIn/Email)",
                                          "enabled": True,
                                          "order": 1,
                                          },
                                         {"id": "profile_enrichment",
                                          "name": "Profile Enrichment",
                                          "description": "Enrich prospect and company profiles",
                                          "enabled": True,
                                          "order": 2,
                                          "agent_id": "profile_enrichment_agent",
                                          "prompt_id": "profile_enrichment_prompt",
                                          },
                                         {"id": "thread_analysis",
                                          "name": "Thread Analysis",
                                          "description": "Analyze conversation thread for insights",
                                          "enabled": True,
                                          "order": 3,
                                          "agent_id": "linkedin_thread_analyzer",
                                          "prompt_id": "linkedin_thread_analysis_prompt",
                                          },
                                         {"id": "faq_processing",
                                          "name": "FAQ Processing",
                                          "description": "Process explicit questions from prospects",
                                          "enabled": True,
                                          "order": 4,
                                          "agent_id": "faq_answer_agent",
                                          },
                                         {"id": "context_assembly",
                                          "name": "Context Assembly",
                                          "description": "Assemble context from all previous steps",
                                          "enabled": True,
                                          "order": 5,
                                          },
                                         {"id": "reply_generation",
                                          "name": "Reply Generation",
                                          "description": "Generate personalized reply sequences",
                                          "enabled": True,
                                          "order": 6,
                                          "agent_id": "linkedin_reply_agent",
                                          },
                                         {"id": "quality_assessment",
                                          "name": "Quality Assessment",
                                          "description": "Assess output quality and confidence",
                                          "enabled": True,
                                          "order": 7,
                                          },
                                         {"id": "escalation_check",
                                          "name": "Escalation Check",
                                          "description": "Check if human escalation is needed",
                                          "enabled": True,
                                          "order": 8,
                                          "agent_id": "escalation_agent",
                                          },
                                         ],
                                  settings={"parallel_execution": True,
                                            "cache_enabled": True,
                                            "cache_ttl": 3600,
                                            "max_retries": 3,
                                            "timeout": 300,
                                            "quality_threshold": 0.7,
                                            },
                                  )

        self.save_workflow_config(workflow)

    def _create_default_tools(self):
        """Create default tool configurations"""
        tools = [
            ToolConfig(
                id="web_search",
                name="Web Search",
                description="Search the web for additional information",
                enabled=True,
                provider="serp_api",
                config={
                    "api_key": "${SERP_API_KEY}",
                    "engine": "google",
                    "num_results": 10,
                },
            ),
            ToolConfig(
                id="linkedin_scraper",
                name="LinkedIn Scraper",
                description="Scrape LinkedIn profiles and company pages",
                enabled=False,
                provider="custom",
                config={"rate_limit": 10, "timeout": 30},
            ),
            ToolConfig(
                id="company_enrichment",
                name="Company Enrichment",
                description="Enrich company data using external APIs",
                enabled=False,
                provider="clearbit",
                config={"api_key": "${CLEARBIT_API_KEY}", "timeout": 15},
            ),
            ToolConfig(
                id="faq_database",
                name="FAQ Database",
                description="Internal FAQ knowledge base",
                enabled=True,
                provider="internal",
                config={"database_path": "faq.json", "similarity_threshold": 0.8},
            ),
        ]

        for tool in tools:
            self.save_tool_config(tool)

    # Agent configuration methods
    def save_agent_config(
            self,
            agent: AgentConfig,
            change_description: str = ""):
        """Save agent configuration to file with version control"""
        # Update version if this is an existing agent
        existing_agent = self.load_agent_config(agent.id)
        if existing_agent:
            agent.version = existing_agent.version + 1
            agent.created_at = existing_agent.created_at

        # Save to file
        file_path = self.config_dir / "agents" / f"{agent.id}.json"
        with open(file_path, "w") as f:
            json.dump(asdict(agent), f, indent=2)

        # Save version history
        self._save_version_history(
            "agent",
            agent.id,
            json.dumps(asdict(agent), indent=2),
            agent.version,
            change_description,
        )

        logger.info(f"Saved agent config: {agent.id} (v{agent.version})")

    def load_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration from file"""
        file_path = self.config_dir / "agents" / f"{agent_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return AgentConfig(**data)
        return None

    def list_agents(self) -> List[AgentConfig]:
        """List all agent configurations"""
        agents = []
        for file_path in (self.config_dir / "agents").glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                agents.append(AgentConfig(**data))
        return agents

    def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration"""
        file_path = self.config_dir / "agents" / f"{agent_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted agent config: {agent_id}")
            return True
        return False

    # Prompt template methods
    def save_prompt_template(
        self, prompt: PromptTemplate, change_description: str = ""
    ):
        """Save prompt template to file with version control"""
        # Update version if this is an existing prompt
        existing_prompt = self.load_prompt_template(prompt.id)
        if existing_prompt:
            prompt.version = existing_prompt.version + 1
            prompt.created_at = existing_prompt.created_at

        # Save to file
        file_path = self.config_dir / "prompts" / f"{prompt.id}.json"
        with open(file_path, "w") as f:
            json.dump(asdict(prompt), f, indent=2)

        # Save version history
        self._save_version_history(
            "prompt",
            prompt.id,
            json.dumps(asdict(prompt), indent=2),
            prompt.version,
            change_description,
        )

        logger.info(f"Saved prompt template: {prompt.id} (v{prompt.version})")

    def load_prompt_template(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Load prompt template from file"""
        file_path = self.config_dir / "prompts" / f"{prompt_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return PromptTemplate(**data)
        return None

    def list_prompts(self) -> List[PromptTemplate]:
        """List all prompt templates"""
        prompts = []
        for file_path in (self.config_dir / "prompts").glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                prompts.append(PromptTemplate(**data))
        return prompts

    def delete_prompt_template(self, prompt_id: str) -> bool:
        """Delete prompt template"""
        file_path = self.config_dir / "prompts" / f"{prompt_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted prompt template: {prompt_id}")
            return True
        return False

    # Workflow configuration methods
    def save_workflow_config(
        self, workflow: WorkflowConfig, change_description: str = ""
    ):
        """Save workflow configuration to file with version control"""
        # Update version if this is an existing workflow
        existing_workflow = self.load_workflow_config(workflow.id)
        if existing_workflow:
            workflow.version = existing_workflow.version + 1
            workflow.created_at = existing_workflow.created_at

        # Save to file
        file_path = self.config_dir / "workflows" / f"{workflow.id}.json"
        with open(file_path, "w") as f:
            json.dump(asdict(workflow), f, indent=2)

        # Save version history
        self._save_version_history(
            "workflow",
            workflow.id,
            json.dumps(asdict(workflow), indent=2),
            workflow.version,
            change_description,
        )

        logger.info(
            f"Saved workflow config: {workflow.id} (v{workflow.version})")

    def load_workflow_config(
            self,
            workflow_id: str) -> Optional[WorkflowConfig]:
        """Load workflow configuration from file"""
        file_path = self.config_dir / "workflows" / f"{workflow_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return WorkflowConfig(**data)
        return None

    def list_workflows(self) -> List[WorkflowConfig]:
        """List all workflow configurations"""
        workflows = []
        for file_path in (self.config_dir / "workflows").glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                workflows.append(WorkflowConfig(**data))
        return workflows

    def delete_workflow_config(self, workflow_id: str) -> bool:
        """Delete workflow configuration"""
        file_path = self.config_dir / "workflows" / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted workflow config: {workflow_id}")
            return True
        return False

    # Tool configuration methods
    def save_tool_config(self, tool: ToolConfig):
        """Save tool configuration to file"""
        file_path = self.config_dir / "tools" / f"{tool.id}.json"
        with open(file_path, "w") as f:
            json.dump(asdict(tool), f, indent=2)
        logger.info(f"Saved tool config: {tool.id}")

    def load_tool_config(self, tool_id: str) -> Optional[ToolConfig]:
        """Load tool configuration from file"""
        file_path = self.config_dir / "tools" / f"{tool_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return ToolConfig(**data)
        return None

    def list_tools(self) -> List[ToolConfig]:
        """List all tool configurations"""
        tools = []
        for file_path in (self.config_dir / "tools").glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                tools.append(ToolConfig(**data))
        return tools

    def delete_tool_config(self, tool_id: str) -> bool:
        """Delete tool configuration"""
        file_path = self.config_dir / "tools" / f"{tool_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted tool config: {tool_id}")
            return True
        return False

    # Model registry methods
    def save_model_config(
            self,
            model: ModelConfig,
            change_description: str = ""):
        """Save model configuration to file with version control"""
        existing_model = self.load_model_config(model.id)
        if existing_model:
            model.version = existing_model.version + 1
            model.created_at = existing_model.created_at
        file_path = self.config_dir / "models" / f"{model.id}.json"
        with open(file_path, "w") as f:
            json.dump(asdict(model), f, indent=2)
        # Save version history
        self._save_version_history(
            "model",
            model.id,
            json.dumps(asdict(model), indent=2),
            model.version,
            change_description,
        )
        logger.info(f"Saved model config: {model.id} (v{model.version})")

    def load_model_config(self, model_id: str) -> Optional[ModelConfig]:
        file_path = self.config_dir / "models" / f"{model_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return ModelConfig(**data)
        return None

    def list_models(self) -> List[ModelConfig]:
        models = []
        for file_path in (self.config_dir / "models").glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                models.append(ModelConfig(**data))
        return models

    def delete_model_config(self, model_id: str) -> bool:
        file_path = self.config_dir / "models" / f"{model_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted model config: {model_id}")
            return True
        return False

    # Backup and restore methods
    def backup_configs(self, backup_path: str):
        """Backup all configurations"""
        shutil.copytree(self.config_dir, backup_path)
        logger.info(f"Backed up configurations to: {backup_path}")

    def restore_configs(self, backup_path: str):
        """Restore configurations from backup"""
        if os.path.exists(backup_path):
            shutil.rmtree(self.config_dir)
            shutil.copytree(backup_path, self.config_dir)
            logger.info(f"Restored configurations from: {backup_path}")
        else:
            raise FileNotFoundError(f"Backup path not found: {backup_path}")


# Global instance
config_manager = ConfigManager()
