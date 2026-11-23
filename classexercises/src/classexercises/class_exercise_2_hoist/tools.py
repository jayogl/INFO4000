"""tools.py -- your hoist design tools. Plain Python: no MCP, no AI."""
import csv
from pathlib import Path

G = 9.81  # m/s^2

def lift_force(mass_kg: float, accel_ms2: float = 0.0) -> dict:
    """Calculate load weight and required cable tension for lifting a mass. Use when determining static and dynamic tension required for a hoist load.
    Args:
      mass_kg: Mass of the load in kilograms (> 0).
      accel_ms2: Upward acceleration in m/s^2 (default 0.0, >= 0).
    Returns:
      dict with 'weight_n' and 'tension_n', or 'error' if input is invalid."""
    # TODO 1: bad input -> return {"error": "..."} (mass_kg must be > 0; accel_ms2 must be >= 0)
    if mass_kg <= 0:
        return {"error": "mass_kg must be greater than 0"}
    if accel_ms2 < 0:
        return {"error": "accel_ms2 must be >= 0"}
    # TODO 2: weight = mass * G ; tension = mass * (G + accel)   (Newton's 2nd law)
    weight = mass_kg * G
    tension = mass_kg * (G + accel_ms2)
    # TODO 3: return {"weight_n": .., "tension_n": ..} rounded to 2 decimals
    return {"weight_n": round(weight, 2), "tension_n": round(tension, 2)}

def select_cable(
    load_n: float,
    safety_factor: float = 5.0,
    catalog_file: str = "cables.csv",
) -> dict:
    """Select the lightest adequate steel cable from catalog given design load. Finds the cable with the smallest breaking load that is at least esign_n = load_n * safety_factor.
    Args:
      load_n: Applied load/tension in Newtons (> 0).
      safety_factor: Safety factor multiplier (default 5.0, >= 1.0).
      catalog_file: CSV filename containing cable catalog data.
    Returns:
      dict with 'design_load_n', 'cable', 'diameter_mm', 'breaking_load_kn','margin_pct'."""
    # TODO 1: bad input -> return {"error": "..."} (load_n must be > 0; safety_factor must be >= 1)
    if load_n <= 0:
        return {"error": "load_n must be greater than 0"}
    if safety_factor < 1.0:
        return {"error": "safety_factor must be >= 1.0"}
    # TODO 2: the file sits next to tools.py:
    path = Path(__file__).parent / catalog_file
    if not path.is_file():
        return {"error": f"Catalog file not found: {catalog_file}"}
    # TODO 3: design_n = load_n * safety_factor
    design_n = load_n * safety_factor
    # TODO 4: read the CSV with csv.DictReader. breaking_load_kn is in kN:multiply by 1000 to compare with newtons.
    candidates = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            breaking_kn = float(row["breaking_load_kn"])
            breaking_n = breaking_kn * 1000.0
            if breaking_n >= design_n:
                candidates.append({
                    "name": row["name"],
                    "diameter_mm": float(row["diameter_mm"]),
                    "breaking_kn": breaking_kn,
                    "breaking_n": breaking_n,
                })
    # TODO 5: keep the cables whose breaking load >= design_n. None left?
    #         return {"error": "no cable in the catalog is strong enough"}
    if not candidates:
        return {"error": "no cable in the catalog is strong enough"}
    # TODO 6: pick the one with the SMALLEST breaking load (the CSV is not
    #         sorted!) and return
    #         {"design_load_n", "cable", "diameter_mm", "breaking_load_kn",
    #          "margin_pct"}   margin_pct = (breaking / design - 1) * 100
    #         rounded to 2 decimals
    best = min(candidates, key=lambda c: c["breaking_n"])
    margin_pct = ((best["breaking_n"] / design_n) - 1.0) * 100.0
    return {
        "design_load_n": round(design_n, 2),
        "cable": best["name"],
        "diameter_mm": round(best["diameter_mm"], 2),
        "breaking_load_kn": round(best["breaking_kn"], 2),
        "margin_pct": round(margin_pct, 2),
    }