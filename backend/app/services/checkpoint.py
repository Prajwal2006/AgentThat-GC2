"""Checkpoint Service - execution state persistence and resumption."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, UTC
from typing import Any


class CheckpointExpiredError(Exception):
    """Raised when a checkpoint has exceeded the maximum workflow duration."""
    pass


class CheckpointService:
    """Persists execution checkpoints for long-running workflows.

    Supports step-level checkpointing, auto-checkpoints for long steps,
    scheduled step pausing, and configurable timeout enforcement.
    """

    MAX_WORKFLOW_DAYS = 30
    DEFAULT_TIMEOUT_SECONDS = 604800  # 7 days
    MIN_TIMEOUT_SECONDS = 3600  # 1 hour
    MAX_TIMEOUT_SECONDS = 2592000  # 30 days
    AUTO_CHECKPOINT_INTERVAL_SECONDS = 60

    def __init__(
        self,
        tenant_id: uuid.UUID,
        execution_id: uuid.UUID,
    ) -> None:
        self.tenant_id = tenant_id
        self.execution_id = execution_id

        # In-memory checkpoint storage (keyed by checkpoint_id)
        self._checkpoints: dict[str, dict[str, Any]] = {}

        # Latest checkpoint reference
        self._latest_checkpoint_id: str | None = None

        # Scheduled steps (step_id -> resume_at)
        self._scheduled_steps: dict[str, str] = {}

        # Execution start time
        self._started_at: datetime = datetime.now(UTC)

        # Last auto-checkpoint time
        self._last_auto_checkpoint: datetime = datetime.now(UTC)

    def save_checkpoint(self, state: dict[str, Any]) -> str:
        """Persist a checkpoint at step completion.

        Args:
            state: Dict with current_step, context, variables, pending_approvals.

        Returns:
            The generated checkpoint_id.
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        checkpoint: dict[str, Any] = {
            "checkpoint_id": checkpoint_id,
            "execution_id": str(self.execution_id),
            "tenant_id": str(self.tenant_id),
            "state": state,
            "created_at": now,
            "is_auto": False,
        }

        self._checkpoints[checkpoint_id] = checkpoint
        self._latest_checkpoint_id = checkpoint_id
        self._last_auto_checkpoint = datetime.now(UTC)

        return checkpoint_id

    def _save_auto_checkpoint(self, state: dict[str, Any]) -> str:
        """Auto-create a checkpoint for long-running steps.

        Called internally when AUTO_CHECKPOINT_INTERVAL_SECONDS has elapsed.

        Args:
            state: Current execution state.

        Returns:
            The generated checkpoint_id.
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        checkpoint: dict[str, Any] = {
            "checkpoint_id": checkpoint_id,
            "execution_id": str(self.execution_id),
            "tenant_id": str(self.tenant_id),
            "state": state,
            "created_at": now,
            "is_auto": True,
        }

        self._checkpoints[checkpoint_id] = checkpoint
        self._latest_checkpoint_id = checkpoint_id
        self._last_auto_checkpoint = datetime.now(UTC)

        return checkpoint_id

    def should_auto_checkpoint(self) -> bool:
        """Check if enough time has elapsed for an auto-checkpoint.

        Returns:
            True if AUTO_CHECKPOINT_INTERVAL_SECONDS have passed since last checkpoint.
        """
        elapsed = (datetime.now(UTC) - self._last_auto_checkpoint).total_seconds()
        return elapsed >= self.AUTO_CHECKPOINT_INTERVAL_SECONDS

    def auto_checkpoint_if_needed(self, state: dict[str, Any]) -> str | None:
        """Auto-create a checkpoint if the interval has elapsed.

        Args:
            state: Current execution state.

        Returns:
            Checkpoint ID if created, None otherwise.
        """
        if self.should_auto_checkpoint():
            return self._save_auto_checkpoint(state)
        return None

    def load_checkpoint(self) -> dict[str, Any] | None:
        """Load the latest checkpoint for this execution.

        Returns:
            The checkpoint state dict, or None if no checkpoint exists.
        """
        if self._latest_checkpoint_id is None:
            return None

        checkpoint = self._checkpoints.get(self._latest_checkpoint_id)
        if checkpoint is None:
            return None

        return checkpoint["state"]

    def schedule_step(self, step_id: str, resume_at: datetime) -> None:
        """Schedule a step to pause and resume at a future time.

        Args:
            step_id: The step to schedule.
            resume_at: The datetime at which to resume the step.

        Raises:
            ValueError: If resume_at exceeds max workflow duration.
        """
        max_allowed = self._started_at + timedelta(days=self.MAX_WORKFLOW_DAYS)
        if resume_at > max_allowed:
            raise ValueError(
                f"Cannot schedule step beyond max workflow duration of "
                f"{self.MAX_WORKFLOW_DAYS} days. Max allowed: {max_allowed.isoformat()}"
            )

        self._scheduled_steps[step_id] = resume_at.isoformat()

    def is_step_ready(self, step_id: str) -> bool:
        """Check if a scheduled step is ready to resume.

        Args:
            step_id: The step to check.

        Returns:
            True if the step's resume time has passed or step is not scheduled.
        """
        resume_at_str = self._scheduled_steps.get(step_id)
        if resume_at_str is None:
            return True

        resume_at = datetime.fromisoformat(resume_at_str)
        return datetime.now(UTC) >= resume_at

    def check_timeout(self, max_wait_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> bool:
        """Check if the execution has exceeded the timeout.

        Args:
            max_wait_seconds: Maximum wait time in seconds (1hr - 30 days).
                Defaults to 7 days (604800 seconds).

        Returns:
            True if the execution has timed out.
        """
        # Clamp to valid range
        clamped = max(
            self.MIN_TIMEOUT_SECONDS,
            min(self.MAX_TIMEOUT_SECONDS, max_wait_seconds),
        )

        elapsed = (datetime.now(UTC) - self._started_at).total_seconds()
        return elapsed > clamped

    def get_workflow_duration(self) -> float:
        """Get the total workflow duration in seconds.

        Returns:
            Duration in seconds since execution started.
        """
        return (datetime.now(UTC) - self._started_at).total_seconds()

    def get_all_checkpoints(self) -> list[dict[str, Any]]:
        """Return all checkpoints for this execution, ordered by creation time.

        Returns:
            List of checkpoint dicts.
        """
        checkpoints = list(self._checkpoints.values())
        checkpoints.sort(key=lambda c: c["created_at"])
        return checkpoints
