"""Write -> Compile -> (Fix loop) for Mermaid diagrams."""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm, compile_mermaid, strip_fence


class WriteAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        feedback = store.get("error", "")
        msg = (
            f"Description:\n{store['description']}\n\n"
            "Generate a valid Mermaid diagram. Reply ONLY with code in a "
            "```mermaid fence."
        )
        if feedback:
            msg += f"\n\nLast attempt failed with:\n{feedback}\nFix it."
        store["diagram"] = strip_fence(call_llm(msg))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["compile"],)


class CompileAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["attempts"] = store.get("attempts", 0) + 1
        store["ok"], store["error"] = compile_mermaid(store["diagram"])
        print(f"\n--- Attempt {store['attempts']} ---\n{store['diagram']}\n[{('OK' if store['ok'] else 'FAIL')}: {store['error']}]")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["ok"] or store["attempts"] >= self.meta.max_attempts:
            return ()
        return (self.successors["write"],)


def build_mermaid_flow() -> BaseFlow:
    w = WriteAgent(meta=BaseMeta(name="write"))
    c = CompileAgent(meta=BaseMeta(name="compile", max_attempts=3))
    w >> c
    c >> w
    return BaseFlow(meta=BaseMeta(name="mermaid_flow"), branches=(w,))
