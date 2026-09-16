frequency_response_analysis.py

Author: Mayank Jindal

## Purpose:

This module extends system modeling into the frequency domain
by analyzing how a system responds to different input frequencies.

It connects:
• ODE-based system simulation
• Signal processing concepts
• Filter behavior understanding

---

## Conceptual Foundation:

## Core Idea:

A system can be tested by feeding sinusoidal inputs of varying frequencies.

```
Input:  F(t) = sin(2π f t)
```

The system responds differently to each frequency.

We measure:

```
Frequency → Output Amplitude
```

This relationship defines the system's:

```
→ Frequency Response
```

---

## System Used:

Second-order damped driven system:

```
dx/dt = v
dv/dt = -2ζω v - ω² x + sin(2π f t)
```

Where:
x(t) → output
f    → input frequency

---

## Key Procedure:

## Step 1: Frequency Sweep

Define range of frequencies:

```
frequencies = np.linspace(f_start, f_end, N)
```

Loop over each frequency:

```
for f in frequencies:
    simulate system
```

---

## Step 2: Time Simulation

For each frequency:

```
• Run Euler simulation
• Store x(t)
```

---

## Step 3: Remove Transient

Initial portion of signal is unstable.

Remove it:

```
steady = positions[int(0.6 * len(positions)):]
```

Meaning:
Ignore first 60% → keep last 40%

---

## Step 4: Measure Amplitude

```
amplitude = (max(steady) - min(steady)) / 2
```

This gives steady-state output strength.

---

## Step 5: Store Mapping

```
frequencies → amplitudes
```

---

## Step 6: Plot Response

```
x-axis → frequency
y-axis → amplitude
```

This produces:

```
→ Frequency Response Curve
```

---

## Physical Interpretation:

The system behaves like a filter.

```
Some frequencies → amplified
Some frequencies → suppressed
```

---

## Resonance:

Peak occurs when:

```
input frequency ≈ natural frequency

f ≈ ω / (2π)
```

At this point:
system absorbs maximum energy

---

## Effect of Damping:

Low damping (ζ small):
• Sharp peak
• High amplification

High damping (ζ large):
• Flat curve
• Reduced peak

---

## System Insight:

Time Domain:
Shows evolution of signal

Frequency Domain:
Shows behavior across frequencies

---

## Connection to DSP:

Fourier Transform:
Tells what frequencies exist in signal

Frequency Response:
Tells how system modifies those frequencies

---

Combined Understanding:

```
Output(f) = Input(f) × System_Response(f)
```

---

## Meaning:

System acts as a frequency-selective operator.

This is the foundation of:

```
• Filters (low-pass, high-pass, band-pass)
• Signal shaping
• Feature extraction
```

---

## Practical Understanding:

You can now:

```
• Probe systems using sinusoidal inputs
• Measure steady-state response
• Identify resonance
• Understand damping effects
• Visualize system as a filter
```

---

## Common Mistakes:

```
• Not removing transient → incorrect amplitude
• Using wrong input signal (missing frequency term)
• Measuring amplitude inside time loop
• Using velocity instead of position
• Converting list to array too early
```

---

## Files Implemented:

```
frequency_response.py
```

---

## Next Step:

```
phase_response_analysis.py
```

Goal:
• Measure phase shift between input and output
• Build complete Bode plot (magnitude + phase)

---

## Final Insight:

We are no longer just simulating systems.

We are now:

```
• characterizing systems
• analyzing frequency behavior
• bridging ODEs with signal processing
```

This is the core of:

```
• control systems
• electronics
• DSP
• AI signal pipelines
```

---
