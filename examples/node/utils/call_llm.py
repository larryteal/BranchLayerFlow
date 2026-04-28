import os

from openai import OpenAI


def call_llm(prompt: str, model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
