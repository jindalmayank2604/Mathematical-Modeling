import numpy as np
import matplotlib.pyplot as plt 

dt = 0.001
t = np.arange(0,20, dt)

omega = 5
zeta = 0.2

frequencies = np.linspace(0.1,5, 50)
amplitudes = []
phases = []

for f in frequencies:
    x = 0
    v = 0
    positions = []
    for time in t:
        sgnl = np.sin(2*np.pi*f*time)
        dxdt = v
        dvdt = -2*omega*zeta*v - (omega**2)*x + sgnl

        x = x + (dxdt)*dt
        v = v + (dvdt)*dt

        positions.append(x)
    positions = np.array(positions)

    cut = int(0.6*len(positions))
    output_steady = positions[cut:]
    input_signal = np.sin(2*np.pi*f*t)
    input_steady = input_signal[cut:]

    amp = (np.max(output_steady)-np.min(input_steady))/2
    amplitudes.append(amp)

    corr = np.correlate(input_steady, output_steady, mode = "full")
    lag = np.argmax(corr) - (len(output_steady)-1)

    delay = lag*dt
    phase = 2*np.pi*f*delay

    phases.append(phase)

phases = np.array(phases)
phases = np.unwrap(phases)


# plot phase response
plt.plot(frequencies, phases)
plt.xlabel("Frequency")
plt.ylabel("Phase (radians)")
plt.title("Phase Response")
plt.grid()
plt.show()