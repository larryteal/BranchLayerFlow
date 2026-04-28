"""Mocked async I/O helpers — stand-ins for a real recipe API and LLM call."""

import asyncio
import random
from typing import List


async def fetch_recipes(ingredient: str) -> List[str]:
    await asyncio.sleep(0.5)
    return [
        f"{ingredient.title()} stir-fry",
        f"Roasted {ingredient}",
        f"{ingredient.title()} salad",
        f"Grilled {ingredient} skewers",
    ]


async def suggest_recipe(recipes: List[str]) -> str:
    await asyncio.sleep(0.3)
    return random.choice(recipes)


async def get_user_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return (await loop.run_in_executor(None, input, prompt)).strip().lower()
