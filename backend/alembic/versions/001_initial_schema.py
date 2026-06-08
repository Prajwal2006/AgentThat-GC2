"""Initial schema - all platform tables

Revision ID: 001
Revises: None
Create Date: 2024-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Tenants ───────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("tier", sa.String(20), server_default="standard"),
        sa.Column("max_concurrent_jobs", sa.Integer, server_default="5"),
        sa.Column("data_residency_region", sa.String(50), nullable=True),
        sa.Column("session_timeout_minutes", sa.Integer, server_default="480"),
        sa.Column("token_refresh_interval_minutes", sa.Integer, server_default="15"),
        sa.Column("mfa_required", sa.Boolean, server_default="false"),
        sa.Column("hourly_cost_rate", sa.Numeric(10, 2), server_default="75.00"),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("audit_retention_days", sa.Integer, server_default="365"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ─── Users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=False),
        sa.Column("email", sa.String(240), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(20), server_default="user"),
        sa.Column("status", sa.String(20), server_default="invited"),
        sa.Column("group_memberships", JSONB, server_default="[]"),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "email"),
        sa.UniqueConstraint("tenant_id", "external_id"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # ─── Teams ─────────────────────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("department", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "name"),
    )
    op.create_index("ix_teams_tenant_id", "teams", ["tenant_id"])

    # ─── Team Memberships ──────────────────────────────────────────────────
    op.create_table(
        "team_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), server_default="member"),
        sa.Column("joined_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "user_id"),
    )

    # ─── Agents ────────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("category", sa.String(80), server_default="General"),
        sa.Column("lifecycle_state", sa.String(20), server_default="draft"),
        sa.Column("deprecation_message", sa.String(500), nullable=True),
        sa.Column("replacement_agent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("usage_count", sa.Integer, server_default="0"),
        sa.Column("current_version", sa.Integer, server_default="1"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_agents_tenant_id", "agents", ["tenant_id"])
    op.create_index("ix_agents_tenant_lifecycle", "agents", ["tenant_id", "lifecycle_state"])

    # ─── Agent Versions ────────────────────────────────────────────────────
    op.create_table(
        "agent_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("components", JSONB, nullable=False),
        sa.Column("connections", JSONB, nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("tools", JSONB, server_default="[]"),
        sa.Column("memory_config", JSONB, nullable=True),
        sa.Column("handoff_rules", JSONB, nullable=True),
        sa.Column("rag_config", JSONB, nullable=True),
        sa.Column("governance_defaults", JSONB, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("agent_id", "version_number"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])
    op.create_index("ix_agent_versions_tenant_id", "agent_versions", ["tenant_id"])

    # ─── Agent State Transitions ───────────────────────────────────────────
    op.create_table(
        "agent_state_transitions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("from_state", sa.String(20), nullable=False),
        sa.Column("to_state", sa.String(20), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("transitioned_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_state_transitions_agent_id", "agent_state_transitions", ["agent_id"])
    op.create_index("ix_agent_state_transitions_tenant_id", "agent_state_transitions", ["tenant_id"])

    # ─── Workflows ─────────────────────────────────────────────────────────
    op.create_table(
        "workflows",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("agent_count", sa.Integer, server_default="1"),
        sa.Column("current_version", sa.Integer, server_default="1"),
        sa.Column("last_run_at", sa.DateTime, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_workflows_tenant_id", "workflows", ["tenant_id"])
    op.create_index("ix_workflows_tenant_status", "workflows", ["tenant_id", "status"])

    # ─── Workflow Versions ─────────────────────────────────────────────────
    op.create_table(
        "workflow_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("steps", JSONB, nullable=False),
        sa.Column("routing_config", JSONB, nullable=False),
        sa.Column("retry_config", JSONB, nullable=False),
        sa.Column("timeout_config", JSONB, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("workflow_id", "version_number"),
    )
    op.create_index("ix_workflow_versions_workflow_id", "workflow_versions", ["workflow_id"])
    op.create_index("ix_workflow_versions_tenant_id", "workflow_versions", ["tenant_id"])

    # ─── Workflow Steps ────────────────────────────────────────────────────
    op.create_table(
        "workflow_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_version_id", UUID(as_uuid=True), sa.ForeignKey("workflow_versions.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("execution_type", sa.String(20), nullable=False),
        sa.Column("config", JSONB, nullable=False),
    )
    op.create_index("ix_workflow_steps_tenant_id", "workflow_steps", ["tenant_id"])

    # ─── Execution Runs ────────────────────────────────────────────────────
    op.create_table(
        "execution_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("version_id", UUID(as_uuid=True), sa.ForeignKey("workflow_versions.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("current_step_index", sa.Integer, server_default="0"),
        sa.Column("total_steps", sa.Integer, nullable=False),
        sa.Column("execution_state", JSONB, nullable=True),
        sa.Column("input_data", JSONB, nullable=True),
        sa.Column("output_data", JSONB, nullable=True),
        sa.Column("total_cost_usd", sa.Numeric(10, 4), server_default="0"),
        sa.Column("total_tokens_input", sa.Integer, server_default="0"),
        sa.Column("total_tokens_output", sa.Integer, server_default="0"),
        sa.Column("total_latency_ms", sa.Integer, server_default="0"),
        sa.Column("error_count", sa.Integer, server_default="0"),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_step_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("initiated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_execution_runs_tenant_id", "execution_runs", ["tenant_id"])
    op.create_index("ix_execution_runs_workflow_started", "execution_runs", ["workflow_id", "started_at"])

    # ─── Step Executions ───────────────────────────────────────────────────
    op.create_table(
        "step_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", UUID(as_uuid=True), sa.ForeignKey("execution_runs.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", sa.String(100), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("input_data", JSONB, nullable=True),
        sa.Column("output_data", JSONB, nullable=True),
        sa.Column("error_details", JSONB, nullable=True),
        sa.Column("retry_attempts", sa.Integer, server_default="0"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 4), server_default="0"),
        sa.Column("tokens_input", sa.Integer, server_default="0"),
        sa.Column("tokens_output", sa.Integer, server_default="0"),
        sa.Column("latency_ms", sa.Integer, server_default="0"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_step_executions_execution_id", "step_executions", ["execution_id"])
    op.create_index("ix_step_executions_tenant_id", "step_executions", ["tenant_id"])

    # ─── Context Entries ───────────────────────────────────────────────────
    op.create_table(
        "context_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_run_id", UUID(as_uuid=True), sa.ForeignKey("execution_runs.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("contributing_agent_id", UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_context_entries_execution_run_id", "context_entries", ["execution_run_id"])
    op.create_index("ix_context_entries_tenant_id", "context_entries", ["tenant_id"])

    # ─── Execution Logs ────────────────────────────────────────────────────
    op.create_table(
        "execution_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("step_id", sa.String(100), nullable=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_execution_logs_execution_id", "execution_logs", ["execution_id"])
    op.create_index("ix_execution_logs_tenant_id", "execution_logs", ["tenant_id"])

    # ─── Marketplace Listings ──────────────────────────────────────────────
    op.create_table(
        "marketplace_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("listing_type", sa.String(30), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("creator_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("install_count", sa.Integer, server_default="0"),
        sa.Column("average_rating", sa.Numeric(3, 2), server_default="0.00"),
        sa.Column("rating_count", sa.Integer, server_default="0"),
        sa.Column("asset_snapshot", JSONB, nullable=False),
        sa.Column("published_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "name"),
    )
    op.create_index("ix_marketplace_listings_tenant_id", "marketplace_listings", ["tenant_id"])

    # ─── Ratings ───────────────────────────────────────────────────────────
    op.create_table(
        "ratings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.Numeric(2, 1), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("listing_id", "user_id"),
    )
    op.create_index("ix_ratings_listing_id", "ratings", ["listing_id"])
    op.create_index("ix_ratings_tenant_id", "ratings", ["tenant_id"])

    # ─── Reviews ───────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.String(2000), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("listing_id", "user_id"),
    )
    op.create_index("ix_reviews_listing_id", "reviews", ["listing_id"])
    op.create_index("ix_reviews_tenant_id", "reviews", ["tenant_id"])

    # ─── Installs ──────────────────────────────────────────────────────────
    op.create_table(
        "installs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("installed_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_installs_listing_id", "installs", ["listing_id"])
    op.create_index("ix_installs_tenant_id", "installs", ["tenant_id"])

    # ─── Forks ─────────────────────────────────────────────────────────────
    op.create_table(
        "forks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("original_version", sa.Integer, nullable=False),
        sa.Column("forked_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_forks_listing_id", "forks", ["listing_id"])
    op.create_index("ix_forks_tenant_id", "forks", ["tenant_id"])

    # ─── Background Jobs ───────────────────────────────────────────────────
    op.create_table(
        "background_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("progress_pct", sa.Integer, server_default="0"),
        sa.Column("status_message", sa.String(200), nullable=True),
        sa.Column("input_data", JSONB, nullable=False),
        sa.Column("result_data", JSONB, nullable=True),
        sa.Column("error_detail", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("max_retries", sa.Integer, server_default="3"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_background_jobs_tenant_id", "background_jobs", ["tenant_id"])
    op.create_index("ix_background_jobs_tenant_status", "background_jobs", ["tenant_id", "status"])

    # ─── Audit Logs ────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=False),
        sa.Column("outcome", sa.String(10), nullable=False),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_tenant_timestamp", "audit_logs", ["tenant_id", "timestamp"])
    op.create_index("ix_audit_logs_tenant_user_timestamp", "audit_logs", ["tenant_id", "user_id", "timestamp"])

    # ─── MCP Servers ───────────────────────────────────────────────────────
    op.create_table(
        "mcp_servers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("current_version", sa.Integer, server_default="1"),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_mcp_servers_tenant_id", "mcp_servers", ["tenant_id"])

    # ─── MCP Server Versions ──────────────────────────────────────────────
    op.create_table(
        "mcp_server_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("mcp_server_id", UUID(as_uuid=True), sa.ForeignKey("mcp_servers.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("config", JSONB, nullable=False),
        sa.Column("is_valid", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("mcp_server_id", "version_number"),
    )
    op.create_index("ix_mcp_server_versions_mcp_server_id", "mcp_server_versions", ["mcp_server_id"])
    op.create_index("ix_mcp_server_versions_tenant_id", "mcp_server_versions", ["tenant_id"])

    # ─── Courses ───────────────────────────────────────────────────────────
    op.create_table(
        "courses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("duration_hours", sa.Numeric(4, 1), nullable=False),
        sa.Column("lesson_count", sa.Integer, nullable=False),
        sa.Column("topic", sa.String(80), nullable=False),
        sa.Column("prerequisite_ids", JSONB, server_default="[]"),
        sa.Column("assessment_config", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_courses_tenant_id", "courses", ["tenant_id"])

    # ─── Learning Paths ────────────────────────────────────────────────────
    op.create_table(
        "learning_paths",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("persona", sa.String(50), nullable=False),
        sa.Column("course_ids", JSONB, server_default="[]"),
        sa.Column("certification_name", sa.String(120), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_learning_paths_tenant_id", "learning_paths", ["tenant_id"])

    # ─── Enrollments ───────────────────────────────────────────────────────
    op.create_table(
        "enrollments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="available"),
        sa.Column("completion_pct", sa.Integer, server_default="0"),
        sa.Column("time_spent_minutes", sa.Integer, server_default="0"),
        sa.Column("lessons_completed", sa.Integer, server_default="0"),
        sa.Column("assessment_score", sa.Integer, nullable=True),
        sa.Column("last_attempt_at", sa.DateTime, nullable=True),
        sa.Column("enrolled_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("user_id", "course_id"),
    )
    op.create_index("ix_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])
    op.create_index("ix_enrollments_tenant_id", "enrollments", ["tenant_id"])

    # ─── Certifications ────────────────────────────────────────────────────
    op.create_table(
        "certifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("learning_path_id", UUID(as_uuid=True), nullable=False),
        sa.Column("earned_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_certifications_user_id", "certifications", ["user_id"])
    op.create_index("ix_certifications_tenant_id", "certifications", ["tenant_id"])


def downgrade() -> None:
    tables = [
        "certifications", "enrollments", "learning_paths", "courses",
        "mcp_server_versions", "mcp_servers",
        "audit_logs", "background_jobs",
        "forks", "installs", "reviews", "ratings", "marketplace_listings",
        "execution_logs", "context_entries", "step_executions", "execution_runs",
        "workflow_steps", "workflow_versions", "workflows",
        "agent_state_transitions", "agent_versions", "agents",
        "team_memberships", "teams", "users", "tenants",
    ]
    for table in tables:
        op.drop_table(table)
