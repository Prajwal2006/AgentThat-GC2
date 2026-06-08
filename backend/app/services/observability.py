"""Observability Service - distributed tracing, span management, and alerting."""
from __future__ import annotations

import uuid
import time
from datetime import datetime, UTC
from typing import Any


class ObservabilityService:
    """Provides distributed tracing, span hierarchy, alerting, and LangFuse integration."""

    VALID_SEVERITIES = ["info", "warning", "error", "critical"]
    VALID_ALERT_TYPES = ["latency", "error_rate", "cost", "token_limit", "custom"]

    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self._spans: dict[str, dict[str, Any]] = {}
        self._traces: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = []
        self._langfuse_buffer: list[dict[str, Any]] = []

    def start_span(
        self,
        name: str,
        metadata: dict[str, Any],
    ) -> str:
        """Start a new tracing span.

        Args:
            name: Human-readable span name (e.g. 'llm_call', 'tool_execution').
            metadata: Additional context (parent_id, execution_id, etc.).

        Returns:
            Unique span_id string.
        """
        span_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        span = {
            "span_id": span_id,
            "tenant_id": str(self.tenant_id),
            "name": name,
            "parent_id": metadata.get("parent_id"),
            "execution_id": metadata.get("execution_id"),
            "start_time": now.isoformat(),
            "end_time": None,
            "duration_ms": None,
            "status": "in_progress",
            "metadata": metadata,
            "token_count": 0,
            "cost": 0.0,
        }
        self._spans[span_id] = span
        self._forward_to_langfuse({"event": "span_start", "span": span})

        return span_id

    def end_span(self, span_id: str, result: dict[str, Any]) -> None:
        """End an active span with result data.

        Args:
            span_id: The span to close.
            result: Execution result including token_count, cost, status, output.
        """
        if span_id not in self._spans:
            return

        span = self._spans[span_id]
        now = datetime.now(UTC)
        start_time = datetime.fromisoformat(span["start_time"])
        duration_ms = (now - start_time).total_seconds() * 1000

        span["end_time"] = now.isoformat()
        span["duration_ms"] = round(duration_ms, 2)
        span["status"] = result.get("status", "completed")
        span["token_count"] = result.get("token_count", 0)
        span["cost"] = result.get("cost", 0.0)
        span["output"] = result.get("output")

        self._traces.append(span)
        self._forward_to_langfuse({"event": "span_end", "span": span})

    def emit_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
    ) -> None:
        """Emit an observability alert.

        Args:
            alert_type: Type of alert (latency, error_rate, cost, token_limit, custom).
            message: Human-readable alert message.
            severity: Alert severity (info, warning, error, critical).
        """
        if severity not in self.VALID_SEVERITIES:
            severity = "info"
        if alert_type not in self.VALID_ALERT_TYPES:
            alert_type = "custom"

        alert = {
            "alert_id": str(uuid.uuid4()),
            "tenant_id": str(self.tenant_id),
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "emitted_at": datetime.now(UTC).isoformat(),
        }
        self._alerts.append(alert)
        self._forward_to_langfuse({"event": "alert", "alert": alert})

    def get_traces(
        self,
        execution_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve completed traces, optionally filtered by execution.

        Args:
            execution_id: Optional filter for a specific execution.
            limit: Maximum number of traces to return.

        Returns:
            List of span/trace dicts ordered by start_time descending.
        """
        traces = self._traces
        if execution_id:
            exec_id_str = str(execution_id)
            traces = [t for t in traces if t.get("execution_id") == exec_id_str]

        # Return most recent first
        sorted_traces = sorted(
            traces, key=lambda t: t.get("start_time", ""), reverse=True
        )
        return sorted_traces[:limit]

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _forward_to_langfuse(self, event: dict[str, Any]) -> None:
        """Forward observability events to LangFuse (simulated via internal buffer).

        In production, this sends events to the LangFuse ingestion endpoint.
        """
        self._langfuse_buffer.append({
            **event,
            "forwarded_at": datetime.now(UTC).isoformat(),
            "tenant_id": str(self.tenant_id),
        })
