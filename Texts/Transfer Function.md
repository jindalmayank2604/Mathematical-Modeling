# 📘 FFT-Based System Analysis & Progression

**Author:** Mayank Jindal

---

## 🔷 Purpose

This document captures the full progression from manual frequency response analysis
to FFT-based system identification using Python.

It connects:

* ODE-based system simulation
* Frequency domain analysis
* DSP-based system understanding
* Real-world signal processing workflows

---

## 🔷 Learning Progression Overview

### Stage 1: Frequency Sweep Method

Initial approach to analyze system behavior:

```
Input: F(t) = sin(2π f t)
```

Process:

```
Loop over frequencies → simulate → measure amplitude
```

Output:

```
Frequency → Amplitude
```

This defines:

```
→ Frequency Response
```

---

## 🔷 System Used

Second-order damped driven system:

```
dx/dt = v  
dv/dt = -2ζω v - ω² x + input(t)
```

Where:

* x(t) → output
* input(t) → external forcing

---

## 🔷 Frequency Sweep Procedure

### Step 1: Frequency Range

```
frequencies = np.linspace(f_start, f_end, N)
```

---

### Step 2: Simulation

```
for f in frequencies:
    simulate system
```

---

### Step 3: Remove Transient

```
steady = positions[int(0.6 * len(positions)):]
```

---

### Step 4: Measure Amplitude

```
amplitude = (max(steady) - min(steady)) / 2
```

---

### Step 5: Mapping

```
frequencies → amplitudes
```

---

### Step 6: Plot

```
Frequency vs Amplitude
```

Produces:

```
→ Frequency Response Curve
```

---

## 🔷 Limitations Identified

```
• Requires multiple simulations  
• Slow and inefficient  
• Manual amplitude extraction  
• Not scalable  
```

---

## 🔷 Transition to FFT-Based Method

### Core Idea:

Instead of testing one frequency at a time:

```
Send all frequencies at once
```

---

## 🔷 New Input Strategy

```
sgnl = random noise OR multi-sine signal
```

Purpose:

```
Excite entire frequency spectrum
```

---

## 🔷 FFT-Based System Extraction

Transform signals:

```
X(f) = FFT(input)  
Y(f) = FFT(output)
```

System behavior:

```
H(f) = Y(f) / X(f)
```

---

## 🔷 Key Procedure (FFT Method)

### Step 1: Time Setup

```
dt = 0.001  
t = np.arange(0, 10, dt)
```

---

### Step 2: Input Signal

```
sgnl = np.random.randn(len(t))
```

---

### Step 3: System Simulation

```
• Single simulation  
• No frequency loop  
• Input applied per timestep  
```

---

### Step 4: FFT Computation

```
X = FFT(input)  
Y = FFT(output)  
freq = fftfreq
```

---

### Step 5: Transfer Function

```
H = Y / (X + 1e-8)
```

---

### Step 6: Extraction

```
magnitude = |H|  
phase = angle(H)
```

---

### Step 7: Visualization

```
Frequency → Magnitude  
Frequency → Phase  
```

---

## 🔷 Physical Interpretation

For each frequency:

```
Output(f) = Input(f) × H(f)
```

---

## 🔷 Meaning

```
• High magnitude → frequency passes  
• Low magnitude → frequency suppressed  
• Phase → delay introduced  
```

---

## 🔷 Resonance

Occurs when:

```
f ≈ ω / (2π)
```

Results:

```
• Peak in magnitude  
• Maximum energy absorption  
```

---

## 🔷 Effect of Damping

Low damping (ζ small):

```
• Sharp peak  
• High amplification  
```

High damping (ζ large):

```
• Flat response  
• Reduced peak  
```

---

## 🔷 System Insight

### Time Domain:

```
Shows signal evolution
```

### Frequency Domain:

```
Shows system behavior across frequencies
```

---

## 🔷 Connection to DSP

* Fast Fourier Transform → extracts frequency components
* Transfer Function → defines system behavior

---

## 🔷 Combined Understanding

```
Output(f) = Input(f) × System_Response(f)
```

---

## 🔷 Comparison Summary

### OLD METHOD (frequency_response.py)

```
• Frequency loop  
• Single sine input  
• Multiple simulations  
• Manual amplitude extraction  
```

---

### NEW METHOD (fft_transfer_function.py)

```
• Single multi-frequency input  
• One simulation  
• FFT-based extraction  
• Direct system identification  
```

---

## 🔷 Common Mistakes

```
• Using single sine input  
• Reverting to frequency loop  
• Not adding epsilon in division  
• Poor input signal (missing frequencies)  
• Overthinking instead of following pipeline  
```

---

## 🔷 Files Implemented

```
frequency_response.py  
fft_transfer_function.py  
```

---

## 🔷 Next Step

```
bode_plot_analysis.py
```

### Goal:

```
• Convert magnitude to dB scale  
• Log-frequency plotting  
• Build Bode plot  
• Compare with theoretical response  
```

---

## 🔷 Final Insight

This progression marks a shift:

```
From simulation → to system identification
```

You are no longer:

```
• manually probing systems
```

You are now:

```
• extracting system behavior from data  
• working like DSP engineers  
• bridging mathematics with real signal analysis  
```

---

## 🔷 Domains This Applies To

```
• Control Systems  
• Signal Processing  
• Electronics  
• Communication Systems  
• AI Feature Pipelines  
```

---
