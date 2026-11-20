# In-class exercise: Road-trip tools, server and client

**Goal.** Build two tools, test them, share them through an MCP server, and call them from a client. One step at a time. No AI model is used today. Each step has a **checkpoint**: do not move on until it passes.

**The two tools**

| Tool | Inputs | Formula | Returns |
|---|---|---|---|
| `fuel_cost` | `distance_km`, `km_per_litre`, `price_per_litre` | litres = distance / km per litre; cost = litres x price | `{"litres": .., "cost": ..}` |
| `trip_time` | `distance_km`, `speed_kmh`, `break_min` (default 0) | drive hours = distance / speed; total = drive hours + break minutes / 60 | `{"drive_h": .., "total_h": ..}` |

Round every returned number to 2 decimals. Bad input returns `{"error": "..."}` (a speed or km per litre of 0, or a negative distance, price or break).

**Check by hand first (use a calculator)**
- `fuel_cost(450, 15, 1.60)`: 450 / 15 = 30 litres, 30 x 1.60 = **48.00**.
- `trip_time(450, 90, 30)`: 450 / 90 = 5.0 h, plus 30 min = **5.5 h**.

---

## Step 0: Set up (10 min)
```bash
uv sync                  # installs mcp and pytest from pyproject.toml
uv run pytest            # everything fails for now. That is expected.
```

## Step 1: Build the tools (20 min)
Open `tools.py`. We write `fuel_cost` together. Then you write `trip_time` alone.
For each tool: (1) type hints are already there, (2) write a **docstring** the model could use: what it does, when to use it, each argument with units, (3) check bad input, (4) calculate, (5) return numbers, not sentences.

## Step 2: Test with no AI (15 min)
Open `tests/test_tools.py`. The `fuel_cost` tests are written. Write the three `trip_time` tests: replace each `pytest.fail(...)` with `assert` lines from your hand calculations.
```bash
uv run pytest tests/test_tools.py
```
**Checkpoint 1: all 6 tool tests pass.**

## Step 3: Build the server (15 min)
Open `server.py` and follow the TODOs: import the tools, create the server, register both tools, run it. **No `print()` in this file.**

## Step 4: Build the client (15 min)
Open `client.py` and follow the TODOs: start the server, open a session, do the handshake, list the tools, call both tools with the numbers above.
```bash
uv run python client.py
```
You should see both tool names, then `"cost": 48.0` and `"total_h": 5.5`.
```bash
uv run pytest            # the two server/client checkpoint tests
```
**Checkpoint 2: all 8 tests pass.**

## Step 5: Break it on purpose (5 min)
Pick one tool. Delete its docstring and its type hints, save, and run `uv run python client.py` again. What does the client show for that tool now? What would a model see? Put everything back afterwards.

---

## If you get stuck
- `ModuleNotFoundError: tools`: run commands from the project folder with `uv run`.
- Nothing prints from the client: did you fill in every TODO, and is the work inside the `async with` blocks?
- The server hangs or the client errors: look for a `print()` in `server.py`.
- Forgot `await`? Python warns "coroutine ... was never awaited".

## Stretch (if you finish early)
Add a third tool, for example `tip_split(total, people, tip_pct)`. Write its tests first, then register it in the server and call it from the client.
