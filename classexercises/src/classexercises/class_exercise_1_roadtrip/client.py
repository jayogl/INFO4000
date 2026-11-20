"""client.py -- YOUR MCP client. No model, no AI. Fill in the TODOs."""
import asyncio
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
    #             async with stdio_client(SERVER) as (read, write):
    # TODO 2: open a session on those channels:
    #             async with ClientSession(read, write) as session:
    # TODO 3: do the handshake:
    #             await session.initialize()
    # TODO 4: list the tools:  listing = await session.list_tools()
    #         and print each tool's name (listing.tools)
    # TODO 5: call fuel_cost with 450 km, 15 km per litre, 1.60 per litre:
    #             result = await session.call_tool("fuel_cost", {...})
    #         and print result.content[0].text
    # TODO 6: do the same for trip_time: 450 km, 90 km/h, 30 minute break
    pass


if __name__ == "__main__":
    asyncio.run(main())
