import asyncio
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.models import ReviewDecision, TaskCreate, TaskStatus
from app.services.orchestrator import manager


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("")
async def create_task(payload: TaskCreate):
    return manager.create(payload.prompt, payload.scenario)


@router.post("/{task_id}/confirm")
async def confirm_task(task_id: str):
    return manager.start(task_id)


@router.get("/{task_id}")
async def get_task(task_id: str):
    return manager.get(task_id)


@router.post("/{task_id}/review")
async def review_task(task_id: str, payload: ReviewDecision):
    return manager.review(task_id, payload)


@router.get("/{task_id}/events")
async def task_events(task_id: str, after: int = Query(default=0, ge=0)):
    manager.get(task_id)

    async def event_stream():
        cursor = after
        idle_cycles = 0
        terminal = {TaskStatus.COMPLETED, TaskStatus.REJECTED, TaskStatus.FAILED}
        while True:
            current = manager.get(task_id)
            while cursor < len(current.events):
                event = current.events[cursor]
                cursor += 1
                yield f"id: {event.sequence}\ndata: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"
                idle_cycles = 0
            if current.status in terminal and cursor >= len(current.events):
                break
            idle_cycles += 1
            if idle_cycles % 25 == 0:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.12)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/{task_id}/report")
async def task_report(task_id: str):
    task = manager.get(task_id)
    return {"task_id": task.id, "status": task.status, "goal": task.goal, "metrics": task.metrics, "assets": task.assets, "review": task.review}

