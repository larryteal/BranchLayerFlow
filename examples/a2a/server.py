"""A2A-shaped JSON-RPC over HTTP. Two methods:

  - tasks/send       run the inner agent, return one artifact
  - agent.card       describe what this agent does

This is a minimal A2A-compatible adapter; production A2A uses richer
streaming + state machine semantics, but the shape is the same.
"""

import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from inner_flow import answer_question


app = FastAPI()


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: Dict[str, Any] = {}


@app.post("/")
async def jsonrpc(req: JsonRpcRequest) -> dict:
    if req.method == "agent.card":
        return _ok(req.id, {
            "name": "blf-research-agent",
            "description": "Answers a question concisely using a BLF flow.",
            "version": "0.1.0",
            "capabilities": ["tasks/send"],
        })
    if req.method == "tasks/send":
        question = (
            req.params.get("message", {}).get("parts", [{}])[0].get("text")
            or req.params.get("question")
            or ""
        )
        if not question:
            raise HTTPException(400, "missing 'question' in params or message.parts[0].text")
        return _ok(req.id, {
            "id": str(uuid.uuid4()),
            "status": {"state": "completed"},
            "artifacts": [{
                "name": "answer",
                "parts": [{"type": "text", "text": answer_question(question)}],
            }],
        })
    raise HTTPException(404, f"unknown method: {req.method}")


def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7820)
