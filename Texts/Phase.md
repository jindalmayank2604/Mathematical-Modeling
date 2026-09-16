## Phase Calculation from Time Delay:

## Core Idea:

Phase represents how much the output signal is shifted relative to the input signal.

Instead of measuring phase directly, we first measure:

```
→ Time delay between input and output
```

Then convert it into phase.

---

## Step 1: Measure Time Delay

Using peak detection:

```
idx_out = np.argmax(output_steady)
idx_in  = np.argmax(input_steady)

delay = (idx_out - idx_in) * dt
```

Where:
idx_out → index of output peak
idx_in  → index of input peak
dt      → time step

Interpretation:
delay → how late (or early) the output occurs compared to input

---

## Step 2: Understand One Cycle

For a sinusoidal signal:

```
frequency = f
```

Time period:

```
T = 1 / f
```

Meaning:
One complete cycle takes T seconds

---

## Step 3: Relate Time to Phase

One full cycle corresponds to:

```
2π radians
```

So:

```
T seconds → 2π radians
```

Using proportional relationship:

```
delay seconds → ?
```

---

## Step 4: Derive Phase Formula

```
phase = (delay / T) × 2π
```

Substitute:

```
T = 1 / f
```

Then:

```
phase = delay × f × 2π
```

---

## Final Formula:

```
phase = 2π f × delay
```

In code:

```
phase = 2 * np.pi * f * delay
```

---

## Physical Interpretation:

```
delay = 0        → phase = 0
delay = T/4      → phase = π/2
delay = T/2      → phase = π
delay = T        → phase = 2π
```

Meaning:
Phase expresses time shift in terms of cycles.

---

## Important Notes:

```
• Phase is measured in radians
• Positive delay → output lags input
• Negative delay → output leads input
```

---

## Limitations of Peak Method:

```
• Multiple peaks can cause incorrect matching
• Noise affects accuracy
• Not reliable for high-frequency signals
```

This method is suitable for:
• learning phase concept
• simple systems

Advanced methods (recommended later):
• cross-correlation
• FFT-based phase extraction

---

## Key Insight:

We converted:

```
index difference → time delay → phase shift
```

This connects:

```
time domain → frequency domain
```

---
