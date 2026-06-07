"""Solution Architect Service - Transforms requirements into architectures."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.config import settings


# Domain-relevant terms for business intent detection
DOMAIN_TERMS = {
    "customer", "employee", "report", "data", "workflow", "process", "sales",
    "support", "ticket", "email", "lead", "onboard", "approve", "review",
    "invoice", "payment", "order", "hr", "marketing", "finance", "compliance",
    "audit", "security", "document", "contract", "schedule", "notify",
    "alert", "dashboard", "analytics", "automate", "integrate", "monitor",
    "agent", "team", "department", "service", "product", "project",
}


@dataclass
class AgentSpec:
    name: str
    purpose: str
    system_prompt: str
    tools: list[str]
    handoff_rules: str
    memory_config: dict[str, Any] = field(default_factory=lambda: {
        "adapter_type": "short-term",
        "retention_policy": "session",
        "max_context_window": 8000,
    })


@dataclass
class WorkflowStepSpec:
    id: str
    name: str
    agent: str
    ordering: str  # sequential or parallel
    human_approval: bool = False


@dataclass
class GeneratedSolution:
    id: str
    name: str
    summary: str
    agents: list[AgentSpec]
    workflow: list[WorkflowStepSpec]
    integrations: list[str]
    governance: dict[str, Any]
    memory_config: dict[str, Any]
    rag_config: dict[str, Any]
    deployment_config: dict[str, Any]
    provider: str  # "azure_openai" or "deterministic"


class ValidationError(Exception):
    """Input validation failure."""
    pass


class BusinessIntentError(Exception):
    """Input lacks identifiable business intent."""
    pass


class SolutionArchitectService:
    """Transforms natural language business requirements into complete workflow architectures."""
    
    def validate_requirement(self, requirement: str) -> None:
        """Validate input length and business intent."""
        length = len(requirement)
        if length < 20 or length > 8000:
            raise ValidationError(
                f"Requirement must be between 20 and 8000 characters (got {length})"
            )
        
        # Check for business intent (minimum 2 domain-relevant terms)
        words = set(re.findall(r'\b\w+\b', requirement.lower()))
        matches = words & DOMAIN_TERMS
        if len(matches) < 2:
            raise BusinessIntentError(
                "Please refine your description to include business context such as "
                "a goal, process, or stakeholder. Try including details about who uses "
                "the solution, what business process it automates, and what outcomes you expect."
            )
    
    def fallback_generate(self, requirement: str, name: str = "AI Workflow") -> GeneratedSolution:
        """Rule-based fallback when LLM is unavailable."""
        tools = self._extract_tools(requirement)
        
        agents = [
            AgentSpec(
                name="Requirements Analyst",
                purpose="Transforms business request into structured objectives and constraints.",
                system_prompt="Identify goals, actors, data sources, risks, and measurable outcomes.",
                tools=["Policy Library", "Audit Log"],
                handoff_rules="Pass validated requirements to workflow planner.",
            ),
            AgentSpec(
                name="Workflow Orchestrator",
                purpose="Coordinates specialist agents, routing, retries, and approvals.",
                system_prompt="Execute workflow plan, route tasks, and pause for required approvals.",
                tools=tools,
                handoff_rules="Send completed work to reviewer.",
            ),
            AgentSpec(
                name="Knowledge Specialist",
                purpose="Retrieves enterprise knowledge and produces grounded context.",
                system_prompt="Search approved knowledge sources, cite sources, flag uncertainty.",
                tools=["Knowledge Base", "Vector Search"],
                handoff_rules="Return grounded context to active workflow step.",
                memory_config={"adapter_type": "semantic", "retention_policy": "persistent", "max_context_window": 16000},
            ),
            AgentSpec(
                name="Governance Reviewer",
                purpose="Checks outputs against security, compliance, and approval policies.",
                system_prompt="Review for risk, privacy, compliance before deployment.",
                tools=["Policy Library", "Human Approval Queue", "Audit Log"],
                handoff_rules="Approve, reject, or request revision with reasons.",
            ),
        ]
        
        workflow = [
            WorkflowStepSpec(id="step-1", name="Intake and classify", agent="Requirements Analyst", ordering="sequential"),
            WorkflowStepSpec(id="step-2", name="Retrieve context", agent="Knowledge Specialist", ordering="sequential"),
            WorkflowStepSpec(id="step-3", name="Execute workflow", agent="Workflow Orchestrator", ordering="sequential"),
            WorkflowStepSpec(id="step-4", name="Review and approve", agent="Governance Reviewer", ordering="sequential", human_approval=True),
        ]
        
        return GeneratedSolution(
            id=f"sol-{uuid.uuid4().hex[:8]}",
            name=name,
            summary=f"{name}: governed multi-agent workflow automating the described business process.",
            agents=agents,
            workflow=workflow,
            integrations=tools,
            governance={
                "tenant_isolation": True,
                "rbac_enforcement": True,
                "audit_logging": True,
                "human_approval_triggers": ["customer-facing output", "data mutation", "external communication"],
            },
            memory_config={
                "default_adapter": "short-term",
                "retention_policy": "session",
                "max_context_window": 8000,
            },
            rag_config={
                "knowledge_sources": ["enterprise_docs", "policy_library"],
                "embedding_model": "text-embedding-3-small",
                "chunking_strategy": "recursive",
                "retrieval_top_k": 5,
                "relevance_threshold": 0.75,
            },
            deployment_config={
                "environment": "development",
                "scaling": {"min_instances": 2, "max_instances": 10},
                "resource_limits": {"memory_mb": 512, "timeout_seconds": 30},
                "region": "us-east-1",
            },
            provider="deterministic",
        )
    
    async def generate(self, requirement: str, name: str = "AI Workflow") -> GeneratedSolution:
        """Generate solution using LLM, falling back to rule-based if unavailable."""
        self.validate_requirement(requirement)
        
        if not settings.azure_openai_configured:
            return self.fallback_generate(requirement, name)
        
        try:
            # TODO: Call Azure OpenAI with structured prompt for full architecture generation
            # For now, use fallback
            return self.fallback_generate(requirement, name)
        except Exception:
            return self.fallback_generate(requirement, name)
    
    def _extract_tools(self, requirement: str) -> list[str]:
        """Extract relevant tools from requirement keywords."""
        lower = requirement.lower()
        tools = ["Audit Log", "Human Approval Queue"]
        keyword_map = {
            "jira": "Jira", "salesforce": "Salesforce", "email": "Microsoft Outlook",
            "ticket": "Zendesk", "support": "Knowledge Base", "report": "Power BI",
            "slack": "Slack", "teams": "Microsoft Teams", "employee": "Microsoft Entra ID",
            "hr": "HRIS", "document": "SharePoint",
        }
        for keyword, tool in keyword_map.items():
            if keyword in lower and tool not in tools:
                tools.append(tool)
        return tools
