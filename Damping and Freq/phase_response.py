import numpy as np
import matplotlib.pyplot as plt

dt = 0.001
t = np.arange(0,20,dt)

omega = 5
zeta = 0.2

frequencies = np.linspace(0.1,5,50)
amplitudes = []
phases = []

for f in frequencies:
    x = 0
    v = 0
    positions = []

    for time in t:
        sgnl = np.sin(2*np.pi*f*time)
        dxdt=v
        dvdt= -2*omega*zeta*v - (omega**2)*x + sgnl

        x = x + (dxdt)*dt
        v = v + (dvdt)*dt

        positions.append(x)
    positions = np.array(positions)

    #remove transient 
    cut = int(0.6*len(positions))
    output_steady = positions[cut:]

    #input signal
    input_signal = np.sin(2*np.pi*f*t)
    input_steady = input_signal[cut:]

    #amplitude
    amp = (np.max(output_steady) - np.min(output_steady)) / 2
    amplitudes.append(amp)

    #phase
    idx_out = np.argmax(output_steady)
    idx_in = np.argmax(input_steady)
    delay = (idx_out - idx_in) * dt
    phase = 2*np.pi*f*delay

    phases.append(phase)

# plot phase response
plt.plot(frequencies, phases)
plt.xlabel("Frequency")
plt.ylabel("Phase (radians)")
plt.title("Phase Response")
plt.grid()
plt.show()