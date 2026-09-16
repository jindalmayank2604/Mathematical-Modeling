import math
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

# -------------------------------
# PARAMETERS (your current model)
# -------------------------------
eta = 20000
beta = 2.2

# -------------------------------
# GENERATE LIFETIMES (Weibull)
# -------------------------------
lifetimes = []

for _ in range(5000):
    U = random.random()
    t = eta * (-math.log(U))**(1 / beta)
    lifetimes.append(t)

# -------------------------------
# FIT WEIBULL FROM DATA
# -------------------------------
shape, loc, scale = weibull_min.fit(lifetimes, floc=0)

fitted_beta = shape
fitted_eta = scale

print(f"Estimated beta: {fitted_beta:.3f}")
print(f"Estimated eta: {fitted_eta:.3f}")

# -------------------------------
# PREPARE CURVE
# -------------------------------
x = np.linspace(min(lifetimes), max(lifetimes), 500)
pdf_fitted = weibull_min.pdf(x, fitted_beta, scale=fitted_eta)

# -------------------------------
# PLOT
# -------------------------------
plt.figure()

# Histogram
plt.hist(lifetimes, bins=50, density=True, alpha=0.3, label="Histogram")

# Fitted Weibull
plt.plot(x, pdf_fitted, color='green', label="Fitted Weibull")

# Mean line
mean_life = np.mean(lifetimes)
plt.axvline(mean_life, linestyle='--', label="Mean Lifetime")

plt.xlabel("Failure Time (hours)")
plt.ylabel("Density")
plt.title("Weibull Fit from Simulated Data")

plt.legend()
plt.grid()

plt.show()