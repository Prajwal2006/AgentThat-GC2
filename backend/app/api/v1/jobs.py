"""Background job API endpoints with SSE streaming."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.middleware.auth import AuthContext, get_current_user
from app.services.job_queue import JobQueueService

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

_queue = JobQueueService()


class JobStatusResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    job_type: str
    status: str
    progress_pct: int
    status_message: str | None
    result_data: dict | None
    error_detail: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
):
    """Get current job status."""
    job = await _queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["tenant_id"] != str(auth.tenant_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**{k: job[k] for k in JobStatusResponse.model_fields})


@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
):
    """SSE stream of job progress updates (≤5 second interval)."""
    job = await _queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["tenant_id"] != str(auth.tenant_id):
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        import redis.asyncio as redis
        from app.config import settings

        r = redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = r.pubsub()
        channel = f"job:progress:{job_id}"
        await pubsub.subscribe(channel)

        try:
            # Send initial state
            current = await _queue.get_job(job_id)
            if current:
                yield f"data: {json.dumps({'job_id': str(job_id), 'progress_pct': current['progress_pct'], 'status_message': current['status_message'], 'status': current['status']})}\n\n"

            # Stream updates
            while True:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0),
                    timeout=6.0,
                )
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                    data = json.loads(message["data"])
                    if data.get("status") in ("completed", "failed", "cancelled"):
                        break
                else:
                    # Heartbeat every 5 seconds
                    yield f": heartbeat\n\n"
        except asyncio.TimeoutError:
            yield f": heartbeat\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
):
    """Cancel a queued or processing job."""
    job = await _queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["tenant_id"] != str(auth.tenant_id):
        raise HTTPException(status_code=404, detail="Job not found")

    cancelled = await _queue.cancel(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job in '{job['status']}' state"
        )
    return {"status": "cancelled", "job_id": str(job_id)}
