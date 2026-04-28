"""Interactive text transformer.

Two agents pass the baton back and forth:

  PromptAgent (asks for text + choice)
      |
      |  handoff -> TransformAgent (if a transform was chosen)
      |  handoff -> ()             (if user typed 'q')
      v
  TransformAgent (applies it, asks "another?")
      |
      |  handoff -> PromptAgent    (loop back for new text)
      |  handoff -> ()             (terminate)

`>>` registers both agents in each other's successor dict so either side
can return the other from `handoff`.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta


TRANSFORMS = {
    "1": ("upper", lambda s: s.upper()),
    "2": ("lower", lambda s: s.lower()),
    "3": ("reverse", lambda s: s[::-1]),
    "4": ("strip", lambda s: " ".join(s.split())),
}


def _read(prompt: str, default: Optional[str] = None) -> str:
    try:
        value = input(prompt).strip()
    except EOFError:
        value = ""
    return value or (default or "")


class PromptAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        if not store.get("text"):
            store["text"] = _read("Enter text (q to quit): ")
        if store["text"].lower() == "q":
            store["choice"] = "q"
            return
        print("Choose a transform:")
        for key, (name, _) in TRANSFORMS.items():
            print(f"  {key}. {name}")
        print("  q. quit")
        store["choice"] = _read("> ", default="q")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["choice"] in TRANSFORMS:
            return (self.successors["transform"],)
        return ()


class TransformAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        name, fn = TRANSFORMS[store["choice"]]
        result = fn(store["text"])
        print(f"[{name}] {result}")
        again = _read("Transform another? (y/n): ", default="n").lower()
        store["again"] = again.startswith("y")
        if store["again"]:
            store["text"] = ""

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["again"]:
            return (self.successors["prompt"],)
        return ()


def build_text_flow() -> BaseFlow:
    prompt = PromptAgent(meta=BaseMeta(name="prompt"))
    transform = TransformAgent(meta=BaseMeta(name="transform"))
    prompt >> transform
    transform >> prompt
    return BaseFlow(meta=BaseMeta(name="text_flow"), branches=(prompt,))
