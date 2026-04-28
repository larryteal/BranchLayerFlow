"""Resume parser using YAML-formatted output.

A single agent prompts the LLM to return YAML matching a fixed schema,
then parses + validates it. Validation failure triggers a retry through
BLF's inheritance-based retry pattern.
"""

from typing import Any, Dict, Optional

import yaml
from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import call_llm


SCHEMA_KEYS = {"name", "email", "experience", "skills"}


PROMPT_TEMPLATE = """Extract the following fields from the resume below.
Return ONLY valid YAML, no surrounding prose, no fencing.

Schema:
  name: string
  email: string
  experience: list of {{title: string, company: string}}
  skills: list of {{index: int, name: string}}

Resume:
---
{resume}
---
"""


def _parse_yaml(text: str) -> Dict[str, Any]:
    if "```" in text:
        # tolerate occasional markdown fencing
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            body = parts[i]
            if body.startswith("yaml"):
                body = body[4:]
            try:
                return yaml.safe_load(body)
            except yaml.YAMLError:
                continue
    return yaml.safe_load(text)


class ResumeParseAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        last_error: Optional[Exception] = None
        for attempt in range(getattr(self.meta, "max_retries", 1)):
            try:
                raw = call_llm(PROMPT_TEMPLATE.format(resume=store["resume"]))
                parsed = _parse_yaml(raw)
                missing = SCHEMA_KEYS - set(parsed or ())
                if missing:
                    raise ValueError(f"missing keys: {sorted(missing)}")
                store["parsed"] = parsed
                return
            except Exception as exc:
                print(f"  attempt {attempt + 1} failed: {exc}")
                last_error = exc
        raise RuntimeError(f"giving up after retries: {last_error}")


def build_resume_flow() -> BaseFlow:
    parser = ResumeParseAgent(meta=BaseMeta(name="resume", max_retries=3))
    return BaseFlow(meta=BaseMeta(name="resume_flow"), branches=(parser,))
