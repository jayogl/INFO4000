"""Discrete PI controller (PID with derivative gain set to zero)."""


class PID:
    def __init__(self, kp=0.03, ki=0.0001, kd=0.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.integral = 0.0
        self.previous_temp = None

    def update(self, setpoint, temperature, dt):
        error = setpoint - temperature
        # Derivative on measurement prevents a setpoint-change derivative kick.
        derivative = 0.0 if self.previous_temp is None else -(temperature - self.previous_temp) / dt
        self.previous_temp = temperature
        candidate = self.integral + error * dt
        raw = self.kp * error + self.ki * candidate + self.kd * derivative
        output = max(0.0, min(1.0, raw))
        # Conditional integration: only integrate if not pushing farther into saturation.
        if (0.0 < raw < 1.0) or (raw >= 1.0 and error < 0) or (raw <= 0.0 and error > 0):
            self.integral = candidate
        raw = self.kp * error + self.ki * self.integral + self.kd * derivative
        return max(0.0, min(1.0, raw))
