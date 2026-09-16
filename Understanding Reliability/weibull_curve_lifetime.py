import math
import random 
import matplotlib.pyplot as plt
import numpy as np

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
    
    def sample_failure_time(self):
        U = random.random()
        eta = 18000
        B = 2.2
        t_fail = eta*(-math.log(U))**(1/B)
        return t_fail

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
    
    def sample_failure_time(self):
        times = [node.sample_failure_time() for node in self.nodes]
        return min(times)
    
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
    
    def sample_failure_time(self):
        times = [node.sample_failure_time() for node in self.nodes]
        return max(times)
    

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

r1 = Component("Resistor", 0.00001)
c1 = Component("Cap A", 0.00002)
c2 = Component("Cap B", 0.00002)
ic1 = Component("IC", 0.00005)

system = Series(
    r1,
    Parallel(c1, c2),
    ic1
)
print("Sample failure times:\n")

lifetimes = []

for i in range(5000):
    lifetimes.append(system.sample_failure_time())

plt.figure()

# Histogram (normalized)
counts, bins, _ = plt.hist(
    lifetimes, bins=50, density=True,
    color='blue', alpha=0.3, label="Histogram"
)

# Bin centers
bin_centers = 0.5 * (bins[1:] + bins[:-1])

# Smooth line (connect histogram shape)
plt.plot(bin_centers, counts, color='red', label="Trend Line")

# Labels
plt.xlabel("System Failure Time (hours)")
plt.ylabel("Density")
plt.title("System Lifetime Distribution")

# Mean line
mean_life = sum(lifetimes) / len(lifetimes)
plt.axvline(mean_life, linestyle='--', label="Mean Lifetime")

plt.grid()
plt.legend()
plt.show()