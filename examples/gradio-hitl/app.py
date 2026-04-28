"""Gradio chat UI in front of the routing flow."""

from collections import deque

import gradio as gr

from flow import build_router_flow


def respond(user_text: str, history: list) -> str:
    store = {"user_text": user_text, "reply": "", "route": ""}
    deque(build_router_flow()(store=store), maxlen=0)
    return f"[{store['route']}] {store['reply']}"


def main() -> None:
    gr.ChatInterface(respond, title="BLF Travel Assistant",
                     description="Routes your message to weather / booking / follow-up.").launch()


if __name__ == "__main__":
    main()
