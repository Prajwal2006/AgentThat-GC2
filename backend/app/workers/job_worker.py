"""Event-driven job execution worker with phase-based processing.

Processes background jobs from the Redis queue, executing them in phases:
  1. Analysis → 2. Design → 3. Configuration → 4. Validation

Each phase emits progress events to subscribers via Redis pub/sub.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, UTC
from typing import Any

from app.services.job_queue import JobQueueService

logger = logging.getLogger(__name__)

# Phase definitions with progress ranges
PHASES = [
    {"name": "analysis", "start_pct": 0, "end_pct": 25, "message": "Analyzing requirements..."},
    {"name": "design", "start_pct": 25, "end_pct": 50, "message": "Designing architecture..."},
    {"name": "configuration", "start_pct": 50, "end_pct": 75, "message": "Generating configuration..."},
    {"name": "validation", "start_pct": 75, "end_pct": 100, "message": "Validating output..."},
]


class JobWorker:
    """Processes jobs from the queue with phase-based execution."""

    def __init__(self):
        self.queue = JobQueueService()
        self._running = False

    async def start(self, poll_interval: float = 1.0) -> None:
        """Start the worker loop."""
        self._running = True
        logger.info("Job worker started")

        while self._running:
            try:
                job = await self.queue.dequeue()
                if job:
                    await self._process_job(job)
                else:
                    await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(poll_interval)

    def stop(self) -> None:
        """Stop the worker loop."""
        self._running = False
        logger.info("Job worker stopping")

    async def _process_job(self, job: dict[str, Any]) -> None:
        """Execute a job through all phases."""
        job_id = uuid.UUID(job["id"])
        job_type = job["job_type"]

        logger.info(f"Processing job {job_id} (type={job_type})")

        try:
            result = await self._execute_phases(job_id, job)
            await self.queue.complete(job_id, result_data=result)
            logger.info(f"Job {job_id} completed successfully")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id} failed: {error_msg}")

            # Retry logic
            retry_count = job.get("retry_count", 0)
            max_retries = job.get("max_retries", 3)

            if retry_count < max_retries:
                # Re-enqueue with incremented retry count
                job["retry_count"] = retry_count + 1
                await self.queue.enqueue(
                    tenant_id=uuid.UUID(job["tenant_id"]),
                    user_id=uuid.UUID(job["user_id"]),
                    job_type=job_type,
                    input_data=job["input_data"],
                )
                logger.info(f"Job {job_id} re-queued (retry {retry_count + 1}/{max_retries})")
            else:
                await self.queue.fail(job_id, error_detail=error_msg)

    async def _execute_phases(
        self, job_id: uuid.UUID, job: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute all phases, emitting progress at each step."""
        result: dict[str, Any] = {"phases_completed": [], "output": None}
        input_data = job.get("input_data", {})

        for phase in PHASES:
            # Update progress at phase start
            await self.queue.update_progress(
                job_id,
                progress_pct=phase["start_pct"],
                status_message=phase["message"],
            )

            # Execute phase (dispatches to handler based on job_type)
            phase_result = await self._run_phase(
                phase["name"], job["job_type"], input_data, result
            )
            result["phases_completed"].append(phase["name"])
            result["output"] = phase_result

            # Update progress at phase end
            await self.queue.update_progress(
                job_id,
                progress_pct=phase["end_pct"],
                status_message=f"{phase['name'].title()} complete",
            )

        return result

    async def _run_phase(
        self,
        phase_name: str,
        job_type: str,
        input_data: dict[str, Any],
        accumulated_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a single phase. Override for custom job types."""
        # Default implementation - simulate work
        # In production, this would dispatch to specific handlers
        # based on job_type (e.g., "solution_generation", "agent_generation")
        await asyncio.sleep(0.5)  # Simulate processing

        if job_type == "solution_generation":
            return await self._phase_solution(phase_name, input_data, accumulated_result)
        elif job_type == "agent_generation":
            return await self._phase_agent(phase_name, input_data, accumulated_result)
        else:
            return {"phase": phase_name, "status": "completed"}

    async def _phase_solution(
        self, phase_name: str, input_data: dict, result: dict
    ) -> dict:
        """Solution generation phases."""
        if phase_name == "analysis":
            return {"objectives": input_data.get("requirement", "")[:500]}
        elif phase_name == "design":
            return {"agents_count": 4, "workflow_steps": 5}
        elif phase_name == "configuration":
            return {"configured": True}
        else:
            return {"validated": True}

    async def _phase_agent(
        self, phase_name: str, input_data: dict, result: dict
    ) -> dict:
        """Agent generation phases."""
        if phase_name == "analysis":
            return {"description_parsed": True}
        elif phase_name == "design":
            return {"tools_selected": [], "memory_config": "short-term"}
        elif phase_name == "configuration":
            return {"agent_config_generated": True}
        else:
            return {"validation_passed": True}


async def run_worker() -> None:
    """Entry point for running the worker process."""
    worker = JobWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
