"""Minimal A2A client that hits the local server."""

import sys
import uuid

import httpx


URL = "http://127.0.0.1:7820/"


def call(method: str, params: dict) -> dict:
    return httpx.post(URL, json={
        "jsonrpc": "2.0", "id": str(uuid.uuid4()),
        "method": method, "params": params,
    }, timeout=120).json()


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What does the BSP barrier discipline buy you?"
    print("--- agent.card ---")
    print(call("agent.card", {})["result"])
    print("\n--- tasks/send ---")
    resp = call("tasks/send", {"message": {"parts": [{"text": question}]}})
    artifact = resp["result"]["artifacts"][0]["parts"][0]["text"]
    print(artifact)
