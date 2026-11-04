"""
multi_agent.py -- a MULTI-AGENT system: Orchestrator + Designer + Checker.

  Same MCP server, same tools, same model. What differs per agent:
    * its own system prompt (its role)
    * its own tool list (Designer sees only divider_design, Checker only divider_check)
    * its own conversation (the Checker never sees the Designer's reasoning, only the numbers)

  The ORCHESTRATOR is plain Python. It passes work between the agents and reads the verdict
  from the Checker's TOOL RESULT ("passes": true/false), not from the model's wording.

  uv run python multi_agent.py
  uv run python multi_agent.py --rtol 1        # add +/-1 % resistors: the design needs a third look
"""
from __future__ import annotations

import argparse
import asyncio
import json

from agent import run_question
from client import connect

DESIGNER = (
    "You are the DESIGNER agent in an electronics team. Your only job is to propose resistor values "
    "for a voltage divider. Always use the divider_design tool; never do arithmetic yourself. "
    "Choose r2_ohms yourself (start with 10000). If told a previous attempt failed, choose a clearly "
    "different r2_ohms. Reply with one line: R1 = ..., R2 = ... in ohms."
)
CHECKER = (
    "You are the CHECKER agent. You do not design anything. You verify a proposed voltage divider by "
    "calling the divider_check tool with exactly the values you are given. Then state PASS or FAIL, "
    "the output voltage and the reason, in two sentences."
)


def last_result(calls, tool):
    """The parsed JSON result of the last call to `tool`, or None."""
    for c in reversed(calls):
        if c["name"] == tool:
            try:
                return c["args"], json.loads(c["result"])
            except (ValueError, TypeError):
                return c["args"], None
    return None, None


async def design_divider(session, model, *, vin, vout, load_ohms, tol_pct=3.0, rtol_pct=0.0,
                         max_rounds=3, client=None, verbose=True):
    spec = (f"Spec: input {vin} V, output {vout} V, tolerance +/-{tol_pct} %, "
            f"the output feeds a load of {load_ohms} ohms")
    feedback, history = "", []
    for rnd in range(1, max_rounds + 1):
        if verbose:
            print(f"\n=== Round {rnd} ===")
        # --- Designer: proposes ---
        d = await run_question(session, model, f"{spec}.{feedback} Propose R1 and R2.",
                               system=DESIGNER, tool_names={"divider_design"}, label="[Designer] ",
                               client=client, verbose=verbose)
        _, des = last_result(d["calls"], "divider_design")
        if not des or "error" in des:
            return {"ok": False, "reason": "Designer produced no valid design", "history": history}
        r1, r2 = des["r1_e24_ohms"], des["r2_e24_ohms"]

        # --- Checker: verifies, knows nothing about how the design was chosen ---
        ask = (f"Check this divider: vin={vin}, r1_ohms={r1}, r2_ohms={r2}, target_vout={vout}, "
               f"load_ohms={load_ohms}, tolerance_pct={tol_pct}, resistor_tol_pct={rtol_pct}.")
        c = await run_question(session, model, ask, system=CHECKER, tool_names={"divider_check"},
                               label="[Checker]  ", client=client, verbose=verbose)
        _, chk = last_result(c["calls"], "divider_check")
        if chk is None or "error" in chk:
            return {"ok": False, "reason": "Checker produced no valid check", "history": history}
        history.append({"round": rnd, "r1": r1, "r2": r2, "check": chk, "checker_says": c["answer"]})
        if verbose:
            print(f"  [Orchestrator] verdict from tool result: passes={chk['passes']}")
        if chk["passes"]:
            return {"ok": True, "r1_ohms": r1, "r2_ohms": r2, "check": chk, "rounds": rnd, "history": history}
        feedback = (f" Your previous design R1={r1}, R2={r2} FAILED: output {chk['vout_v']} V "
                    f"(worst-case error {chk['worst_case_error_pct']} %). {chk.get('hint', '')}")
    return {"ok": False, "reason": f"no passing design in {max_rounds} rounds", "history": history}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:4b")
    ap.add_argument("--vin", type=float, default=12)
    ap.add_argument("--vout", type=float, default=3.3)
    ap.add_argument("--load", type=float, default=100000, help="load resistance in ohms")
    ap.add_argument("--tol", type=float, default=3.0, help="allowed output error, percent")
    ap.add_argument("--rtol", type=float, default=0.0, help="resistor tolerance, percent (worst-case check)")
    args = ap.parse_args()
    async with connect() as session:
        r = await design_divider(session, args.model, vin=args.vin, vout=args.vout, load_ohms=args.load,
                                 tol_pct=args.tol, rtol_pct=args.rtol)
    print("\n=== Result ===")
    if r["ok"]:
        c = r["check"]
        print(f"R1 = {r['r1_ohms']:.0f} ohm, R2 = {r['r2_ohms']:.0f} ohm  (after {r['rounds']} round(s))")
        print(f"Vout = {c['vout_v']} V ({c['error_pct']} %), {c['divider_current_ma']} mA, {c['power_mw']} mW")
    else:
        print("No design found:", r["reason"])


if __name__ == "__main__":
    asyncio.run(main())
