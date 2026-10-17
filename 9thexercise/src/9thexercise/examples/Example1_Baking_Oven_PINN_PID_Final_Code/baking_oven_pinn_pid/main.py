"""Train physics-only PINN, validate, then run PID with PINN as the plant."""
from pathlib import Path
import numpy as np
import torch
import matplotlib.pyplot as plt
from oven import AMBIENT, DT, exact_step
from pinn import train_pinn, pinn_step
from pid import PID


def run_control(step_fn, minutes=90):
    pid = PID()
    temperature = AMBIENT
    times, temperatures, powers, targets = [], [], [], []
    for i in range(int(minutes * 60 / DT)):
        t = i * DT
        target = 180.0 if t < 60 * 60 else 160.0
        power = pid.update(target, temperature, DT)
        times.append(t / 60)
        temperatures.append(temperature)
        powers.append(power)
        targets.append(target)
        temperature = step_fn(temperature, power)
    return np.array(times), np.array(temperatures), np.array(powers), np.array(targets)


def main():
    folder = Path(__file__).resolve().parent
    model = train_pinn()
    torch.save(model.state_dict(), folder / 'oven_pinn.pt')
    # Validation: unseen random samples compared with the exact ODE solution.
    rng = np.random.default_rng(123)
    errors = []
    for t0, u, dt in zip(rng.uniform(25, 225, 100), rng.uniform(0, 1, 100), rng.uniform(0, DT, 100)):
        errors.append(abs(pinn_step(model, t0, u, dt) - exact_step(t0, u, dt)))
    print(f'Independent one-step validation MAE: {np.mean(errors):.4f} °C')

    times, temperatures, powers, targets = run_control(lambda t, u: pinn_step(model, t, u))
    _, reference, reference_powers, _ = run_control(exact_step)
    print(f'Closed-loop temperature MAE versus reference: {np.mean(abs(temperatures-reference)):.4f} °C')

    fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    ax[0].plot(times, temperatures, label='PINN oven (PID feedback)')
    ax[0].plot(times, reference, '--', label='Physics oven (separate PID)')
    ax[0].plot(times, targets, ':', label='Setpoint')
    ax[0].set_ylabel('Temperature (°C)')
    ax[0].legend()
    ax[0].grid(alpha=0.3)
    ax[1].plot(times, 100 * powers, label='PINN heater command')
    ax[1].plot(times, 100 * reference_powers, '--', label='Reference heater command')
    ax[1].set(xlabel='Time (minutes)', ylabel='Heater power (%)')
    ax[1].legend()
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(folder / 'oven_results.png', dpi=170)
    print('Saved oven_results.png and oven_pinn.pt')


if __name__ == '__main__':
    main()
