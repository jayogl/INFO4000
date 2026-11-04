# Build an agent, one component at a time

One mechanical-engineering tool (a cantilever beam calculator). Eight small files. Each step adds one idea,
and each file runs on its own, so you can type it live or run it ready-made. No frameworks.

```bash
uv sync
ollama pull qwen3:4b          # any tool-calling model works; MODEL=qwen3:8b uv run python s5_agent_loop.py
uv run python s1_tool.py      # no AI yet
uv run python s5_agent_loop.py
uv run python s5_agent_loop.py "Same beam in aluminum. How much more does it bend?"
uv run pytest                 # no model needed: every step runs against a scripted fake
```

| Step | File | New component | Blackboard word |
|---|---|---|---|
| 0 | `s0_model_alone.py` | nothing: the model alone | **guess** |
| 1 | `s1_tool.py` | the tool, a plain function | **calculate** |
| 2 | `s2_describe.py` | the description the model reads | **menu** |
| 3 | `s3_model_asks.py` | the model asks, nothing runs | **ask** |
| 4 | `s4_run_and_answer.py` | we run it and hand back the result | **run** |
| 5 | `s5_agent_loop.py` | the loop. This is the agent | **repeat** |
| 6 | `s6_guardrails.py` | prompt, step limit, allowed tools, errors back | **limits** |
| 7 | `s7_mcp_server.py` | the same function shared over MCP (bonus) | **share** |

`llm.py` is plumbing (one call to Ollama). Do not teach it.

The beam on the board: steel, L = 300 mm, b = 20 mm, h = 10 mm, P = 100 N at the free end.
**Answer: 2.7 mm deflection, 90 MPa, safety factor 2.78.** Check every step against this.
See `BLACKBOARD.md` for what to draw, say and ask at each step.
