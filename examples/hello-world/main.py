from collections import deque

from flow import build_qa_flow


def main() -> None:
    store = {
        "question": "In one sentence, what's the end of universe?",
        "answer": None,
    }
    qa_flow = build_qa_flow()
    deque(qa_flow(store=store), maxlen=0)
    print(f"Question: {store['question']}")
    print(f"Answer:   {store['answer']}")


if __name__ == "__main__":
    main()
