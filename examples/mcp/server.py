"""Tiny MCP server exposing add/subtract/multiply tools.

Run as a stdio MCP server: `python server.py` (the agent spawns it).
"""

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("blf-math-server")


@mcp.tool()
def add(a: float, b: float) -> float:
    return a + b


@mcp.tool()
def sub(a: float, b: float) -> float:
    return a - b


@mcp.tool()
def mul(a: float, b: float) -> float:
    return a * b


if __name__ == "__main__":
    mcp.run()
