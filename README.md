# PID-Controlled Perishable Pricing — NTU Fintech Hackathon 2016

*Applying classical control theory to grocery markdown pricing — clearing stock before it expires.*

> **Live demo:** open [`demo.html`](demo.html) — interactive simulation with price trajectory, inventory, welfare, and a Monte-Carlo head-to-head. No Python required.

---

## 1. Motivation

A grocery item is stocked with a fixed **shelf life**. As it ages toward its expiration date, customers value it less. The shop has to decide how to price it down over time.

The **classical** approach is what you see on supermarket shelves: hold the sticker price flat, then — only when the expiry date is close — slap on a markdown ("reduced to clear"). Because the discount comes *late and all at once*, a large fraction of the stock spoils unsold. The shop eats the spoilage loss, and the discount benefit reaches customers in a narrow, last-minute window.

This project treats the markdown problem as a **control system** and applies a **PID (Proportional-Integral-Derivative)** controller — the workhorse of industrial process control — to ease the price down *continuously*, so that inventory clears right as the item expires. This balances **customer happiness** (consumer surplus) against **shop happiness** (margin minus spoilage).

The analogy is direct:
- **Setpoint** → ideal inventory level on each day (a linear sell-down to zero at expiry)
- **Process variable** → actual inventory remaining
- **Error signal** → actual − ideal (too much stock left ⇒ push price down)
- **Control output** → the price reduction applied that day

---

## 2. PID control theory

A PID controller computes a correction from three terms:

```
u(t) = Kp · e(t)  +  Ki · ∫e(t) dt  +  Kd · de(t)/dt

where:
    e(t)          = inventory(t) − ideal_inventory(t)     [error]
    Kp · e(t)     = proportional — reacts to today's excess stock
    Ki · ∫e(t)dt  = integral     — chases away persistent over-stock
    Kd · de/dt    = derivative   — damps over-discounting as stock drops fast

    price(t)      = clamp( price(t-1) − u(t),  floor,  list_price )
```

A positive error (more stock than the ideal sell-down line) drives the price down to stimulate demand. The three gains are exposed as sliders in the demo, so the classic speed/stability trade-off is directly observable.

### Auto-tuning the gains

Picking Kp, Ki, Kd by hand is fiddly, so both the script and the demo can **search the gain space automatically**. The objective rewards good performance but penalises a jumpy price path:

```
maximise   mean_runs( net_welfare )  −  λ · mean_runs( Σ (Δprice)² )
                                           └ control effort / price volatility ┘
```

Without the volatility penalty the "optimum" is simply *maximally aggressive* gains (clear the stock as fast as possible). Penalising control effort (λ = 0.5) yields a genuine **interior optimum** — gains that clear the inventory smoothly, exactly the trade-off a real markdown controller wants. The search itself is a **compass / pattern search** with step-halving over the three gains (~1000 cheap Monte-Carlo evaluations, well under a second). In the demo, click **Auto-tune ✦**; the script auto-tunes on startup and prints the gains it found.

---

## 3. Market model

The same model runs in both [`auto_pricing.py`](auto_pricing.py) and [`demo.html`](demo.html).

#### Item value decays toward expiry — and the *shape* depends on the product

Earlier drafts of this project assumed value decays linearly. That turns out to be only half right. Empirical work measuring **willingness-to-pay for freshness** finds the decline is **roughly linear for produce and dairy, but exponential for meat and poultry/seafood** as they approach the expiration date.¹ This matches the classical operations-research treatment of perishables, where value/quantity loss is modelled as **exponential deterioration** (Ghare & Schrader, 1963),² with later work using accelerating (quadratic) decay for fast-spoiling goods. So the model uses a per-product decay shape (both forms start at `V₀` and reach `V₀·(1−drop)` at expiry):

```
linear (produce, dairy):  V(t) = V₀ · (1 − drop · t/T)
exponential (meat, fish): V(t) = V₀ · (1 − drop)^(t/T)
```

**Example products** — each carries its own elasticity, decay shape, shelf life, and stock:

| Product | η (elasticity) | Value decay | Shelf life |
|---|---|---|---|
| Milk — dairy staple | 0.35 (inelastic) | linear | 14 d |
| Bananas — produce | 0.60 | linear | 8 d |
| Bread — bakery | 0.70 | exponential | 5 d |
| Fresh fish — seafood | 1.10 (elastic) | exponential | 3 d |

**Demand** — each day, buyers whose willingness-to-pay (uniform up to `V(t)`) exceeds the price buy the item, subject to daily footfall and random noise; elasticity scales how sharply demand reacts to price.

#### The ideal sell-down is convex, not linear

The PID setpoint is the *ideal* inventory trajectory. A constant (linear) sell-down ignores that the item is worth more while fresh. The classical deteriorating-inventory equation `dI/dt = −D − θ·I` with the boundary `I(T) = 0` solves to `I(t) ∝ e^{θ(T−t)} − 1` — a **convex** path that depletes **faster early**.² So the setpoint is

```
I_target(t) = I₀ · (e^{γ(1−t/T)} − 1) / (e^{γ} − 1)        (γ → 0 recovers the linear case)
```

with curvature `γ` larger for the fast-decaying products (clear them while they are still worth something).

**Two strategies are compared:**

- **Classical clearance** — flat list price for ~70% of the shelf life, then a first partial markdown, then a deep "reduced to clear" markdown in the final stretch.
- **PID controller** — continuous price glide-down tracking the convex ideal sell-down above.

### Surplus / welfare

```
Consumer Surplus (CS)  = Σ  q · (V − P)/2      (buyers' value above the price)
Producer Surplus (PS)  = Σ  q · (P − cost)     (the shop's margin)
Spoilage loss          = leftover_at_expiry · cost
Net welfare            = CS + PS − spoilage loss
```

To compare strategies fairly, the simulation runs the season many times (**Monte-Carlo**); on each run both strategies face the **same** random demand realization, then the net-welfare difference is accumulated.

---

## 4. Output charts

**Browser demo** ([`demo.html`](demo.html)) — consolidated into a KPI strip plus two figures, with Monte-Carlo **uncertainty bands** (the shaded P10–P90 spread across all runs):

1. **Price & inventory over the shelf life** — one figure, two stacked panels sharing the day axis. Median price (PID glide-down vs. classical flat-then-late-markdown) over the decaying value line, above median inventory (PID clears to ≈ 0; classical leaves a spoiled remainder) over the ideal sell-down line — each wrapped in its P10–P90 band.
2. **Net-welfare outcome distribution** — the spread of per-season net welfare for PID vs. classical, with medians marked; PID's whole distribution sits to the right of classical's.

**Python script** ([`auto_pricing.py`](auto_pricing.py)) produces four matplotlib panels for one representative season plus the Monte-Carlo run: price trajectory, inventory remaining, cumulative net welfare, and the histogram of (PID − classical) net welfare.

---

## 5. Key findings

Across all four products (300-run Monte-Carlo each, with auto-tuned gains):

- **PID clears the stock; classical wastes it.** PID spoilage runs ≈ 0–4% of stock vs ≈ 42–62% for the classical late-markdown strategy.
- **PID wins 100% of Monte-Carlo runs**, and the *entire* per-run welfare distribution sits to the right of classical's.
- The classical approach posts **negative** average net welfare (spoilage swamps the margin earned at full price); PID stays **positive** for every product.
- **The optimal gains depend on the product.** Auto-tuning lands on a gentle Kp ≈ 0.17 for slow-decaying milk but an aggressive Kp ≈ 0.8 for fast-decaying, 3-day-shelf fish.
- **Auto-tuning is essential for the hard cases.** At the hand-set default gains, bread and fish actually post *negative* PID welfare (the controller is too sluggish for a short, exponentially-decaying shelf life); tuning flips both to clearly positive.

---

## 6. Run

```bash
pip install matplotlib
python auto_pricing.py
```

The script is non-interactive: it auto-tunes the PID gains, runs one representative season plus a 300-run Monte-Carlo comparison, prints the welfare/waste summary, and shows the four charts. Change the `PRODUCT` constant at the top (`"milk"`, `"banana"`, `"bread"`, `"fish"`) to simulate a different item, or edit the `PRODUCTS` table to add your own.

**Browser demo:** open [`demo.html`](demo.html) — same model in JavaScript with interactive sliders and an **Auto-tune ✦** button, no Python required.

---

## 7. References

The value-decay shapes and convex sell-down are grounded in:

1. Sumner et al. *Measuring willingness to pay for freshness in perishable goods: an empirical analysis.* (WTP for freshness declines roughly linearly for produce/dairy, exponentially for meat/poultry.) — [ScienceDirect S2667259625000037](https://www.sciencedirect.com/science/article/pii/S2667259625000037)
2. P. M. Ghare and G. F. Schrader. *A Model for an Exponentially Decaying Inventory.* Journal of Industrial Engineering, 14:238–243, 1963. (Foundational exponential-deterioration inventory model; convex depletion path.)
3. *Optimal markdown policies for perishable products with fixed shelf life.* International Journal of Production Research, 63(15), 2025. — [tandfonline 10.1080/00207543.2025.2461133](https://www.tandfonline.com/doi/full/10.1080/00207543.2025.2461133)

General background:

4. K. J. Åström and R. M. Murray. *Feedback Systems: An Introduction for Scientists and Engineers.* Princeton University Press, 2008. (PID / control theory)
5. A. Pigou. *The Economics of Welfare.* Macmillan, 1920. (Consumer/producer surplus framework)
6. R. Phillips. *Pricing and Revenue Optimization.* Stanford Business Books, 2005. (Markdown / perishable pricing)
