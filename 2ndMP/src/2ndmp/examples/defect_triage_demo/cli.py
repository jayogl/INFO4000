"""
cli.py -- run one report through one mode from the terminal.

  uv run python cli.py --mode agent --report R-001 --backend ollama --model qwen3:4b
  uv run python cli.py --mode workflow --report R-007 --backend rules
  uv run python cli.py --mode multi --report R-004 --backend rules --create
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from core import OllamaBrain, RuleBrain, execute, file_ticket

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
ICON = {"step": "▶", "handoff": "→", "llm": "🧠", "tool_call": "🔧", "tool_result": "📦", "gate": "🚦", "error": "⚠"}


def show(ev):
    print(f"  {ICON.get(ev.kind, '·')} [{ev.t:>5}s] {ev.actor}: {ev.text[:160]}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["agent", "workflow", "multi"], default="workflow")
    ap.add_argument("--report", default="R-001", help="a sample id (R-001..R-007) or free text")
    ap.add_argument("--backend", choices=["ollama", "rules"], default="ollama")
    ap.add_argument("--model", default="qwen3:4b")
    ap.add_argument("--create", action="store_true", help="act as the human: approve and file the ticket")
    a = ap.parse_args()
    samples = {r["id"]: r for r in json.loads((Path(__file__).parent / "data" / "reports.json").read_text(encoding="utf-8"))}
    s = samples.get(a.report)
    text, key = (s["text"], s["expected"]) if s else (a.report, None)
    brain = OllamaBrain(a.model) if a.backend == "ollama" else RuleBrain()
    print(f"Report: {text}\nMode: {a.mode}  Backend: {a.backend}\n")
    out = await execute(a.mode, text, brain, show, key)
    r = out["result"]
    print(f"\nSeverity: {r['severity']}   Team: {r['team']}\nAction: {r['action']}\nSummary: {r['summary']}")
    print("Metrics:", out["metrics"])
    for label, ok in out["audit"]:
        print("  " + {True: "PASS", False: "FAIL", None: "n/a "}[ok], label)
    if a.create and r["ticket"]:
        print("Ticket:", await file_ticket(r["ticket"], s["id"] if s else ""))


if __name__ == "__main__":
    asyncio.run(main())
