"""tools.py -- your hoist design tools. Plain Python: no MCP, no AI."""
import csv
from pathlib import Path

G = 9.81  # m/s^2


def lift_force(mass_kg: float, accel_ms2: float = 0.0) -> dict:
    """TODO: write the docstring the MODEL will read.

    Say what the tool does, when to use it, and each argument with units.
    """
    # TODO 1: bad input -> return {"error": "..."}
    #         (mass_kg must be > 0; accel_ms2 must be >= 0)
    # TODO 2: weight = mass * G ; tension = mass * (G + accel)   (Newton's 2nd law)
    # TODO 3: return {"weight_n": .., "tension_n": ..} rounded to 2 decimals
    raise NotImplementedError


def select_cable(
    load_n: float,
    safety_factor: float = 5.0,
    catalog_file: str = "cables.csv",
) -> dict:
    """TODO: write the docstring the MODEL will read."""
    # TODO 1: bad input -> return {"error": "..."}
    #         (load_n must be > 0; safety_factor must be >= 1)
    # TODO 2: the file sits next to tools.py:
    #             path = Path(__file__).parent / catalog_file
    #         if it does not exist, return {"error": "..."}
    # TODO 3: design_n = load_n * safety_factor
    # TODO 4: read the CSV with csv.DictReader. breaking_load_kn is in kN:
    #         multiply by 1000 to compare with newtons.
    # TODO 5: keep the cables whose breaking load >= design_n. None left?
    #         return {"error": "no cable in the catalog is strong enough"}
    # TODO 6: pick the one with the SMALLEST breaking load (the CSV is not
    #         sorted!) and return
    #         {"design_load_n", "cable", "diameter_mm", "breaking_load_kn",
    #          "margin_pct"}   margin_pct = (breaking / design - 1) * 100
    #         rounded to 2 decimals
    raise NotImplementedError
