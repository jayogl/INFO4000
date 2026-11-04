# Running the control-lab MCP server in LM Studio

LM Studio is the MCP client here (the role `client.py` plays in the terminal demo).
Same server, same tools, no code changes.

## 1. Setup (once)
1. Install LM Studio (0.3.17 or newer) from lmstudio.ai.
2. Download a tool-capable model: search `qwen3 4b` in the Discover tab (look for the hammer/tool icon). Load it.
3. Make sure `uv` is on your PATH (`uv --version` in a fresh terminal). On Windows, restart LM Studio after installing uv.
4. Run `uv sync` once inside the project folder so the first tool call is not slow.

## 2. Register the server
In LM Studio: right sidebar > **Program** tab > **Install > Edit mcp.json**.
Paste `lmstudio/mcp.mac.json` or `lmstudio/mcp.windows.json`, replacing the path with the
absolute path of this folder. Use forward slashes on Windows. Save.

The `control-lab` server should appear in the Program tab with 3 tools:
`simulate_pid`, `design_rc_lowpass`, `read_log_stats`. Toggle it on.

## 3. Try it
- "What is the overshoot of a PI controller with Kp=2, Ki=8 on a plant with tau=2 s?" (expect 32.37%)
- "Design an RC low-pass filter for 1 kHz with a 10 nF capacitor." (expect about 16 kOhm)
- "Did the oven exceed 220 C, and for how long?"
- "Find PI gains for tau=2 s, overshoot under 10%, settling under 8 s." (multi-call tuning)

Each tool call shows a confirmation dialog with the arguments. You can edit them before
approving. Teach with that dialog: it is the model's request, visible before it runs.

## 4. Differences from client.py
- No `[model asks]` / `[server returns]` printout, but the dialog and the collapsed tool
  block in the chat show the same information.
- The system prompt is LM Studio's, not ours. Set it in the chat's System Prompt box;
  copy `SYSTEM` from `agent.py` to get multi-step tuning behaviour.
- `think` mode is controlled in LM Studio's model settings.

## 5. Troubleshooting
- Server missing or red: open a terminal and run the same command by hand
  (`uv run --directory <path> python server.py`). It should wait silently. Ctrl+C to stop.
- "uv not found": LM Studio did not inherit your PATH. Use the full path to uv
  (`which uv` on Mac, `where uv` on Windows) as the `command`.
- Model ignores the tools: confirm the model shows the tool-use icon and the server is toggled on.
- On Windows, a path with spaces is fine inside the JSON string; backslashes must be doubled
  or replaced with forward slashes.
