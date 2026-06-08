"""Agent Collaboration - delegation, exchanges, and human approval requests."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any


class CollaborationError(Exception):
    """Base exception for collaboration failures."""
    pass


class AgentNotEligibleError(CollaborationError):
    """Raised when target agent is not in an eligible lifecycle state."""
    def __init__(self, agent_id: uuid.UUID, state: str):
        self.agent_id = agent_id
        self.state = state
        super().__init__(
            f"Agent {agent_id} is in state '{state}' and is not eligible for delegation. "
            f"Must be in: testing, staging, or production."
        )


class MaxExchangesReachedError(CollaborationError):
    """Raised when max collaboration exchanges are exhausted."""
    pass


ELIGIBLE_STATES = {"testing", "staging", "production"}


class AgentCollaboration:
    """Manages inter-agent delegation, collaboration exchanges,
    and human approval requests within an execution.
    """

    QUESTION_MIN_LENGTH = 1
    QUESTION_MAX_LENGTH = 500
    OPTIONS_MIN_COUNT = 2
    OPTIONS_MAX_COUNT = 5

    def __init__(
        self,
        tenant_id: uuid.UUID,
        execution_id: uuid.UUID,
        max_exchanges: int = 10,
    ) -> None:
        self.tenant_id = tenant_id
        self.execution_id = execution_id
        self.max_exchanges = max_exchanges

        # Exchange tracking
        self._exchange_count: int = 0
        self._exchanges: list[dict[str, Any]] = []

        # Execution trace
        self._trace: list[dict[str, Any]] = []

        # Agent state registry (in-memory mock; production would query DB)
        self._agent_states: dict[str, str] = {}

        # Delegation results
        self._delegations: list[dict[str, Any]] = []

        # Human approval requests
        self._approval_requests: list[dict[str, Any]] = []

    def _record_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Record an event to the execution trace."""
        event = {
            "event_type": event_type,
            "execution_id": str(self.execution_id),
            "tenant_id": str(self.tenant_id),
            "timestamp": datetime.now(UTC).isoformat(),
            **details,
        }
        self._trace.append(event)

    def register_agent_state(self, agent_id: uuid.UUID, state: str) -> None:
        """Register an agent's lifecycle state for eligibility checks.

        In production, this would be queried from the database.
        """
        self._agent_states[str(agent_id)] = state

    def _validate_agent_eligibility(self, agent_id: uuid.UUID) -> None:
        """Validate target agent is in an eligible lifecycle state."""
        state = self._agent_states.get(str(agent_id), "unknown")
        if state not in ELIGIBLE_STATES:
            raise AgentNotEligibleError(agent_id, state)

    def delegate(
        self,
        from_agent_id: uuid.UUID,
        to_agent_id: uuid.UUID,
        subtask: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate a subtask from one agent to another.

        Validates target agent eligibility, passes subtask and context,
        and records the delegation event.

        Args:
            from_agent_id: The delegating agent.
            to_agent_id: The target agent to receive the subtask.
            subtask: Description of the subtask to delegate.
            context: Structured context to pass to the target agent.

        Returns:
            Delegation record dict.
        """
        self._validate_agent_eligibility(to_agent_id)

        delegation_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        delegation: dict[str, Any] = {
            "delegation_id": delegation_id,
            "from_agent_id": str(from_agent_id),
            "to_agent_id": str(to_agent_id),
            "subtask": subtask,
            "context": context,
            "status": "pending",
            "result": None,
            "created_at": now,
        }

        self._delegations.append(delegation)

        self._record_event("delegation_created", {
            "delegation_id": delegation_id,
            "from_agent_id": str(from_agent_id),
            "to_agent_id": str(to_agent_id),
            "subtask": subtask[:200],
        })

        return delegation

    def exchange(self, agent_id: uuid.UUID, message: str) -> dict[str, Any]:
        """Record a collaboration exchange message.

        Enforces max exchanges limit. On reaching the limit without
        convergence, terminates and uses the last message as output.

        Args:
            agent_id: The agent sending the message.
            message: The exchange message content.

        Returns:
            Exchange record dict with status.
        """
        if self._exchange_count >= self.max_exchanges:
            # Terminate: use last message as output, log warning
            self._record_event("max_exchanges_reached", {
                "agent_id": str(agent_id),
                "exchange_count": self._exchange_count,
                "final_message": message[:500],
                "warning": "Max exchanges reached without convergence. "
                           "Using last message as output.",
            })

            return {
                "exchange_id": str(uuid.uuid4()),
                "agent_id": str(agent_id),
                "message": message,
                "exchange_number": self._exchange_count,
                "status": "terminated",
                "warning": "Max exchanges reached. Session terminated.",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        self._exchange_count += 1

        exchange_record: dict[str, Any] = {
            "exchange_id": str(uuid.uuid4()),
            "agent_id": str(agent_id),
            "message": message,
            "exchange_number": self._exchange_count,
            "status": "active",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self._exchanges.append(exchange_record)

        self._record_event("exchange_recorded", {
            "agent_id": str(agent_id),
            "exchange_number": self._exchange_count,
            "message_preview": message[:100],
        })

        return exchange_record

    def request_human_approval(
        self,
        agent_id: uuid.UUID,
        question: str,
        options: list[str],
    ) -> dict[str, Any]:
        """Create a human approval request from an agent.

        Args:
            agent_id: The agent requesting approval.
            question: The question to present (1-500 chars).
            options: List of 2-5 option strings.

        Returns:
            Approval request record dict.

        Raises:
            ValueError: If question or options are invalid.
        """
        # Validate question length
        question_len = len(question.strip())
        if question_len < self.QUESTION_MIN_LENGTH or question_len > self.QUESTION_MAX_LENGTH:
            raise ValueError(
                f"Question must be between {self.QUESTION_MIN_LENGTH} and "
                f"{self.QUESTION_MAX_LENGTH} characters. Got {question_len}."
            )

        # Validate options count
        if len(options) < self.OPTIONS_MIN_COUNT or len(options) > self.OPTIONS_MAX_COUNT:
            raise ValueError(
                f"Must provide between {self.OPTIONS_MIN_COUNT} and "
                f"{self.OPTIONS_MAX_COUNT} options. Got {len(options)}."
            )

        request_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        approval_request: dict[str, Any] = {
            "request_id": request_id,
            "agent_id": str(agent_id),
            "question": question.strip(),
            "options": options,
            "status": "pending",
            "response": None,
            "created_at": now,
        }

        self._approval_requests.append(approval_request)

        self._record_event("human_approval_requested", {
            "request_id": request_id,
            "agent_id": str(agent_id),
            "question": question.strip()[:100],
            "options_count": len(options),
        })

        return approval_request

    def get_exchange_count(self) -> int:
        """Return the current number of collaboration exchanges."""
        return self._exchange_count

    def get_trace(self) -> list[dict[str, Any]]:
        """Return the full execution trace of collaboration events."""
        return list(self._trace)
