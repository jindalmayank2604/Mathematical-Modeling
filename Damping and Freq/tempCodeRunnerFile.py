import numpy as np
import matplotlib.pyplot as plt

dt = 0.001
t = np.arange(0,10, dt)

omega = 5
zeta = 0.2

positions = []

frequencies = np.linspace(0.1, 5, 50)
amplitudes = []

for f in frequencies:
    x = 0
    v = 0
    positions = []

    for time in t:
        sgnl = np.sin(2 * np.pi * f * time)
        dxdt = v
        dvdt = -2*zeta*omega*v - (omega**2)*x + sgnl

        x = x + dxdt * dt
        v = v + dvdt * dt

        positions.append(x)
    positions = np.array(positions)

    #Removing transient
    steady = positions[int(0.6 * len(positions)):]

    #amplitude calculation
    amp = (np.max(steady) - np.min(steady))/2
    amplitudes.append(amp)
