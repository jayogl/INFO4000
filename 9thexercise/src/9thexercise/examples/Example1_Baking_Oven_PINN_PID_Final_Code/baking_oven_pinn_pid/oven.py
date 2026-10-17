"""Reference lumped oven: exact response over a constant-power interval."""
import math

AMBIENT = 25.0            # deg C
CAPACITY = 10_000.0       # J / deg C
MAX_POWER = 2_000.0       # W
LOSS = 10.0               # W / deg C
DT = 10.0                 # seconds per PID step


def exact_step(temperature, power, dt=DT):
    """Reference solution, ONLY for validation (never used to train PINN)."""
    equilibrium = AMBIENT + MAX_POWER * power / LOSS
    return equilibrium + (temperature - equilibrium) * math.exp(-LOSS * dt / CAPACITY)
