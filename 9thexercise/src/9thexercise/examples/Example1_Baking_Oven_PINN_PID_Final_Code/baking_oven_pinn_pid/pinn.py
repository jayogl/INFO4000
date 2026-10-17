"""Physics-only PINN: (elapsed time, start T, constant heater power) -> T."""
import torch
from torch import nn
from oven import AMBIENT, CAPACITY, MAX_POWER, LOSS, DT


class OvenPINN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(3, 32), nn.Tanh(),
                                 nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1))

    def forward(self, tau, t0, power):
        # Inputs normalized for easier training.
        features = torch.cat((tau / DT, (t0 - AMBIENT) / 200.0, power), dim=1)
        # Hard constraint: at elapsed time zero, return t0 exactly.
        # Scale network output so its derivative can represent deg C / sec.
        return t0 + (tau / DT) * self.net(features) * 10.0


def train_pinn(steps=1600, batch_size=256, seed=7):
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    model = OvenPINN()
    opt = torch.optim.Adam(model.parameters(), lr=0.003)
    for step in range(steps):
        tau = (torch.rand(batch_size, 1) * DT).requires_grad_(True)
        t0 = 25.0 + torch.rand(batch_size, 1) * 200.0
        power = torch.rand(batch_size, 1)
        predicted = model(tau, t0, power)
        slope = torch.autograd.grad(predicted, tau, torch.ones_like(predicted), create_graph=True)[0]
        # Normalized residual: slope predicted by network vs thermal energy balance.
        required_slope = (MAX_POWER * power - LOSS * (predicted - AMBIENT)) / CAPACITY
        loss = ((slope - required_slope) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if (step + 1) % 400 == 0:
            print(f"training step {step+1:4d} / {steps}, physics loss = {loss.item():.6f}")
    return model


@torch.no_grad()
def pinn_step(model, temperature, power, dt=DT):
    tau = torch.tensor([[dt]], dtype=torch.float32)
    t0 = torch.tensor([[temperature]], dtype=torch.float32)
    u = torch.tensor([[power]], dtype=torch.float32)
    return float(model(tau, t0, u).item())
