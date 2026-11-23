"""client.py -- YOUR MCP client. No model, no AI. Fill in the TODOs."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(              # provided: how to start the server
    command=sys.executable,
    args=[str(Path(__file__).with_name("server.py"))],
)

async def main():
    # TODO 1: start the server and get its channels:
    async with stdio_client(SERVER) as (read, write):
    # TODO 2: open a session on those channels:
        async with ClientSession(read, write) as session:
    # TODO 3: do the handshake:
            await session.initialize()
    # TODO 4: list the tools:  listing = await session.list_tools()
    listing = await session.list_tools()
    for tool in listing.tools:
        print(f"Tool: {tool.name}")
    # TODO 5: call lift_force for a 500 kg load accelerating at 2.0 m/s^2:
    #             force = await session.call_tool("lift_force", {...})
    #         print force.content[0].text, then get the number out:
    #             tension = json.loads(force.content[0].text)["tension_n"]
    force = await session.call_tool(
        "lift_force", {"mass_kg": 500, "accel_ms2": 2.0}
    )
    print(force.content.text)
    tension = json.loads(force.content.text)["tension_n"]
    # TODO 6: THE DESIGN STEP: call select_cable with load_n = tension and safety_factor 5.0, and print the result's content[0].text
    cable = await session.call_tool(
        "select_cable", {"load_n": tension, "safety_factor": 5.0}
    )
    print(cable.content.text)
    pass

if __name__ == "__main__":
    asyncio.run(main())