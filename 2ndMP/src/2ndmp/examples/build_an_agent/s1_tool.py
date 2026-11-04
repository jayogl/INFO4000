"""STEP 1 -- The tool. A plain Python function. No AI here.

Cantilever beam, point load P at the free end, rectangular section b x h:

    I      = b * h^3 / 12                  second moment of area   (mm^4)
    delta  = P * L^3 / (3 * E * I)         tip deflection          (mm)
    sigma  = 6 * P * L / (b * h^2)         max bending stress      (MPa = N/mm^2)
    SF     = yield strength / sigma        safety factor

Units: N, mm, MPa.  (1 GPa = 1000 N/mm^2)
"""
MATERIALS = {                     # E in GPa, yield strength in MPa
    "steel": (200.0, 250.0),      # mild steel
    "aluminum": (69.0, 275.0),    # 6061-T6
    "titanium": (110.0, 880.0),   # Ti-6Al-4V
}


def cantilever_beam(load_n: float, length_mm: float, width_mm: float, height_mm: float, material: str = "steel") -> dict:
    """Deflection, stress and safety factor of a cantilever beam with a rectangular cross-section and a
    point load at the free end. Use it for any question about how much a cantilever bends or whether it is safe.

    Args:
        load_n: load at the free end in newtons (> 0)
        length_mm: beam length in millimetres (> 0)
        width_mm: section width b in millimetres (> 0): the side PARALLEL to the bending axis
        height_mm: section height h in millimetres (> 0): the side in the direction of the load. It matters most
        material: steel, aluminum or titanium (default steel)
    """
    if min(load_n, length_mm, width_mm, height_mm) <= 0:
        return {"error": "load_n, length_mm, width_mm and height_mm must all be greater than 0"}
    if material not in MATERIALS:
        return {"error": f"unknown material '{material}'", "available": list(MATERIALS)}
    e_gpa, yield_mpa = MATERIALS[material]
    inertia = width_mm * height_mm ** 3 / 12
    delta = load_n * length_mm ** 3 / (3 * e_gpa * 1000 * inertia)
    sigma = 6 * load_n * length_mm / (width_mm * height_mm ** 2)
    sf = yield_mpa / sigma
    return {"deflection_mm": round(delta, 3), "max_stress_mpa": round(sigma, 1), "safety_factor": round(sf, 2),
            "verdict": "safe" if sf >= 2 else "marginal" if sf >= 1 else "fails",
            "material": material, "youngs_modulus_gpa": e_gpa, "yield_mpa": yield_mpa}


if __name__ == "__main__":
    print(cantilever_beam(100, 300, 20, 10, "steel"))      # compare with the hand calculation on the board
