# coding: utf-8
"""
PID-controlled perishable pricing — NTU Fintech Hackathon 2016.

A grocery item is stocked with a fixed shelf life.  Its perceived value decays
as it ages toward the expiration date.  We compare two pricing strategies:

  * Classical clearance  : hold the sticker price flat, then apply one partial
                           and one deep markdown only near the expiry date
                           ("reduced to clear").  A lot of stock spoils unsold.
  * PID controller       : continuously ease the price down so that inventory
                           tracks an ideal linear sell-down to zero at expiry,
                           balancing customer happiness (consumer surplus)
                           against shop happiness (margin minus spoilage).

Running the season many times (Monte-Carlo) shows the total surplus the
classical approach leaves on the table.

This script is the reference implementation behind demo.html — the two use the
same model, so the browser demo shows exactly what this script computes.

    pip install matplotlib numpy
    python auto_pricing.py
"""

import math
import random
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- parameters --
# Example grocery items. The value-decay shape and rate come from the
# willingness-to-pay-for-freshness literature: produce/dairy lose value roughly
# LINEARLY, while meat/seafood lose it ~EXPONENTIALLY as they near expiry
# (Sumner et al.; Ghare & Schrader 1963 deteriorating-inventory model).
#   eta   = price elasticity of demand     drop  = fraction of value lost by expiry
#   decay = "linear" | "exp"               gamma = ideal sell-down curvature
#                                                   (0 = linear; higher = clear faster while fresh)
PRODUCTS = {
    "milk":   dict(name="Milk — dairy staple",  eta=0.35, decay="linear", drop=0.45, gamma=0.8, shelf=14, stock=240, foot=55),
    "banana": dict(name="Bananas — produce",    eta=0.60, decay="linear", drop=0.55, gamma=1.1, shelf=8,  stock=200, foot=50),
    "bread":  dict(name="Bread — bakery",       eta=0.70, decay="exp",    drop=0.55, gamma=1.8, shelf=5,  stock=160, foot=55),
    "fish":   dict(name="Fresh fish — seafood", eta=1.10, decay="exp",    drop=0.62, gamma=2.4, shelf=3,  stock=90,  foot=48),
}
PRODUCT = "banana"          # <- pick the item to simulate


def make_params(key):
    pr = PRODUCTS[key]
    return dict(
        T=pr["shelf"], I0=pr["stock"], footfall=pr["foot"],
        V0=140.0, cost=60.0, p0=100.0,     # fresh value, unit cost, list price
        depth=0.5,                          # classical final markdown -> depth * p0
        noise=0.30,                         # daily demand noise amplitude
        eta=pr["eta"], decay=pr["decay"], drop=pr["drop"], gamma=pr["gamma"],
        Kp=0.200, Ki=0.005, Kd=0.020,       # starting PID gains (auto-tuned in main)
    )


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def day_value(P, t):
    """Item value as it ages: linear (produce/dairy) or exponential (meat/seafood).
    Both shapes start at V0 and reach V0*(1-drop) at expiry."""
    tau = t / P["T"]
    if P["decay"] == "linear":
        return P["V0"] * (1 - P["drop"] * tau)
    return P["V0"] * (1 - P["drop"]) ** tau


def ideal_stock(P, t):
    """Ideal sell-down (PID setpoint): convex depletion from deteriorating-inventory
    theory (dI/dt = -D - theta*I, I(T)=0) -> sell faster while the item is fresh."""
    tau, g = t / P["T"], P["gamma"]
    if g < 1e-6:
        return P["I0"] * (1 - tau)
    return P["I0"] * (math.exp(g * (1 - tau)) - 1) / (math.exp(g) - 1)


def classical_price(p0, t, T, depth):
    """Flat list price, then one partial and one deep markdown in the final stretch.
    r = (t+1)/T (fraction of shelf life elapsed by end of day t) so even
    short-life items still trigger the markdown."""
    r = (t + 1) / T
    if r <= 0.7:
        return p0                    # full price for most of the shelf life
    if r <= 0.9:
        return p0 * (1 + depth) / 2  # first, partial reduction
    return p0 * depth                # final "reduced to clear" sticker


def simulate(strategy, P, seed):
    """Run one season under a given demand realization. Returns a result dict."""
    rng = random.Random(seed)
    T, I0, footfall = P["T"], P["I0"], P["footfall"]
    V0, cost, p0, eta = P["V0"], P["cost"], P["p0"], P["eta"]
    depth, noise = P["depth"], P["noise"]
    Kp, Ki, Kd = P["Kp"], P["Ki"], P["Kd"]

    inv = I0
    integral = prev_err = 0.0
    price = prev_p = p0
    CS = PS = cum = effort = 0.0
    sens = 0.5 + eta                 # elastic goods react more to price

    days, prices, invs, vals, targets, cums = [], [], [], [], [], []
    for t in range(T):
        V = day_value(P, t)
        target = ideal_stock(P, t)   # convex ideal sell-down (sell faster while fresh)

        if strategy == "classical":
            price = classical_price(p0, t, T, depth)
        else:                        # PID: excess stock vs target pushes price down
            e = inv - target
            integral += e
            der = e - prev_err
            prev_err = e
            u = -(Kp * e + Ki * integral + Kd * der)
            price = max(cost * 0.5, min(p0, price + u))

        effort += (price - prev_p) ** 2          # control effort (price volatility)
        prev_p = price

        # Demand: buyers whose willingness-to-pay (uniform up to V) beats price.
        frac = clamp01((V - price) / V * sens)
        q = footfall * (1 + noise * (rng.random() * 2 - 1)) * frac
        q = max(0.0, min(inv, q))
        inv -= q

        PS += (price - cost) * q                  # shop margin
        CS += q * (V - price) / 2                 # consumer surplus (triangle)
        cum += (price - cost) * q + q * (V - price) / 2

        days.append(t); prices.append(price); invs.append(inv)
        vals.append(V); targets.append(target); cums.append(cum)

    waste = inv                                   # unsold stock spoils
    waste_cost = waste * cost
    cums[-1] -= waste_cost                         # spoilage hits the books at expiry
    return dict(days=days, prices=prices, invs=invs, vals=vals, targets=targets,
                cums=cums, CS=CS, PS=PS, waste=waste, effort=effort,
                welfare=CS + PS - waste_cost)


def monte_carlo(P, n_runs):
    """Same demand seed per run for both strategies -> fair head-to-head."""
    pid_tot = cls_tot = pid_waste = cls_waste = 0.0
    diffs = []
    for i in range(n_runs):
        pid = simulate("pid", P, 1000 + i)
        cls = simulate("classical", P, 1000 + i)
        pid_tot += pid["welfare"]; cls_tot += cls["welfare"]
        pid_waste += pid["waste"]; cls_waste += cls["waste"]
        diffs.append(pid["welfare"] - cls["welfare"])
    wins = sum(1 for d in diffs if d > 0)
    return dict(pid_avg=pid_tot / n_runs, cls_avg=cls_tot / n_runs,
                suppressed=pid_tot - cls_tot, diffs=diffs,
                pid_waste=pid_waste / n_runs, cls_waste=cls_waste / n_runs,
                win_rate=wins / n_runs)


# --------------------------------------------------------------- auto-tuning --
# Objective: maximise mean net welfare while penalising price volatility
# (control effort), so the "optimal" gains give smooth, stable pricing rather
# than maximally aggressive markdowns.
LAMBDA = 0.5


def tune_objective(P, Kp, Ki, Kd, M):
    s = 0.0
    for i in range(M):
        r = simulate("pid", dict(P, Kp=Kp, Ki=Ki, Kd=Kd), 1000 + i)
        s += r["welfare"] - LAMBDA * r["effort"]
    return s / M


def auto_tune(P, M=60):
    """Compass / pattern search with step halving over the three PID gains."""
    bounds = dict(Kp=(0.01, 1.2), Ki=(0.0, 0.3), Kd=(0.0, 1.5))
    step = dict(Kp=0.3, Ki=0.02, Kd=0.3)
    min_step = dict(Kp=0.005, Ki=0.0005, Kd=0.005)
    best = dict(Kp=P["Kp"], Ki=P["Ki"], Kd=P["Kd"])
    best_val = tune_objective(P, best["Kp"], best["Ki"], best["Kd"], M)
    for _ in range(120):
        improved = False
        for k in ("Kp", "Ki", "Kd"):
            for d in (1, -1):
                cand = dict(best)
                lo, hi = bounds[k]
                cand[k] = min(hi, max(lo, best[k] + d * step[k]))
                if cand[k] == best[k]:
                    continue
                v = tune_objective(P, cand["Kp"], cand["Ki"], cand["Kd"], M)
                if v > best_val + 1e-6:
                    best_val, best, improved = v, cand, True
        if not improved:
            for k in step:
                step[k] *= 0.5
            if all(step[k] < min_step[k] for k in step):
                break
    return best


def main():
    P = make_params(PRODUCT)
    n_runs = 300
    print("Product          : %s  (%s decay, %d-day shelf)\n"
          % (PRODUCTS[PRODUCT]["name"], P["decay"], P["T"]))

    # Auto-tune the PID gains for this scenario, then adopt them.
    before = monte_carlo(P, n_runs)["pid_avg"]
    best = auto_tune(P)
    P.update(best)
    print("Auto-tuned gains : Kp=%.3f  Ki=%.4f  Kd=%.3f" % (best["Kp"], best["Ki"], best["Kd"]))
    print("PID welfare/run  : %.0f (default gains) -> %.0f (auto-tuned)\n"
          % (before, monte_carlo(P, n_runs)["pid_avg"]))

    # One representative season for the trajectory charts.
    pid = simulate("pid", P, 1000)
    cls = simulate("classical", P, 1000)
    mc = monte_carlo(P, n_runs)

    print("PID net welfare / run       : %9.0f" % mc["pid_avg"])
    print("Classical net welfare / run : %9.0f" % mc["cls_avg"])
    print("Surplus classical suppresses: %9.0f  (over %d runs)" % (mc["suppressed"], n_runs))
    print("PID wins in %.0f%% of runs" % (mc["win_rate"] * 100))
    print("Avg spoilage  PID %.1f u  vs  classical %.1f u" % (mc["pid_waste"], mc["cls_waste"]))

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))

    # 1) Price trajectory
    ax[0, 0].plot(pid["days"], pid["prices"], label="PID price", color="#1f77b4")
    ax[0, 0].plot(cls["days"], cls["prices"], label="Classical price", color="#d62728")
    ax[0, 0].plot(pid["days"], pid["vals"], "--", label="Item value", color="#888")
    ax[0, 0].set_title("Price trajectory"); ax[0, 0].set_xlabel("day"); ax[0, 0].legend()

    # 2) Inventory remaining
    ax[0, 1].plot(pid["days"], pid["invs"], label="PID (clears)", color="#1f77b4")
    ax[0, 1].plot(cls["days"], cls["invs"], label="Classical (spoils)", color="#d62728")
    ax[0, 1].plot(pid["days"], pid["targets"], "--", label="Ideal sell-down", color="#2ca02c")
    ax[0, 1].set_title("Inventory remaining"); ax[0, 1].set_xlabel("day"); ax[0, 1].legend()

    # 3) Cumulative net welfare
    ax[1, 0].plot(pid["days"], pid["cums"], label="PID", color="#1f77b4")
    ax[1, 0].plot(cls["days"], cls["cums"], label="Classical", color="#d62728")
    ax[1, 0].set_title("Cumulative net welfare"); ax[1, 0].set_xlabel("day"); ax[1, 0].legend()

    # 4) Monte-Carlo distribution of PID - Classical welfare
    ax[1, 1].hist(mc["diffs"], bins=24, color="#2ca02c")
    ax[1, 1].axvline(0, color="k", linestyle="--")
    ax[1, 1].set_title("Monte-Carlo: PID - Classical welfare per run")
    ax[1, 1].set_xlabel("welfare difference")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
