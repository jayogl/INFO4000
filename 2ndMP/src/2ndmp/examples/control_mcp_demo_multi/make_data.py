"""Generate data/oven.csv: a synthetic oven log with a temperature spike (the 'event')."""
import numpy as np, pandas as pd
rng = np.random.default_rng(7)
t = np.arange(0, 1800, 5.0)
sp = np.where(t < 60, 25 + t * 2.9, 200.0)                  # ramp then hold at 200 C
temp = 25 + (sp - 25) * (1 - np.exp(-t / 90)) + rng.normal(0, 0.6, t.size)
spike = (t >= 1200) & (t < 1260)                              # fault: 60 s excursion
temp = temp + np.where(spike, 32 * np.sin(np.pi * (t - 1200) / 60), 0)
heater = np.clip(35 + 0.55 * (sp - temp) + rng.normal(0, 1.0, t.size), 0, 100)
pd.DataFrame({"time_s": t, "temp_c": temp.round(2), "setpoint_c": sp.round(1),
              "heater_pct": heater.round(1)}).to_csv("data/oven.csv", index=False)
print("wrote data/oven.csv")
