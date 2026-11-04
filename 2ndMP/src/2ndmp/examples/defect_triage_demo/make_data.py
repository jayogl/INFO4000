"""make_data.py -- writes data/inspection_log.csv, data/parts.json, data/reports.json (synthetic, seeded).

Story lots are fixed so every sample report has a known right answer; background lots add noise
but never touch a (line, defect) pair that a story depends on.
"""
import csv, json, random
from datetime import date, timedelta
from pathlib import Path

D = Path(__file__).parent / "data"; D.mkdir(exist_ok=True)
AS_OF = date(2026, 10, 14)

# (date, line, lot, units, defect_code, part, defects)
STORY = [
    (AS_OF, 2, "L-2231", 1200, "SOLDER_BRIDGE", "U7", 31),
    (date(2026, 10, 10), 2, "L-2220", 1100, "SOLDER_BRIDGE", "U7", 9),
    (date(2026, 10, 6), 2, "L-2212", 1000, "SOLDER_BRIDGE", "U7", 7),
    (date(2026, 10, 2), 2, "L-2205", 1150, "SOLDER_BRIDGE", "U7", 5),
    (AS_OF, 1, "L-2240", 1000, "COLD_JOINT", "Q3", 6),
    (AS_OF, 3, "L-2244", 1500, "COSMETIC_SCRATCH", "H1", 3),
    (AS_OF, 2, "L-2236", 1000, "MISSING_COMP", "C12", 53),
    (AS_OF, 1, "L-2238", 1200, "TOMBSTONE", "C12", 6),
    (date(2026, 10, 11), 1, "L-2223", 1000, "TOMBSTONE", "C12", 5),
    (date(2026, 10, 1), 1, "L-2201", 1100, "TOMBSTONE", "C12", 4),
    (date(2026, 9, 28), 1, "L-2190", 1000, "TOMBSTONE", "C12", 4),
    (AS_OF, 3, "L-2250", 900, "WRONG_POLARITY", "D9", 2),
]
PAIRS = {(r[1], r[4]) for r in STORY}
NOISE_CODES = ["SOLDER_BRIDGE", "TOMBSTONE", "COLD_JOINT", "MISSING_COMP", "WRONG_POLARITY", "COSMETIC_SCRATCH"]
NOISE_PARTS = {"SOLDER_BRIDGE": "U7", "TOMBSTONE": "C12", "COLD_JOINT": "J2", "MISSING_COMP": "C12",
               "WRONG_POLARITY": "D5", "COSMETIC_SCRATCH": "H1"}

rng = random.Random(7)
rows = list(STORY)
lot_no = 2100
for _ in range(60):
    d = AS_OF - timedelta(days=rng.randint(1, 40)); line = rng.randint(1, 3); code = rng.choice(NOISE_CODES)
    if (line, code) in PAIRS:
        continue
    lot_no += 1
    rows.append((d, line, f"L-{lot_no}", rng.choice([900, 1000, 1100, 1200]), code, NOISE_PARTS[code], rng.randint(1, 4)))
rows.sort(key=lambda r: (r[0], r[2]))
with open(D / "inspection_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date", "line", "lot", "units_inspected", "defect_code", "part", "defects"])
    for r in rows:
        w.writerow([r[0].isoformat(), *r[1:]])

parts = {
    "U7": {"description": "STM32 microcontroller", "safety_critical": False, "owner_team": "SMT Process", "supplier": "Alpha Semi"},
    "Q3": {"description": "Motor-drive MOSFET gate driver", "safety_critical": True, "owner_team": "Power Electronics", "supplier": "Beta Power"},
    "C12": {"description": "100 nF decoupling capacitor", "safety_critical": False, "owner_team": "SMT Process", "supplier": "Gamma Passives"},
    "H1": {"description": "Enclosure housing", "safety_critical": False, "owner_team": "Assembly", "supplier": "Delta Plastics"},
    "J2": {"description": "Field wiring connector", "safety_critical": False, "owner_team": "Assembly", "supplier": "Epsilon Conn"},
    "D5": {"description": "Flyback diode, brake circuit", "safety_critical": True, "owner_team": "Power Electronics", "supplier": "Beta Power"},
}
(D / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")

reports = [
    {"id": "R-001", "title": "Solder bridges on the MCU", "expected": {"severity": "P2", "team": "SMT Process"},
     "text": "Line 2, lot L-2231: AOI flagged solder bridges on U7 (the STM32 MCU) on 14 boards this morning. Operator reworked two by hand. Please advise."},
    {"id": "R-002", "title": "Cold joints on a motor-drive part", "expected": {"severity": "P1", "team": "Power Electronics"},
     "text": "Line 1, lot L-2240. Dull, cold-looking joints on the Q3 gate driver, spotted on 6 boards at final test. These are motor-drive boards."},
    {"id": "R-003", "title": "Cosmetic scratch on housings", "expected": {"severity": "P3", "team": "Assembly"},
     "text": "Line 3, lot L-2244: 3 enclosures (H1) have a cosmetic scratch near the label. Functionally fine."},
    {"id": "R-004", "title": "Missing capacitor, many boards", "expected": {"severity": "P1", "team": "SMT Process"},
     "text": "Line 2, lot L-2236: pick-and-place skipped C12 on 53 boards. The pads are bare."},
    {"id": "R-005", "title": "Tombstones again", "expected": {"severity": "P2", "team": "SMT Process"},
     "text": "Line 1, lot L-2238: tombstoned C12 again, 6 boards with the part standing on one end. Third time this month I think."},
    {"id": "R-006", "title": "Vague report (no lot, no part)", "expected": {"severity": "NEEDS_INFO", "team": "Triage Desk"},
     "text": "Something looks off on a few boards from line 3 today. Maybe soldering? Not sure which lot."},
    {"id": "R-007", "title": "Part not in the database", "expected": {"severity": "P2", "team": "Triage Desk"},
     "text": "Line 3, lot L-2250: D9 installed backwards (wrong polarity) on 2 boards. Caught at ICT."},
]
(D / "reports.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
print("wrote", len(rows), "log rows,", len(parts), "parts,", len(reports), "reports")
