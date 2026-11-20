"""test_server_client.py -- checkpoints for the server and the client."""
import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def list_tools_from_server():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(
            command=sys.executable, args=[str(ROOT / "server.py")])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return (await session.list_tools()).tools

    return asyncio.run(go())


def test_checkpoint_server_lists_both_tools():
    tools = list_tools_from_server()
    assert sorted(t.name for t in tools) == ["fuel_cost", "trip_time"]


def test_checkpoint_client_prints_both_results():
    run = subprocess.run([sys.executable, str(ROOT / "client.py")],
                         capture_output=True, text=True, timeout=60, cwd=ROOT)
    assert run.returncode == 0, run.stderr
    flat = run.stdout.replace(" ", "").replace("\n", "")
    assert '"cost":48.0' in flat and '"total_h":5.5' in flat
