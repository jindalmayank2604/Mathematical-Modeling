## Phase Sign Correction in Cross-Correlation:

## Core Issue:

While computing phase using cross-correlation, the sign of the phase may appear reversed.

## Observed Behavior:

Phase curve increases from:

```
0 → +π
```

But physically expected behavior:

```
0 → -π
```

This indicates incorrect interpretation of delay direction.

---

## Root Cause:

Cross-correlation is defined as:

```
corr = correlate(signal_A, signal_B)
```

This answers:

```
“How much should signal_B be shifted to match signal_A?”
```

---

## Incorrect Implementation:

```
corr = np.correlate(output_steady, input_steady, mode='full')
```

Interpretation:

```
“How much should input be shifted to match output?”
```

This reverses the physical meaning of delay and produces:

```
→ Positive phase (incorrect)
```

---

## Correct Implementation:

```
corr = np.correlate(input_steady, output_steady, mode='full')
```

Interpretation:

```
“How much should output be shifted to match input?”
```

This correctly measures:

```
→ Output lag relative to input
```

---

## Effect on Phase:

Using correct order:

```
delay > 0 → output lags input → negative phase
```

Resulting phase behavior:

```
Low frequency   → phase ≈ 0  
Resonance       → phase ≈ -π/2  
High frequency  → phase ≈ -π  
```

---

## Key Insight:

Order of signals in cross-correlation determines:

```
→ Direction of delay  
→ Sign of phase  
```

---

## Final Rule:

To measure system phase:

```
Always use:

    correlate(input, output)
```

NOT:

```
    correlate(output, input)
```

---

## Physical Meaning:

System behavior:

```
Input → System → Output
```

Phase represents:

```
“How much output is delayed relative to input”
```

---

## Common Mistake:

Reversing signal order leads to:

```
• Correct magnitude  
• Incorrect phase sign  
```

---

## Conclusion:

Cross-correlation is not just a mathematical tool.

It encodes direction:

```
→ Which signal leads  
→ Which signal lags  
```

Correct ordering ensures physically meaningful phase response.

---
