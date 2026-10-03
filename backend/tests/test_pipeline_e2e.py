"""End-to-end test: Pipeline agent qualifies lead, gates CRM write, gets approval."""
import pytest
import asyncio
import json
from uuid import uuid4
from datetime import datetime

from app.agents.orchestrator import create_default_agents
from app.agents.dispatch import OrchestratorDispatch, TaskEnvelope
from app.tools.manager import ToolManager
from app.models import ActionType, ApprovalStatus
from app.database import get_supabase


@pytest.fixture
def org_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


@pytest.fixture
async def setup_org(org_id, user_id):
    """Create test org and setup."""
    supabase = get_supabase()

    # Create org
    supabase.table("org").insert({
        "id": str(org_id),
        "name": "Test Org",
        "slug": f"test-{org_id}",
        "subscription_tier": "saas"
    }).execute()

    # Create user
    supabase.table("user").insert({
        "id": str(user_id),
        "auth_user_id": str(uuid4()),
        "org_id": str(org_id),
        "email": "shawn@example.com",
        "full_name": "Shawn Getty",
        "role": "owner"
    }).execute()

    # Create default agents
    await create_default_agents(org_id)

    yield org_id, user_id

    # Cleanup
    supabase.table("org").delete().eq("id", str(org_id)).execute()


@pytest.mark.asyncio
async def test_pipeline_agent_e2e(setup_org, conversation_id):
    """Test: Lead comes in → Pipeline qualifies → CRM write gated → approval flow → logged."""
    org_id, user_id = setup_org
    supabase = get_supabase()

    # Simulate a webhook lead coming in
    fake_lead = {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "555-1234",
        "message": "Interested in your properties",
        "source": "website_form"
    }

    # Create conversation
    conv = supabase.table("conversation").insert({
        "org_id": str(org_id),
        "user_id": str(user_id),
        "channel": "webhook",
        "title": f"Inbound lead: {fake_lead['name']}"
    }).execute()
    conversation_id = conv.data[0]["id"]

    # Initialize orchestrator
    orchestrator = OrchestratorDispatch(org_id, user_id)

    # Simulate lead coming in
    # In real flow: webhook → "inbound_lead" event → orchestrator
    # For test: directly call pipeline agent

    # Create a task envelope
    task = TaskEnvelope(
        task_id="test_lead_task_001",
        user_message=f"New lead: {json.dumps(fake_lead)}",
        org_id=org_id,
        user_id=user_id,
        conversation_id=conversation_id
    )

    # Execute task
    result = await orchestrator._orchestrate(task)

    # Verify result
    assert result["status"] in ["success", "clarification_needed"]

    # Check that a delegation happened to lead_qualification
    delegations = result.get("delegations", [])
    assert any(d["agent"] == "lead_qualification" for d in delegations), \
        f"Expected lead_qualification delegation, got {delegations}"

    # Verify actions_log was created
    logs = supabase.table("actions_log").select("*").eq(
        "org_id", str(org_id)
    ).execute()

    assert len(logs.data) > 0, "No action logs created"

    # Verify usage was logged
    usages = supabase.table("usage").select("*").eq(
        "org_id", str(org_id)
    ).execute()

    assert len(usages.data) > 0, "No usage logged"

    # Verify tokens were tracked
    usage = usages.data[0]
    assert usage["model_tokens_input"] > 0, "No tokens tracked"

    print(f"✅ Lead qualified successfully")
    print(f"   Task: {task.task_id}")
    print(f"   Hops: {task.hops}/{task.max_hops}")
    print(f"   Tokens: {task.tokens_used}/{task.token_budget}")
    print(f"   Model calls: {len(task.model_calls or [])}")

    return task, result


@pytest.mark.asyncio
async def test_approval_gate_for_crm_write(setup_org, conversation_id):
    """Test: CRM write goes through approval gate."""
    org_id, user_id = setup_org
    supabase = get_supabase()

    # Initialize tool manager
    tool_manager = ToolManager(supabase)

    # Attempt CRM write (should be gated)
    result = await tool_manager.execute_tool(
        agent_id=None,
        agent_role="lead_qualification",
        tool_name="crm_write",
        tool_params={
            "entity_type": "contact",
            "action": "create",
            "data": {
                "name": "John Smith",
                "email": "john@example.com",
                "relationship_type": "lead"
            }
        },
        org_id=org_id,
        user_id=user_id,
        conversation_id=conversation_id
    )

    # Verify approval is required
    assert result["status"] == "approval_required", \
        f"Expected approval_required, got {result['status']}"

    approval_id = result.get("approval_id")
    assert approval_id, "No approval_id returned"

    # Check that approval request was created in actions_log
    approvals = supabase.table("actions_log").select("*").eq(
        "approval_status", ApprovalStatus.PENDING.value
    ).execute()

    assert len(approvals.data) > 0, "No approval request created"

    print(f"✅ CRM write gated successfully")
    print(f"   Approval ID: {approval_id}")


@pytest.mark.asyncio
async def test_email_draft_flow(setup_org, conversation_id):
    """Test: Communications agent drafts email, doesn't send."""
    org_id, user_id = setup_org
    supabase = get_supabase()

    tool_manager = ToolManager(supabase)

    # Draft an email (no approval needed)
    draft_result = await tool_manager.execute_tool(
        agent_id=None,
        agent_role="communications",
        tool_name="email_draft",
        tool_params={
            "to": "john@example.com",
            "subject": "Thank you for your interest",
            "body": "Hi John, thanks for reaching out..."
        },
        org_id=org_id,
        user_id=user_id,
        conversation_id=conversation_id
    )

    assert draft_result["status"] == "drafted", \
        f"Expected drafted status, got {draft_result}"

    draft_id = draft_result.get("draft_id")
    assert draft_id, "No draft_id returned"

    print(f"✅ Email drafted successfully")
    print(f"   Draft ID: {draft_id}")
    print(f"   To: {draft_result['to']}")
    print(f"   Subject: {draft_result['subject']}")

    return draft_result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
