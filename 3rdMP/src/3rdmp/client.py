"""client.py -- MCP Client for motor maintenance tools (stdio connection, no LLM)."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).with_name("server.py"))],
)

async def main():
  print("--- Connecting to Motor Maintenance MCP Server ---")
  async with stdio_client(SERVER) as (read, write):
    async with ClientSession(read, write) as session:
      await session.initialize()

      # 1. List tools
      listing = await session.list_tools()
      print("\nAvailable Registered Tools:")
      for tool in listing.tools:
        print(f" - Tool: {tool.name}")

      # 2. Call motor_health_check with scenario numbers
      print("\n1. Executing motor_health_check...")
      health_res = await session.call_tool(
          "motor_health_check",
          {
              "vibration_rms": 3.1,
              "operating_temp_c": 150.0,
              "current_a": 28.0,
              "rated_current_a": 25.0,
              "rated_temp_c": 130.0,
          },
      )
      health_data = json.loads(health_res.content.text)
      print(f"   Result: {json.dumps(health_data, indent=2)}")

      # 3. Call motor_life_estimate
      print("\n2. Executing motor_life_estimate...")
      life_res = await session.call_tool(
          "motor_life_estimate",
          {
              "rated_temp_c": 130.0,
              "operating_temp_c": 150.0,
              "rated_life_h": 20000.0,
          },
      )
      life_data = json.loads(life_res.content.text)
      print(f"   Result: {json.dumps(life_data, indent=2)}")

if __name__ == "__main__":
  asyncio.run(main())