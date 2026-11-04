"""
compare.py -- run the same questions on several models; score tool choice and arguments.

  uv run python compare.py
  uv run python compare.py --models qwen3:4b qwen2.5-coder:7b llama3.2:3b

Pull the models first (ollama pull <tag>). Writes results.md.
"""
import argparse
import asyncio

from agent import run_question
from client import connect

# (question, expected tool or None, expected arguments)
CASES = [
    ("Simulate a PID controller with Kp=2 and Ki=8 on a plant with time constant 2 s. What is the overshoot?",
     "simulate_pid", {"kp": 2, "ki": 8, "tau": 2}),
    ("Did the oven temperature ever go above 220 degrees C, and when?",
     "read_log_stats", {"column": "temp_c", "threshold": 220}),
    ("I need an RC low-pass filter with a 1 kHz cutoff using a 10 nF capacitor. Which resistor should I use?",
     "design_rc_lowpass", {"cutoff_hz": 1000, "capacitance_nf": 10}),
    ("What was the maximum heater output in the oven log?",
     "read_log_stats", {"column": "heater_pct"}),
    ("Write a one-line joke about transformers.", None, {}),
]


def args_ok(expected: dict, got: dict) -> bool:
    for k, v in expected.items():
        if k not in got:
            return False
        g = got[k]
        if isinstance(v, (int, float)):
            try:
                if abs(float(g) - v) > 0.01 * max(abs(v), 1):
                    return False
            except (TypeError, ValueError):
                return False
        elif str(g).strip().lower() != str(v).lower():
            return False
    return True


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen3:4b", "qwen2.5-coder:7b"])
    models = ap.parse_args().models
    rows = []
    async with connect() as session:
        for m in models:
            for i, (q, exp_tool, exp_args) in enumerate(CASES, 1):
                try:
                    out = await run_question(session, m, q, think=False, verbose=False)
                except Exception as e:
                    rows.append((m, i, "ERROR", "-", "-", str(e)[:60])); print(m, i, "ERROR", e); continue
                first = out["calls"][0] if out["calls"] else None
                tool = first["name"] if first else None
                tool_ok = tool == exp_tool
                a_ok = tool_ok if exp_tool is None else (tool_ok and args_ok(exp_args, first["args"]))
                rows.append((m, i, tool or "(none)", "yes" if tool_ok else "NO", "yes" if a_ok else "NO", f"{out['seconds']} s"))
                print(f"{m:22} Q{i}  tool={tool or '(none)':18} tool_ok={tool_ok}  args_ok={a_ok}  {out['seconds']} s")
    lines = ["| model | Q | tool called | right tool | right args | time |", "|---|---|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |" for r in rows]
    open("results.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\nwrote results.md")


if __name__ == "__main__":
    asyncio.run(main())
