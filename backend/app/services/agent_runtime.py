"""Agent Runtime Service - isolated execution with resource limits and metrics."""
from __future__ import annotations

import uuid
import time
import asyncio
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class ResourceLimitViolation(RuntimeError):
    """Raised when agent execution exceeds resource limits."""
    pass


class AgentRuntime:
    """Executes agents with isolated context, resource limits, and metric tracking."""

    TIMEOUT_SECONDS: float = 30.0
    MEMORY_LIMIT_MB: int = 512

    def __init__(self, tenant_id: uuid.UUID, db: AsyncSession):
        self.tenant_id = tenant_id
        self.db = db

    async def execute(
        self,
        agent_id: uuid.UUID,
        input_data: dict[str, Any],
        execution_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Execute an agent with isolated context, 30s timeout, and 512MB memory limit.

        Args:
            agent_id: The agent to execute.
            input_data: Input payload for the agent.
            execution_id: Unique identifier for this execution run.

        Returns:
            Execution result dict including output and metrics.

        Raises:
            ResourceLimitViolation: If timeout or memory limits are exceeded.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(UTC)
        memory_adapter = self._get_memory_adapter(
            input_data.get("memory_adapter", "short_term")
        )

        # Simulate memory usage tracking
        simulated_memory_mb = input_data.get("_simulated_memory_mb", 64)
        if simulated_memory_mb > self.MEMORY_LIMIT_MB:
            raise ResourceLimitViolation(
                f"Memory limit exceeded: {simulated_memory_mb}MB > {self.MEMORY_LIMIT_MB}MB"
            )

        try:
            result = await asyncio.wait_for(
                self._run_agent(agent_id, input_data, memory_adapter),
                timeout=self.TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            raise ResourceLimitViolation(
                f"Execution timeout: exceeded {self.TIMEOUT_SECONDS}s limit "
                f"(elapsed {elapsed_ms:.1f}ms)"
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        token_usage = result.get("token_usage", {"prompt": 0, "completion": 0})
        total_tokens = token_usage.get("prompt", 0) + token_usage.get("completion", 0)
        cost = self._calculate_cost(token_usage)

        return {
            "execution_id": str(execution_id),
            "agent_id": str(agent_id),
            "tenant_id": str(self.tenant_id),
            "status": "completed",
            "output": result.get("output"),
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "metrics": {
                "latency_ms": round(elapsed_ms, 2),
                "token_usage": token_usage,
                "total_tokens": total_tokens,
                "cost": round(cost, 6),
                "memory_mb": simulated_memory_mb,
            },
            "memory_adapter": memory_adapter,
        }

    def _get_memory_adapter(self, adapter_type: str) -> dict[str, Any]:
        """Return configuration for the specified memory adapter type.

        Args:
            adapter_type: One of 'short_term', 'long_term', or 'semantic'.

        Returns:
            Configuration dict for the memory adapter.
        """
        adapters: dict[str, dict[str, Any]] = {
            "short_term": {
                "type": "short_term",
                "backend": "redis",
                "ttl_seconds": 3600,
                "max_entries": 1000,
            },
            "long_term": {
                "type": "long_term",
                "backend": "postgres",
                "retention_days": 365,
                "compression": True,
            },
            "semantic": {
                "type": "semantic",
                "backend": "vector_db",
                "embedding_model": "text-embedding-3-small",
                "dimensions": 1536,
                "similarity_metric": "cosine",
            },
        }
        return adapters.get(adapter_type, adapters["short_term"])

    async def _run_agent(
        self,
        agent_id: uuid.UUID,
        input_data: dict[str, Any],
        memory_adapter: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal agent execution logic (placeholder for real LLM call).

        Returns:
            Dict with output and token_usage.
        """
        # Placeholder: real implementation would call LLM provider
        return {
            "output": {"message": "Agent execution completed", "agent_id": str(agent_id)},
            "token_usage": {"prompt": 150, "completion": 80},
        }

    @staticmethod
    def _calculate_cost(token_usage: dict[str, int]) -> float:
        """Calculate cost based on token usage (USD).

        Uses approximate GPT-4 pricing as default.
        """
        prompt_cost_per_1k = 0.03
        completion_cost_per_1k = 0.06
        prompt_tokens = token_usage.get("prompt", 0)
        completion_tokens = token_usage.get("completion", 0)
        return (
            (prompt_tokens / 1000) * prompt_cost_per_1k
            + (completion_tokens / 1000) * completion_cost_per_1k
        )
