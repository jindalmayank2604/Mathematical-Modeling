import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def smooth(y, window=20):
    return np.convolve(y, np.ones(window)/window, mode='same')

def generate_signal(mode, t):
    if mode == "Noise":
        return np.random.randn(len(t))
    elif mode == "Sine":
        return np.sin(2*np.pi*1*t)
    elif mode == "Multi-Sine":
        return (np.sin(2*np.pi*0.5*t) +
                0.5*np.sin(2*np.pi*1.5*t) +
                0.3*np.sin(2*np.pi*3*t))

def simulate():
    L = l_scale.get()
    C = c_scale.get()
    R = r_scale.get()
    mode = signal_var.get()

    dt = 0.001
    t = np.arange(0, 10, dt)

    v = generate_signal(mode, t)

    q = 0
    i_curr = 0
    positions = []

    for idx in range(len(t)):
        dqdt = i_curr
        didt = (1/L)*(v[idx] - R*i_curr - (1/C)*q)

        q += dqdt * dt
        i_curr += didt * dt

        positions.append(i_curr)

    positions = np.array(positions)

    X = np.fft.fft(v)
    Y = np.fft.fft(positions)
    freq = np.fft.fftfreq(len(t), dt)

    H = Y / (X + 1e-8)

    magnitude = np.abs(H)
    phase = np.angle(H)

    mask = (freq > 0) & (freq < 5)

    f_plot = freq[mask]
    mag_plot = smooth(magnitude[mask], 30)
    phase_plot = phase[mask]

    ax1.clear()
    ax2.clear()

    ax1.plot(f_plot, mag_plot, color="#00ffaa", linewidth=2)
    ax1.set_title("Magnitude Response", color="white")
    ax1.set_facecolor("#1e1e2f")
    ax1.grid(True, linestyle="--", alpha=0.3)
    ax1.tick_params(colors='white')

    peak_idx = np.argmax(mag_plot)
    ax1.scatter(f_plot[peak_idx], mag_plot[peak_idx], color="red")
    ax1.text(f_plot[peak_idx], mag_plot[peak_idx],
             f" {f_plot[peak_idx]:.2f} Hz", color="red")

    ax2.plot(f_plot, phase_plot, color="#ffaa00", linewidth=2)
    ax2.set_title("Phase Response", color="white")
    ax2.set_facecolor("#1e1e2f")
    ax2.grid(True, linestyle="--", alpha=0.3)
    ax2.tick_params(colors='white')

    canvas.draw()

def on_change(val=None):
    simulate()

def save_plot():
    fig.savefig("lcr_plot.png")

# UI
root = tk.Tk()
root.title("LCR Analyzer")
root.geometry("1000x650")
root.configure(bg="#1e1e2f")

title = tk.Label(root, text="LCR Circuit Analyzer",
                 font=("Arial", 20, "bold"),
                 bg="#1e1e2f", fg="white")
title.pack(pady=10)

control = tk.Frame(root, bg="#1e1e2f")
control.pack(side="left", padx=20)

def slider(label, frm, to):
    tk.Label(control, text=label, fg="white", bg="#1e1e2f").pack()
    s = tk.Scale(control, from_=frm, to=to, resolution=0.01,
                 orient="horizontal", length=200,
                 command=on_change,
                 bg="#1e1e2f", fg="white",
                 troughcolor="#444",
                 highlightthickness=0)
    s.pack(pady=5)
    return s

l_scale = slider("Inductance (L)", 0.1, 5)
c_scale = slider("Capacitance (C)", 0.01, 1)
r_scale = slider("Resistance (R)", 0.1, 5)

tk.Label(control, text="Input Signal", fg="white", bg="#1e1e2f").pack(pady=10)
signal_var = tk.StringVar(value="Noise")
ttk.Combobox(control, textvariable=signal_var,
             values=["Noise", "Sine", "Multi-Sine"]).pack()

tk.Button(control, text="Save Plot",
          command=save_plot,
          bg="#ff4c4c", fg="white").pack(pady=10)

# Graph
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6,5))
fig.patch.set_facecolor("#1e1e2f")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

simulate()

root.mainloop()