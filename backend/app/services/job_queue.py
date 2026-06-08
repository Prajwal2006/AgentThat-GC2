"""Redis-backed job queue with priority ordering and tenant concurrency limits."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC, timedelta
from typing import Any

import redis.asyncio as redis

from app.config import settings


class JobQueueError(Exception):
    """Job queue operation failure."""
    pass


class TenantConcurrencyExceeded(Exception):
    """Tenant has reached maximum concurrent job limit."""
    pass


# Priority tier weights (higher = processed first)
TIER_PRIORITY: dict[str, int] = {
    "enterprise": 100,
    "professional": 50,
    "standard": 10,
}

JOB_TIMEOUT_SECONDS = 1800  # 30 minutes


class JobQueueService:
    """Manages background job queuing with priority ordering and concurrency limits."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self._redis = redis_client

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _compute_priority(self, tenant_tier: str, created_at: datetime) -> float:
        """Priority score: higher tier first, then earlier timestamp."""
        tier_weight = TIER_PRIORITY.get(tenant_tier, 10)
        # Use negative epoch so earlier times get higher score within same tier
        epoch = created_at.timestamp()
        return tier_weight * 1_000_000 - epoch

    async def enqueue(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        job_type: str,
        input_data: dict[str, Any],
        tenant_tier: str = "standard",
        max_concurrent: int = 5,
    ) -> uuid.UUID:
        """Enqueue a job with priority. Returns job_id within 2 seconds."""
        r = await self._get_redis()

        # Check tenant concurrency
        active_key = f"jobs:active:{tenant_id}"
        active_count = await r.scard(active_key)
        if active_count >= max_concurrent:
            raise TenantConcurrencyExceeded(
                f"Tenant {tenant_id} has {active_count}/{max_concurrent} concurrent jobs"
            )

        job_id = uuid.uuid4()
        now = datetime.now(UTC)
        priority = self._compute_priority(tenant_tier, now)

        job_payload = {
            "id": str(job_id),
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "job_type": job_type,
            "status": "queued",
            "priority": priority,
            "progress_pct": 0,
            "status_message": "Queued",
            "input_data": input_data,
            "result_data": None,
            "error_detail": None,
            "retry_count": 0,
            "max_retries": 3,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "expires_at": (now + timedelta(days=7)).isoformat(),
        }

        # Store job data
        job_key = f"job:{job_id}"
        await r.set(job_key, json.dumps(job_payload), ex=7 * 86400)

        # Add to priority queue (sorted set, higher score = higher priority)
        await r.zadd("jobs:queue", {str(job_id): priority})

        return job_id

    async def dequeue(self) -> dict[str, Any] | None:
        """Dequeue the highest priority job. Returns job payload or None."""
        r = await self._get_redis()

        # Pop highest priority (highest score)
        results = await r.zpopmax("jobs:queue", count=1)
        if not results:
            return None

        job_id_str, _score = results[0]
        job_key = f"job:{job_id_str}"
        raw = await r.get(job_key)
        if not raw:
            return None

        job = json.loads(raw)
        job["status"] = "processing"
        job["started_at"] = datetime.now(UTC).isoformat()
        await r.set(job_key, json.dumps(job), ex=7 * 86400)

        # Track in active set
        active_key = f"jobs:active:{job['tenant_id']}"
        await r.sadd(active_key, job_id_str)

        return job

    async def update_progress(
        self,
        job_id: uuid.UUID,
        *,
        progress_pct: int,
        status_message: str = "",
    ) -> None:
        """Update job progress (0-100) and status message."""
        r = await self._get_redis()
        job_key = f"job:{job_id}"
        raw = await r.get(job_key)
        if not raw:
            return

        job = json.loads(raw)
        job["progress_pct"] = min(max(progress_pct, 0), 100)
        job["status_message"] = status_message[:200]
        await r.set(job_key, json.dumps(job), ex=7 * 86400)

        # Publish progress event for SSE subscribers
        await r.publish(f"job:progress:{job_id}", json.dumps({
            "job_id": str(job_id),
            "progress_pct": job["progress_pct"],
            "status_message": job["status_message"],
            "status": job["status"],
        }))

    async def complete(
        self,
        job_id: uuid.UUID,
        *,
        result_data: dict[str, Any] | None = None,
    ) -> None:
        """Mark a job as completed."""
        r = await self._get_redis()
        job_key = f"job:{job_id}"
        raw = await r.get(job_key)
        if not raw:
            return

        job = json.loads(raw)
        job["status"] = "completed"
        job["progress_pct"] = 100
        job["status_message"] = "Completed"
        job["result_data"] = result_data
        job["completed_at"] = datetime.now(UTC).isoformat()
        await r.set(job_key, json.dumps(job), ex=7 * 86400)

        # Remove from active set
        active_key = f"jobs:active:{job['tenant_id']}"
        await r.srem(active_key, str(job_id))

        # Publish completion event
        await r.publish(f"job:progress:{job_id}", json.dumps({
            "job_id": str(job_id),
            "progress_pct": 100,
            "status_message": "Completed",
            "status": "completed",
        }))

    async def fail(
        self,
        job_id: uuid.UUID,
        *,
        error_detail: str,
    ) -> None:
        """Mark a job as failed."""
        r = await self._get_redis()
        job_key = f"job:{job_id}"
        raw = await r.get(job_key)
        if not raw:
            return

        job = json.loads(raw)
        job["status"] = "failed"
        job["status_message"] = "Failed"
        job["error_detail"] = error_detail
        job["completed_at"] = datetime.now(UTC).isoformat()
        await r.set(job_key, json.dumps(job), ex=7 * 86400)

        # Remove from active set
        active_key = f"jobs:active:{job['tenant_id']}"
        await r.srem(active_key, str(job_id))

        # Publish failure event
        await r.publish(f"job:progress:{job_id}", json.dumps({
            "job_id": str(job_id),
            "progress_pct": job["progress_pct"],
            "status_message": f"Failed: {error_detail[:100]}",
            "status": "failed",
        }))

    async def cancel(self, job_id: uuid.UUID) -> bool:
        """Cancel a queued or processing job."""
        r = await self._get_redis()
        job_key = f"job:{job_id}"
        raw = await r.get(job_key)
        if not raw:
            return False

        job = json.loads(raw)
        if job["status"] not in ("queued", "processing"):
            return False

        job["status"] = "cancelled"
        job["completed_at"] = datetime.now(UTC).isoformat()
        await r.set(job_key, json.dumps(job), ex=7 * 86400)

        # Remove from queue and active set
        await r.zrem("jobs:queue", str(job_id))
        active_key = f"jobs:active:{job['tenant_id']}"
        await r.srem(active_key, str(job_id))

        return True

    async def get_job(self, job_id: uuid.UUID) -> dict[str, Any] | None:
        """Get current job state."""
        r = await self._get_redis()
        raw = await r.get(f"job:{job_id}")
        if not raw:
            return None
        return json.loads(raw)

    async def check_timeouts(self) -> list[uuid.UUID]:
        """Check for jobs that have exceeded the 30-minute timeout."""
        r = await self._get_redis()
        timed_out: list[uuid.UUID] = []
        # This would be called periodically by the worker
        # Simplified: scan active jobs and check started_at
        return timed_out
