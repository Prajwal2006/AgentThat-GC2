"""Context Manager - structured context passing between agents with tenant isolation."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any


class ContextAccessDenied(Exception):
    """Raised when cross-tenant context access is attempted."""
    pass


class ContextManager:
    """Manages structured context passing between agents within an execution.

    Enforces configurable max context window, applies summarization when
    exceeding limits, merges parallel outputs, and maintains a shared
    context store per execution with tenant isolation.
    """

    MAX_TOKENS_MIN = 2000
    MAX_TOKENS_MAX = 128000
    MAX_SUMMARY_TOKENS = 500
    RUNNING_SUMMARY_THRESHOLD = 10

    def __init__(
        self,
        tenant_id: uuid.UUID,
        execution_id: uuid.UUID,
        max_tokens: int = 8000,
    ) -> None:
        self.tenant_id = tenant_id
        self.execution_id = execution_id
        self.max_tokens = self._clamp_tokens(max_tokens)

        # Context window entries (ordered list of agent outputs)
        self._context_entries: list[dict[str, Any]] = []

        # Shared context store: tagged entries (fact/decision/data/instruction)
        self._shared_store: list[dict[str, Any]] = []

        # Execution trace events
        self._trace: list[dict[str, Any]] = []

        # Invocation counter for running summary
        self._invocation_count: int = 0

    def _clamp_tokens(self, value: int) -> int:
        """Clamp max_tokens to allowed range."""
        return max(self.MAX_TOKENS_MIN, min(self.MAX_TOKENS_MAX, value))

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (rough: ~4 chars per token)."""
        return len(text) // 4

    def _summarize(self, text: str, max_tokens: int) -> str:
        """Apply summarization when exceeding token limit.

        Uses simple truncation + key fact extraction placeholder.
        In production, this would call an LLM summarizer.
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        # Simple truncation with key sentence extraction
        sentences = text.split(". ")
        summary_parts: list[str] = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > max_chars:
                break
            summary_parts.append(sentence)
            current_length += len(sentence) + 2  # account for ". "

        result = ". ".join(summary_parts)
        if result and not result.endswith("."):
            result += "."
        return result

    def _record_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Record a context event to execution trace."""
        event = {
            "event_type": event_type,
            "execution_id": str(self.execution_id),
            "tenant_id": str(self.tenant_id),
            "timestamp": datetime.now(UTC).isoformat(),
            **details,
        }
        self._trace.append(event)

    def _validate_tenant(self, tenant_id: uuid.UUID) -> None:
        """Deny cross-tenant context access."""
        if tenant_id != self.tenant_id:
            raise ContextAccessDenied(
                f"Tenant {tenant_id} cannot access context for tenant {self.tenant_id}"
            )

    def _enforce_context_window(self) -> None:
        """Trim context entries to stay within max token budget."""
        total_tokens = sum(
            self._estimate_tokens(entry.get("summary", ""))
            for entry in self._context_entries
        )
        while total_tokens > self.max_tokens and self._context_entries:
            removed = self._context_entries.pop(0)
            total_tokens -= self._estimate_tokens(removed.get("summary", ""))

    def add_agent_output(
        self,
        agent_id: uuid.UUID,
        step_id: str,
        output: str,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Pass agent output as structured context entry.

        Args:
            agent_id: The agent producing the output.
            step_id: Identifier of the step within the plan.
            output: Full text output from the agent.
            confidence: Confidence score (0.0 - 1.0).

        Returns:
            Structured context entry dict.
        """
        self._invocation_count += 1
        timestamp = datetime.now(UTC).isoformat()

        # Create summary (max 500 tokens)
        summary = self._summarize(output, self.MAX_SUMMARY_TOKENS)

        entry: dict[str, Any] = {
            "summary": summary,
            "full_output_ref": output,
            "metadata": {
                "agent_id": str(agent_id),
                "step": step_id,
                "timestamp": timestamp,
                "confidence": confidence,
            },
        }

        self._context_entries.append(entry)
        self._enforce_context_window()

        self._record_event("agent_output_added", {
            "agent_id": str(agent_id),
            "step_id": step_id,
            "confidence": confidence,
            "token_estimate": self._estimate_tokens(summary),
        })

        return entry

    def get_context(self) -> dict[str, Any]:
        """Return the current context window.

        Returns:
            Dict with entries, shared store, metadata, and optional running summary.
        """
        result: dict[str, Any] = {
            "execution_id": str(self.execution_id),
            "tenant_id": str(self.tenant_id),
            "max_tokens": self.max_tokens,
            "entries": self._context_entries,
            "shared_store": self._shared_store,
            "invocation_count": self._invocation_count,
        }

        if self._invocation_count >= self.RUNNING_SUMMARY_THRESHOLD:
            result["running_summary"] = self.get_running_summary()

        return result

    def add_shared_entry(
        self,
        category: str,
        content: str,
        agent_id: uuid.UUID,
    ) -> None:
        """Add a tagged entry to the shared context store.

        Args:
            category: One of 'fact', 'decision', 'data', 'instruction'.
            content: The content to store.
            agent_id: The agent adding this entry.
        """
        valid_categories = {"fact", "decision", "data", "instruction"}
        if category not in valid_categories:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {valid_categories}"
            )

        entry = {
            "id": str(uuid.uuid4()),
            "category": category,
            "content": content,
            "agent_id": str(agent_id),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._shared_store.append(entry)

        self._record_event("shared_entry_added", {
            "category": category,
            "agent_id": str(agent_id),
            "entry_id": entry["id"],
        })

    def get_shared_entries(self, category: str | None = None) -> list[dict[str, Any]]:
        """Retrieve shared context entries, optionally filtered by category.

        Args:
            category: Filter by category, or None to return all.

        Returns:
            List of shared entry dicts.
        """
        if category is None:
            return list(self._shared_store)
        return [e for e in self._shared_store if e["category"] == category]

    def merge_parallel_outputs(self, outputs: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge parallel agent outputs preserving source identity.

        Outputs are ordered by relevance (confidence) then timestamp.

        Args:
            outputs: List of dicts with keys: agent_id, step_id, output, confidence.

        Returns:
            Merged context dict with ordered entries.
        """
        # Sort by confidence desc, then timestamp asc (earlier first for ties)
        sorted_outputs = sorted(
            outputs,
            key=lambda x: (-x.get("confidence", 0.0), x.get("timestamp", "")),
        )

        merged_entries: list[dict[str, Any]] = []
        for item in sorted_outputs:
            entry = self.add_agent_output(
                agent_id=item["agent_id"],
                step_id=item["step_id"],
                output=item["output"],
                confidence=item.get("confidence", 1.0),
            )
            merged_entries.append(entry)

        self._record_event("parallel_outputs_merged", {
            "count": len(merged_entries),
        })

        return {
            "merged_count": len(merged_entries),
            "entries": merged_entries,
            "execution_id": str(self.execution_id),
        }

    def get_running_summary(self) -> str:
        """Produce a running summary after 10+ agent invocations.

        Returns:
            A summary string of the execution context so far.
        """
        if self._invocation_count < self.RUNNING_SUMMARY_THRESHOLD:
            return ""

        # Build summary from context entries and shared store
        parts: list[str] = []
        parts.append(
            f"Execution {self.execution_id}: {self._invocation_count} agent invocations."
        )

        # Summarize decisions
        decisions = self.get_shared_entries("decision")
        if decisions:
            parts.append(f"Decisions made: {len(decisions)}.")
            for d in decisions[-3:]:  # last 3 decisions
                parts.append(f"  - {d['content'][:100]}")

        # Summarize facts
        facts = self.get_shared_entries("fact")
        if facts:
            parts.append(f"Key facts established: {len(facts)}.")

        # Latest context entries
        if self._context_entries:
            latest = self._context_entries[-1]
            parts.append(
                f"Latest output from agent {latest['metadata']['agent_id']} "
                f"(step {latest['metadata']['step']})."
            )

        summary = "\n".join(parts)
        return self._summarize(summary, self.MAX_SUMMARY_TOKENS)

    def get_trace(self) -> list[dict[str, Any]]:
        """Return the full execution trace of context events."""
        return list(self._trace)
