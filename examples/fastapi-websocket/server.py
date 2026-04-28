"""FastAPI WebSocket chat. Each connection gets its own message history."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from flow import build_chat_flow


app = FastAPI()


@app.websocket("/chat")
async def chat_ws(ws: WebSocket) -> None:
    await ws.accept()
    messages = []
    try:
        while True:
            user_text = await ws.receive_text()

            async def send(chunk: str) -> None:
                await ws.send_text(chunk)

            store = {"user_text": user_text, "messages": messages, "ws_send": send}
            async for _ in build_chat_flow()(store=store):
                pass
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7823)
