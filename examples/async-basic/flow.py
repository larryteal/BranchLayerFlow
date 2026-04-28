"""Async pipeline with rejection loop.

  FetchAgent     (gets ingredient, fetches recipes)
       |
       v
  SuggestAgent   (picks one) <----+
       |                          |
       v                          | (retry handoff)
  ApprovalAgent  ----[reject]-----+
       |
       v
       () terminate (accept)

The retry "loop" is just an `AsyncBaseAgent.handoff` returning the
SuggestAgent again.
"""

from typing import Any, Optional, Tuple

from branchlayerflow import AsyncBaseAgent, AsyncBaseFlow, BaseAgent, BaseMeta

from utils import fetch_recipes, get_user_input, suggest_recipe


class FetchAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        if not store.get("ingredient"):
            store["ingredient"] = await get_user_input("Ingredient: ") or "tofu"
        store["recipes"] = await fetch_recipes(store["ingredient"])
        print(f"Fetched {len(store['recipes'])} recipes for {store['ingredient']!r}.")

    async def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["suggest"],)


class SuggestAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        store["suggestion"] = await suggest_recipe(store["recipes"])
        print(f"Suggestion: {store['suggestion']}")

    async def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["approve"],)


class ApprovalAgent(AsyncBaseAgent):
    async def takeover(self, store: Any) -> None:
        ans = await get_user_input("Accept? (y/n): ")
        store["accepted"] = ans.startswith("y")

    async def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["accepted"]:
            print(f"\nFinal pick: {store['suggestion']} (with {store['ingredient']})")
            return ()
        print("Trying another...")
        return (self.successors["suggest"],)


def build_recipe_flow() -> AsyncBaseFlow:
    fetch = FetchAgent(meta=BaseMeta(name="fetch"))
    suggest = SuggestAgent(meta=BaseMeta(name="suggest"))
    approve = ApprovalAgent(meta=BaseMeta(name="approve"))
    fetch >> suggest
    suggest >> approve
    approve >> suggest
    return AsyncBaseFlow(meta=BaseMeta(name="recipe_flow"), branches=(fetch,))
