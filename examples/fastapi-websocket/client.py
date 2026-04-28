"""Tiny WebSocket client that pipes stdin lines to the chat server."""

import asyncio
import sys

import websockets


async def chat() -> None:
    async with websockets.connect("ws://127.0.0.1:7823/chat") as ws:
        print("Connected. Type a message (Ctrl-D to quit).")
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            except (KeyboardInterrupt, EOFError):
                return
            if not line:
                return
            await ws.send(line.strip())
            print("Assistant: ", end="", flush=True)
            while True:
                chunk = await ws.recv()
                if chunk == "[[END]]":
                    print()
                    break
                print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(chat())
