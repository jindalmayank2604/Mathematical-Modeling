import numpy as np
import matplotlib.pyplot as plt

#Setting up time 

dt = 0.01
t = np.arange(0,5,dt)

y = 10
values = []

for i in t:
    dy = -2*y
    y = y+dy*dt
    values.append(y)

plt.plot(t, values)
plt.title("First Order System: dy/dt = -2y")
plt.xlabel("Time")
plt.ylabel("y")
plt.grid()
plt.show()

