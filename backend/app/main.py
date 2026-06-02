from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    environment: str = Field(default_factory=lambda: os.getenv("AGENTTHAT_ENV", "development"))
    allowed_origins: list[str] = Field(
        default_factory=lambda: _csv_env(
            "AGENTTHAT_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        )
    )
    azure_openai_endpoint: str | None = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    azure_openai_api_key: str | None = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY"))
    azure_openai_deployment: str | None = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    azure_openai_api_version: str = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    )
    azure_openai_temperature: float = Field(
        default_factory=lambda: float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.2"))
    )

    @property
    def azure_openai_configured(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        )


settings = Settings()

app = FastAPI(title="AgentThat Backend", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImprovePromptRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=6000)
    business_context: str | None = Field(default=None, max_length=2000)


class ImprovePromptResponse(BaseModel):
    original_prompt: str
    improved_prompt: str
    improvements: list[str]
    provider: Literal["azure_openai", "deterministic"]


class GenerateSolutionRequest(BaseModel):
    name: str = Field(default="Untitled Solution", max_length=120)
    requirement: str = Field(min_length=8, max_length=8000)
    mode: Literal["agent", "workflow", "optimization"] = "workflow"
    department: str | None = Field(default=None, max_length=80)


class AgentSpec(BaseModel):
    name: str
    purpose: str
    prompt: str
    tools: list[str]
    handoff: str


class WorkflowStep(BaseModel):
    id: str
    name: str
    agent: str
    action: str
    human_approval: bool = False


class GeneratedSolution(BaseModel):
    id: str
    name: str
    summary: str
    improved_prompt: str
    agents: list[AgentSpec]
    workflow: list[WorkflowStep]
    integrations: list[str]
    governance: list[str]
    observability: list[str]
    deployment: dict[str, str]
    provider: Literal["azure_openai", "deterministic"]


class ManualAgentRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=4, max_length=1000)
    category: str = Field(default="General", max_length=80)


class SavedAgent(BaseModel):
    id: str
    name: str
    description: str
    status: str
    usage: int
    created: str
    category: str


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=8, max_length=1000)
    agents: int = Field(default=2, ge=1, le=12)


class WorkflowControlRequest(BaseModel):
    action: Literal["run", "pause", "resume"]


class ProfileSettings(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=240)
    role: Literal["Admin", "Developer", "User"]


class NotificationItem(BaseModel):
    label: str
    enabled: bool


class TeamMember(BaseModel):
    id: str
    name: str
    role: Literal["Admin", "Developer", "User"]
    status: Literal["Active", "Invited"]


class TeamMemberCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: Literal["Admin", "Developer", "User"] = "User"


class DeploySolutionRequest(BaseModel):
    solution: GeneratedSolution


DASHBOARD_STATS = [
    {"title": "Total Agents", "value": "24", "change": "+3 this month", "icon": "Zap"},
    {"title": "Active Workflows", "value": "12", "change": "+2 deployments", "icon": "Workflow"},
    {"title": "Team Members", "value": "8", "change": "All active", "icon": "Users"},
    {"title": "Avg. Efficiency", "value": "94%", "change": "+5% from last week", "icon": "TrendingUp"},
]

RECENT_ACTIVITY = [
    {
        "id": "1",
        "type": "agent_created",
        "title": "Customer Support Agent",
        "description": "Created by Sarah Chen",
        "timestamp": "2 hours ago",
        "status": "active",
    },
    {
        "id": "2",
        "type": "workflow_deployed",
        "title": "Sales Lead Qualification",
        "description": "Deployed by Mike Johnson",
        "timestamp": "5 hours ago",
        "status": "success",
    },
    {
        "id": "3",
        "type": "agent_improved",
        "title": "Email Responder Agent",
        "description": "Prompt improved by AI Architect",
        "timestamp": "1 day ago",
        "status": "pending",
    },
    {
        "id": "4",
        "type": "marketplace_install",
        "title": "Installed: HR Onboarding Template",
        "description": "Installed by James Wilson",
        "timestamp": "2 days ago",
        "status": "success",
    },
]

AGENTS: list[dict[str, Any]] = [
    {
        "id": "1",
        "name": "Customer Support Agent",
        "description": "Handles customer inquiries and resolves common issues",
        "status": "active",
        "usage": 2847,
        "created": "2 weeks ago",
        "category": "Support",
    },
    {
        "id": "2",
        "name": "Content Generator",
        "description": "Automatically creates marketing content and social posts",
        "status": "active",
        "usage": 1562,
        "created": "3 weeks ago",
        "category": "Marketing",
    },
    {
        "id": "3",
        "name": "Data Analyzer",
        "description": "Analyzes business metrics and generates reports",
        "status": "testing",
        "usage": 342,
        "created": "1 week ago",
        "category": "Analytics",
    },
    {
        "id": "4",
        "name": "Email Responder",
        "description": "Drafts professional email responses",
        "status": "inactive",
        "usage": 0,
        "created": "2 weeks ago",
        "category": "Communication",
    },
]

WORKFLOWS = [
    {
        "id": "1",
        "name": "Sales Lead Pipeline",
        "description": "Research prospects, score leads, draft outreach",
        "agents": 3,
        "status": "active",
        "lastRun": "2 hours ago",
    },
    {
        "id": "2",
        "name": "Customer Onboarding",
        "description": "Collect info, assign tasks, generate reports",
        "agents": 4,
        "status": "active",
        "lastRun": "30 minutes ago",
    },
    {
        "id": "3",
        "name": "Content Production",
        "description": "Generate, edit, and schedule content",
        "agents": 2,
        "status": "testing",
        "lastRun": "1 day ago",
    },
]

MARKETPLACE_ITEMS = [
    {
        "id": "1",
        "name": "Customer Support Agent",
        "creator": "AgentThat Team",
        "description": "Enterprise-ready customer support with knowledge base",
        "installs": 1240,
        "rating": 4.8,
        "category": "Support",
        "price": "Free",
        "icon": "MessageSquare",
    },
    {
        "id": "2",
        "name": "Sales Enablement Workflow",
        "creator": "RevOps Team",
        "description": "Complete sales pipeline automation",
        "installs": 892,
        "rating": 4.9,
        "category": "Sales",
        "price": "Free",
        "icon": "TrendingUp",
    },
    {
        "id": "3",
        "name": "HR Onboarding System",
        "creator": "People Ops Team",
        "description": "Automated employee onboarding workflow",
        "installs": 654,
        "rating": 4.7,
        "category": "HR",
        "price": "Free",
        "icon": "Users",
    },
    {
        "id": "4",
        "name": "Content Management Agent",
        "creator": "Marketing Team",
        "description": "AI-powered content creation and management",
        "installs": 521,
        "rating": 4.6,
        "category": "Marketing",
        "price": "Free",
        "icon": "FileText",
    },
]

ANALYTICS = [
    {"month": "Jan", "adoption": 32, "efficiency": 78, "savings": 2400},
    {"month": "Feb", "adoption": 45, "efficiency": 82, "savings": 3200},
    {"month": "Mar", "adoption": 58, "efficiency": 85, "savings": 4100},
    {"month": "Apr", "adoption": 71, "efficiency": 88, "savings": 5200},
    {"month": "May", "adoption": 84, "efficiency": 91, "savings": 6300},
    {"month": "Jun", "adoption": 95, "efficiency": 94, "savings": 7400},
]

COURSES = [
    {
        "id": "1",
        "title": "AI Fundamentals",
        "description": "Learn the basics of AI and how to use AgentThat",
        "duration": "2 hours",
        "lessons": 8,
        "completion": 100,
        "status": "completed",
    },
    {
        "id": "2",
        "title": "Prompt Engineering Mastery",
        "description": "Create powerful prompts that drive results",
        "duration": "3 hours",
        "lessons": 12,
        "completion": 65,
        "status": "in_progress",
    },
    {
        "id": "3",
        "title": "Building Multi-Agent Systems",
        "description": "Design and orchestrate complex workflows",
        "duration": "4 hours",
        "lessons": 15,
        "completion": 0,
        "status": "available",
    },
    {
        "id": "4",
        "title": "Advanced Optimization",
        "description": "Optimize agents and workflows for maximum performance",
        "duration": "3 hours",
        "lessons": 10,
        "completion": 0,
        "status": "available",
    },
]

PROFILE_SETTINGS = {
    "full_name": "Sarah Chen",
    "email": "sarah@company.com",
    "role": "Admin",
}

NOTIFICATION_SETTINGS = [
    {"label": "Agent deployments", "enabled": True},
    {"label": "Workflow runs", "enabled": True},
    {"label": "Team invitations", "enabled": True},
    {"label": "Weekly reports", "enabled": False},
]

TEAM_MEMBERS = [
    {"id": "team-1", "name": "Sarah Chen", "role": "Admin", "status": "Active"},
    {"id": "team-2", "name": "Mike Johnson", "role": "Developer", "status": "Active"},
    {"id": "team-3", "name": "James Wilson", "role": "User", "status": "Active"},
]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "solution"


def _now_label() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _log_activity(activity_type: str, title: str, description: str, status: str = "success") -> None:
    RECENT_ACTIVITY.insert(
        0,
        {
            "id": str(len(RECENT_ACTIVITY) + 1),
            "type": activity_type,
            "title": title,
            "description": description,
            "timestamp": "just now",
            "status": status,
        },
    )
    del RECENT_ACTIVITY[20:]


def _overview_stats() -> list[dict[str, str]]:
    active_workflows = len([item for item in WORKFLOWS if item["status"] == "active"])
    return [
        {
            "title": "Total Agents",
            "value": str(len(AGENTS)),
            "change": "Live inventory",
            "icon": "Zap",
        },
        {
            "title": "Active Workflows",
            "value": str(active_workflows),
            "change": "Live orchestration",
            "icon": "Workflow",
        },
        {
            "title": "Team Members",
            "value": str(len(TEAM_MEMBERS)),
            "change": "Workspace access",
            "icon": "Users",
        },
        {
            "title": "Avg. Efficiency",
            "value": "94%",
            "change": "Rolling 30d",
            "icon": "TrendingUp",
        },
    ]


def _learning_payload() -> dict[str, Any]:
    completed = len([course for course in COURSES if course["completion"] == 100])
    in_progress = len([course for course in COURSES if 0 < course["completion"] < 100])
    total_progress = int(sum(course["completion"] for course in COURSES) / max(len(COURSES), 1))
    return {
        "stats": [
            {
                "title": "Courses Completed",
                "value": str(completed),
                "change": f"{total_progress}% progress overall",
                "icon": "CheckCircle",
            },
            {
                "title": "Certifications",
                "value": "0",
                "change": "Complete pathways to earn",
                "icon": "Award",
            },
            {
                "title": "Active Courses",
                "value": str(in_progress),
                "change": "Currently in progress",
                "icon": "Target",
            },
        ],
        "path": [
            {"step": 1, "title": "AI Fundamentals", "status": COURSES[0]["status"]},
            {"step": 2, "title": "Prompt Engineering Mastery", "status": COURSES[1]["status"]},
            {"step": 3, "title": "Building Multi-Agent Systems", "status": COURSES[2]["status"]},
            {"step": 4, "title": "Advanced Optimization", "status": COURSES[3]["status"]},
        ],
        "courses": COURSES,
        "certifications": [
            {"name": "AgentThat Fundamentals", "courses": 2, "level": "Beginner"},
            {"name": "Advanced Agent Builder", "courses": 3, "level": "Intermediate"},
            {"name": "Enterprise Architect", "courses": 4, "level": "Advanced"},
            {"name": "Certified Prompt Engineer", "courses": 2, "level": "Advanced"},
        ],
    }


def _workflow_or_404(workflow_id: str) -> dict[str, Any]:
    item = next((workflow for workflow in WORKFLOWS if workflow["id"] == workflow_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    return item


def _marketplace_or_404(item_id: str) -> dict[str, Any]:
    item = next((asset for asset in MARKETPLACE_ITEMS if asset["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="marketplace item not found")
    return item


def _course_or_404(course_id: str) -> dict[str, Any]:
    item = next((course for course in COURSES if course["id"] == course_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="course not found")
    return item


def _keyword_tools(requirement: str) -> list[str]:
    lower = requirement.lower()
    tools = ["Audit Log", "Human Approval Queue"]
    keyword_map = {
        "jira": "Jira",
        "salesforce": "Salesforce",
        "email": "Microsoft Outlook",
        "ticket": "Zendesk",
        "support": "Knowledge Base",
        "report": "Power BI",
        "slack": "Slack",
        "teams": "Microsoft Teams",
        "employee": "Microsoft Entra ID",
        "hr": "HRIS",
        "document": "SharePoint",
    }
    for keyword, tool in keyword_map.items():
        if keyword in lower and tool not in tools:
            tools.append(tool)
    return tools


def _fallback_improve_prompt(prompt: str, business_context: str | None = None) -> ImprovePromptResponse:
    additions = [
        "state the target users and business outcome",
        "define data sources, tools, and system boundaries",
        "include human approval for irreversible or customer-facing actions",
        "add success metrics, audit logging, and escalation criteria",
    ]
    context_clause = f" Context: {business_context.strip()}" if business_context else ""
    improved = (
        f"Create an enterprise-ready AI workflow for: {prompt.strip()}.{context_clause} "
        "Include clear objectives, agent responsibilities, required integrations, knowledge sources, "
        "workflow routing, human-in-the-loop approvals, governance controls, observability, "
        "cost and latency considerations, and measurable success criteria."
    )
    return ImprovePromptResponse(
        original_prompt=prompt,
        improved_prompt=improved,
        improvements=additions,
        provider="deterministic",
    )


def _fallback_solution(payload: GenerateSolutionRequest) -> GeneratedSolution:
    improved = _fallback_improve_prompt(payload.requirement, payload.department).improved_prompt
    tools = _keyword_tools(payload.requirement)
    base_name = payload.name.strip() or "AI Workflow"
    agents = [
        AgentSpec(
            name="Requirements Analyst",
            purpose="Transforms the business request into structured objectives, constraints, and acceptance criteria.",
            prompt="Identify goals, actors, data sources, risks, and measurable outcomes before execution begins.",
            tools=["Policy Library", "Audit Log"],
            handoff="Pass validated requirements to the workflow planner.",
        ),
        AgentSpec(
            name="Workflow Orchestrator",
            purpose="Coordinates specialist agents, routing decisions, retries, and human approvals.",
            prompt="Execute the approved workflow plan, route tasks to specialists, and pause for required approvals.",
            tools=tools,
            handoff="Send completed work to the reviewer and reporting agent.",
        ),
        AgentSpec(
            name="Knowledge Specialist",
            purpose="Retrieves enterprise knowledge and produces grounded context for every decision.",
            prompt="Search approved knowledge sources, cite source names, and flag uncertainty before output is used.",
            tools=["Knowledge Base", "SharePoint", "Vector Search"],
            handoff="Return grounded context to the active workflow step.",
        ),
        AgentSpec(
            name="Governance Reviewer",
            purpose="Checks generated outputs against security, compliance, brand, and approval policies.",
            prompt="Review outputs for risk, privacy, compliance, and approval requirements before deployment.",
            tools=["Policy Library", "Human Approval Queue", "Audit Log"],
            handoff="Approve, reject, or request revision with reasons.",
        ),
    ]
    workflow = [
        WorkflowStep(
            id="step-1",
            name="Intake and classify request",
            agent="Requirements Analyst",
            action="Capture business goal, department, data needs, risk level, and success metrics.",
        ),
        WorkflowStep(
            id="step-2",
            name="Retrieve enterprise context",
            agent="Knowledge Specialist",
            action="Search approved knowledge sources and attach citations or uncertainty flags.",
        ),
        WorkflowStep(
            id="step-3",
            name="Execute workflow",
            agent="Workflow Orchestrator",
            action="Coordinate tools and agents, retry failed actions, and record every state transition.",
        ),
        WorkflowStep(
            id="step-4",
            name="Review and approve",
            agent="Governance Reviewer",
            action="Check policy compliance and pause for a human when customer-facing or high-risk.",
            human_approval=True,
        ),
        WorkflowStep(
            id="step-5",
            name="Publish metrics",
            agent="Workflow Orchestrator",
            action="Emit cost, latency, adoption, usage, time-saved, and exception metrics.",
        ),
    ]
    return GeneratedSolution(
        id=f"sol-{_slug(base_name)}",
        name=base_name,
        summary=(
            f"{base_name} is a governed multi-agent workflow that turns the request into "
            "a reusable enterprise AI asset with approvals, integrations, and observability."
        ),
        improved_prompt=improved,
        agents=agents,
        workflow=workflow,
        integrations=tools,
        governance=[
            "Tenant isolation and RBAC on every workflow action",
            "Human approval before external communication or record mutation",
            "Prompt, tool, data-access, and output audit logs",
            "PII minimization and approved knowledge-source enforcement",
        ],
        observability=[
            "Cost per run and cost per successful task",
            "Latency by agent, tool, and workflow step",
            "Escalation rate, approval rate, and policy-block rate",
            "Adoption, time saved, and ROI by team",
        ],
        deployment={
            "runtime": "FastAPI orchestration API with Azure OpenAI chat completions",
            "hosting": "Azure Container Apps or AKS",
            "state": "PostgreSQL plus workflow event log",
            "secrets": "Azure Key Vault",
        },
        provider="deterministic",
    )


async def _azure_chat_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    if not settings.azure_openai_configured:
        raise RuntimeError("Azure OpenAI is not configured")

    endpoint = settings.azure_openai_endpoint.rstrip("/")  # type: ignore[union-attr]
    deployment = settings.azure_openai_deployment
    url = (
        f"{endpoint}/openai/deployments/{deployment}/chat/completions"
        f"?api-version={settings.azure_openai_api_version}"
    )
    body = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.azure_openai_temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "api-key": settings.azure_openai_api_key or "",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Azure OpenAI error: {response.text}")
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Azure OpenAI returned non-JSON content") from exc


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentthat-backend"}


@app.get("/v1/tenants/{tenant_id}/health")
def tenant_health(tenant_id: str) -> dict[str, str]:
    normalized = tenant_id.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    return {"status": "ok", "tenantId": normalized}


@app.get("/v1/ai/status")
def ai_status() -> dict[str, Any]:
    return {
        "provider": "azure_openai",
        "configured": settings.azure_openai_configured,
        "deployment": settings.azure_openai_deployment,
        "apiVersion": settings.azure_openai_api_version,
        "mode": "live" if settings.azure_openai_configured else "deterministic-fallback",
    }


@app.get("/v1/platform/overview")
def platform_overview() -> dict[str, Any]:
    return {
        "dashboardStats": _overview_stats(),
        "recentActivity": RECENT_ACTIVITY,
        "agents": AGENTS,
    }


@app.get("/v1/agents")
def list_agents() -> list[dict[str, Any]]:
    return AGENTS


@app.post("/v1/agents", response_model=SavedAgent)
def create_agent(payload: ManualAgentRequest) -> SavedAgent:
    agent = SavedAgent(
        id=f"agent-{len(AGENTS) + 1}",
        name=payload.name.strip(),
        description=payload.description.strip(),
        status="testing",
        usage=0,
        created="just now",
        category=payload.category.strip() or "General",
    )
    AGENTS.insert(0, agent.model_dump())
    return agent


@app.get("/v1/workflows")
def list_workflows() -> list[dict[str, Any]]:
    return WORKFLOWS


@app.post("/v1/workflows")
def create_workflow(payload: WorkflowCreateRequest) -> dict[str, Any]:
    workflow = {
        "id": str(len(WORKFLOWS) + 1),
        "name": payload.name.strip(),
        "description": payload.description.strip(),
        "agents": payload.agents,
        "status": "testing",
        "lastRun": "never",
    }
    WORKFLOWS.insert(0, workflow)
    _log_activity("workflow_created", f"Workflow created: {workflow['name']}", "Created in Workflow Studio")
    return workflow


@app.post("/v1/workflows/{workflow_id}/control")
def control_workflow(workflow_id: str, payload: WorkflowControlRequest) -> dict[str, Any]:
    workflow = _workflow_or_404(workflow_id)
    if payload.action == "run":
        workflow["status"] = "active"
        workflow["lastRun"] = _now_label()
    if payload.action == "pause":
        workflow["status"] = "paused"
    if payload.action == "resume":
        workflow["status"] = "active"
    _log_activity(
        "workflow_control",
        f"Workflow {payload.action}: {workflow['name']}",
        "Workflow state changed from UI controls",
    )
    return workflow


@app.get("/v1/marketplace")
def marketplace() -> list[dict[str, Any]]:
    return MARKETPLACE_ITEMS


@app.post("/v1/marketplace/{item_id}/install")
def install_marketplace_item(item_id: str) -> dict[str, Any]:
    item = _marketplace_or_404(item_id)
    item["installs"] += 1
    _log_activity(
        "marketplace_install",
        f"Installed: {item['name']}",
        "Installed from marketplace",
    )
    if "workflow" in item["name"].lower() or "system" in item["name"].lower():
        WORKFLOWS.insert(
            0,
            {
                "id": str(len(WORKFLOWS) + 1),
                "name": item["name"],
                "description": item["description"],
                "agents": 3,
                "status": "testing",
                "lastRun": "never",
            },
        )
    else:
        AGENTS.insert(
            0,
            {
                "id": str(len(AGENTS) + 1),
                "name": item["name"],
                "description": item["description"],
                "status": "testing",
                "usage": 0,
                "created": "just now",
                "category": item["category"],
            },
        )
    return {"status": "installed", "item": item}


@app.get("/v1/analytics")
def analytics() -> dict[str, Any]:
    return {
        "roiMetrics": [
            {"title": "Time Saved (Hours)", "value": "2,847", "change": "+12% this month", "icon": "Zap"},
            {"title": "Cost Reduction", "value": "$450K", "change": "+18% savings", "icon": "DollarSign"},
            {"title": "User Adoption", "value": "95%", "change": "+8% from last quarter", "icon": "Users"},
            {"title": "Efficiency Gain", "value": "94%", "change": "+6% improvement", "icon": "TrendingUp"},
        ],
        "series": ANALYTICS,
        "departments": [
            {"dept": "Engineering", "adoption": 98, "users": 42},
            {"dept": "Sales", "adoption": 85, "users": 35},
            {"dept": "Marketing", "adoption": 92, "users": 28},
            {"dept": "Operations", "adoption": 78, "users": 22},
            {"dept": "HR", "adoption": 65, "users": 15},
        ],
    }


@app.get("/v1/learning")
def learning() -> dict[str, Any]:
    return _learning_payload()


@app.post("/v1/learning/courses/{course_id}/start")
def start_course(course_id: str) -> dict[str, Any]:
    course = _course_or_404(course_id)
    if course["completion"] == 100:
        return _learning_payload()
    if course["completion"] == 0:
        course["completion"] = 10
    course["status"] = "in_progress"
    _log_activity("learning", f"Started course: {course['title']}", "Learning path progress updated")
    return _learning_payload()


@app.post("/v1/learning/courses/{course_id}/complete")
def complete_course(course_id: str) -> dict[str, Any]:
    course = _course_or_404(course_id)
    course["completion"] = 100
    course["status"] = "completed"
    _log_activity("learning", f"Completed course: {course['title']}", "Certification progress updated")
    return _learning_payload()


@app.get("/v1/settings/profile", response_model=ProfileSettings)
def get_profile_settings() -> ProfileSettings:
    return ProfileSettings.model_validate(PROFILE_SETTINGS)


@app.put("/v1/settings/profile", response_model=ProfileSettings)
def update_profile_settings(payload: ProfileSettings) -> ProfileSettings:
    PROFILE_SETTINGS.update(payload.model_dump())
    _log_activity("settings", "Profile updated", "User updated profile settings")
    return ProfileSettings.model_validate(PROFILE_SETTINGS)


@app.get("/v1/settings/notifications", response_model=list[NotificationItem])
def get_notification_settings() -> list[NotificationItem]:
    return [NotificationItem.model_validate(item) for item in NOTIFICATION_SETTINGS]


@app.put("/v1/settings/notifications", response_model=list[NotificationItem])
def update_notification_settings(payload: list[NotificationItem]) -> list[NotificationItem]:
    NOTIFICATION_SETTINGS.clear()
    NOTIFICATION_SETTINGS.extend(item.model_dump() for item in payload)
    _log_activity("settings", "Notifications updated", "User saved notification preferences")
    return [NotificationItem.model_validate(item) for item in NOTIFICATION_SETTINGS]


@app.get("/v1/team/members", response_model=list[TeamMember])
def list_team_members() -> list[TeamMember]:
    return [TeamMember.model_validate(member) for member in TEAM_MEMBERS]


@app.post("/v1/team/members", response_model=TeamMember)
def add_team_member(payload: TeamMemberCreateRequest) -> TeamMember:
    member = TeamMember(
        id=f"team-{len(TEAM_MEMBERS) + 1}",
        name=payload.name.strip(),
        role=payload.role,
        status="Invited",
    )
    TEAM_MEMBERS.append(member.model_dump())
    _log_activity("team", f"Invited {member.name}", "New member invited to workspace")
    return member


@app.post("/v1/ai/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(payload: ImprovePromptRequest) -> ImprovePromptResponse:
    if not settings.azure_openai_configured:
        return _fallback_improve_prompt(payload.prompt, payload.business_context)

    system_prompt = (
        "You are AgentThat's enterprise prompt improvement engine. "
        "Return strict JSON with original_prompt, improved_prompt, and improvements array."
    )
    data = await _azure_chat_json(
        system_prompt,
        json.dumps(payload.model_dump(), ensure_ascii=True),
    )
    data["provider"] = "azure_openai"
    return ImprovePromptResponse.model_validate(data)


@app.post("/v1/solutions/generate", response_model=GeneratedSolution)
async def generate_solution(payload: GenerateSolutionRequest) -> GeneratedSolution:
    if not settings.azure_openai_configured:
        return _fallback_solution(payload)

    fallback = _fallback_solution(payload)
    system_prompt = (
        "You are AgentThat's flagship AI Solution Architect. Design governed enterprise "
        "AI agents and multi-agent workflows. Return strict JSON matching this shape: "
        "id, name, summary, improved_prompt, agents[{name,purpose,prompt,tools,handoff}], "
        "workflow[{id,name,agent,action,human_approval}], integrations[], governance[], "
        "observability[], deployment{runtime,hosting,state,secrets}. Use ASCII only."
    )
    data = await _azure_chat_json(
        system_prompt,
        json.dumps(
            {
                "request": payload.model_dump(),
                "fallback_shape": fallback.model_dump(),
            },
            ensure_ascii=True,
        ),
    )
    data["provider"] = "azure_openai"
    return GeneratedSolution.model_validate(data)


@app.post("/v1/solutions/deploy")
def deploy_solution(payload: DeploySolutionRequest) -> dict[str, Any]:
    solution = payload.solution
    workflow_id = str(len(WORKFLOWS) + 1)
    WORKFLOWS.insert(
        0,
        {
            "id": workflow_id,
            "name": solution.name,
            "description": solution.summary,
            "agents": len(solution.agents),
            "status": "active",
            "lastRun": _now_label(),
        },
    )
    created_agents = 0
    for spec in solution.agents:
        AGENTS.insert(
            0,
            {
                "id": str(len(AGENTS) + 1),
                "name": spec.name,
                "description": spec.purpose,
                "status": "active",
                "usage": 0,
                "created": "just now",
                "category": "Generated",
            },
        )
        created_agents += 1
    _log_activity(
        "workflow_deployed",
        f"Deployed solution: {solution.name}",
        "Generated architecture deployed to workflow runtime",
    )
    return {
        "status": "deployed",
        "workflowId": workflow_id,
        "agentsCreated": created_agents,
        "provider": solution.provider,
    }
