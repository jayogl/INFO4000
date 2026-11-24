"""multi_agent.py -- Multi-Agent Tandem Workflow for Motor Maintenance."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama

MODEL = "qwen3:4b"
SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).with_name("server.py"))],
)

INSPECTOR_ROLE = {
    "name": "Inspector Agent",
    "tools": ["motor_health_check"],
    "system": (
        "You are an Industrial Motor Inspection Specialist. Your ONLY job is"
        " to check operational health, vibration zone, load percentage, and"
        " thermal margin using `motor_health_check`. Always invoke"
        " `motor_health_check` with the provided telemetry. State the health"
        " status, vibration zone, and reasons clearly. Additionally at the end"
        " of your response, always output a single line: 'STATUS: <OK|WATCH|ACT>'"
    ),
}

ESTIMATOR_ROLE = {
    "name": "Estimator Agent",
    "tools": ["motor_life_estimate"],
    "system": (
        "You are a Motor Insulation Life Estimator. Your ONLY job is to compute"
        " remaining insulation life based on operating temperature using"
        " `motor_life_estimate`. Always invoke `motor_life_estimate` with the"
        " rated and operating temperatures. State the remaining insulation"
        " hours, estimated years, and life ratio clearly."
    ),
}

DEFAULT_QUESTION = (
    "What is the health status and remaining insulation life of a motor"
    " operating at 150°C (rated 130°C), drawing 28 A (rated 25 A), with 3.1 mm/s"
    " RMS vibration?"
)


def to_ollama(tool):
  schema = getattr(tool, "input_schema", None) or tool.inputSchema
  return {
      "type": "function",
      "function": {
          "name": tool.name,
          "description": tool.description or "",
          "parameters": schema,
      },
  }


async def run_agent(session, role_config, task_prompt, available_tools):
  """Run a single role agent with a restricted tool set."""
  role_tools = [
      t
      for t in available_tools
      if t["function"]["name"] in role_config["tools"]
  ]
  messages = [
      {"role": "system", "content": role_config["system"]},
      {"role": "user", "content": task_prompt},
  ]

  print(f"\n>>> [{role_config['name']}] Started Task...")

  for step in range(1, 5):
    reply = await ollama.AsyncClient().chat(
        model=MODEL, messages=messages, tools=role_tools
    )
    msg = reply.message
    messages.append(msg)

    tool_calls = getattr(msg, "tool_calls", None) or []

    if not tool_calls and msg.content:
      content_str = msg.content.strip()
      if content_str.startswith("{") and content_str.endswith("}"):
        try:
          parsed = json.loads(content_str)
          call_name = parsed.get("name") or parsed.get("tool")
          call_args = parsed.get("arguments") or parsed.get("args") or {}
          if call_name in role_config["tools"]:
            tool_calls = [
                {"function": {"name": call_name, "arguments": call_args}}
            ]
        except Exception:
          pass

    if not tool_calls:
      print(f">>> [{role_config['name']}] Complete Output:\n{msg.content}\n")
      return msg.content

    for call in tool_calls:
      if hasattr(call, "function"):
        fn_name = call.function.name
        fn_args = dict(call.function.arguments)
      else:
        fn_name = call["function"]["name"]
        fn_args = dict(call["function"]["arguments"])

      print(f"    Tool Call -> {fn_name}({fn_args})")
      out = await session.call_tool(fn_name, fn_args)
      res_text = out.content[0].text
      print(f"    Tool Result -> {res_text}")
      messages.append(
          {"role": "tool", "tool_name": fn_name, "content": res_text}
      )

  return "Agent step limit reached."


async def main():
  question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION

  print("==================================================")
  print("      MULTI-AGENT TANDEM MAINTENANCE WORKFLOW     ")
  print("==================================================")
  print(f"Input Task: {question}\n")

  async with stdio_client(SERVER) as (read, write):
    async with ClientSession(read, write) as session:
      await session.initialize()

      listing = await session.list_tools()
      all_tools_schema = [to_ollama(t) for t in listing.tools]

      # -------------------------------------------------------------
      # Stage 1: Inspector Agent (motor_health_check ONLY)
      # -------------------------------------------------------------
      inspector_output = await run_agent(
          session, INSPECTOR_ROLE, question, all_tools_schema
      )

      # -------------------------------------------------------------
      # Stage 2: Plain Python Orchestrator Gate
      # -------------------------------------------------------------
      print("--- [Orchestrator Gate] Analyzing Inspector Findings ---")
      if "STATUS: OK" in inspector_output:
        print("Gate Decision: Motor status is OK. Skipping Estimator Agent.")
        print(
            "Motor is operating within normal parameters. No life degradation"
            " analysis required."
        )
        return

      print(
          "Gate Decision: Motor status is NOT OK (WATCH/ACT detected)."
          " Triggering Estimator Agent in tandem."
      )

      # -------------------------------------------------------------
      # Stage 3: Estimator Agent (motor_life_estimate ONLY)
      # -------------------------------------------------------------
      estimator_task = (
          f"Original Request: {question}\n"
          f"Inspector Findings: {inspector_output}\n"
          "Calculate the remaining insulation life and life degradation ratio"
          " for this operating temperature."
      )

      estimator_output = await run_agent(
          session, ESTIMATOR_ROLE, estimator_task, all_tools_schema
      )

      # -------------------------------------------------------------
      # Stage 4: Final Unified Summary Report
      # -------------------------------------------------------------
      print("==================================================")
      print("         FINAL TANDEM AGENT SUMMARY REPORT        ")
      print("==================================================")
      print(f"1. Health Inspection Findings:\n{inspector_output}\n")
      print(f"2. Insulation Life Estimation:\n{estimator_output}")


if __name__ == "__main__":
  asyncio.run(main())