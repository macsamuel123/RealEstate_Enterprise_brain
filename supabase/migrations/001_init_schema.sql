-- Layer 1: Auth + Database Schema
-- AI Chief of Staff for Real Estate
-- Tenant isolation via org_id + RLS

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- ORGANIZATIONS (Tenants)
-- ============================================================================
CREATE TABLE orgs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  subscription_tier TEXT DEFAULT 'free' -- free, saas, custom
);

ALTER TABLE orgs ENABLE ROW LEVEL SECURITY;

-- All users can see their own org
CREATE POLICY orgs_select ON orgs
  FOR SELECT USING (
    id = (SELECT org_id FROM users WHERE auth.uid() = auth_user_id LIMIT 1)
  );

-- ============================================================================
-- USERS
-- ============================================================================
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  role TEXT DEFAULT 'member', -- owner, admin, member, viewer
  full_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(auth_user_id, org_id)
);

CREATE INDEX users_org_id_idx ON users(org_id);
CREATE INDEX users_auth_user_id_idx ON users(auth_user_id);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can see other users in their org
CREATE POLICY users_select ON users
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- Users can update their own profile
CREATE POLICY users_update ON users
  FOR UPDATE USING (auth.uid() = auth_user_id)
  WITH CHECK (auth.uid() = auth_user_id);

-- ============================================================================
-- PROFILES (Onboarding output)
-- ============================================================================
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Business profile
  business_name TEXT,
  business_type TEXT, -- real_estate, consultant, agency, broker, etc
  industry TEXT,
  market_description TEXT,

  -- Market info
  primary_market TEXT, -- e.g. "Calgary AB"
  competitors JSONB, -- array of competitor names/info
  market_focus JSONB, -- array of focus areas

  -- Work style
  working_hours_start TIME,
  working_hours_end TIME,
  timezone TEXT DEFAULT 'America/Denver',

  -- Communication preferences
  communication_style TEXT, -- formal, casual, direct, etc

  -- Personal interests for briefing
  personal_interests JSONB, -- array of topics they follow (sport, politics, etc)

  -- Morning ritual
  morning_ritual TEXT, -- meditation, prayer, music, motivational, etc
  morning_ritual_duration_minutes INT DEFAULT 15,

  -- Operational metrics targets
  target_lead_response_time_minutes INT DEFAULT 60,
  target_follow_up_touchpoints INT DEFAULT 5,

  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX profiles_org_id_idx ON profiles(org_id);
CREATE INDEX profiles_user_id_idx ON profiles(user_id);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select ON profiles
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

CREATE POLICY profiles_insert ON profiles
  FOR INSERT WITH CHECK (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

CREATE POLICY profiles_update ON profiles
  FOR UPDATE USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id))
  WITH CHECK (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- AGENTS (Agent definitions)
-- ============================================================================
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  name TEXT NOT NULL,
  role TEXT NOT NULL, -- research, lead_qualification, content, communications, operational_heartbeat, concierge, custom
  description TEXT,

  -- Agent configuration
  system_prompt TEXT NOT NULL,
  model TEXT DEFAULT 'claude-opus-5-5', -- which model to use
  temperature FLOAT DEFAULT 0.7,
  max_tokens INT DEFAULT 2000,

  -- Permissions
  permitted_tools JSONB DEFAULT '[]', -- array of tool names this agent can call
  requires_approval BOOLEAN DEFAULT TRUE, -- whether writes/sends need approval

  -- Scheduling
  should_run_on_schedule BOOLEAN DEFAULT FALSE,
  schedule_cron TEXT, -- cron expression if scheduled

  is_system_provided BOOLEAN DEFAULT FALSE, -- whether this is a standard agent
  is_active BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX agents_org_id_idx ON agents(org_id);
CREATE INDEX agents_role_idx ON agents(role);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY agents_select ON agents
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

CREATE POLICY agents_insert ON agents
  FOR INSERT WITH CHECK (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- CONVERSATIONS
-- ============================================================================
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

  channel TEXT DEFAULT 'chat', -- chat, voice, call, email, sms
  title TEXT,

  participants JSONB, -- array of user/contact ids in this conversation

  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ended_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX conversations_org_id_idx ON conversations(org_id);
CREATE INDEX conversations_user_id_idx ON conversations(user_id);
CREATE INDEX conversations_agent_id_idx ON conversations(agent_id);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_select ON conversations
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- MESSAGES
-- ============================================================================
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

  role TEXT NOT NULL, -- user, assistant, system
  content TEXT NOT NULL,

  -- Embeddings for memory
  embedding VECTOR(1536),

  metadata JSONB DEFAULT '{}', -- tokens, latency, model version, etc

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX messages_org_id_idx ON messages(org_id);
CREATE INDEX messages_conversation_id_idx ON messages(conversation_id);
CREATE INDEX messages_embedding_idx ON messages USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY messages_select ON messages
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- CONTACTS
-- ============================================================================
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  company TEXT,

  -- Relationship info
  relationship_type TEXT, -- lead, client, prospect, agent, other
  last_contacted_at TIMESTAMP WITH TIME ZONE,

  -- Semantic memory embedding
  embedding VECTOR(1536),

  metadata JSONB DEFAULT '{}', -- custom fields per vertical

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX contacts_org_id_idx ON contacts(org_id);
CREATE INDEX contacts_embedding_idx ON contacts USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY contacts_select ON contacts
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- DEALS / PIPELINE
-- ============================================================================
CREATE TABLE deals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,

  title TEXT NOT NULL,
  description TEXT,

  -- Pipeline tracking
  stage TEXT NOT NULL, -- lead, qualified, proposal, negotiation, closed_won, closed_lost
  value DECIMAL(12, 2),
  probability INT DEFAULT 50, -- 0-100

  -- Dates
  created_date DATE,
  expected_close_date DATE,
  closed_date DATE,

  -- Activity tracking
  last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX deals_org_id_idx ON deals(org_id);
CREATE INDEX deals_stage_idx ON deals(stage);
CREATE INDEX deals_contact_id_idx ON deals(contact_id);

ALTER TABLE deals ENABLE ROW LEVEL SECURITY;

CREATE POLICY deals_select ON deals
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- TASKS / COMMITMENTS
-- ============================================================================
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  title TEXT NOT NULL,
  description TEXT,

  due_date DATE,
  completed_at TIMESTAMP WITH TIME ZONE,

  priority TEXT DEFAULT 'medium', -- low, medium, high, critical

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX tasks_org_id_idx ON tasks(org_id);
CREATE INDEX tasks_owner_id_idx ON tasks(owner_id);
CREATE INDEX tasks_due_date_idx ON tasks(due_date);

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tasks_select ON tasks
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- MEMORIES (Durable facts and decisions)
-- ============================================================================
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  fact TEXT NOT NULL,
  category TEXT, -- preference, decision, context, relationship, operational

  source TEXT, -- which conversation/document this came from
  source_id UUID, -- reference to conversation/message/document

  -- Embeddings for semantic recall
  embedding VECTOR(1536),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX memories_org_id_idx ON memories(org_id);
CREATE INDEX memories_category_idx ON memories(category);
CREATE INDEX memories_embedding_idx ON memories USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY memories_select ON memories
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- DOCUMENTS (Uploaded files, chunked + embedded)
-- ============================================================================
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  filename TEXT NOT NULL,
  file_type TEXT, -- pdf, docx, txt, csv, etc
  file_size INT,

  content TEXT,
  chunks JSONB, -- array of text chunks

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX documents_org_id_idx ON documents(org_id);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY documents_select ON documents
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- CONNECTIONS (OAuth tokens and credentials - stored as vaulted references)
-- ============================================================================
CREATE TABLE connections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  service TEXT NOT NULL, -- gmail, google_calendar, crm, slack, etc
  service_account_id TEXT, -- email or account ID at the service

  -- Vault reference (not raw token)
  vault_key_id UUID,

  is_active BOOLEAN DEFAULT TRUE,
  last_synced_at TIMESTAMP WITH TIME ZONE,
  sync_error TEXT,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX connections_org_id_idx ON connections(org_id);
CREATE INDEX connections_service_idx ON connections(service);

ALTER TABLE connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY connections_select ON connections
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- ACTIONS_LOG (Audit trail - every tool call, agent action, timestamp, approval)
-- ============================================================================
CREATE TABLE actions_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

  action_type TEXT NOT NULL, -- tool_call, agent_dispatch, approval_request, etc
  tool_name TEXT, -- which tool was called

  input_data JSONB,
  output_data JSONB,

  approval_required BOOLEAN DEFAULT FALSE,
  approval_status TEXT, -- pending, approved, denied
  approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_at TIMESTAMP WITH TIME ZONE,

  status TEXT DEFAULT 'success', -- success, error, pending
  error_message TEXT,

  metadata JSONB DEFAULT '{}',

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX actions_log_org_id_idx ON actions_log(org_id);
CREATE INDEX actions_log_user_id_idx ON actions_log(user_id);
CREATE INDEX actions_log_agent_id_idx ON actions_log(agent_id);
CREATE INDEX actions_log_created_at_idx ON actions_log(created_at DESC);
CREATE INDEX actions_log_approval_status_idx ON actions_log(approval_status);

ALTER TABLE actions_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY actions_log_select ON actions_log
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- USAGE (Voice exchanges, model tokens - drives billing)
-- ============================================================================
CREATE TABLE usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,

  period_start DATE NOT NULL,
  period_end DATE NOT NULL,

  voice_exchanges INT DEFAULT 0,
  voice_minutes DECIMAL(10, 2) DEFAULT 0,
  model_tokens_input INT DEFAULT 0,
  model_tokens_output INT DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX usage_org_id_idx ON usage(org_id);
CREATE INDEX usage_period_idx ON usage(period_start, period_end);
CREATE UNIQUE INDEX usage_org_period_idx ON usage(org_id, period_start, period_end);

ALTER TABLE usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY usage_select ON usage
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- BRIEFS (Generated daily briefs - for history and value recap)
-- ============================================================================
CREATE TABLE briefs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  brief_date DATE NOT NULL,

  -- Brief sections (as JSONB for flexibility)
  content JSONB, -- {calendar, emails, market_news, competitors, personal_interests}

  delivered_at TIMESTAMP WITH TIME ZONE,
  delivery_channel TEXT, -- email, sms, voice

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX briefs_org_id_idx ON briefs(org_id);
CREATE INDEX briefs_user_id_idx ON briefs(user_id);
CREATE INDEX briefs_brief_date_idx ON briefs(brief_date);

ALTER TABLE briefs ENABLE ROW LEVEL SECURITY;

CREATE POLICY briefs_select ON briefs
  FOR SELECT USING (org_id IN (SELECT org_id FROM users WHERE auth.uid() = auth_user_id));

-- ============================================================================
-- BENCHMARKS (Phase 2 - anonymized aggregate metrics by vertical + geography)
-- ============================================================================
CREATE TABLE benchmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  vertical TEXT NOT NULL, -- real_estate, consultant, broker, etc
  geography TEXT NOT NULL, -- e.g. "Calgary AB"

  metric_name TEXT NOT NULL, -- response_time, conversion_rate, follow_up_cadence, etc
  metric_value DECIMAL(10, 2),

  sample_size INT,
  percentile INT, -- 25, 50 (median), 75

  calculated_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX benchmarks_vertical_geography_idx ON benchmarks(vertical, geography);
CREATE UNIQUE INDEX benchmarks_unique_idx ON benchmarks(vertical, geography, metric_name, percentile);

-- Benchmarks table has no org_id - it is aggregate data visible to all tenants
-- No RLS needed; read-only, pre-computed

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_orgs_updated_at BEFORE UPDATE ON orgs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_connections_updated_at BEFORE UPDATE ON connections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_updated_at BEFORE UPDATE ON usage
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
