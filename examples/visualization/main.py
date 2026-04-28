from flow import build_order_flow
from visualizer import render_mermaid


def main() -> None:
    flow = build_order_flow()
    mermaid = render_mermaid(flow)
    print("```mermaid")
    print(mermaid)
    print("```")


if __name__ == "__main__":
    main()
