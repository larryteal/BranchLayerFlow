"""Two-agent Taboo game.

  HinterAgent  --(handoff)--> GuesserAgent --(handoff)--> HinterAgent --> ...
                                            \---(correct)---> ()

The "message queue" is just a `store["transcript"]` list. Each agent
reads what was said, contributes the next utterance, and hands the
baton to the other side. Termination = `handoff` returning `()` when
the guess matches.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import AsyncBaseAgent, AsyncBaseFlow, BaseMeta

from utils import chat


def _transcript(store: Any) -> str:
    return "\n".join(f"{role}: {msg}" for role, msg in store["transcript"])


class HinterAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        reply = await chat([
            {"role": "system", "content": (
                "You are the Hinter in a Taboo word game. "
                f"The target word is '{store['target']}'. "
                f"You must NOT use any of these forbidden words: {store['forbidden']}. "
                "Give one short clue (one sentence). Do NOT reveal the target word."
            )},
            {"role": "user", "content": f"Conversation so far:\n{_transcript(store)}\n\nNext clue:"},
        ])
        store["transcript"].append(("Hinter", reply))
        print(f"Hinter: {reply}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        return (self.successors["guesser"],)


class GuesserAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        reply = await chat([
            {"role": "system", "content": (
                "You are the Guesser in a Taboo word game. Read the clues "
                "and guess the target word. Reply with a single word — your guess."
            )},
            {"role": "user", "content": f"Clues so far:\n{_transcript(store)}\n\nYour single-word guess:"},
        ])
        guess = reply.strip().split()[0].strip(".,!?\"'").lower()
        store["transcript"].append(("Guesser", guess))
        store["guess"] = guess
        print(f"Guesser: {guess}")

    async def handoff(self, store: Any) -> Optional[Tuple[AsyncBaseAgent, ...]]:
        if store["guess"] == store["target"].lower():
            print(f"\nCorrect — '{store['target']}' guessed in {len(store['transcript'])//2} round(s).")
            return ()
        if len(store["transcript"]) // 2 >= store["max_rounds"]:
            print(f"\nGiving up after {store['max_rounds']} rounds. Target was '{store['target']}'.")
            return ()
        return (self.successors["hinter"],)


def build_taboo_flow() -> AsyncBaseFlow:
    hinter = HinterAgent(meta=BaseMeta(name="hinter"))
    guesser = GuesserAgent(meta=BaseMeta(name="guesser"))
    hinter >> guesser
    guesser >> hinter
    return AsyncBaseFlow(meta=BaseMeta(name="taboo_flow"), branches=(hinter,))
