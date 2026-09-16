import numpy as np
import matplotlib.pyplot as plt

dt = 0.001
t = np.arange(0,10, dt)

x = 0
v = 0

omega = 5
zeta = 0.2

positions = []

for time in t:
    sgnl = np.sin(2*time)
    dxdt = v
    dvdt = -2*zeta*omega*v - (omega**2)*x + sgnl

    x = x + dxdt * dt
    v = v + dvdt * dt

    positions.append(x)

plt.plot(t, positions)
plt.title("Driven Oscillator")
plt.xlabel("Time")
plt.ylabel("Position")
plt.grid()
plt.show()