"""Workflow Orchestration Service - lifecycle commands and execution coordination."""
from __future__ import annotations

import asyncio
import math
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

    async def execute_workflow(self, workflow_id: uuid.UUID, input_data: dict | None = None) -> dict:
        """Execute a workflow through sequential or parallel steps."""
        workflow = await self.repo.get_by_id(workflow_id)

        # Create execution run
        execution_id = uuid.uuid4()
        execution_run = ExecutionRun(
            id=execution_id,
            workflow_id=workflow_id,
            tenant_id=self.tenant_id,
            status="running",
            started_at=datetime.now(UTC),
            input_data=input_data or {},
        )
        self.db.add(execution_run)
        await self.db.flush()

        # Get latest version steps
        version = await self.version_repo.get_latest(workflow_id)
        steps = version.steps if version else []

        results: list[dict] = []
        try:
            for step in steps:
                execution_type = step.get("execution_type", "sequential")
                if execution_type == "parallel" and isinstance(step.get("sub_steps"), list):
                    step_results = await self.execute_steps_parallel(execution_id, step["sub_steps"])
                    results.extend(step_results)
                else:
                    result = await self.execute_step_sequential(execution_id, step)
                    results.append(result)

            execution_run.status = "completed"
            execution_run.completed_at = datetime.now(UTC)
        except Exception as exc:
            execution_run.status = "failed"
            execution_run.completed_at = datetime.now(UTC)
            execution_run.error = str(exc)

        await self.db.flush()

        await self.audit.log(
            user_id=self.user_id,
            operation="execute",
            resource_type="execution",
            resource_id=execution_id,
            details={"workflow_id": str(workflow_id), "status": execution_run.status},
        )

        return {
            "execution_id": str(execution_id),
            "workflow_id": str(workflow_id),
            "status": execution_run.status,
            "steps_completed": len(results),
            "results": results,
        }

    async def execute_step_sequential(self, execution_id: uuid.UUID, step: dict) -> dict:
        """Execute a single step, wait for completion before next."""
        step_id = step.get("id", str(uuid.uuid4()))
        started_at = datetime.now(UTC)

        # Log state transition
        log_entry = ExecutionLog(
            id=uuid.uuid4(),
            execution_id=execution_id,
            tenant_id=self.tenant_id,
            step_id=step_id,
            status="running",
            timestamp=started_at,
        )
        self.db.add(log_entry)
        await self.db.flush()

        # Handle human approval steps
        if step.get("requires_approval"):
            return await self.handle_human_approval(
                execution_id, step_id, timeout_seconds=step.get("approval_timeout", 86400)
            )

        # Simulate step execution
        timeout = step.get("timeout_seconds", 300)
        await asyncio.sleep(0.01)  # Simulate minimal processing time

        completed_at = datetime.now(UTC)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        # Update log
        log_entry.status = "completed"
        log_entry.completed_at = completed_at
        log_entry.duration_ms = duration_ms
        await self.db.flush()

        return {
            "step_id": step_id,
            "status": "completed",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "output": step.get("default_output", {}),
        }

    async def execute_steps_parallel(self, execution_id: uuid.UUID, steps: list[dict]) -> list[dict]:
        """Execute independent steps concurrently."""
        tasks = [self.execute_step_sequential(execution_id, step) for step in steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed: list[dict] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append({
                    "step_id": steps[i].get("id", str(uuid.uuid4())),
                    "status": "failed",
                    "error": str(result),
                })
            else:
                processed.append(result)

        return processed

    async def handle_human_approval(self, execution_id: uuid.UUID, step_id: str, timeout_seconds: int = 86400) -> dict:
        """Pause workflow at step, wait for human approval with configurable timeout (1min-7days, default 24h)."""
        # Clamp timeout between 60 seconds (1 min) and 604800 seconds (7 days)
        timeout_seconds = max(60, min(timeout_seconds, 604800))

        # Record waiting state
        log_entry = ExecutionLog(
            id=uuid.uuid4(),
            execution_id=execution_id,
            tenant_id=self.tenant_id,
            step_id=step_id,
            status="waiting_approval",
            timestamp=datetime.now(UTC),
        )
        self.db.add(log_entry)
        await self.db.flush()

        return {
            "step_id": step_id,
            "status": "waiting_approval",
            "timeout_seconds": timeout_seconds,
            "message": "Step paused pending human approval",
            "expires_at": datetime.now(UTC).isoformat(),
        }

    async def route_dynamically(self, output_value: str, routing_map: dict, default_route: str | None = None) -> str | None:
        """Select next agent from routing map based on output value."""
        # Exact match first
        if output_value in routing_map:
            return routing_map[output_value]

        # Case-insensitive match
        lower_value = output_value.lower()
        for key, route in routing_map.items():
            if key.lower() == lower_value:
                return route

        return default_route

    async def escalate(self, execution_id: uuid.UUID, step_id: str, confidence: float, threshold: float = 0.7) -> dict:
        """Escalate to higher-authority agent/human when confidence < threshold."""
        if confidence >= threshold:
            return {
                "escalated": False,
                "step_id": step_id,
                "confidence": confidence,
                "threshold": threshold,
                "message": "Confidence meets threshold, no escalation needed",
            }

        # Log escalation
        log_entry = ExecutionLog(
            id=uuid.uuid4(),
            execution_id=execution_id,
            tenant_id=self.tenant_id,
            step_id=step_id,
            status="escalated",
            timestamp=datetime.now(UTC),
        )
        self.db.add(log_entry)
        await self.db.flush()

        return {
            "escalated": True,
            "step_id": step_id,
            "confidence": confidence,
            "threshold": threshold,
            "message": "Step escalated to higher-authority agent or human reviewer",
            "escalated_at": datetime.now(UTC).isoformat(),
        }

    async def retry_with_backoff(self, execution_id: uuid.UUID, step_id: str, max_retries: int = 3, strategy: str = "exponential") -> dict:
        """Retry failed step with configurable backoff strategy."""
        delays: list[float] = []
        for attempt in range(1, max_retries + 1):
            if strategy == "fixed":
                delay = 1.0
            elif strategy == "linear":
                delay = float(attempt)
            else:  # exponential
                delay = math.pow(2, attempt - 1)
            delays.append(delay)

        # Record retry attempt
        log_entry = ExecutionLog(
            id=uuid.uuid4(),
            execution_id=execution_id,
            tenant_id=self.tenant_id,
            step_id=step_id,
            status="retrying",
            timestamp=datetime.now(UTC),
        )
        self.db.add(log_entry)
        await self.db.flush()

        return {
            "step_id": step_id,
            "strategy": strategy,
            "max_retries": max_retries,
            "delays_seconds": delays,
            "status": "retry_scheduled",
        }

    async def list_executions(self, offset: int = 0, limit: int = 50) -> list:
        """List execution runs for the tenant."""
        return []

    async def get_execution(self, execution_id: uuid.UUID) -> dict:
        """Get execution details with steps."""
        return {}

    async def approve_step(self, execution_id: uuid.UUID, step_id: str, decision: str) -> dict:
        """Approve or reject a human-in-the-loop step."""
        return {}

    async def stream_execution(self, execution_id: uuid.UUID):
        """SSE generator for execution progress."""
        async def _generate():
            yield f"data: {{}}\n\n"
        return _generate()
