import numpy as np
import matplotlib.pyplot as plt

dt = 0.001
t = np.arange(0,10, dt)

omega = 5
zeta = 0.2
sgnl = np.random.randn(len(t))

x = 0
v = 0

positions = []

for i,time in enumerate(t):
    dxdt = v
    dvdt = -2*omega*zeta*v-(omega**2)*x + sgnl[i]

    x = x+(dxdt)*dt
    v = v + (dvdt)*dt

    positions.append(x)

positions = np.array(positions)

#FFT because mixed freq -> Seperated
X = np.fft.fft(sgnl) # Input signal
Y = np.fft.fft(positions) #Output signal

freq = np.fft.fftfreq(len(t), dt)

mask = freq > 0

H = Y/X + (1e-8)

magnitude = np.abs(H)
phase = np.angle(H)

plt.figure()
plt.plot(freq[mask], magnitude[mask])
plt.title("Magnitude Response")
plt.xlabel("Frequency")
plt.ylabel("Magnitude")
plt.xlim(0, 10)

plt.figure()
plt.plot(freq[mask], phase[mask])
plt.title("Phase Response")
plt.xlabel("Frequency")
plt.ylabel("Phase")
plt.xlim(0, 10)

plt.show()