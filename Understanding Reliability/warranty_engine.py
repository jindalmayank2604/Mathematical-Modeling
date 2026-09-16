import math 
import random
import matplotlib.pyplot as plt


components = [
    {"name": "Resistor", "lambda": 0.00001},
    {"name": "Capacitor", "lambda": 0.00002},
    {"name": "IC", "lambda": 0.00005}
]

def exact_reliability(components, t):
    totalLambda = sum(comp["lambda"] for comp in components)
    return math.exp(-totalLambda*t)

def simulate_once(components, t):
    for comp in components:
        prob_fail = 1 - math.exp(-comp["lambda"] * t) # Formula for probability 

        if random.random() < prob_fail:
            return False  # system failed
         
    return True  # system survived

def monte_carlo(components, t, trials = 10000):
    survived = 0
    for i in range(trials):
        if simulate_once(components, t):
            survived+=1

    return survived/trials

def warranty_calc(components, target_reliability):
    totalLambda = sum(comp["lambda"] for comp in components)
    t = -math.log(target_reliability) / totalLambda
    return t

times = list(range(0, 50001, 100))
exact_values = []
sim_values = []

for t in times:
    exact_values.append(exact_reliability(components, t))
    sim_values.append(monte_carlo(components, t))

target_R = 0.9
warranty_time = warranty_calc(components, target_R)

print(f"Warranty Time for {target_R*100}% reliability: {warranty_time/24:.2f} Days")
plt.figure()

plt.plot(times, exact_values, label="Exact Reliability")
plt.plot(times, sim_values, label="Monte Carlo")

# Warranty line
plt.axhline(y=target_R, linestyle='--', label="Target Reliability")
plt.axvline(x=warranty_time, linestyle='--', label="Warranty Time")

plt.xlabel("Time (hours)")
plt.ylabel("Reliability")
plt.title("Reliability vs Time with Warranty")

plt.legend()
plt.grid()

plt.show()

