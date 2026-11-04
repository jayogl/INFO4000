"""
server.py -- the MCP SERVER.

It does only three things:
  1. register the tools from tools.py          (mcp.tool()(function))
  2. answer "what tools do you have?"          (tools/list -> names, descriptions, schemas)
  3. run a tool when asked                     (tools/call)

Transport is stdio: the client starts this file as a subprocess and talks over
stdin/stdout. Never print() in this file -- stdout is the protocol channel.

Inspect it without any AI:   uv run mcp dev server.py
"""
import tools

try:                                           # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                            # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("control-lab")

mcp.tool()(tools.simulate_pid)
mcp.tool()(tools.design_rc_lowpass)
mcp.tool()(tools.read_log_stats)
mcp.tool()(tools.divider_design)
mcp.tool()(tools.divider_check)

if __name__ == "__main__":
    mcp.run()          # default transport: stdio
