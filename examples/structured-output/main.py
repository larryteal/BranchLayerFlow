from collections import deque
from pprint import pprint

from flow import build_resume_flow


SAMPLE_RESUME = """\
John Smith
john.smith@example.com

Experience:
  Senior Engineer at Acme Corp (2020-2024)
  Engineer at Globex (2017-2020)

Skills: team leadership, CRM software, Python, distributed systems.
"""


def main() -> None:
    store = {"resume": SAMPLE_RESUME, "parsed": None}
    deque(build_resume_flow()(store=store), maxlen=0)
    pprint(store["parsed"])


if __name__ == "__main__":
    main()
