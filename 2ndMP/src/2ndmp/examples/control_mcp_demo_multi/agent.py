"""
agent.py -- the AGENT LOOP (what Claude Code / OpenCode do for their models).

  list tools from the MCP server -> hand their schemas to the model ->
  if the model asks for a tool: run it on the server, give the result back -> repeat.
"""
from __future__ import annotations

import re
import time

import ollama

SYSTEM = (
    "You are a control-systems and electronics lab assistant. "
    "Use the provided tools for any calculation or data lookup; never do arithmetic yourself. "
    "You may call tools several times in a row: to reach a goal, try values, read each result, and adjust. "
    "Do not give up until you have tried. Only answer without a tool when the question has nothing to do with the tools."
)


def mcp_tool_to_ollama(tool) -> dict:
    """MCP tool -> Ollama tool format. It is just a rename of the same three fields."""
    return {"type": "function",
            "function": {"name": tool.name,
                         "description": tool.description or "",
                         "parameters": getattr(tool, "input_schema", None) or tool.inputSchema}}


def strip_thinking(text: str) -> str:
    """Remove leaked reasoning. Qwen3 sometimes puts its thinking in the reply even with think=False:
    either a full <think>...</think> block, or reasoning followed by a lone </think>."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    if "</think>" in text:                       # no opening tag: everything before it is reasoning
        text = text.split("</think>")[-1]
    return text.replace("<think>", "").strip()


def result_text(result) -> str:
    return "\n".join(getattr(c, "text", str(c)) for c in result.content)


async def _chat(client, model, messages, tools, think):
    kw = dict(model=model, messages=messages, tools=tools, options={"temperature": 0, "num_ctx": 8192})
    if think is not None:
        try:
            return await client.chat(**kw, think=think)
        except (TypeError, ollama.ResponseError) as e:
            if isinstance(e, ollama.ResponseError) and "think" not in str(e).lower():
                raise                      # a real error, not "model has no thinking mode"
    return await client.chat(**kw)


async def run_question(session, model, question, *, client=None, think=False,
                       max_steps=8, verbose=True, system=None, tool_names=None, label="") -> dict:
    """Ask one question. Returns {"answer", "calls", "seconds"}.
    system:     this agent's instructions (default: the lab assistant prompt)
    tool_names: if given, the agent only sees these tools (one MCP server, different roles)
    label:      prefix for the printed trace, e.g. "[Designer]" """
    client = client or ollama.AsyncClient()
    tools = [mcp_tool_to_ollama(t) for t in (await session.list_tools()).tools
             if tool_names is None or t.name in tool_names]
    messages = [{"role": "system", "content": system or SYSTEM}, {"role": "user", "content": question}]
    calls, t0 = [], time.time()

    for _ in range(max_steps):
        resp = await _chat(client, model, messages, tools, think)
        msg = resp.message
        messages.append(msg)
        if not msg.tool_calls:
            answer = strip_thinking(msg.content or "")
            return {"answer": answer, "calls": calls, "seconds": round(time.time() - t0, 1)}
        for tc in msg.tool_calls:
            name, args = tc.function.name, dict(tc.function.arguments)
            if verbose:
                print(f"  {label}[model asks] {name}({args})")
            try:
                text = result_text(await session.call_tool(name, args))
            except Exception as e:           # bad tool name / bad arguments: tell the model
                text = f"Tool error: {e}"
            if verbose:
                print(f"  {label}[server returns] {text}")
            calls.append({"name": name, "args": args, "result": text})
            messages.append({"role": "tool", "tool_name": name, "content": text})

    return {"answer": "(stopped: too many tool steps)", "calls": calls,
            "seconds": round(time.time() - t0, 1)}
