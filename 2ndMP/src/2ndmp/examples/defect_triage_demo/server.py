"""server.py -- the MCP SERVER. Registers the plain functions in tools.py as MCP tools."""
import tools
try:                                           # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                            # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("defect-triage")
for fn in (tools.lookup_part, tools.defect_stats, tools.find_similar, tools.severity_policy, tools.create_ticket):
    mcp.tool()(fn)

if __name__ == "__main__":
    mcp.run()
