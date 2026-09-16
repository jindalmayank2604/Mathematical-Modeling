import numpy as np
import matplotlib.pyplot as plt

#Time Domains

dt = 0.01
t = np.arange(0,10,dt)

#Initialising
x = 1
v = 0

omega = 2
zeta = 0.2 #damping factor

positions = []

for i in t:
    dxdt = v
    dvdt = -2*zeta*omega*v - (omega**2)*x # Damping Signal

    x = x+(dxdt)*dt
    v = v+(dvdt)*dt

    positions.append(x)

plt.plot(t, positions)
plt.title("Damped Oscillation")
plt.xlabel("Time")
plt.ylabel("Position")
plt.grid()
plt.show()


