"""tools.py -- Motor maintenance tools. Plain Python: no MCP, no AI."""

def motor_life_estimate(
    rated_temp_c: float,
    operating_temp_c: float,
    rated_life_h: float = 20000.0,
) -> dict:
  """Calculate remaining insulation life based on operating temperature using Arrhenius 10-degree rule.

  Use when estimating insulation lifespan degradation due to thermal stress.

  Args:
      rated_temp_c: Insulation class rated temperature in Celsius (> 0).
      operating_temp_c: Measured operating temperature in Celsius.
      rated_life_h: Nominal insulation life at rated temperature in hours
        (default 20000.0, > 0).

  Returns:
      dict with 'life_h', 'life_years', 'life_ratio', or 'error' if input is
      invalid.
  """
  if rated_temp_c <= 0 or rated_life_h <= 0:
    return {"error": "rated_temp_c and rated_life_h must be greater than 0"}
  if operating_temp_c < -50 or operating_temp_c > 250:
    return {"error": "operating_temp_c out of realistic physical range"}

  # Arrhenius 10-degree rule: insulation life halves for every 10°C rise above rated temp
  temp_diff = operating_temp_c - rated_temp_c
  life_h = rated_life_h * (0.5 ** (temp_diff / 10.0))
  life_years = life_h / (24.0 * 365.0)
  life_ratio = life_h / rated_life_h

  return {
      "life_h": round(life_h, 2) if life_h % 1 != 0 else int(life_h),
      "life_years": round(life_years, 1),
      "life_ratio": round(life_ratio, 2),
  }


def motor_health_check(
    vibration_rms: float,
    operating_temp_c: float,
    current_a: float,
    rated_current_a: float,
    rated_temp_c: float = 130.0,
) -> dict:
  """Evaluate motor operational health status, vibration severity zone, thermal margin, and load percentage.

  Use when assessing motor health to determine whether immediate action (ACT),
  close monitoring (WATCH), or normal operation (OK) is required.

  Args:
      vibration_rms: Overall vibration velocity in mm/s RMS (>= 0).
      operating_temp_c: Measured winding temperature in Celsius.
      current_a: Measured stator current in Amperes (>= 0).
      rated_current_a: Nameplate rated current in Amperes (> 0).
      rated_temp_c: Rated insulation temperature in Celsius (default 130.0, >
        0).

  Returns:
      dict with 'status', 'reasons', 'vib_zone', 'load_pct', 'temp_margin_c',
      or 'error' if input is invalid.
  """
  if vibration_rms < 0 or current_a < 0:
    return {"error": "vibration_rms and current_a must be >= 0"}
  if rated_current_a <= 0 or rated_temp_c <= 0:
    return {"error": "rated_current_a and rated_temp_c must be > 0"}
  if operating_temp_c < -50 or operating_temp_c > 250:
    return {"error": "operating_temp_c out of realistic physical range"}

  # ISO 10816 Vibration Severity Zones
  if vibration_rms <= 0.71:
    vib_zone = "A"
  elif vibration_rms <= 2.8:
    vib_zone = "B"
  elif vibration_rms <= 4.5:
    vib_zone = "C"
  else:
    vib_zone = "D"

  load_pct = (current_a / rated_current_a) * 100.0
  temp_margin_c = rated_temp_c - operating_temp_c

  reasons = []
  if vib_zone in ["C", "D"]:
    reasons.append("vibration")
  if temp_margin_c <= 10.0:
    reasons.append("hot")
  if load_pct > 100.0:
    reasons.append("overload")

  # Determine Health Status
  if (
      vib_zone == "D"
      or temp_margin_c < 0
      or vib_zone == "C"
      or len(reasons) >= 2
      or load_pct > 110.0
  ):
    status = "ACT"
  elif len(reasons) > 0 or vib_zone == "B" or load_pct > 90.0:
    status = "WATCH"
  else:
    status = "OK"

  return {
      "status": status,
      "reasons": reasons,
      "vib_zone": vib_zone,
      "load_pct": round(load_pct, 1),
      "temp_margin_c": round(temp_margin_c, 1),
  }
