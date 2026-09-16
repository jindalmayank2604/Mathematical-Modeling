# 📘 LCR Circuit Analyzer (FFT-Based GUI Tool)

**Author:** Mayank Jindal

---

## 🔷 Purpose

This project builds a **real-time LCR circuit analyzer with GUI**, combining:

* Numerical ODE simulation
* FFT-based system identification
* Interactive parameter tuning
* Visualization of magnitude & phase response

It upgrades earlier FFT work into a **fully interactive engineering tool**.

---

## 🔷 Core Objective

```
Simulate LCR system → Apply input signal → Extract transfer function → Visualize response
```

---

## 🔷 System Modeled

Standard LCR differential equation:

```
dq/dt = i  
di/dt = (1/L)(v(t) - R*i - (1/C)*q)
```

Where:

* q → charge
* i → current (output)
* v(t) → input signal
* L → inductance
* R → resistance
* C → capacitance

---

## 🔷 Input Signal Types

### 1. Noise

```
v(t) = random signal
```

Purpose:

```
• Excites all frequencies  
• Best for system identification  
```

---

### 2. Sine

```
v(t) = sin(2πt)
```

Purpose:

```
• Single frequency testing  
• Basic response observation  
```

---

### 3. Multi-Sine

```
v(t) = sin(2π0.5t) + 0.5sin(2π1.5t) + 0.3sin(2π3t)
```

Purpose:

```
• Controlled multi-frequency excitation  
• Faster than sweep method  
```

---

## 🔷 Simulation Pipeline

### Step 1: Time Setup

```
dt = 0.001  
t = np.arange(0, 10, dt)
```

---

### Step 2: Generate Input

```
v = generate_signal(mode, t)
```

---

### Step 3: Initialize State

```
q = 0  
i = 0
```

---

### Step 4: Numerical Integration

Loop over time:

```
dqdt = i  
didt = (1/L)(v - R*i - (1/C)*q)

q += dqdt * dt  
i += didt * dt
```

---

### Step 5: Output Storage

```
positions = current values over time
```

---

## 🔷 FFT-Based System Extraction

### Step 1: Transform Signals

```
X = FFT(input)  
Y = FFT(output)
```

---

### Step 2: Frequency Axis

```
freq = fftfreq(N, dt)
```

---

### Step 3: Transfer Function

```
H(f) = Y / (X + 1e-8)
```

(Epsilon avoids division errors)

---

### Step 4: Extract Components

```
Magnitude = |H|  
Phase = angle(H)
```

---

### Step 5: Frequency Filtering

```
0 < f < 5 Hz
```

Reason:

```
• Removes noise  
• Focus on useful range  
```

---

### Step 6: Smoothing

```
Moving average applied to magnitude
```

Purpose:

```
• Cleaner visualization  
• Reduces FFT noise  
```

---

## 🔷 Visualization

### Magnitude Plot

```
Frequency → Gain
```

Highlights:

```
• Resonance peak detected  
• Peak frequency marked  
```

---

### Phase Plot

```
Frequency → Phase shift
```

Shows:

```
• Delay introduced by system  
```

---

## 🔷 GUI Components

### Sliders

```
L → Inductance  
C → Capacitance  
R → Resistance  
```

Behavior:

```
• Real-time updates  
• Triggers simulation instantly  
```

---

### Dropdown

```
Select input signal:
Noise / Sine / Multi-Sine
```

---

### Button

```
Save Plot → exports graph as PNG
```

---

### Graph Panel

```
Top → Magnitude  
Bottom → Phase  
```

---

## 🔷 Real-Time Interaction

Whenever user changes:

```
• L, C, R  
• Signal type
```

System automatically:

```
→ Re-simulates  
→ Recomputes FFT  
→ Updates plots  
```

---

## 🔷 Physical Interpretation

For each frequency:

```
Output(f) = Input(f) × H(f)
```

---

## 🔷 Meaning of Graphs

### Magnitude

```
High → frequency passes  
Low → frequency blocked  
```

---

### Phase

```
Shows delay / lag  
```

---

## 🔷 Resonance Behavior

Occurs when:

```
f ≈ 1 / (2π√(LC))
```

Effects:

```
• Peak in magnitude  
• Maximum energy transfer  
```

---

## 🔷 Effect of Resistance (R)

Low R:

```
• Sharp peak  
• High amplification  
```

High R:

```
• Flat response  
• Damped system  
```

---

## 🔷 Advantages Over Previous Method

### Compared to Frequency Sweep

```
OLD:
• Multiple simulations  
• Slow  
• Manual amplitude extraction  

NEW:
• Single simulation  
• FFT-based  
• Real-time interaction  
• Fully automated  
```

---

## 🔷 Code Architecture

### Functions

```
generate_signal() → creates input  
simulate() → runs system + FFT  
smooth() → cleans magnitude  
```

---

### GUI Flow

```
User input → simulate() → FFT → Plot update
```

---

## 🔷 Common Mistakes

```
• Using only sine input → incomplete spectrum  
• Removing epsilon → division errors  
• Not smoothing → noisy graph  
• Wrong dt → poor frequency resolution  
```

---

## 🔷 Files Suggested

```
lcr_gui_fft_analyzer.py
```

---

## 🔷 Next Step

```
bode_plot_gui.py
```

### Goals:

```
• Convert magnitude → dB  
• Log scale frequency  
• Full Bode plot  
• Theoretical vs simulated comparison  
```

---

## 🔷 Final Insight

This project represents a major shift:

```
From:
Manual simulation

To:
Interactive system analysis tool
```

You are now:

```
• Building engineering tools  
• Understanding real systems  
• Thinking like a DSP + Control Systems engineer  
```

---

## 🔷 Domain Applications

```
• Control Systems  
• Signal Processing  
• Circuit Design  
• Communication Systems  
• Embedded Systems  
```

---

## 🔷 Reference

This builds directly on your previous FFT system understanding:



---
