"""
client.py -- the MCP CLIENT + CLI around the agent loop.

  uv run python client.py --list-tools
  uv run python client.py "Simulate a PID with Kp=2, Ki=8 on a plant with time constant 2 s."
  uv run python client.py --model qwen2.5-coder:7b "Did the oven go above 220 C?"
  uv run python client.py            # interactive
"""
import argparse
import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent import mcp_tool_to_ollama, run_question

# Windows consoles often default to a legacy code page; make printing safe (degrees, ohms, arrows...).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).parent


@asynccontextmanager
async def connect():
    """Start server.py as a subprocess (same Python env) and open an MCP session."""
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--model", default="qwen3:4b")
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--think", action="store_true", help="enable thinking mode (default off)")
    args = ap.parse_args()

    async with connect() as session:
        if args.list_tools:
            for t in (await session.list_tools()).tools:
                print(mcp_tool_to_ollama(t)["function"]["name"], "-", (t.description or "").splitlines()[0])
                print("   schema:", (getattr(t, "input_schema", None) or t.inputSchema).get("properties", {}).keys())
            return
        think = True if args.think else False
        questions = [args.question] if args.question else iter(lambda: input("\nask> ").strip(), "exit")
        for q in questions:
            if not q:
                continue
            out = await run_question(session, args.model, q, think=think)
            print(f"\n{out['answer']}\n({out['seconds']} s, {len(out['calls'])} tool call(s))")


if __name__ == "__main__":
    asyncio.run(main())
