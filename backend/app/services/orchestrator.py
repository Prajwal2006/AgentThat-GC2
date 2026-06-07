"""Workflow Orchestration Service - lifecycle commands and execution coordination."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.workflow import Workflow, WorkflowVersion
from app.models.db.execution import ExecutionRun, ExecutionLog
from app.repositories.workflow_repo import WorkflowRepository, WorkflowVersionRepository
from app.services.audit import AuditService


class WorkflowValidationError(Exception):
    """Workflow validation failure."""
    pass


class InvalidWorkflowCommand(Exception):
    """Invalid lifecycle command for current workflow status."""
    def __init__(self, current_status: str, command: str, allowed: list[str]):
        self.current_status = current_status
        self.command = command
        self.allowed = allowed
        super().__init__(
            f"Cannot '{command}' workflow in '{current_status}' status. "
            f"Allowed commands: {', '.join(allowed)}"
        )


# Valid commands per status
VALID_COMMANDS: dict[str, list[str]] = {
    "draft": ["run"],
    "testing": ["run"],
    "active": ["pause"],
    "paused": ["resume", "run"],
    "failed": ["run"],
    "completed": ["run"],
}


class OrchestratorService:
    """Coordinates workflow lifecycle and multi-agent execution."""
    
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = WorkflowRepository(db, tenant_id)
        self.version_repo = WorkflowVersionRepository(db, tenant_id)
        self.audit = AuditService(db, tenant_id)
    
    async def create_workflow(
        self, *, name: str, description: str, agent_count: int,
        steps: list[dict[str, Any]] | None = None,
        routing_config: dict[str, Any] | None = None,
    ) -> Workflow:
        """Create a new workflow with validation."""
        # Validate
        name_len = len(name.strip())
        if name_len < 3 or name_len > 120:
            raise WorkflowValidationError("Workflow name must be between 3 and 120 characters")
        desc_len = len(description.strip())
        if desc_len < 8 or desc_len > 1000:
            raise WorkflowValidationError("Workflow description must be between 8 and 1000 characters")
        if agent_count < 1 or agent_count > 12:
            raise WorkflowValidationError("Agent count must be between 1 and 12")
        
        workflow = Workflow(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            name=name.strip(),
            description=description.strip(),
            status="draft",
            agent_count=agent_count,
            current_version=1,
            created_by=self.user_id,
        )
        await self.repo.create(workflow)
        
        # Create initial version
        version = WorkflowVersion(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            tenant_id=self.tenant_id,
            version_number=1,
            steps=steps or [],
            routing_config=routing_config or {},
            retry_config={"max_retries": 3, "backoff": "exponential"},
            timeout_config={"step_timeout_seconds": 300, "workflow_timeout_seconds": 1800},
            created_by=self.user_id,
        )
        await self.version_repo.create(version)
        
        await self.audit.log(
            user_id=self.user_id,
            operation="create",
            resource_type="workflow",
            resource_id=workflow.id,
            details={"name": name, "agent_count": agent_count},
        )
        
        return workflow
    
    async def control_workflow(self, workflow_id: uuid.UUID, command: str) -> Workflow:
        """Execute a lifecycle command (run/pause/resume) on a workflow."""
        workflow = await self.repo.get_by_id(workflow_id)
        current_status = workflow.status
        
        # Validate command
        allowed = VALID_COMMANDS.get(current_status, [])
        if command not in allowed:
            raise InvalidWorkflowCommand(current_status, command, allowed)
        
        # Apply command
        if command == "run":
            workflow.status = "active"
            workflow.last_run_at = datetime.now(UTC)
        elif command == "pause":
            workflow.status = "paused"
        elif command == "resume":
            workflow.status = "active"
        
        await self.repo.update(workflow)
        
        await self.audit.log(
            user_id=self.user_id,
            operation="execute",
            resource_type="workflow",
            resource_id=workflow.id,
            details={"command": command, "new_status": workflow.status},
        )
        
        return workflow
    
    async def list_workflows(self, *, offset: int = 0, limit: int = 50):
        """List workflows for the current tenant."""
        return await self.repo.list_all(offset=offset, limit=limit)
    
    async def get_workflow(self, workflow_id: uuid.UUID) -> Workflow:
        """Get workflow by ID."""
        return await self.repo.get_by_id(workflow_id)
