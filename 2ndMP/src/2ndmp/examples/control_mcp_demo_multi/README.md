# Control MCP demo — tools → MCP server → local model

Teaches two ideas with one small project:
1. **What a tool is** and how it is built — `tools.py` (plain Python functions, no AI).
2. **What an MCP server is** and how it exposes tools — `server.py`, used by `client.py`/`agent.py`.

```
 qwen3:4b (Ollama)  <->  client.py + agent.py  <->  server.py (MCP, stdio)  ->  tools.py
      the model           the agent loop             lists + runs tools        the functions
```

## Setup (macOS and Windows)
Install once: [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/download), and (optional, for the
Inspector in Lesson 2) [Node.js](https://nodejs.org/).

All commands below are identical on macOS (Terminal) and Windows (PowerShell). Run them from inside this folder.
```
ollama pull qwen3:4b              # ~2.5 GB
ollama pull qwen2.5-coder:7b      # ~4.7 GB, for the comparison

uv sync                           # creates .venv here from pyproject.toml
uv run pytest -q                  # 7 tests, no Ollama needed
```
Or use your existing uv project instead of `uv sync`:
`uv add "mcp[cli]" numpy scipy pandas "ollama>=0.5.1"` and `uv add --dev pytest`.

Make sure Ollama is running (menu-bar app on macOS, tray icon on Windows) before Lessons 3-4.

**Models on an external drive** (optional):
- macOS: `launchctl setenv OLLAMA_MODELS "/Volumes/YourSSD/ollama/models"`, then quit and reopen Ollama.
- Windows (PowerShell): `setx OLLAMA_MODELS "E:\ollama\models"`, then quit Ollama from the tray and reopen it.
The drive must be connected before Ollama starts.

**mcp versions:** works with both mcp 1.x (`FastMCP`) and mcp 2.x (`MCPServer`, renamed); `server.py` picks whichever
is installed, and the tests pass on 1.30 and 2.3. `uv run mcp dev server.py` (Inspector) was not exercised on 2.x here.

**Platform notes:** all paths use `pathlib`, the server is launched with the same Python (`sys.executable`), and
console output is forced to UTF-8, so nothing is OS-specific. The code was reviewed for Windows and tested on Linux;
if something differs on your Windows machine, start with the Troubleshooting notes at the bottom.

## Lesson 1 — what is a tool? (`tools.py`)
Open `tools.py`. Each function has a clear verb name, typed arguments, a docstring written *for the model*,
and returns a dict. Call them directly — no AI (`try_tools.py` calls all three):
```bash
uv run python try_tools.py
```
| tool | what it does |
|---|---|
| `simulate_pid(kp, ki, tau, kd=0, plant_gain=1)` | closed-loop step response of PID + first-order plant → overshoot, rise, settle |
| `design_rc_lowpass(cutoff_hz, capacitance_nf)` | ideal R, nearest E24 resistor, actual cutoff |
| `read_log_stats(column, threshold=None)` | stats and threshold crossings from `data/oven.csv` (there is a spike at 1200–1260 s) |

## Lesson 2 — what is an MCP server? (`server.py`)
`server.py` is ~10 lines: it registers the three functions and calls `mcp.run()` (stdio).
Look at it with **no AI** in the MCP Inspector (needs Node):
```bash
uv run mcp dev server.py
```
Open the Tools tab: see the names, descriptions and JSON schemas — exactly what the model will be shown.
Run a tool by hand there.

## Lesson 3 — connect the model (`client.py`, `agent.py`)
```bash
uv run python client.py --list-tools
uv run python client.py "Simulate a PID controller with Kp=2 and Ki=8 on a plant with time constant 2 s. What is the overshoot?"
uv run python client.py "Did the oven temperature ever go above 220 C, and when?"
uv run python client.py "I need a 1 kHz RC low-pass using a 10 nF capacitor. Which resistor?"
uv run python client.py            # interactive; type exit to quit
```
You will see `[model asks] tool(args)` and `[server returns] ...` — that is the whole loop.
Expected for the PID question: overshoot ≈ 32 %.

## Lesson 4 — compare models
```bash
uv run python compare.py --models qwen3:4b qwen2.5-coder:7b
```
Scores right tool / right arguments on 5 questions (the last one needs *no* tool). Writes `results.md`.

## Exercises
- Add a tool (e.g. `ziegler_nichols(ku, tu)`), register it in `server.py`; the model uses it with no other change.
- Make a docstring vague on purpose; watch the wrong tool get chosen.
- Ask it to *write* a setpoint — there is no such tool, by design (read-only / advisory).
- Compare `think=False` vs `--think`.

## Notes
- Never `print()` in `server.py` (stdout is the protocol channel).
- If a 4B model fumbles: fewer tools, shorter descriptions, `temperature` is already 0, one tool call per question.
- Tests cover tools, a real server round trip over stdio, and the agent loop with a fake model.
  The live Ollama path is exercised only when you run `client.py` / `compare.py` on your Mac.

## Troubleshooting
- **`ollama` connection error:** Ollama is not running; start it, or run `ollama list` to check.
- **Model not found:** `ollama pull <tag>` with the exact tag (e.g. `qwen3:4b`).
- **Windows: odd characters in output:** already handled; if you still see them, run `chcp 65001` first.
- **Windows: `uv`/`python` not found:** reopen PowerShell after installing uv; use `uv run python ...`, not bare `python`.
- **Windows firewall prompt:** Ollama listens on localhost only; allow it for private networks if asked.
- **Inspector will not start:** install Node.js; `npx` must be on PATH.
- **Tool calls look wrong:** print the `[model asks]` line first; see Notes below.

## Challenge questions (the model has to do more than fill in arguments)
```
uv run python client.py "Find PI gains for a plant with tau = 2 s that keep overshoot under 10%."
uv run python client.py "The oven spiked around 1200 s. Did the heater output react?"
uv run python client.py "Is Kp=0 and Ki=-3 on a plant with tau 1 a good design? Explain."
```
The first needs several `simulate_pid` calls (try, read, adjust); for example Kp=2, Ki=2 gives ~7.9% overshoot, so a
solution exists. A 4B model may stop early or give up -- that is the lesson about where small models stop being agents.
How well a model uses tools depends heavily on the tool *descriptions* (see the docstring of `simulate_pid`) and on the
system prompt in `agent.py`.

## Lesson 5: multi-agent (voltage divider)

Two new tools, `divider_design` and `divider_check`, and `multi_agent.py`:

    uv run python multi_agent.py                 # 12 V -> 3.3 V +/-3 %, ADC load 100 kOhm
    uv run python multi_agent.py --rtol 1        # +/-1 % resistors: worst-case check

* **Orchestrator** (plain Python) passes work between the agents and reads the verdict from the
  Checker's *tool result* (`"passes": true/false`), not from the model's wording.
* **Designer** sees only `divider_design`. **Checker** sees only `divider_check`. Each has its own
  system prompt and its own conversation: the Checker never sees how the Designer chose the values.
* Expected run: round 1 proposes 27 kOhm / 10 kOhm and fails (loaded output 3.02 V, -8.4 %);
  round 2 uses a smaller R2, e.g. 2.7 kOhm / 1 kOhm, and passes (3.22 V, -2.43 %, 3.24 mA, 39 mW).
  With `--rtol 1` that design fails the worst case (-3.85 %), so the team has to keep going.
* A 4B model may pick different R2 values than the slides show; the orchestrator logic is the same.
  The scripted test (`test_multi_agent_two_rounds_with_fake_model`) pins the expected flow.
