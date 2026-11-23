"""server.py -- YOUR MCP server. Fill in the TODOs."""

# TODO 1: import fuel_cost and trip_time from tools
from tools import fuel_cost, trip_time

try:                                         # provided: mcp 2.x ...
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:                          # ... or mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

# TODO 2: create the server, named "roadtrip":
mcp = Server("roadtrip")
# TODO 3: register both tools, one line each:
mcp.tool()(fuel_cost)
mcp.tool()(trip_time)
# TODO 4: run the server when this file is executed directly:
if __name__ == "__main__":
  mcp.run()
# Reminder: NEVER print() in a server file. Output on stdout breaks it.