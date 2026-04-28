"""Self-looping chatbot.

A single agent owns one full conversation turn:
  read user input -> append to messages -> call LLM -> append response -> loop.

The loop is `handoff` returning `(self,)` until the user types 'exit'.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat_completion


class ChatAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store.setdefault("messages", [])
        try:
            user = input("You: ").strip()
        except EOFError:
            user = "exit"
        if user.lower() == "exit":
            store["done"] = True
            return
        store["messages"].append({"role": "user", "content": user})
        reply = chat_completion(store["messages"])
        store["messages"].append({"role": "assistant", "content": reply})
        print(f"Assistant: {reply}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return () if store.get("done") else (self,)


def build_chat_flow() -> BaseFlow:
    chat = ChatAgent(meta=BaseMeta(name="chat"))
    return BaseFlow(meta=BaseMeta(name="chat_flow"), branches=(chat,))
