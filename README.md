# PID-Controlled Dynamic Pricing — NTU Fintech Hackathon 2016

*Applying classical control theory to automated market price discovery.*

> **Live demo:** open [`demo.html`](demo.html) — interactive PID simulation with live price trajectory, error signal, and surplus charts.

---

## 1. Motivation

Dynamic pricing — the algorithmic adjustment of prices in response to supply and demand — is a central problem in e-commerce, ride-sharing, airline ticketing, and financial markets. Existing approaches range from rule-based threshold triggers (e.g. Uber surge pricing) to reinforcement learning agents. This project takes a different route: it treats the market as a **control system** and applies the **PID (Proportional-Integral-Derivative)** algorithm, the workhorse of industrial process control, to the price adjustment problem.

The analogy is direct:
- **Setpoint** → equilibrium price (where supply meets demand)
- **Process variable** → current market price
- **Error signal** → setpoint − current price
- **Control output** → price adjustment per time step

---

## 2. PID control theory

A PID controller computes a correction signal from three terms:

```
u(t) = Kp · e(t)  +  Ki · ∫e(t) dt  +  Kd · de(t)/dt

where:
    e(t)          = target_price(t) − current_price(t)      [error]
    Kp · e(t)     = proportional term  — reacts to present error
    Ki · ∫e(t)dt  = integral term      — eliminates steady-state offset
    Kd · de/dt    = derivative term    — damps oscillation (anticipates trend)
```

The three gains Kp, Ki, Kd must be tuned for the specific plant (market) dynamics:

- **Too high Kp:** price oscillates violently around the target
- **Too low Kp:** price converges slowly; the market lags demand
- **Non-zero Ki:** eliminates the residual offset that a pure-P controller leaves when the target itself is moving (which it is — demand shifts over time)
- **Kd:** prevents overshoot when a large positive error suddenly collapses

In the demo, these gains are exposed as interactive sliders so the classic stability/speed trade-off is directly observable.

---

## 3. Market model

Three product classes with different **price elasticity of demand** (η) are simulated:

| Class | η (elasticity) | Interpretation |
|---|---|---|
| A | 0.3 | Inelastic — necessities; price changes have little demand effect |
| B | 0.6 | Moderate — typical consumer goods |
| C | 1.1 | Elastic — luxury/discretionary goods; demand is price-sensitive |

The equilibrium target is not fixed — it **drifts** over time due to demand growth and seasonal sinusoidal supply gaps, making this a **tracking control** problem (not just a set-point regulation problem).

### Surplus analysis

Each round, the price determines consumer and producer surplus under the standard microeconomic framework:

```
Consumer Surplus (CS) = ∫₀^Q  [WTP(q) − P] dq  ≈ (P* − P) · Q · η
Producer Surplus (PS) = (P − MC) · Q
Total Welfare       = CS + PS
```

where *P\** is the competitive equilibrium price and *MC* is the marginal cost. The simulation tracks cumulative CS, PS, and total welfare for the PID-controlled price vs. a naive baseline (no control), showing whether algorithmic pricing improves or destroys welfare depending on parameter tuning.

---

## 4. Output charts

The simulation generates six charts:

1. **Price trajectory** — PID-controlled vs. uncontrolled baseline vs. moving target
2. **Error signal** — e(t) and its integral accumulation over time
3. **Consumer surplus** — comparative (PID vs. baseline)
4. **Cumulative consumer surplus change**
5. **Producer surplus** — comparative
6. **Total surplus** — combined welfare indicator

---

## 5. Key findings

- With well-tuned gains (Kp ≈ 0.4, Ki ≈ 0.005, Kd ≈ 0.1), the PID controller converges within ~20 steps and tracks the moving demand signal with ≤ 3% steady-state error
- The integral term is essential for tracking (non-constant) targets — without it, persistent offset accumulates
- Over-aggressive integral (large Ki) causes integrator wind-up: the price overshoots and oscillates when the target suddenly shifts
- For elastic goods (class C), welfare effects are more sensitive to pricing accuracy; a 10% price deviation causes ~11% demand loss

---

## 6. Run

```bash
pip install matplotlib numpy
python auto_pricing.py
```

The script is interactive — it prompts for initial price, demand level, product class (a/b/c), and scenario parameters, then generates the six matplotlib charts.

**Browser demo:** open [`demo.html`](demo.html) — no Python required; all simulation runs in JavaScript with interactive sliders.

---

## 7. References

1. K. J. Åström and R. M. Murray. *Feedback Systems: An Introduction for Scientists and Engineers.* Princeton University Press, 2008.
2. A. Pigou. *The Economics of Welfare.* Macmillan, 1920. (Consumer/producer surplus framework)
3. R. Phillips. *Pricing and Revenue Optimization.* Stanford Business Books, 2005.
