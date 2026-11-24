"""server.py -- MCP Server for motor maintenance tools."""

from tools import motor_health_check, motor_life_estimate

try:  # mcp 2.x
  from mcp.server.mcpserver import MCPServer as Server
except ImportError:  # mcp 1.x
  from mcp.server.fastmcp import FastMCP as Server

mcp = Server("motor-maintenance")

# Register tools
mcp.tool()(motor_health_check)
mcp.tool()(motor_life_estimate)

if __name__ == "__main__":
  # Run server over stdio (NEVER print() in this file)
  mcp.run()