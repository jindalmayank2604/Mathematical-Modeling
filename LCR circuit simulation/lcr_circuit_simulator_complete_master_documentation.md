# LCR Circuit Simulator Complete Master Documentation

Source file: `D:\LEARNING PYTHON\Mathematical System Modeling\LCR circuit simulation\lcr_circuit_simulator.py`

This document is written as a textbook, not as a short project note. Its purpose is to teach the reader from first principles and then connect those principles to the exact implementation of the simulator. The reader is assumed to begin with little or no knowledge of signals, numerical simulation, FFT-based analysis, graph-based circuit interpretation, or Tkinter application structure.

The educational structure of this document follows the way understanding usually develops in a real human learner.

1. First we ask what a signal is and why systems need simulation.
2. Then we study the electrical meaning of resistors, inductors, and capacitors.
3. Then we study discrete time, sampling, and numerical approximation.
4. Then we examine the signal families used by the project.
5. Then we study Fourier analysis, convolution, FFT, windowing, spectral leakage, frequency response, magnitude, and phase.
6. Then we map those ideas into the code: state models, signal generation, manual simulation, graph parsing, topology analysis, graph solving, metric extraction, plotting, and controller orchestration.
7. Finally, we show how the entire project can be mentally reconstructed as one coherent system.

Every chapter ends with implementation references so the theory can be tied back to the code. That means the reader is never left with theory alone and never left with code alone. The goal is always to connect:

- what the concept is
- why it exists
- how it works
- where it appears in the implementation

# Chapter 1. What a Signal Is, What a System Is, and Why a Simulator Exists

A signal is any quantity that changes in a way we care about. The word is broad on purpose. A signal may be a voltage, a current, a pressure, a stock price, a temperature, a sound wave, or a digital sensor stream. In this project, the most important signals are electrical. The input signal is the source waveform applied to the circuit. The output signals are the responses produced by the network, such as circuit current, capacitor voltage, inductor voltage, resistor voltage, and the corresponding frequency-domain representations.

A system is a rule that transforms an input signal into an output signal. If we supply a waveform to an electrical network and measure the resulting current, then the circuit is acting as a system. The same input waveform can produce very different outputs depending on the values of the resistor, inductor, capacitor, and the topology connecting them.

Why simulation is needed at all:
- Real circuits with energy storage do not respond instantaneously in a trivial way.
- A resistor dissipates energy, but an inductor and capacitor store energy.
- Once energy storage is present, the circuit develops memory.
- Once memory is present, the output at the current time depends on past behavior, not just the current input value.
- That dependence creates transient behavior, resonance, damping, overshoot, settling, and phase shift.

A simulator exists because these behaviors are difficult to predict by intuition alone, especially when the circuit is not a single simple branch. The simulator lets the user explore three things at once.

1. Topology: how parts are connected.
2. Excitation: what kind of signal drives the network.
3. Response: how the network behaves in time and frequency.

From a software-architecture point of view, the application is a bridge between four worlds.

The first world is the visual world. The user sees components, wires, cards, plots, buttons, and pages.

The second world is the symbolic world. Components become `ComponentModel` objects. Wires become `ConnectionModel` objects. Circuits become `CircuitGraph` objects.

The third world is the mathematical world. Signals become arrays. Networks become differential equations or nodal matrices. Spectra become complex arrays. Metrics become formulas over those arrays.

The fourth world is the interpretation world. A user sees resonance frequency, peak gain, damping ratio, rise time, settling time, and plotted curves. These are not raw internal objects. They are the system’s behavior translated back into human understanding.

This project therefore is not just a “circuit drawer” and not just a “solver.” It is an educational scientific instrument.

## Chapter 1 Implementation References

Code regions that embody this chapter:
- Global configuration and vocabulary: `lcr_circuit_simulator.py:1-119`
- Core state and signal settings: `lcr_circuit_simulator.py:867-902`
- Scientific engines: `lcr_circuit_simulator.py:1309-1676`
- Simulation page and controller flow: `lcr_circuit_simulator.py:1991-2599`, `lcr_circuit_simulator.py:4123-4370`

### Small Source Snippet: Global Vocabulary

```python
THEME = {
    "bg": "#0f0f0f",
    "panel": "#1a1a1a",
    "accent": "#00ffcc",
    "secondary": "#ffaa00",
}

SIGNAL_OPTIONS = ["Noise", "Sine", "Multi-Sine", "Step", "Square", "Pulse", "Impulse", "Chirp"]
```

### Small Source Snippet: Shared State Initialization

```python
self.dt = 0.001
self.duration = 12.0
self.analysis_min_hz = 0.05
self.analysis_max_hz = 8.0
self.smoothing_window = 21
self.time = np.arange(0.0, self.duration, self.dt)
```

### Small Source Snippet: App Startup Orchestration

```python
self._configure_root()
self._configure_styles()
self._build_shell()
self._seed_demo_circuit()
self._push_undo_state()
self.handle_circuit_change()
self.show_page("builder")
```

# Chapter 2. Resistors, Inductors, Capacitors, and the Physics Behind the Project

To understand the simulator deeply, one must understand what the circuit elements mean physically and mathematically.

## 2.1 The Resistor

A resistor is the simplest element in the project. Its defining equation is Ohm’s law:

`v(t) = R i(t)`

Symbol-by-symbol explanation:
- `v(t)` is voltage across the resistor at time `t`
- `R` is resistance in ohms
- `i(t)` is current through the resistor at time `t`

What the resistor does physically:
- It opposes current flow.
- It dissipates electrical energy as heat.
- It does not store energy.
- It creates damping in dynamic systems.

Why it matters in the simulator:
- It controls how quickly oscillations decay.
- It affects damping ratio.
- It affects quality factor.
- It affects the magnitude of current for a given source voltage.

## 2.2 The Inductor

The inductor is an energy-storage element. Its defining equation is:

`v_L(t) = L * di(t)/dt`

Symbol-by-symbol explanation:
- `v_L(t)` is voltage across the inductor
- `L` is inductance in henries
- `di(t)/dt` is the rate of change of current

What the inductor does physically:
- It stores energy in a magnetic field.
- It resists sudden changes in current.
- A fast change in current demands a larger inductor voltage.

Why it matters in the simulator:
- It introduces dynamic behavior.
- It contributes to resonance with the capacitor.
- It introduces phase behavior because its voltage depends on current derivative.

## 2.3 The Capacitor

The capacitor is also an energy-storage element. Its common equation is:

`i_C(t) = C * dv_C(t)/dt`

A rearranged form used in intuition is:

`v_C(t) = (1/C) * integral(i(t) dt)`

Symbol-by-symbol explanation:
- `i_C(t)` is current through the capacitor
- `C` is capacitance in farads
- `dv_C(t)/dt` is the rate of change of capacitor voltage

What the capacitor does physically:
- It stores energy in an electric field.
- It resists sudden changes in voltage.
- It accumulates charge, and that stored charge determines voltage.

Why it matters in the simulator:
- The manual solver explicitly tracks charge.
- Capacitor voltage is reconstructed from charge divided by capacitance.
- Capacitor behavior is central to transient response and resonant effects.

## 2.4 Why R, L, and C Together Produce Rich Dynamics

A resistor alone is memoryless. An inductor and capacitor are not memoryless. When R, L, and C coexist, the circuit has both storage and dissipation.

That creates:
- oscillation when energy moves between inductor and capacitor
- damping when resistance removes energy from the system
- resonance when the circuit strongly responds near a natural frequency
- phase shift because storage elements create delay-like behavior between input and output

This is why the simulator is interesting. Without storage, the system would be much less dynamic and much less educational.

## Chapter 2 Implementation References

Code regions that embody this chapter:
- Component metadata and defaults: `lcr_circuit_simulator.py:42-50`
- Manual solver voltage/current logic: `lcr_circuit_simulator.py:1350-1388`
- Container reduction formulas: `lcr_circuit_simulator.py:446-494`, `lcr_circuit_simulator.py:680-688`
- Graph-solver admittance formulas: `lcr_circuit_simulator.py:1518-1527`

### Small Source Snippet: Component Defaults and Units

```python
COMPONENT_META = {
    "Resistor": {"prefix": "R", "unit": "Ohm", "default": 1.0},
    "Inductor": {"prefix": "L", "unit": "H", "default": 1.0},
    "Capacitor": {"prefix": "C", "unit": "F", "default": 0.5},
}
```

### Small Source Snippet: Reduced-Circuit Physics in Code

```python
capacitor_drop = inv_c * charge
resistive_drop = effective_resistance * current
didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
charge += dqdt * dt
current += didt * dt
```

### Small Source Snippet: Frequency-Domain Element Modeling

```python
if component.type == "Resistor":
    return 1.0 / value
if component.type == "Inductor":
    return 1.0 / complex(max(state.inductor_series_resistance, 1e-12), max(omega, 1e-12) * value)
if component.type == "Capacitor":
    capacitive_reactance = -1.0 / (max(omega, 1e-9) * value)
    return 1.0 / complex(max(state.capacitor_esr, 1e-12), capacitive_reactance)
```

# Chapter 3. Continuous Time, Discrete Time, Sampling, and the Importance of dt

Real physical systems evolve continuously. Software does not. A computer stores numbers in discrete memory locations and processes them step by step. Therefore, a continuous-time signal must be represented by a finite set of sampled values.

## 3.1 What Sampling Means

If a continuous signal is represented by values taken every `dt` seconds, then `dt` is the time step. The corresponding sampling frequency is:

`f_s = 1 / dt`

If `dt = 0.001`, then:
- `f_s = 1000 Hz`
- the simulator evaluates the signal 1000 times per second

The Nyquist frequency is:

`f_N = f_s / 2`

This is the highest frequency that can be represented without ambiguity in standard sampled analysis.

## 3.2 Why dt Matters in This Project

`dt` affects multiple things at the same time.

1. Time-domain accuracy.
A smaller `dt` means more faithful tracking of fast changes.

2. Numerical stability.
If the time step is too large, a forward stepping method can become inaccurate or unstable.

3. Frequency-domain range.
The sample rate determines the highest representable frequency.

4. Frequency resolution.
Resolution depends on total duration as well as sample spacing.

5. Plot appearance.
A coarse `dt` can make waveforms look jagged or under-resolved.

## 3.3 Discretization as Approximation

In differential equations, derivatives are exact rate-of-change objects. In code, we approximate them. For example, if:

`dx/dt ≈ (x_next - x_current) / dt`

then rearranging gives the explicit Euler update:

`x_next = x_current + (dx/dt) * dt`

This simple formula is one of the most important ideas in the project, because the manual simulator uses it directly.

## 3.4 Time Vector Construction in the Project

The code builds the time axis with NumPy as an evenly spaced array from zero to the configured duration. That array is reused by signal generation, simulation, plotting, and metrics.

This is important architecturally because one shared time base keeps the whole system consistent. If separate parts of the app generated separate time bases independently, subtle bugs and mismatches would appear.

## Chapter 3 Implementation References

Code regions that embody this chapter:
- Time-base initialization in `SystemState`: `lcr_circuit_simulator.py:895-902`
- Time-base restoration during snapshot loading: `lcr_circuit_simulator.py:1245-1249`
- Signal generation uses shared time vector: `lcr_circuit_simulator.py:1313-1348`
- Manual time stepping uses `dt`: `lcr_circuit_simulator.py:1350-1388`

### Small Source Snippet: Time Vector Setup

```python
self.dt = 0.001
self.duration = 12.0
self.time = np.arange(0.0, self.duration, self.dt)
```

### Small Source Snippet: Time Vector Rebuild After Loading

```python
self.dt = float(snapshot.get("dt", self.dt))
self.duration = float(snapshot.get("duration", self.duration))
self.time = np.arange(0.0, self.duration, self.dt)
```

### Small Source Snippet: Frequency Grid Generation

```python
frequency = np.fft.rfftfreq(len(input_signal), dt)
```
# Chapter 4. The Signal Families Used by the Project

The project supports several input signal types because no single waveform reveals every useful aspect of a system.

## 4.1 Noise

Noise in this project is random-valued excitation drawn from a Gaussian distribution.

What it is:
- a stochastic signal whose sample values vary irregularly
- broad-spectrum excitation in practical finite-sample analysis

Why it exists:
- it excites many frequencies at once
- it helps reveal general frequency behavior without choosing a single pure tone

Where it is used:
- in `SignalGenerator.generate()` when `mode == "Noise"`
- as a selectable source option in the simulation controls

How it behaves:
- time domain: irregular fluctuations with no obvious smooth pattern
- frequency domain: spread energy across many bins, though not perfectly flat in any one realization

How it is generated in code:
- the code uses `self.rng.normal(...)`
- the standard deviation scales with `amplitude`
- the result is shifted by `offset`

## 4.2 Sine

The sine wave is the canonical pure tone:

`x(t) = offset + A * sin(2*pi*f*t)`

Symbol-by-symbol explanation:
- `A` is amplitude
- `f` is frequency in hertz
- `t` is time
- `offset` is the DC shift

Why it exists:
- it isolates one frequency
- it is the cleanest waveform for understanding phase and gain at a single tone

Time-domain intuition:
- smooth periodic oscillation
- equal positive and negative curvature over each cycle when offset is zero

Frequency-domain intuition:
- one dominant frequency component at the chosen tone

## 4.3 Multi-Sine

The multi-sine signal is a sum of several sinusoids with different weights and phases.

Why it exists:
- it excites multiple frequencies deterministically
- it is often more informative than a single sine while remaining more structured than noise

How it behaves:
- time domain: a richer periodic or quasi-periodic waveform
- frequency domain: several discrete peaks at the constituent frequencies

## 4.4 Step

A step changes level abruptly after a chosen instant.

Why it exists:
- transient response is often most clearly seen under a step input
- rise time, settling time, overshoot, and peak time become meaningful under this kind of excitation

Time-domain intuition:
- one sudden transition followed by system adjustment

Frequency-domain intuition:
- broad spectral content because sharp transitions require many frequencies

## 4.5 Square

A square wave is generated in this project from the sign of a sine.

Why it exists:
- it is a classic switching-like excitation
- it carries strong harmonic content

How it behaves:
- time domain: repeated abrupt high/low transitions
- frequency domain: strong fundamental plus harmonics

## 4.6 Pulse

The pulse mode creates a periodic waveform that remains high for part of each cycle and low for the rest.

Why it exists:
- it lets the user explore duty-cycle effects
- it provides a more adjustable switching-style input than a symmetric square wave

Important parameter:
- `pulse_width`, which controls the fraction of the period spent high

## 4.7 Impulse

A perfect mathematical impulse is not directly representable in sampled code. The project therefore approximates an impulse by placing a large value in the first sample so the finite-sampled area remains meaningful.

Why it exists:
- an impulse is deeply connected to system identification and impulse response thinking
- it excites many frequencies at once

## 4.8 Chirp

A chirp is a frequency sweep over time. Its phase law in the code is based on:

`phase(t) = 2*pi*(f0*t + 0.5*k*t^2)`

where:
- `f0` is the starting frequency
- `k` is the sweep rate

Why it exists:
- it provides a smooth sweep across a frequency band
- it is especially useful for visually believable transfer-function plots

Time-domain intuition:
- oscillation whose rate increases with time

Frequency-domain intuition:
- the input energy sweeps across a range rather than concentrating on one tone

## 4.9 Why the Project Needs Multiple Signal Families

Different questions require different inputs.
- “What is the transient step response?” needs a step.
- “What is the phase shift at one tone?” needs a sine.
- “What is the response across a band?” often benefits from chirp or multi-sine.
- “What happens under stochastic excitation?” uses noise.

This is why the project exposes signal type as a first-class user control rather than hard-coding one waveform.

## Chapter 4 Implementation References

Code regions that embody this chapter:
- Signal vocabulary: `lcr_circuit_simulator.py:52`
- Signal settings in state: `lcr_circuit_simulator.py:874-883`, `lcr_circuit_simulator.py:1103-1125`
- Signal synthesis: `lcr_circuit_simulator.py:1309-1348`

### Small Source Snippet: Supported Signal Names

```python
SIGNAL_OPTIONS = ["Noise", "Sine", "Multi-Sine", "Step", "Square", "Pulse", "Impulse", "Chirp"]
```

### Small Source Snippet: Signal Settings API

```python
if amplitude is not None:
    self.signal_amplitude = max(float(amplitude), 0.0)
if frequency is not None:
    self.signal_frequency = max(float(frequency), 0.01)
if pulse_width is not None:
    self.pulse_width = min(max(float(pulse_width), 0.01), 0.95)
```

### Small Source Snippet: Waveform Dispatch Logic

```python
if mode == "Sine":
    return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
if mode == "Step":
    step_time = time_vector[0] + max(time_vector[-1] - time_vector[0], 1e-9) * 0.08
    return offset + amplitude * (time_vector >= step_time).astype(float)
if mode == "Chirp":
    sweep_rate = (max(state.chirp_end_frequency, base_frequency) - base_frequency) / max(time_vector[-1] - time_vector[0], 1e-6)
    phase = 2.0 * np.pi * (base_frequency * time_vector + 0.5 * sweep_rate * np.square(time_vector))
    return offset + amplitude * np.sin(phase)
```

# Chapter 5. Numerical Simulation Logic: How the Manual Solver Turns Equations into Arrays

The reduced-circuit manual solver is one of the clearest places where mathematics becomes executable code.

## 5.1 State Variables

The solver tracks two evolving state quantities:
- `charge`
- `current`

Why those variables were chosen:
- capacitor voltage is naturally related to charge
- inductor voltage is naturally related to rate of change of current
- together, charge and current capture the key energy-storage state of the reduced RLC model

## 5.2 Effective Resistance and Non-Ideal Losses

The code constructs an `effective_resistance` by summing:
- nominal circuit resistance
- source resistance
- inductor series resistance
- capacitor ESR

Why this exists:
- real systems are not ideal
- parasitic losses affect damping and realism
- the app explicitly includes those knobs so the user can study non-ideal behavior

## 5.3 Step-by-Step Logic of the Manual Solver

Within the loop over the excitation array, the solver performs the following logic.

1. `dqdt = current`
   Why: current is the time derivative of charge.

2. `capacitor_drop = inv_c * charge`
   Why: capacitor voltage can be reconstructed from charge divided by capacitance.

3. `resistive_drop = effective_resistance * current`
   Why: Ohm’s law gives the voltage lost to dissipative elements.

4. `didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)`
   Why: the inductor equation is rearranged to solve for current derivative.

5. `charge += dqdt * dt`
   Why: explicit Euler integration step for charge.

6. `current += didt * dt`
   Why: explicit Euler integration step for current.

Then the code stores traces for later plotting and metric extraction.

## 5.4 Why This Is an Approximation and Not an Exact Solution

The solver is not doing symbolic calculus. It is doing finite-step approximation. This is important because users and developers must understand the limitations.

- smaller `dt` usually improves fidelity
- large `dt` can distort or destabilize dynamic behavior
- output accuracy depends on sampling choices as well as equations

## 5.5 Why Component Trace Dictionaries Are Stored

The result object stores:
- `component_voltages`
- `component_currents`

This is not just a convenience. It is what enables the trace selector in the simulation page. Without those dictionaries, the UI would be limited to one raw output trace.

## Chapter 5 Implementation References

Code regions that embody this chapter:
- Loss settings in state: `lcr_circuit_simulator.py:1127-1139`
- `SimulationResult`: `lcr_circuit_simulator.py:795-804`
- `SimulationEngine.run()`: `lcr_circuit_simulator.py:1350-1388`

### Small Source Snippet: Loss-Model Controls

```python
if source_resistance is not None:
    self.source_resistance = max(float(source_resistance), 0.0)
if inductor_series_resistance is not None:
    self.inductor_series_resistance = max(float(inductor_series_resistance), 0.0)
if capacitor_esr is not None:
    self.capacitor_esr = max(float(capacitor_esr), 0.0)
```

### Small Source Snippet: Simulation Result Structure

```python
class SimulationResult:
    time: np.ndarray
    input_signal: np.ndarray
    current: np.ndarray
    charge: np.ndarray
    component_voltages: dict[str, np.ndarray] = field(default_factory=dict)
    component_currents: dict[str, np.ndarray] = field(default_factory=dict)
```

### Small Source Snippet: Manual Integration Loop

```python
for index, source_voltage in enumerate(excitation):
    dqdt = current
    capacitor_drop = inv_c * charge
    resistive_drop = effective_resistance * current
    didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
    charge += dqdt * dt
    current += didt * dt
```

# Chapter 6. Convolution, Fourier Transform, FFT, Window Functions, and Spectral Leakage

This chapter is one of the most important conceptual chapters in the whole documentation because it explains why the project can move between time-domain thinking and frequency-domain thinking.

## 6.1 Convolution from First Principles

If a system is linear and time-invariant, then the output can be described as the convolution of the input with the system’s impulse response.

Continuous-time form:

`y(t) = integral( x(tau) * h(t - tau) d tau )`

Discrete-time form:

`y[n] = sum_k x[k] * h[n-k]`

Why convolution works conceptually:
- the impulse response describes how the system reacts to one ideal concentrated input event
- any input can be thought of as a weighted combination of shifted impulses
- because the system is linear and time-invariant, the total response is the sum of shifted impulse responses weighted by the input

Why this matters in the project:
- even when the code does not call a direct long convolution in the main path, the graph solver’s frequency-domain multiplication followed by inverse FFT is the dual expression of the same idea

## 6.2 Fourier Transform Intuition

The Fourier transform decomposes a signal into sinusoidal components. Instead of asking “what is the value at time t?” it asks “how much of each frequency is present?”

For sampled data, the practical tool is the discrete Fourier transform and its fast implementation, the FFT.

## 6.3 FFT in the Project

The project uses `np.fft.rfft()` for real-valued signals.

Why `rfft` is used:
- the input arrays are real
- for real signals, negative-frequency content is redundant information
- `rfft` is more efficient and directly produces the nonnegative-frequency half-spectrum that the UI needs

The frequency axis is created with `np.fft.rfftfreq(...)`.

## 6.4 Transfer Function Estimation

The FFT processor estimates the transfer function by computing:

`transfer = output_spectrum / input_spectrum`

but only on bins with sufficient input excitation.

Why thresholding is needed:
- if the input contains almost no energy at a bin, dividing by that tiny number creates nonsense or numerical blow-up
- the threshold prevents low-excitation bins from dominating the result with meaningless values

## 6.5 Window Functions and Why the Hann Window Is Needed

A finite sampled record is not the same as an infinitely repeating periodic signal. But the FFT effectively treats the sampled block as if it repeats. If the start and end of the block do not align smoothly, the implied repetition creates a discontinuity at the record boundary.

That discontinuity spreads energy across frequency bins. This spreading is spectral leakage.

The Hann window reduces leakage by tapering the beginning and end of the record toward zero.

Why that helps:
- smoother boundaries mean smaller artificial jumps at repetition boundaries
- smaller jumps mean less leakage into unrelated bins

Trade-off:
- peak shapes broaden somewhat
- amplitude interpretation changes slightly
- but the overall estimate becomes more stable and more visually meaningful

## 6.6 Magnitude, Phase, and Unwrapping

Magnitude is computed from the absolute value of the complex transfer.
Phase is computed from the complex angle.
Phase is then unwrapped so that jumps of `2*pi` do not create visually misleading sawtooth discontinuities.

## 6.7 Moving-Average Smoothing

The processor smooths magnitude with a moving average implemented through convolution.

Why smoothing exists:
- raw estimates can be jagged due to noise, limited duration, sparse excitation, or spectral fluctuations
- smoothing provides a more readable engineering trend without changing the core solver path

## Chapter 6 Implementation References

Code regions that embody this chapter:
- FFT processor: `lcr_circuit_simulator.py:1393-1417`
- Graph spectral simulation: `lcr_circuit_simulator.py:1457-1487`
- Plot update in transfer-function mode: `lcr_circuit_simulator.py:1753-1783`

### Small Source Snippet: Windowing and Transfer Estimation

```python
window = np.hanning(len(input_signal))
spectrum_in = np.fft.rfft(input_signal * window)
spectrum_out = np.fft.rfft(output_signal * window)
frequency = np.fft.rfftfreq(len(input_signal), dt)
transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]
```

### Small Source Snippet: Frequency-Domain Multiplication Back to Time Domain

```python
input_spectrum = np.fft.rfft(input_signal)
output_spectrum = graph_result.transfer * input_spectrum
current = np.fft.irfft(output_spectrum, n=len(input_signal))
```

### Small Source Snippet: Transfer Plot Update

```python
self.magnitude_line.set_data(frequency, magnitude)
self.phase_line.set_data(frequency, phase)
self.peak_label.set_text(f"Peak  {peak_x:.3f} Hz\\nGain  {peak_y:.3f}")
```
# Chapter 7. Graph Representation, Topology Detection, and Why Builder State Must Become a Circuit Graph

The builder canvas is not the same thing as an electrical graph. A user sees boxes and wires placed in a 2D workspace. The solver, however, needs node relationships and element connectivity independent of screen position.

This is why the project defines a graph layer.

Important graph-level dataclasses:
- `Node`
- `GraphComponent`
- `CircuitGraph`
- `TopologyAnalysis`

## 7.1 Why a Graph Representation Exists

A circuit is fundamentally about connectivity, not screen coordinates. Two components drawn far apart can still belong to the same electrical node if wires and junctions connect them. Conversely, two components drawn near each other may be electrically unrelated.

Therefore the code must translate:
- visual terminals -> equivalence classes of electrically identical terminals
- equivalence classes -> node IDs
- component bodies -> graph edges between nodes

## 7.2 Union-Find Style Parsing

The parser uses a union-find-like process.

Conceptually:
1. treat every terminal as separate initially
2. unify all terminals belonging to the same explicit `Node` component
3. unify terminals connected by wires
4. collapse roots into node IDs such as `N1`, `N2`, etc.

This is elegant because it separates the question “which terminals are electrically the same?” from the later question “which components connect which nodes?”

## 7.3 Containers and Recursive Expansion

Containers complicate the story because they can represent nested series or parallel substructures.

The parser must decide whether a container:
- reduces to one equivalent component
- or expands into multiple graph elements and internal nodes

That is why `_expand_child_spec_to_graph()` is recursive. A nested container may contain other nested containers, which themselves may or may not reduce cleanly.

## 7.4 Topology Analysis and Floating Nodes

Once a graph exists, the code analyzes whether it is usable.

The analysis checks:
- whether there is exactly one source
- whether invalid containers are present
- whether passive components exist
- whether source terminals collapse into the same node
- whether floating nodes exist
- whether the topology matches reducible series/parallel families
- whether the network should instead be treated as a general graph network

Why floating-node detection is important:
- a circuit can be visually plausible but electrically incomplete
- if part of the graph is disconnected from the source-connected network, simulation results would be misleading or undefined

## 7.5 Series and Parallel Family Recognition

The project recognizes classical families using graph predicates.

Parallel-family recognition checks whether the passive network can be decomposed into branches between the same two source nodes.
Series-family recognition checks whether the passive network forms a source-to-source chain with appropriate node degrees.

This is a strong example of “how” and “where” mattering more than labels alone. The system does not merely name a topology based on component counts. It checks actual connectivity.

## Chapter 7 Implementation References

Code regions that embody this chapter:
- Graph dataclasses: `lcr_circuit_simulator.py:122-156`
- Graph-building helpers: `lcr_circuit_simulator.py:158-551`
- Topology analysis and family detection: `lcr_circuit_simulator.py:553-764`

### Small Source Snippet: Graph Data Structures

```python
class GraphComponent:
    id: str
    type: str
    value: float
    node1: str
    node2: str
    display_name: str
```

### Small Source Snippet: Builder State to Graph Conversion

```python
root_a = find(f"{component.component_id}:{terminal_names[0]}")
root_b = find(f"{component.component_id}:{terminal_names[1]}")
node_a = root_to_node_id.setdefault(root_a, f"N{len(root_to_node_id) + 1}")
node_b = root_to_node_id.setdefault(root_b, f"N{len(root_to_node_id) + 1}")
```

### Small Source Snippet: Topology Analysis Entry Point

```python
sources = [component for component in graph.components if component.type == "Source"]
if len(sources) != 1:
    return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)
```

# Chapter 8. Graph-Network Solving, Admittance Thinking, and the Mixed-Topology Path

When a circuit cannot be reduced to one equivalent `L`, `C`, and `R` triplet, the project uses graph-based nodal analysis.

## 8.1 Why Admittance Is Used

In AC or frequency-domain analysis, two equivalent languages are common:
- impedance language
- admittance language

Admittance is the reciprocal of impedance and is especially convenient for nodal analysis because currents at a node can be expressed naturally through admittance relationships.

In the code:
- resistor admittance is `1/R`
- inductor admittance is the reciprocal of `R_series + j*omega*L`
- capacitor admittance is the reciprocal of `R_esr - j/(omega*C)`

## 8.2 Frequency-by-Frequency Solving

The graph solver does not solve one giant symbolic expression for all frequencies. Instead, it iterates across the frequency grid and solves one linear system per frequency.

Why this is reasonable:
- the equations depend on `omega`
- a numerical frequency sweep is straightforward and robust
- the resulting transfer arrays can later be analyzed or transformed back into time-domain traces

## 8.3 Matrix Stamping

Matrix stamping means adding each component’s contribution into the system matrix.

Conceptually:
- diagonal terms collect self-admittances connected to a node
- off-diagonal terms collect negative mutual coupling between connected nodes

The source adds an additional equation so that a known voltage relation is enforced while source current becomes part of the solved state.

## 8.4 Reconstructing Time-Domain Behavior from the Graph Solver

After solving the transfer behavior in frequency space, the code multiplies that transfer spectrum by the input signal’s spectrum and applies inverse FFT.

Why this works:
- multiplication in the frequency domain corresponds to convolution in the time domain
- the transfer spectrum therefore acts like a filtering description of the circuit

This is one of the deepest places where theory, signal processing, and implementation meet directly.

## Chapter 8 Implementation References

Code regions that embody this chapter:
- Graph solver entry points: `lcr_circuit_simulator.py:1420-1487`
- Frequency-specific solve path: `lcr_circuit_simulator.py:1489-1516`
- Admittance conversion: `lcr_circuit_simulator.py:1518-1527`
- Matrix stamping: `lcr_circuit_simulator.py:1529-1544`

### Small Source Snippet: Frequency Sweep Solve Loop

```python
for index, freq_hz in enumerate(frequency):
    solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
    transfer[index] = solution["source_current"]
```

### Small Source Snippet: Single-Frequency Matrix Solve

```python
try:
    solution = np.linalg.solve(matrix, vector)
except np.linalg.LinAlgError:
    return None
```

### Small Source Snippet: Admittance and Stamping Logic

```python
if index_a is not None:
    matrix[index_a, index_a] += admittance
if index_b is not None:
    matrix[index_b, index_b] += admittance
if index_a is not None and index_b is not None:
    matrix[index_a, index_b] -= admittance
    matrix[index_b, index_a] -= admittance
```

# Chapter 9. Metrics, Plot Meaning, and How the User Learns from the Output

A simulator is not complete when it computes arrays. It becomes useful when it presents interpretable behavior.

## 9.1 Steady-State Metrics

The analyzer extracts:
- resonance frequency
- peak gain
- quality factor
- damping ratio
- system type

Why these metrics matter:
- they summarize response shape in compact form
- they make comparison easier across circuits and parameter changes
- they convert a graph into engineering language

Quality factor intuition:
- high `Q` usually means narrow and sharp resonant behavior
- low `Q` usually means broader and more damped behavior

Damping ratio intuition:
- underdamped systems oscillate or ring visibly
- critically damped systems return quickly without oscillation
- overdamped systems return slowly without oscillation

## 9.2 Transient Metrics

The transient analyzer extracts:
- rise time
- settling time
- overshoot
- peak time

These depend on the shape of the time-domain response and are especially meaningful under step-like excitation.

## 9.3 Plot Interpretation

Transfer-function view:
- x-axis: frequency in hertz
- top plot y-axis: gain magnitude
- bottom plot y-axis: phase in radians

Signal-response view:
- x-axis: time in seconds
- top plot y-axis: input excitation amplitude
- bottom plot y-axis: selected output trace amplitude

Why curves look the way they do:
- jagged magnitude may come from noisy excitation or sparse energy distribution
- a smooth chirp-driven curve often looks more believable because more of the band is excited in an orderly way
- a resonance near the right edge may indicate the true peak lies outside the displayed range
- phase curves often shift sharply near resonant regions because storage elements alter timing relationships between input and output

## 9.4 Overlay and Watermark Behavior

The excitation overlay is contextual information, not the actual transfer magnitude.
The watermark is a plot-embedded brand mark that appears both on screen and in exported PNG files.

## Chapter 9 Implementation References

Code regions that embody this chapter:
- `Analyzer.analyze()`: `lcr_circuit_simulator.py:1573-1599`
- `Analyzer.analyze_transient()`: `lcr_circuit_simulator.py:1601-1637`
- `PlotManager` styling and rendering: `lcr_circuit_simulator.py:1677-1884`
- Metric updates in simulation refresh: `lcr_circuit_simulator.py:2383-2395`

### Small Source Snippet: Steady-State Metrics

```python
peak_index = int(np.argmax(magnitude))
resonance_hz = float(frequency[peak_index])
peak_gain = float(magnitude[peak_index])
```

### Small Source Snippet: Transient Metrics

```python
final_value = float(np.mean(output_trace[-max(len(output_trace) // 10, 1) :]))
peak_index = int(np.argmax(np.abs(output_trace)))
peak_time = float(simulation.time[peak_index])
```

### Small Source Snippet: Plot Styling and Watermarking

```python
axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
self._add_watermark(axis)
```

# Chapter 10. The Simulation Page, Builder Canvas, Controller, and the Full System Map

At this point the reader knows the concepts. This chapter explains how the whole application is wired together.

## 10.1 The Simulation Page as a Scientific Console

`SimulationPage` is where the user’s settings become executed experiments.

Its refresh pipeline does the following:
- reads control values
- writes them into `SystemState`
- interprets the builder circuit
- parses the graph
- decides whether graph mode or manual mode should run
- generates the excitation
- runs simulation
- computes metrics
- updates plots and cards

This is the central operational pipeline of the entire app.

## 10.2 The Builder Canvas as a Visual Circuit Authoring Tool

`CircuitCanvas` owns:
- drawing
- selection
- dragging
- connection preview
- zooming
- panning
- centering
- component rendering
- container rendering
- export behavior

Why this matters:
- the builder is not a passive sketch pad
- it is the front-end authoring layer for a real electrical graph model

## 10.3 The Controller as System Orchestrator

`AppController` ties the whole project together.

It configures:
- the root window
- styles
- page shell
- startup preset
- status bar
- save/load
- undo/redo
- page navigation
- workspace reset behavior

## 10.4 Reworked Atlas Embedded as a System Map

The source file can be understood in this layered order:
- global vocabulary and presets: `1-119`
- graph structures and parsing: `122-764`
- runtime-state objects and persistence: `765-1307`
- scientific engines: `1309-1676`
- plotting and small UI primitives: `1677-1990`
- simulation page: `1991-2599`
- builder canvas and builder page: `2600-4122`
- controller and entry point: `4123-4370`

That is the atlas, but it is placed here only after the reader has learned enough for the map to be meaningful.

## 10.5 Final Learning Outcome

By the end of the project, a reader should be able to explain:
- what each signal family means physically and mathematically
- how the manual solver approximates time-domain dynamics
- why FFT, windowing, and spectral leakage matter
- how the graph parser turns canvas state into circuit structure
- how topology recognition determines solver choice
- how graph nodal solving works frequency by frequency
- how plots and metrics translate computation into understanding
- how the controller coordinates the entire application

## Chapter 10 Implementation References

Code regions that embody this chapter:
- `SimulationPage`: `lcr_circuit_simulator.py:1991-2599`
- `CircuitCanvas`: `lcr_circuit_simulator.py:2600-3672`
- Builder support classes: `lcr_circuit_simulator.py:3674-4122`
- `AppController` and `main()`: `lcr_circuit_simulator.py:4123-4370`

### Small Source Snippet: Simulation Refresh Pipeline

```python
interpretation = CircuitInterpreter().interpret(self.state)
self.state.update_derived_parameters(interpretation)
graph = parse_system_state(self.state)
graph_analysis = analyze_circuit(graph) if self.state.components else None
```

### Small Source Snippet: Canvas Initial Centering and Redraw Flow

```python
if self._pending_initial_center and self.state.components:
    width = self.canvas.winfo_width()
    height = self.canvas.winfo_height()
    if width > 64 and height > 64:
        self._pending_initial_center = False
        self.center_view()
        return
```

### Small Source Snippet: Preset Loading and Page Coordination

```python
self.state.clear_circuit()
for component_type, x, y, value in preset["components"]:
    component = self.state.add_component(component_type, x, y, value)
self.pages["builder"].canvas_workspace.center_view()
self.pages["simulation"].sync_from_state()
```
# Appendix 1. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 1:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 2. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 2:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 3. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 3:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 4. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 4:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 5. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 5:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 6. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 6:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

## Lifetime Simulation & Failure Modeling

### Snapshot vs Lifetime

- Snapshot mode asks: "Is the system alive at time `t`?"
- Lifetime mode asks: "When does the system fail?"
- Snapshot outputs reliability curves at selected time points.
- Lifetime outputs a distribution of failure time and an empirical reliability curve from sampled failure events.

### Failure Time Formula

For an exponential component failure model with constant failure rate `lambda`:

- Draw `U ~ Uniform(0, 1)`
- Compute failure time:
  - `t_fail = -ln(U) / lambda`

This maps uniform randomness into exponentially distributed time-to-failure samples.

### System Failure Rules

- Series block:
  - System fails when the first child fails.
  - `T_system = min(T_1, T_2, ..., T_n)`
- Parallel block:
  - System fails when the last surviving branch fails.
  - `T_system = max(T_1, T_2, ..., T_n)`
- Nested topologies are evaluated recursively using the same series/parallel rules.

### Reliability Outputs

Given `N` sampled lifetime trials:

- Lifetime histogram shows the spread of failure times.
- Empirical reliability is estimated as:
  - `R(t) = P(T > t)`
  - Numerically: count of samples with failure time greater than `t`, divided by `N`.

### Practical Interpretation

- Snapshot mode is useful for warranty checkpoints and fixed-time compliance decisions.
- Lifetime mode is useful for understanding failure timing, spread, and tail behavior.
- Editing component lambda immediately changes both modes, enabling design tradeoff studies (cost vs reliability vs warranty horizon).

# Appendix 7. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 7:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 8. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 8:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 9. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 9:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 10. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 10:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 11. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 11:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 12. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 12:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 13. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 13:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 14. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 14:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 15. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 15:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 16. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 16:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 17. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 17:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 18. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 18:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 19. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 19:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 20. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 20:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 21. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 21:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 22. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 22:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 23. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 23:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 24. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 24:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 25. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 25:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 26. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 26:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 27. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 27:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 28. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 28:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 29. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 29:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 30. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 30:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 31. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 31:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 32. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 32:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 33. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 33:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 34. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 34:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 35. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 35:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 36. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 36:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 37. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 37:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 38. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 38:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 39. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 39:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 40. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 40:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 41. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 41:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 42. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 42:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 43. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 43:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 44. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 44:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 45. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 45:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 46. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 46:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 47. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 47:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 48. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 48:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 49. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 49:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 50. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 50:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 51. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 51:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 52. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 52:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 53. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 53:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 54. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 54:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 55. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 55:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 56. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 56:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 57. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 57:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 58. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 58:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 59. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 59:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 60. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 60:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 61. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 61:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 62. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 62:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 63. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 63:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 64. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 64:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 65. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 65:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 66. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 66:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 67. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 67:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 68. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 68:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 69. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 69:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 70. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 70:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 71. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 71:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 72. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 72:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 73. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 73:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 74. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 74:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 75. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 75:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 76. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 76:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 77. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 77:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 78. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 78:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 79. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 79:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 81. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 81:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 82. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 82:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 83. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 83:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 84. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 84:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 85. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 85:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 86. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 86:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 87. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 87:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 88. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 88:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 89. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 89:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 90. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 90:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 91. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 91:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 92. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 92:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 93. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 93:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 94. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 94:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 95. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 95:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 96. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 96:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 97. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 97:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 98. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 98:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 99. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 99:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 100. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 100:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 101. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 101:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 102. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 102:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

# Appendix 103. Guided Expansion on plot semantics and interpretation

## What This Appendix Is About

This appendix revisits the concept of plot semantics and interpretation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why plot semantics and interpretation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. plot semantics and interpretation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand plot semantics and interpretation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About plot semantics and interpretation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 103:
A user changes one control and reruns the simulation. If that control affects plot semantics and interpretation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to plot semantics and interpretation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1677-1884`
- `lcr_circuit_simulator.py:1817-1826`
- `lcr_circuit_simulator.py:1840-1854`

## Small Source Snippet A

```python
widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)
        self._add_watermark(axis)

    def _add_watermark(self, axis) -> None:
        axis.text(
            0.985,
            0.035,
            "Powered by Mayank Jindal",
```

## Small Source Snippet B

```python
self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
```

## Small Source Snippet C

```python
overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, plot semantics and interpretation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain plot semantics and interpretation in your own words without using the project’s class names?
- Can you point to at least one code region where plot semantics and interpretation is implemented directly?
- Can you explain how plot semantics and interpretation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if plot semantics and interpretation were misunderstood?

# Appendix 104. Guided Expansion on builder interaction and visual circuit authoring

## What This Appendix Is About

This appendix revisits the concept of builder interaction and visual circuit authoring from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why builder interaction and visual circuit authoring Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. builder interaction and visual circuit authoring matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand builder interaction and visual circuit authoring, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About builder interaction and visual circuit authoring

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 104:
A user changes one control and reruns the simulation. If that control affects builder interaction and visual circuit authoring, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to builder interaction and visual circuit authoring, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:2600-3672`
- `lcr_circuit_simulator.py:3842-4122`
- `lcr_circuit_simulator.py:4229-4257`

## Small Source Snippet A

```python
class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._pending_initial_center = True

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
```

## Small Source Snippet B

```python
class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
```

## Small Source Snippet C

```python
self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, builder interaction and visual circuit authoring would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain builder interaction and visual circuit authoring in your own words without using the project’s class names?
- Can you point to at least one code region where builder interaction and visual circuit authoring is implemented directly?
- Can you explain how builder interaction and visual circuit authoring affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if builder interaction and visual circuit authoring were misunderstood?

# Appendix 105. Guided Expansion on signals and system thinking

## What This Appendix Is About

This appendix revisits the concept of signals and system thinking from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why signals and system thinking Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. signals and system thinking matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand signals and system thinking, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About signals and system thinking

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 105:
A user changes one control and reruns the simulation. If that control affects signals and system thinking, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to signals and system thinking, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:867-902`
- `lcr_circuit_simulator.py:1309-1348`
- `lcr_circuit_simulator.py:1991-2396`

## Small Source Snippet A

```python
class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
```

## Small Source Snippet B

```python
def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
```

## Small Source Snippet C

```python
self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, signals and system thinking would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain signals and system thinking in your own words without using the project’s class names?
- Can you point to at least one code region where signals and system thinking is implemented directly?
- Can you explain how signals and system thinking affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if signals and system thinking were misunderstood?

# Appendix 106. Guided Expansion on sampling and time-step design

## What This Appendix Is About

This appendix revisits the concept of sampling and time-step design from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why sampling and time-step design Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. sampling and time-step design matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand sampling and time-step design, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About sampling and time-step design

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 106:
A user changes one control and reruns the simulation. If that control affects sampling and time-step design, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to sampling and time-step design, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:895-902`
- `lcr_circuit_simulator.py:1245-1249`
- `lcr_circuit_simulator.py:1397-1400`

## Small Source Snippet A

```python
self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
```

## Small Source Snippet B

```python
"message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
```

## Small Source Snippet C

```python
spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, sampling and time-step design would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain sampling and time-step design in your own words without using the project’s class names?
- Can you point to at least one code region where sampling and time-step design is implemented directly?
- Can you explain how sampling and time-step design affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if sampling and time-step design were misunderstood?

# Appendix 107. Guided Expansion on RLC physics and state evolution

## What This Appendix Is About

This appendix revisits the concept of RLC physics and state evolution from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why RLC physics and state evolution Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. RLC physics and state evolution matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand RLC physics and state evolution, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About RLC physics and state evolution

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 107:
A user changes one control and reruns the simulation. If that control affects RLC physics and state evolution, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to RLC physics and state evolution, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1350-1388`
- `lcr_circuit_simulator.py:1127-1139`
- `lcr_circuit_simulator.py:1573-1599`

## Small Source Snippet A

```python
class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
```

## Small Source Snippet B

```python
*,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
```

## Small Source Snippet C

```python
def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, RLC physics and state evolution would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain RLC physics and state evolution in your own words without using the project’s class names?
- Can you point to at least one code region where RLC physics and state evolution is implemented directly?
- Can you explain how RLC physics and state evolution affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if RLC physics and state evolution were misunderstood?

# Appendix 108. Guided Expansion on FFT and transfer estimation

## What This Appendix Is About

This appendix revisits the concept of FFT and transfer estimation from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why FFT and transfer estimation Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. FFT and transfer estimation matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand FFT and transfer estimation, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About FFT and transfer estimation

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 108:
A user changes one control and reruns the simulation. If that control affects FFT and transfer estimation, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to FFT and transfer estimation, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1393-1417`
- `lcr_circuit_simulator.py:1457-1487`
- `lcr_circuit_simulator.py:1753-1783`

## Small Source Snippet A

```python
class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")
```

## Small Source Snippet B

```python
impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
```

## Small Source Snippet C

```python
self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, FFT and transfer estimation would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain FFT and transfer estimation in your own words without using the project’s class names?
- Can you point to at least one code region where FFT and transfer estimation is implemented directly?
- Can you explain how FFT and transfer estimation affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if FFT and transfer estimation were misunderstood?

# Appendix 109. Guided Expansion on graph parsing and topology analysis

## What This Appendix Is About

This appendix revisits the concept of graph parsing and topology analysis from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph parsing and topology analysis Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph parsing and topology analysis matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph parsing and topology analysis, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph parsing and topology analysis

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 109:
A user changes one control and reruns the simulation. If that control affects graph parsing and topology analysis, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph parsing and topology analysis, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:295-408`
- `lcr_circuit_simulator.py:553-764`
- `lcr_circuit_simulator.py:1638-1676`

## Small Source Snippet A

```python
def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )
```

## Small Source Snippet B

```python
def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )
```

## Small Source Snippet C

```python
class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph parsing and topology analysis would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph parsing and topology analysis in your own words without using the project’s class names?
- Can you point to at least one code region where graph parsing and topology analysis is implemented directly?
- Can you explain how graph parsing and topology analysis affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph parsing and topology analysis were misunderstood?

# Appendix 110. Guided Expansion on graph-network nodal solving

## What This Appendix Is About

This appendix revisits the concept of graph-network nodal solving from a slower, more tutorial angle. The purpose of the repetition is not redundancy for its own sake. The purpose is to help a beginner internalize the idea through multiple explanations, multiple examples, and multiple links back into the implementation.

## Why graph-network nodal solving Matters in This Project

The simulator is not a collection of isolated tricks. It is a chain of transformations. graph-network nodal solving matters because it changes how the chain behaves, how the user interprets results, and how the code chooses algorithms. If the reader does not understand graph-network nodal solving, then later chapters can still be read, but they will not feel connected into one system.

## How to Think About graph-network nodal solving

A useful learning technique is to imagine asking four questions every time this concept appears.

1. What is the idea in plain language?
2. Why did the author need it in the project?
3. How does it change data, equations, or control flow?
4. Where in the code should I look to see it directly?

This appendix keeps those four questions visible on purpose.

## Worked Example

Example scenario 110:
A user changes one control and reruns the simulation. If that control affects graph-network nodal solving, then the numerical arrays change, the analyzer may produce different metrics, the plot may change shape, and the user may draw a different engineering conclusion. This chain is exactly what scientific software is for: one conceptual change leading to a visible change in behavior.

## Graph and Visual Interpretation Note

When reading a graph related to graph-network nodal solving, never ask only “what curve is drawn?” Ask also:
- what is on the horizontal axis?
- what quantity is on the vertical axis?
- is the curve a raw measurement, a smoothed measurement, a derived transfer estimate, or an overlay?
- is the behavior expected from theory, or does it reveal a modeling or setup limitation?

That discipline is especially important in this simulator because transfer-function plots, signal-response plots, overlays, and metrics coexist in the same interface.

## Code Reference Map

Primary reference set for this appendix:
- `lcr_circuit_simulator.py:1419-1570`
- `lcr_circuit_simulator.py:1518-1544`
- `lcr_circuit_simulator.py:2383-2395`

## Small Source Snippet A

```python
class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
```

## Small Source Snippet B

```python
try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
```

## Small Source Snippet C

```python
self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
```

## How This Helps the Reader Rebuild the Project

If the reader wanted to rebuild the project independently, graph-network nodal solving would not be optional. It would become one of the design decisions to be made explicitly. That is why the appendix ends by restating the reconstruction lesson: concepts are not ornaments around the code; they are the reasons the code exists in its current form.

## Review Questions

- Can you explain graph-network nodal solving in your own words without using the project’s class names?
- Can you point to at least one code region where graph-network nodal solving is implemented directly?
- Can you explain how graph-network nodal solving affects a graph, waveform, metric, or UI behavior?
- Can you explain what would break or become misleading if graph-network nodal solving were misunderstood?

