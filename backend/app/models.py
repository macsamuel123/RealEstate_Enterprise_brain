"""Database models for AI Chief of Staff."""
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum
from uuid import UUID
from sqlmodel import SQLModel, Field, JSON
from pydantic import EmailStr
import json

# ============================================================================
# ENUMS
# ============================================================================
class SubscriptionTier(str, Enum):
    FREE = "free"
    SAAS = "saas"
    CUSTOM = "custom"

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    MEMORY_SCRIBE = "memory_scribe"
    RESEARCH = "research"
    LEAD_QUALIFICATION = "lead_qualification"
    CONTENT = "content"
    COMMUNICATIONS = "communications"
    OPERATIONAL_HEARTBEAT = "operational_heartbeat"
    CONCIERGE = "concierge"
    AGENT_BUILDER = "agent_builder"
    CUSTOM = "custom"

class ConversationChannel(str, Enum):
    CHAT = "chat"
    VOICE = "voice"
    CALL = "call"
    EMAIL = "email"
    SMS = "sms"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class DealStage(str, Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    AGENT_DISPATCH = "agent_dispatch"
    APPROVAL_REQUEST = "approval_request"
    BRIEF_GENERATED = "brief_generated"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

# ============================================================================
# ORGANIZATION & USER MANAGEMENT
# ============================================================================
class Org(SQLModel, table=True):
    """Organization (tenant)."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE

class User(SQLModel, table=True):
    """User within an organization."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    auth_user_id: UUID
    org_id: UUID = Field(foreign_key="org.id")
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# PROFILE (Onboarding)
# ============================================================================
class Profile(SQLModel, table=True):
    """User's business profile from onboarding."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    user_id: UUID = Field(foreign_key="user.id")

    business_name: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    market_description: Optional[str] = None

    primary_market: Optional[str] = None  # e.g. "Calgary AB"
    competitors: Optional[dict] = Field(default=None, sa_type=JSON)
    market_focus: Optional[dict] = Field(default=None, sa_type=JSON)

    working_hours_start: Optional[time] = None
    working_hours_end: Optional[time] = None
    timezone: str = "America/Denver"

    communication_style: Optional[str] = None
    personal_interests: Optional[dict] = Field(default=None, sa_type=JSON)

    morning_ritual: Optional[str] = None
    morning_ritual_duration_minutes: int = 15

    target_lead_response_time_minutes: int = 60
    target_follow_up_touchpoints: int = 5

    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# AGENTS
# ============================================================================
class Agent(SQLModel, table=True):
    """Agent definition."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    name: str
    role: AgentRole
    description: Optional[str] = None

    system_prompt: str
    model: str = "claude-opus-5-5"
    temperature: float = 0.7
    max_tokens: int = 2000

    permitted_tools: Optional[dict] = Field(default=None, sa_type=JSON)
    requires_approval: bool = True

    should_run_on_schedule: bool = False
    schedule_cron: Optional[str] = None

    is_system_provided: bool = False
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# CONVERSATIONS & MESSAGES
# ============================================================================
class Conversation(SQLModel, table=True):
    """Conversation with an agent."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    user_id: UUID = Field(foreign_key="user.id")
    agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")

    channel: ConversationChannel = ConversationChannel.CHAT
    title: Optional[str] = None

    participants: Optional[dict] = Field(default=None, sa_type=JSON)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Message(SQLModel, table=True):
    """Message in a conversation."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    conversation_id: UUID = Field(foreign_key="conversation.id")

    role: MessageRole
    content: str

    embedding: Optional[dict] = Field(default=None, sa_type=JSON)  # vector(1536)
    message_metadata: Optional[dict] = Field(default=None, sa_type=JSON)

    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# CONTACTS & DEALS
# ============================================================================
class Contact(SQLModel, table=True):
    """Contact/person in the business."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None

    relationship_type: Optional[str] = None  # lead, client, prospect, agent
    last_contacted_at: Optional[datetime] = None

    embedding: Optional[dict] = Field(default=None, sa_type=JSON)
    contact_metadata: Optional[dict] = Field(default=None, sa_type=JSON)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Deal(SQLModel, table=True):
    """Pipeline opportunity."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    user_id: UUID = Field(foreign_key="user.id")
    contact_id: Optional[UUID] = Field(default=None, foreign_key="contact.id")

    title: str
    description: Optional[str] = None

    stage: DealStage
    value: Optional[float] = None
    probability: int = 50

    created_date: Optional[date] = None
    expected_close_date: Optional[date] = None
    closed_date: Optional[date] = None

    last_activity_at: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# TASKS & MEMORIES
# ============================================================================
class Task(SQLModel, table=True):
    """Task/commitment."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    owner_id: UUID = Field(foreign_key="user.id")

    title: str
    description: Optional[str] = None

    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None

    priority: str = "medium"  # low, medium, high, critical

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Memory(SQLModel, table=True):
    """Durable fact or decision."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    fact: str
    category: Optional[str] = None  # preference, decision, context, relationship, operational

    source: Optional[str] = None
    source_id: Optional[UUID] = None

    embedding: Optional[dict] = Field(default=None, sa_type=JSON)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# DOCUMENTS & CONNECTIONS
# ============================================================================
class Document(SQLModel, table=True):
    """Uploaded document."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None

    content: Optional[str] = None
    chunks: Optional[dict] = Field(default=None, sa_type=JSON)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Connection(SQLModel, table=True):
    """External service connection."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    service: str  # gmail, google_calendar, crm, slack, etc
    service_account_id: Optional[str] = None

    vault_key_id: Optional[UUID] = None

    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# AUDIT & USAGE
# ============================================================================
class ActionsLog(SQLModel, table=True):
    """Audit log of agent actions."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")

    action_type: ActionType
    tool_name: Optional[str] = None

    input_data: Optional[dict] = Field(default=None, sa_type=JSON)
    output_data: Optional[dict] = Field(default=None, sa_type=JSON)

    approval_required: bool = False
    approval_status: Optional[ApprovalStatus] = None
    approved_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    approved_at: Optional[datetime] = None

    status: str = "success"  # success, error, pending
    error_message: Optional[str] = None

    action_metadata: Optional[dict] = Field(default=None, sa_type=JSON)

    created_at: datetime = Field(default_factory=datetime.utcnow)

class Usage(SQLModel, table=True):
    """Usage tracking for billing."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")

    period_start: date
    period_end: date

    voice_exchanges: int = 0
    voice_minutes: float = 0.0
    model_tokens_input: int = 0
    model_tokens_output: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Brief(SQLModel, table=True):
    """Generated daily brief."""
    id: Optional[UUID] = Field(default=None, primary_key=True)
    org_id: UUID = Field(foreign_key="org.id")
    user_id: UUID = Field(foreign_key="user.id")

    brief_date: date
    content: Optional[dict] = Field(default=None, sa_type=JSON)

    delivered_at: Optional[datetime] = None
    delivery_channel: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

class Benchmark(SQLModel, table=True):
    """Aggregate metrics by vertical/geography (Phase 2)."""
    id: Optional[UUID] = Field(default=None, primary_key=True)

    vertical: str  # real_estate, consultant, broker, etc
    geography: str

    metric_name: str
    metric_value: Optional[float] = None

    sample_size: Optional[int] = None
    percentile: Optional[int] = None  # 25, 50, 75

    calculated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
