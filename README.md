# PID-Controlled Dynamic Pricing — NTU Fintech Hackathon 2016

A Python simulation of **PID (Proportional-Integral-Derivative) controller-based dynamic pricing**, modelling how market prices respond to shifting supply and demand across multiple product categories.

---

## Overview

Dynamic pricing is a core challenge in fintech and e-commerce. This project applies **control theory** — specifically the PID algorithm typically used in robotics and engineering — as an analogy for automated price adjustment in a competitive market.

The simulation models:
- **Three product categories** (A, B, C) with different elasticity coefficients
- **Three market scenarios** per category — varying leftover production and demand growth rates
- Price trajectories tracked over **192 time steps** (4 scenarios × 48 steps each)

---

## What the PID Controller Does

```
error = target_price - current_price
Δprice = Kp × (error + Ki × ∫error + Kd × Δerror/Δt)
```

The controller nudges the price toward a moving target driven by supply/demand dynamics, avoiding both over- and under-correction.

---

## Output Charts

The simulation generates 6 matplotlib charts:
1. **Price trajectory** over time
2. **Consumer surplus** — new vs. old pricing comparison
3. **Cumulative consumer surplus change**
4. **Producer surplus** — new vs. old pricing comparison
5. **Cumulative producer surplus change**
6. **Total surplus** — combined welfare analysis

---

## Run

```bash
pip install matplotlib numpy
python auto_pricing.py
```

The script is interactive — it prompts for initial price, demand, product class (a/b/c), and scenario parameters for each of three market situations.

