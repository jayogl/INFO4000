"""STEP 7 (bonus) -- Share the SAME function with any AI app by wrapping it in an MCP server.

Nothing about the tool changes. Try it without any model:   uv run mcp dev s7_mcp_server.py
Then any MCP client (LM Studio, Claude Desktop, our own code) can list and call cantilever_beam.
Never print() in a stdio server: stdout is the protocol channel.
"""
from s1_tool import cantilever_beam

try:                                           # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                            # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("beam-lab")
mcp.tool()(cantilever_beam)                    # the type hints and the docstring become the description

if __name__ == "__main__":
    mcp.run()
