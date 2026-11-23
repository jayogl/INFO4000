"""server.py -- YOUR MCP server. Fill in the TODOs."""

# TODO 1: import lift_force and select_cable from tools
from tools import lift_force, select_cable

try:                                         # provided: mcp 2.x ...
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:                          # ... or mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

# TODO 2: create the server, named "hoist":
mcp = Server("hoist")
# TODO 3: register both tools, one line each:
mcp.tool()(lift_force)
mcp.tool()(select_cable)
# TODO 4: run the server when this file is executed directly:
if __name__ == "__main__":
    mcp.run()
#
# Reminder: NEVER print() in a server file. Output on stdout breaks it.
