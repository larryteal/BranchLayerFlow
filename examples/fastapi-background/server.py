"""FastAPI app exposing the writing flow as a background job + SSE progress."""

import asyncio
import json
import uuid
from collections import deque
from typing import Dict

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from flow import build_writing_flow


app = FastAPI()
JOBS: Dict[str, asyncio.Queue] = {}


class StartRequest(BaseModel):
    topic: str


def _run_job(job_id: str, topic: str, loop: asyncio.AbstractEventLoop) -> None:
    queue = JOBS[job_id]

    def sink(event: dict) -> None:
        # called from the worker thread; bounce onto the event loop's thread-safe API
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    store = {"topic": topic, "sink": sink}
    flow = build_writing_flow()
    deque(flow(store=store), maxlen=0)
    asyncio.run_coroutine_threadsafe(queue.put({"stage": "done", "status": "done"}), loop)


@app.post("/generate")
async def generate(req: StartRequest, bg: BackgroundTasks) -> dict:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = asyncio.Queue()
    bg.add_task(_run_job, job_id, req.topic, asyncio.get_running_loop())
    return {"job_id": job_id}


@app.get("/events/{job_id}")
async def events(job_id: str) -> StreamingResponse:
    if job_id not in JOBS:
        return StreamingResponse(iter(["data: {\"error\": \"unknown job\"}\n\n"]), media_type="text/event-stream")
    queue = JOBS[job_id]

    async def stream():
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("stage") == "done":
                return

    return StreamingResponse(stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7821)
