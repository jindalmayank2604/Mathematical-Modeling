import math
import random 
import matplotlib.pyplot as plt

class Node:
    def reliability(self, t):
        pass
    def simulate(self, t):
        pass

class Component(Node):
    def __init__(self, name, faliure_rate):
        self.name = name
        self.lambda_ = faliure_rate

    def reliability(self, t):
        return math.exp(-self.lambda_*t)
    
    def simulate(self, t):
        prob_fail = 1-math.exp(-self.lambda_*t)
        return random.random() >= prob_fail # Survived or Not 
    
class Series(Node):
    def __init__(self, *nodes):
        self.nodes = nodes

    def reliability(self, t):
        R = 1
        for node in self.nodes:
            R *= node.reliability(t)

        return R
    
    def simulate(self, t):
        for node in self.nodes:
            if not node.simulate(t):
                return False
            
        return True 
    
class Parallel(Node):
    def __init__(self, *nodes):
        self.nodes = nodes

    def reliability(self, t):
        product = 1
        for node in self.nodes:
            product *= (1 - node.reliability(t))
        return 1 - product

    def simulate(self, t):
        for node in self.nodes:
            if node.simulate(t):
                return True  # any survives -> system survives
        return False
    
def monte_carlo(system, t, trials=5000):
    survived = 0
    for _ in range(trials):
        if system.simulate(t):
            survived += 1
    return survived / trials

def calculate_warranty(system, target_R):
    # binary search (works for ANY topology)
    low, high = 0, 10000

    while high - low > 1:
        mid = (low + high) / 2
        if system.reliability(mid) > target_R:
            low = mid
        else:
            high = mid

    return mid

# Series( Resistor---- Parallel(C1, C2) ---- IC )
system = Series(
    
    Parallel(
        Component("Power A", 0.000002),
        Component("Power B", 0.000002)
    ),
    
    Component("Motor", 0.000006),
    
    Parallel(
        Component("Cap A", 0.000004),
        Component("Cap B", 0.000004)
    ),
    
    Component("Bearings", 0.000004)
)

times = list(range(0, 15001, 200))
exact_vals = []
sim_vals = []

for t in times:
    exact_vals.append(system.reliability(t))
    sim_vals.append(monte_carlo(system, t))

# Run Simulation
print("Time | Exact | Simulated")
print("------------------------")

for t in range(0, 50001, 100):
    exact = system.reliability(t)
    sim = monte_carlo(system, t)

    print(f"{t:4} | {exact*100:.4f}% Survive | {sim*100:.4f}% Survive")

target_R = 0.90
warranty_time = calculate_warranty(system, target_R)

print(f"\nWarranty for {target_R*100}% reliability: {(warranty_time/24)/30:.2f} Months")

plt.figure()

plt.plot(times, exact_vals, label="Exact Reliability")
plt.plot(times, sim_vals, label="Monte Carlo")

# Warranty lines
plt.axhline(y=target_R, linestyle='--', label="Target Reliability")
plt.axvline(x=warranty_time, linestyle='--', label="Warranty Time")

plt.xlabel("Time (hours)")
plt.ylabel("Reliability")
plt.title("Reliability vs Time (Topology-Based System)")

plt.legend()
plt.grid()

plt.show()
