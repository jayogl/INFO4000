"""
tools.py -- the TOOLS. Plain Python functions. No AI and no MCP in this file.

A function becomes a good tool when it has:
  1. a short, clear verb name          (the model picks tools by name)
  2. typed arguments                   (type hints become the JSON schema)
  3. a docstring written for the model (this is the only description it reads)
  4. plain-data output                 (a dict of numbers / strings it can explain)

You can test every function here in a notebook or with pytest -- no AI needed.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal

DATA_DIR = Path(os.environ.get("CONTROL_DEMO_DATA", Path(__file__).parent / "data"))
LOG_FILE = DATA_DIR / "oven.csv"

E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]


def nearest_e24(value: float) -> float:
    """Nearest E24 standard value to `value` (ohms), compared on a log scale."""
    decade = 10 ** math.floor(math.log10(value))
    return min((v * decade * m for v in E24 for m in (1, 10)), key=lambda r: abs(math.log(r / value)))


def simulate_pid(kp: float, ki: float, tau: float, kd: float = 0.0, plant_gain: float = 1.0) -> dict:
    """Simulate the unit-step response of a PID controller on a first-order plant
    G(s) = plant_gain / (tau*s + 1) in a closed loop, and return overshoot, rise time
    and settling time.

    To TUNE a controller or find gains that meet a requirement (for example overshoot
    under 10 percent), call this tool several times with different kp and ki, read
    overshoot_pct each time, and adjust: raise ki to speed up (more overshoot), raise
    kp or lower ki to reduce overshoot. Stop when the requirement is met.

    Args:
        kp: proportional gain (>= 0)
        ki: integral gain (>= 0)
        tau: plant time constant in seconds (> 0)
        kd: derivative gain (default 0)
        plant_gain: plant DC gain (default 1)
    """
    if tau <= 0:
        return {"error": "tau must be greater than 0"}
    K = plant_gain
    if ki != 0:
        # closed loop: K(kd s^2 + kp s + ki) / (s(tau s + 1) + K(kd s^2 + kp s + ki))
        num = K * np.array([kd, kp, ki], dtype=float)
        den = np.polyadd(np.array([tau, 1.0, 0.0]), num)
    else:
        # no integrator: K(kd s + kp) / ((tau s + 1) + K(kd s + kp))
        num = K * np.array([kd, kp], dtype=float)
        den = np.polyadd(np.array([tau, 1.0]), num)
    num = np.trim_zeros(num, "f")
    if num.size == 0:
        return {"error": "kp, ki and kd are all zero, so there is no control action"}

    poles = np.roots(den)
    if np.any(poles.real >= 0):
        return {"stable": False, "note": "The closed loop is unstable for these gains."}

    dc_gain = float(num[-1] / den[-1])
    slowest = float(np.min(-poles.real))
    t_end = float(np.clip(10.0 / slowest, 5.0, 500.0))
    t = np.linspace(0, t_end, 4000)
    _, y = signal.step(signal.TransferFunction(num, den), T=t)

    overshoot = max(0.0, (float(y.max()) - dc_gain) / abs(dc_gain) * 100.0) if dc_gain != 0 else None

    def first_time(level: float):
        idx = np.argmax(y >= level)
        return float(t[idx]) if y[idx] >= level else None

    t10, t90 = first_time(0.1 * dc_gain), first_time(0.9 * dc_gain)
    rise = round(t90 - t10, 3) if (t10 is not None and t90 is not None) else None

    outside = np.where(np.abs(y - dc_gain) > 0.02 * abs(dc_gain))[0]
    if outside.size == 0:
        settle = 0.0
    elif outside[-1] >= len(t) - 1:
        settle = None            # did not settle inside the simulated window
    else:
        settle = round(float(t[outside[-1] + 1]), 3)

    return {
        "stable": True,
        "overshoot_pct": None if overshoot is None else round(overshoot, 2),
        "rise_s": rise,
        "settle_s": settle,
        "steady_state_value": round(dc_gain, 4),
        "steady_state_error": round(1.0 - dc_gain, 4),
    }


def design_rc_lowpass(cutoff_hz: float, capacitance_nf: float) -> dict:
    """Design a first-order RC low-pass filter. Given the wanted cutoff frequency and a
    capacitor value, return the ideal resistor, the nearest standard E24 resistor, and
    the cutoff frequency that standard resistor actually gives.

    Args:
        cutoff_hz: wanted -3 dB cutoff frequency in hertz (> 0)
        capacitance_nf: capacitor value in nanofarads (> 0)
    """
    if cutoff_hz <= 0 or capacitance_nf <= 0:
        return {"error": "cutoff_hz and capacitance_nf must be greater than 0"}
    c = capacitance_nf * 1e-9
    r_ideal = 1.0 / (2 * math.pi * cutoff_hz * c)
    r_std = nearest_e24(r_ideal)
    f_actual = 1.0 / (2 * math.pi * r_std * c)
    return {
        "ideal_r_ohms": round(r_ideal, 1),
        "nearest_e24_ohms": round(r_std, 1),
        "actual_cutoff_hz": round(f_actual, 1),
        "cutoff_error_pct": round((f_actual - cutoff_hz) / cutoff_hz * 100, 2),
    }


def read_log_stats(column: str, threshold: float | None = None) -> dict:
    """Read statistics from the oven sensor log (columns: time_s, temp_c, setpoint_c,
    heater_pct). Returns min, max, mean and when the maximum happened. If a threshold
    is given, also returns when the column first and last went above it.

    Args:
        column: column name, one of time_s, temp_c, setpoint_c, heater_pct
        threshold: optional value; report when the column went above it
    """
    df = pd.read_csv(LOG_FILE)
    if column not in df.columns:
        return {"error": f"unknown column '{column}'", "available_columns": list(df.columns)}
    s = df[column]
    out = {
        "samples": int(len(s)),
        "min": round(float(s.min()), 2),
        "max": round(float(s.max()), 2),
        "mean": round(float(s.mean()), 2),
        "max_at_s": float(df.loc[s.idxmax(), "time_s"]),
    }
    if threshold is not None:
        above = df[s > threshold]
        dt = float(df["time_s"].diff().median())
        out["threshold"] = threshold
        out["samples_above"] = int(len(above))
        out["seconds_above"] = round(len(above) * dt, 1)
        out["first_above_s"] = float(above["time_s"].iloc[0]) if len(above) else None
        out["last_above_s"] = float(above["time_s"].iloc[-1]) if len(above) else None
    return out


def divider_design(vin: float, vout: float, r2_ohms: float = 10000.0) -> dict:
    """Design a resistive voltage divider (R1 from Vin to the output, R2 from the output to ground).
    Given the input voltage, the wanted output voltage and a chosen R2, return the ideal R1 and the
    nearest standard E24 values for R1 and R2, plus the output voltage those parts give with NO load.
    This tool does not know about any load; use divider_check to test the design with a load.

    Args:
        vin: input voltage in volts (> 0)
        vout: wanted output voltage in volts (0 < vout < vin)
        r2_ohms: chosen lower resistor R2 in ohms (> 0). Smaller values are less affected by a load.
    """
    if vin <= 0 or r2_ohms <= 0 or not (0 < vout < vin):
        return {"error": "need vin > 0, r2_ohms > 0 and 0 < vout < vin"}
    r1_ideal = r2_ohms * (vin / vout - 1)
    r1, r2 = nearest_e24(r1_ideal), nearest_e24(r2_ohms)
    v_unloaded = vin * r2 / (r1 + r2)
    return {"r1_ideal_ohms": round(r1_ideal, 1), "r1_e24_ohms": round(r1, 1), "r2_e24_ohms": round(r2, 1),
            "vout_unloaded_v": round(v_unloaded, 3),
            "vout_error_pct": round((v_unloaded - vout) / vout * 100, 2)}


def divider_check(vin: float, r1_ohms: float, r2_ohms: float, target_vout: float,
                  load_ohms: float | None = None, tolerance_pct: float = 3.0,
                  resistor_tol_pct: float = 0.0) -> dict:
    """Check a voltage divider against a requirement. Computes the output voltage WITH the load
    connected across R2, its error against the target, the divider current and power, and whether
    it passes the allowed tolerance. If resistor_tol_pct is given, it also checks the worst case with
    both resistors at their tolerance limits. Use this to verify any divider design.

    Args:
        vin: input voltage in volts (> 0)
        r1_ohms: upper resistor R1 in ohms (> 0)
        r2_ohms: lower resistor R2 in ohms (> 0)
        target_vout: required output voltage in volts (> 0)
        load_ohms: resistance of whatever the output feeds, in ohms (omit if unloaded)
        tolerance_pct: allowed output error in percent (default 3)
        resistor_tol_pct: resistor tolerance in percent for a worst-case check (default 0 = nominal only)
    """
    if min(vin, r1_ohms, r2_ohms, target_vout) <= 0 or (load_ohms is not None and load_ohms <= 0):
        return {"error": "all values must be greater than 0"}

    def vout_of(r1, r2):
        r2e = r2 if load_ohms is None else r2 * load_ohms / (r2 + load_ohms)
        return vin * r2e / (r1 + r2e)

    def err(v):
        return (v - target_vout) / target_vout * 100

    v = vout_of(r1_ohms, r2_ohms)
    worst = err(v)
    if resistor_tol_pct:
        k = resistor_tol_pct / 100
        corners = [vout_of(r1_ohms * (1 + a * k), r2_ohms * (1 + b * k)) for a in (-1, 1) for b in (-1, 1)]
        worst = max((err(c) for c in corners), key=abs)
    v_unloaded = vin * r2_ohms / (r1_ohms + r2_ohms)
    passes = abs(worst) <= tolerance_pct
    out = {"vout_v": round(v, 3), "error_pct": round(err(v), 2),
           "unloaded_vout_v": round(v_unloaded, 3), "loading_effect_pct": round((v - v_unloaded) / v_unloaded * 100, 2),
           "divider_current_ma": round(vin / (r1_ohms + r2_ohms) * 1e3, 2),
           "power_mw": round(vin ** 2 / (r1_ohms + r2_ohms) * 1e3, 1),
           "worst_case_error_pct": round(worst, 2), "passes": passes}
    if not passes and load_ohms is not None and abs(v - v_unloaded) / v_unloaded * 100 > tolerance_pct / 2:
        out["hint"] = ("The load pulls the output down. Use a much smaller R2 (and R1), "
                       "so the load resistance is far larger than R2.")
    elif not passes and resistor_tol_pct:
        out["hint"] = "Nominal values are close, but resistor tolerance breaks the margin. Use closer values or tighter parts."
    return out
