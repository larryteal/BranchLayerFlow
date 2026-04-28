"""Spec -> tests -> implementation -> run -> (fix loop).

  GenerateTestsAgent  (write pytest cases)
        |
        v
  ImplementAgent      (write candidate solution)
        |
        v
  RunTestsAgent       (exec; capture failures into store["failures"])
        |
        +--[pass]--> ()
        +--[fail]--> ReviseAgent  (decide whether to fix tests or code)
                          |
                          v (loop back to RunTests via re-execution)
"""

import io
import textwrap
import traceback
import unittest
from typing import Any, Optional, Tuple

from branchlayerflow import BaseAgent, BaseFlow, BaseMeta

from utils import chat, strip_code_block


def _exec_module(source: str, name: str = "candidate"):
    module_globals: dict = {}
    exec(compile(source, f"<{name}>", "exec"), module_globals)
    return module_globals


def _run_tests(impl_src: str, tests_src: str) -> Tuple[bool, str]:
    """Run tests against implementation; return (passed, log)."""
    try:
        ns = _exec_module(impl_src, "impl")
        ns_tests = dict(ns)
        exec(compile(tests_src, "<tests>", "exec"), ns_tests)
    except Exception:
        return False, traceback.format_exc()

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name, obj in ns_tests.items():
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            suite.addTests(loader.loadTestsFromTestCase(obj))
    buf = io.StringIO()
    result = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
    return result.wasSuccessful(), buf.getvalue()


class GenerateTestsAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["tests"] = strip_code_block(chat([
            {"role": "system", "content": "You write thorough pytest-style unittest classes."},
            {"role": "user", "content": (
                f"Problem:\n{store['problem']}\n\n"
                "Write a single Python module with one `unittest.TestCase` subclass "
                "exercising the function described in the problem (including edge cases). "
                "Assume the function is already imported into the test module's namespace. "
                "Return code only, in a single python fence."
            )},
        ]))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["implement"],)


class ImplementAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        feedback = store.get("feedback", "")
        msg = (
            f"Problem:\n{store['problem']}\n\nTests (already written):\n{store['tests']}\n\n"
            "Write a Python implementation that satisfies the tests. "
            "Return code only, in a single python fence."
        )
        if feedback:
            msg += f"\n\nPrior failure feedback:\n{feedback}"
        store["impl"] = strip_code_block(chat([
            {"role": "system", "content": "You write minimal correct Python code."},
            {"role": "user", "content": msg},
        ]))

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["run"],)


class RunTestsAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        store["passed"], store["log"] = _run_tests(store["impl"], store["tests"])
        store["attempts"] = store.get("attempts", 0) + 1
        print(f"\n--- Attempt {store['attempts']} ---\n{store['log']}")

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        if store["passed"] or store["attempts"] >= self.meta.max_attempts:
            return ()
        return (self.successors["revise"],)


class ReviseAgent(BaseAgent):
    def takeover(self, store: Any) -> None:
        decision = chat([
            {"role": "system", "content": (
                "You read failing test logs and decide whether the bug is in the "
                "TESTS or the CODE. Reply EXACTLY `FIX_TESTS` or `FIX_CODE`."
            )},
            {"role": "user", "content": (
                f"Problem: {store['problem']}\n\nTests:\n{store['tests']}\n\n"
                f"Code:\n{store['impl']}\n\nFailures:\n{store['log']}"
            )},
        ]).strip().upper()
        store["feedback"] = store["log"]
        if "FIX_TESTS" in decision:
            store["tests"] = strip_code_block(chat([
                {"role": "system", "content": "Fix the test module based on the failure log."},
                {"role": "user", "content": f"Tests:\n{store['tests']}\n\nFailures:\n{store['log']}"},
            ]))
        # CODE case: ImplementAgent will use store["feedback"]

    def handoff(self, store: Any) -> Optional[Tuple[BaseAgent, ...]]:
        return (self.successors["implement"],)


def build_codegen_flow() -> BaseFlow:
    gen_tests = GenerateTestsAgent(meta=BaseMeta(name="gen_tests"))
    impl = ImplementAgent(meta=BaseMeta(name="implement"))
    run = RunTestsAgent(meta=BaseMeta(name="run", max_attempts=4))
    revise = ReviseAgent(meta=BaseMeta(name="revise"))
    gen_tests >> impl
    impl >> run
    run >> revise
    revise >> impl
    return BaseFlow(meta=BaseMeta(name="codegen_flow"), branches=(gen_tests,))
