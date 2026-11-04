"""
tools.py -- the TOOLS for defect triage. Plain Python, no AI and no MCP in this file.

Read-only tools (safe for a model to call): lookup_part, defect_stats, find_similar, severity_policy.
Write tool (a side effect): create_ticket. In this demo NO model gets create_ticket;
the app calls it only after a human clicks Approve.
"""
from __future__ import annotations

import json
import os
from datetime import timedelta, date
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("TRIAGE_DATA", Path(__file__).parent / "data"))
TICKETS = Path(os.environ.get("TRIAGE_TICKETS", DATA_DIR / "tickets.jsonl"))
AS_OF = date(2026, 10, 14)          # "today" in the synthetic data, so results never change
DEFECT_CODES = ["SOLDER_BRIDGE", "TOMBSTONE", "MISSING_COMP", "COLD_JOINT", "WRONG_POLARITY", "COSMETIC_SCRATCH"]


def _log() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "inspection_log.csv", parse_dates=["date"])


def lookup_part(part_id: str) -> dict:
    """Look up a part by its reference designator (for example U7 or Q3). Returns what it is,
    whether it is safety critical, and which team owns it. Returns an error if the part is
    not in the database.

    Args:
        part_id: reference designator, for example U7
    """
    parts = json.loads((DATA_DIR / "parts.json").read_text(encoding="utf-8"))
    key = part_id.strip().upper()
    if key not in parts:
        return {"error": f"part '{part_id}' is not in the parts database"}
    return {"part_id": key, **parts[key]}


def defect_stats(lot_id: str, defect_code: str | None = None) -> dict:
    """Defect statistics for one production lot from the inspection log. Give the defect_code
    to get the defect rate for that defect; without it the rate is for all defects in the lot.

    Args:
        lot_id: lot identifier, for example L-2231
        defect_code: optional, one of SOLDER_BRIDGE, TOMBSTONE, MISSING_COMP, COLD_JOINT, WRONG_POLARITY, COSMETIC_SCRATCH
    """
    sub = _log()
    sub = sub[sub["lot"] == lot_id.strip().upper()]
    if sub.empty:
        return {"error": f"lot '{lot_id}' is not in the inspection log"}
    units = int(sub["units_inspected"].max())
    by_code = {k: int(v) for k, v in sub.groupby("defect_code")["defects"].sum().items()}
    n = by_code.get(defect_code, 0) if defect_code else sum(by_code.values())
    return {"lot": lot_id.strip().upper(), "line": int(sub["line"].iloc[0]), "units_inspected": units,
            "defects_counted": n, "defect_rate_pct": round(n / units * 100, 2), "by_code": by_code}


def find_similar(defect_code: str, line: int, exclude_lot: str | None = None, days: int = 30) -> dict:
    """Find earlier lots on the same production line with the same defect in the last N days.
    Use this to see whether a defect is a one-off or keeps coming back (recurring).

    Args:
        defect_code: one of SOLDER_BRIDGE, TOMBSTONE, MISSING_COMP, COLD_JOINT, WRONG_POLARITY, COSMETIC_SCRATCH
        line: production line number
        exclude_lot: the lot being triaged, so it is not counted against itself
        days: look-back window in days (default 30)
    """
    df = _log()
    start = pd.Timestamp(AS_OF - timedelta(days=days))
    df = df[(df["defect_code"] == defect_code) & (df["line"] == int(line)) & (df["date"] >= start)
            & (df["date"] <= pd.Timestamp(AS_OF))]
    if exclude_lot:
        df = df[df["lot"] != exclude_lot.strip().upper()]
    df = df.sort_values("date", ascending=False)
    lots = [{"lot": r.lot, "date": r.date.date().isoformat(), "defects": int(r.defects)} for r in df.itertuples()]
    return {"previous_lots": len(lots), "lots": lots[:5], "recurring": len(lots) >= 2, "window_days": days}


def severity_policy(defect_code: str, defect_rate_pct: float, safety_critical: bool, recurring: bool) -> dict:
    """Apply the factory severity policy and return P1, P2 or P3 with the recommended action.
    Always use this tool to decide severity; never choose it yourself.

    Args:
        defect_code: the defect type
        defect_rate_pct: defect rate for this lot in percent
        safety_critical: true if the part is safety critical (treat an unknown part as true)
        recurring: true if the same defect appeared on the same line in 2 or more earlier lots
    """
    if defect_rate_pct >= 5:
        sev, rule = "P1", "defect rate is 5% or more"
    elif safety_critical and defect_rate_pct >= 0.5:
        sev, rule = "P1", "safety-critical part and rate is 0.5% or more"
    elif defect_rate_pct >= 1:
        sev, rule = "P2", "defect rate is 1% or more"
    elif recurring:
        sev, rule = "P2", "the defect is recurring on this line"
    elif safety_critical:
        sev, rule = "P2", "safety-critical part"
    else:
        sev, rule = "P3", "low rate, not recurring, not safety critical"
    action = {"P1": "HOLD the lot and stop the line", "P2": "Quarantine the lot for inspection",
              "P3": "Log it and monitor"}[sev]
    return {"severity": sev, "recommended_action": action, "rule": rule, "requires_approval": sev in ("P1", "P2")}


def create_ticket(team: str, severity: str, summary: str, report_id: str = "") -> dict:
    """Create a defect ticket for a team. This WRITES a record: it must only be called after a human approved.

    Args:
        team: team that will own the ticket
        severity: P1, P2 or P3
        summary: short description of the problem and the recommended action
        report_id: optional id of the source report
    """
    TICKETS.parent.mkdir(parents=True, exist_ok=True)
    n = sum(1 for _ in TICKETS.open(encoding="utf-8")) if TICKETS.exists() else 0
    t = {"ticket_id": f"DEF-{1001 + n}", "team": team, "severity": severity, "summary": summary, "report_id": report_id}
    with TICKETS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(t) + "\n")
    return t
