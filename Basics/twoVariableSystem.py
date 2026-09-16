import numpy as np
import matplotlib.pyplot as plt


#Time domains
dt = 0.01
t = np.arange(0,10,dt)
#Initialising position and vel
x = 1
v = 0 

omega = 7

positions = []

for i in t:
    dxdt = v
    dvdt = (-omega**2)*x

    x = x + (dxdt)*dt
    v = v + (dvdt)*dt

    positions.append(x)

plt.plot(t, positions)
plt.title("Undamped Oscillation")
plt.xlabel("Time")
plt.ylabel("Position")
plt.grid()
plt.show()