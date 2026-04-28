"""FastAPI HITL: submit, watch progress via SSE, send approve/reject."""

import asyncio
import json
import threading
import uuid
from collections import deque
from typing import Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from flow import build_hitl_flow


app = FastAPI()


class Job:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()
        self.review_event = threading.Event()
        self.store: dict = {}


JOBS: Dict[str, Job] = {}


class StartRequest(BaseModel):
    text: str


class DecisionRequest(BaseModel):
    decision: str  # 'approve' | 'reject'


def _run(job: Job, text: str, loop: asyncio.AbstractEventLoop) -> None:
    def sink(event: dict) -> None:
        asyncio.run_coroutine_threadsafe(job.queue.put(event), loop)

    job.store = {
        "text": text,
        "sink": sink,
        "review_event": job.review_event,
        "last_decision": "reject",
    }
    deque(build_hitl_flow()(store=job.store), maxlen=0)
    asyncio.run_coroutine_threadsafe(job.queue.put({"stage": "done"}), loop)


@app.post("/jobs")
async def create_job(req: StartRequest, bg: BackgroundTasks) -> dict:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = Job()
    bg.add_task(_run, JOBS[job_id], req.text, asyncio.get_running_loop())
    return {"job_id": job_id}


@app.get("/jobs/{job_id}/events")
async def events(job_id: str) -> StreamingResponse:
    if job_id not in JOBS:
        raise HTTPException(404, "unknown job")
    job = JOBS[job_id]

    async def stream():
        while True:
            event = await job.queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("stage") == "done":
                return

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/jobs/{job_id}/review")
async def review(job_id: str, req: DecisionRequest) -> dict:
    if job_id not in JOBS:
        raise HTTPException(404, "unknown job")
    job = JOBS[job_id]
    job.store["last_decision"] = req.decision
    job.review_event.set()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7822)
