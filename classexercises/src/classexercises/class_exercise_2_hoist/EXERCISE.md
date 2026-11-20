# In-class exercise 2: Hoist design (tools that read a CSV)

**Goal.** Design a hoist: work out the force in the cable (Newton's second law), then choose a cable from a catalog stored in a CSV file. Two tools, tested, shared through an MCP server, called from a client. One step at a time. No AI model today. Each step has a **checkpoint**: do not move on until it passes.

**The two tools**

| Tool | Inputs | What it does | Returns |
|---|---|---|---|
| `lift_force` | `mass_kg`, `accel_ms2` (default 0) | weight = m x g, with g = 9.81 m/s^2. Tension = m x (g + a). The cable must also accelerate the load upward. | `{"weight_n": .., "tension_n": ..}` |
| `select_cable` | `load_n`, `safety_factor` (default 5), `catalog_file` (default `cables.csv`) | design load = load x safety factor. Read `cables.csv`. Choose the cable with the **smallest breaking load that is still at least the design load**. | `{"design_load_n", "cable", "diameter_mm", "breaking_load_kn", "margin_pct"}` |

`margin_pct = (breaking load / design load - 1) x 100`. Round returned numbers to 2 decimals. Bad input returns `{"error": "..."}`: a zero or negative mass, a negative acceleration, a negative load, a safety factor below 1, a missing catalog file, or a load so large that no cable is strong enough.

**The catalog** `cables.csv` (breaking load is in **kN**, the tools work in **N**): open it and look. The rows are **not** in order.

**Check by hand first (use a calculator)**
- `lift_force(500, 2)`: weight = 500 x 9.81 = 4905 N. Tension = 500 x (9.81 + 2) = **5905 N**.
- `select_cable(5905, 5)`: design load = 5905 x 5 = 29 525 N = 29.525 kN. Rope-6 (18 kN) is too weak, **Rope-8 (32 kN)** holds. Margin = (32 / 29.525 - 1) x 100 = **8.38 %**.
- A second case: `lift_force(200, 1)` gives 2162 N. Design load 10 810 N. Which cable?

---

## Step 0: Set up (10 min)
```bash
uv sync                  # installs mcp and pytest from pyproject.toml
uv run pytest            # everything fails for now. That is expected.
```
Open `cables.csv` in your editor or spreadsheet and read it.

## Step 1: Build the tools (25 min)
Open `tools.py`. We write `lift_force` together. Then you write `select_cable` alone.
For each tool: (1) type hints are already there, (2) write a **docstring** the model could use: what it does, when to use it, each argument with units, (3) check bad input, (4) calculate, (5) return numbers, not sentences.
Reading the file: `csv.DictReader` gives each row as a dictionary, but every value is **text**. Convert with `float(...)`.

## Step 2: Test with no AI (15 min)
Open `tests/test_tools.py`. The `lift_force` tests are written. Write the three `select_cable` tests: replace each `pytest.fail(...)` with `assert` lines from your hand calculations.
```bash
uv run pytest tests/test_tools.py
```
**Checkpoint 1: all 6 tool tests pass.**

## Step 3: Build the server (15 min)
Open `server.py` and follow the TODOs: import the tools, create the server, register both tools, run it. **No `print()` in this file.**

## Step 4: Build the client (20 min)
Open `client.py` and follow the TODOs: start the server, open a session, do the handshake, list the tools, call `lift_force`, then use its answer to call `select_cable`. That chain **is** the design.
```bash
uv run python client.py
```
You should see both tool names, then `"tension_n": 5905.0` and `"cable": "Rope-8"`.
```bash
uv run pytest            # the two server/client checkpoint tests
```
**Checkpoint 2: all 8 tests pass.**

## Step 5: Change the data, not the code (5 min)
Add a row to `cables.csv`, for example `Rope-7,7,30,0.23`. Run the client again **without touching any Python**. Which cable do you get now, and what is its margin? Why? Remove the row afterwards.

## Step 6: Break it on purpose (5 min)
Pick one tool. Delete its docstring and its type hints, save, and run `uv run python client.py` again. What does the client show for that tool now? What would a model see? Put everything back afterwards.

---

## If you get stuck
- `ModuleNotFoundError: tools`: run commands from the project folder with `uv run`.
- `TypeError` comparing text and numbers: you forgot `float(...)` on a CSV value.
- The wrong cable is returned: did you pick the first strong enough row, instead of the smallest strong enough one?
- Nothing prints from the client: did you fill in every TODO, and is the work inside the `async with` blocks?
- The server hangs or the client errors: look for a `print()` in `server.py`.

## Stretch (if you finish early)
Add the cable's own weight to the load: `mass_kg_per_m` x the lift height. How would you change the tools? Write the test first.
