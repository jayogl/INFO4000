# Physics-only PINN Digital Twin + PID for a Baking Oven

A small teaching project. The oven has one uniform temperature (lumped model). The PINN becomes the simulated oven in a closed-loop PID experiment.

## Run

From this folder, with Python 3.10+:

```bash
pip install -r requirements.txt
python main.py
```

Alternatively, with `uv` installed:

```bash
uv run --with torch --with numpy --with matplotlib main.py
```

`main.py` trains the PINN, prints validation errors, saves the trained weights as `oven_pinn.pt`, and creates `oven_results.png`.

## Thermal physics

The governing energy balance is

`C dT/dt = Pmax*u - k*(T-Ta)`

where C = 10,000 J/°C, Pmax = 2,000 W, k = 10 W/°C, and ambient Ta = 25°C. The heater input `u` ranges from 0 (off) to 1 (fully on). These are *illustrative parameters*, not measurements from a real oven.

## What is trained?

`pinn.py` defines `T_theta(tau, T0, u)`:

- `tau`: elapsed seconds **within one control interval** (0–10 s)
- `T0`: temperature at the beginning of the interval
- `u`: heater power **held constant** over the interval
- output: temperature after `tau` seconds

Training generates random combinations of the three inputs. It **does not use correct temperature labels**. Instead, PyTorch differentiates the network output with respect to `tau` and trains it to satisfy the physical energy balance. The network output is designed so `T_theta(0,T0,u)=T0` exactly.

## Where is PID?

After training, `main.py` runs the feedback loop:

1. PID reads the latest **PINN-predicted** temperature.
2. PID selects a heater command in [0,1].
3. PINN predicts the next temperature after 10 seconds.
4. Repeat.

The setpoint is 180°C for 60 minutes, then 160°C for 30 minutes. For simplicity, the supplied `PID` class defaults to PI (`kd=0`); set a nonzero `kd` if you want to experiment with derivative action.

## Validation

`oven.py` contains the exact solution of this **lumped ODE** for a constant heater command. This solution is *not used in PINN training*. It is used after training to check one-step predictions, and in a separate reference PID run to compare closed-loop trajectories.

A low one-step error is necessary but not sufficient: repeated predictions can accumulate error over time. The second comparison examines the full controlled trajectory.

## Important limitations

- This simulates a **lumped average oven temperature**, not spatial heat conduction, convection, radiation, or food temperature.
- With completely known parameters, directly solving this ODE is easier and typically more accurate than training a PINN. Here the PINN is an educational demonstration.
- A trained model is a virtual/surrogate oven. Connecting it to a measured, continuously updated physical oven would be a step toward an operational digital twin.
- The training range is T0 = 25–225°C, heater u = 0–100%, tau = 0–10 s. Outside these ranges the model is not validated.
- This is a simulation, not a controller to attach to an actual heater.

## Suggested exploration

Change `kp`, `ki`, `kd` in `pid.py`; change the setpoint schedule in `main.py`; try reducing the number of PINN training steps and observe validation errors.
