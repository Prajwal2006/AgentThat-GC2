"""Planning Engine - task decomposition and plan management."""
from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import datetime, UTC
from typing import Any


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in plan steps."""
    pass


class PlanningEngine:
    """Detects complex tasks, decomposes them into executable plans,
    and evaluates step outputs against expectations.
    """

    COMPLEXITY_CHAR_THRESHOLD = 200
    COMPLEXITY_OBJECTIVE_THRESHOLD = 2
    MIN_STEPS = 2
    MAX_STEPS = 20

    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.tenant_id = tenant_id
        self.user_id = user_id

        # In-memory plan storage (keyed by plan_id)
        self._plans: dict[str, dict[str, Any]] = {}

    def is_complex(self, task_description: str) -> bool:
        """Detect whether a task is complex based on heuristics.

        A task is complex if:
        - Length exceeds 200 characters, OR
        - Contains more than 2 objectives (sentences or semicolons).

        Args:
            task_description: Natural language task description.

        Returns:
            True if the task is considered complex.
        """
        if len(task_description) > self.COMPLEXITY_CHAR_THRESHOLD:
            return True

        # Count objectives: sentences (period-terminated) and semicolons
        objective_count = self._count_objectives(task_description)
        return objective_count > self.COMPLEXITY_OBJECTIVE_THRESHOLD

    def _count_objectives(self, text: str) -> int:
        """Count number of objectives in text using sentence/semicolon heuristic."""
        # Split on sentence boundaries and semicolons
        separators_count = text.count(";")
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        return len(sentences) + separators_count

    def create_plan(
        self,
        task_description: str,
        available_tools: list[str],
    ) -> dict[str, Any]:
        """Decompose a task into 2-20 steps with dependencies.

        Each step contains: goal, tools, expected_output, dependencies.
        Validates no circular dependencies exist.

        Args:
            task_description: The task to decompose.
            available_tools: List of tool identifiers available for planning.

        Returns:
            Plan dict with steps, metadata, and status.
        """
        steps = self._decompose_task(task_description, available_tools)

        # Validate no circular dependencies
        if not self.validate_dependencies(steps):
            raise CircularDependencyError(
                "Plan contains circular dependencies and cannot be executed."
            )

        plan_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        plan: dict[str, Any] = {
            "plan_id": plan_id,
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "task_description": task_description,
            "steps": steps,
            "created_at": now,
            "status": "pending",
            "execution_summary": None,
        }

        self._plans[plan_id] = plan
        return plan

    def _decompose_task(
        self,
        task_description: str,
        available_tools: list[str],
    ) -> list[dict[str, Any]]:
        """Break a task into sequential steps.

        This is a heuristic decomposition. In production, an LLM would be
        used for intelligent decomposition.
        """
        # Split task into sub-goals by sentences and semicolons
        raw_parts: list[str] = []
        for part in task_description.replace(";", ".").split("."):
            stripped = part.strip()
            if stripped:
                raw_parts.append(stripped)

        # Clamp to allowed step range
        if len(raw_parts) < self.MIN_STEPS:
            # Pad with a synthesis step
            raw_parts.append("Synthesize and validate results")
        if len(raw_parts) > self.MAX_STEPS:
            raw_parts = raw_parts[: self.MAX_STEPS]

        steps: list[dict[str, Any]] = []
        for idx, goal in enumerate(raw_parts):
            step_id = f"step_{idx + 1}"

            # Assign tools heuristically (distribute available tools)
            step_tools = (
                [available_tools[idx % len(available_tools)]]
                if available_tools
                else []
            )

            # Dependencies: each step depends on the previous (sequential)
            dependencies = [f"step_{idx}"] if idx > 0 else []

            step: dict[str, Any] = {
                "step_id": step_id,
                "goal": goal,
                "tools": step_tools,
                "expected_output": f"Completed: {goal}",
                "dependencies": dependencies,
                "status": "pending",
                "actual_output": None,
            }
            steps.append(step)

        return steps

    def validate_dependencies(self, steps: list[dict[str, Any]]) -> bool:
        """Validate no circular dependencies exist using topological sort.

        Args:
            steps: List of step dicts with 'step_id' and 'dependencies'.

        Returns:
            True if dependency graph is a valid DAG (no cycles).
        """
        # Build adjacency list and in-degree count
        step_ids = {step["step_id"] for step in steps}
        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {sid: 0 for sid in step_ids}

        for step in steps:
            for dep in step.get("dependencies", []):
                if dep in step_ids:
                    graph[dep].append(step["step_id"])
                    in_degree[step["step_id"]] += 1

        # Kahn's algorithm for topological sort
        queue: deque[str] = deque()
        for sid, degree in in_degree.items():
            if degree == 0:
                queue.append(sid)

        visited_count = 0
        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we visited all nodes, no cycle exists
        return visited_count == len(step_ids)

    def evaluate_step_output(self, step: dict[str, Any], actual_output: str) -> float:
        """Evaluate similarity between expected and actual step output.

        Uses a placeholder similarity metric (normalized word overlap).
        Returns a score between 0.0 and 1.0, with threshold at 0.7.

        Args:
            step: Step dict containing 'expected_output'.
            actual_output: The actual output produced by the step.

        Returns:
            Similarity score (0.0 - 1.0).
        """
        expected = step.get("expected_output", "")
        if not expected or not actual_output:
            return 0.0

        # Placeholder similarity: normalized word overlap (Jaccard-like)
        expected_words = set(expected.lower().split())
        actual_words = set(actual_output.lower().split())

        if not expected_words and not actual_words:
            return 1.0
        if not expected_words or not actual_words:
            return 0.0

        intersection = expected_words & actual_words
        union = expected_words | actual_words
        similarity = len(intersection) / len(union)

        return round(similarity, 4)

    def get_execution_summary(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Generate an execution summary for a plan.

        Args:
            plan: The plan dict to summarize.

        Returns:
            Summary dict with step statuses, completion rate, and timing.
        """
        steps = plan.get("steps", [])
        total = len(steps)
        completed = sum(1 for s in steps if s.get("status") == "completed")
        failed = sum(1 for s in steps if s.get("status") == "failed")
        pending = total - completed - failed

        summary: dict[str, Any] = {
            "plan_id": plan.get("plan_id"),
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "completion_rate": round(completed / total, 4) if total > 0 else 0.0,
            "status": plan.get("status"),
            "created_at": plan.get("created_at"),
            "generated_at": datetime.now(UTC).isoformat(),
        }

        return summary
