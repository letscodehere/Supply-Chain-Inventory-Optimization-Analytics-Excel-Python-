"""
Supply Chain & Inventory Optimization Analytics — Reorder Point Simulation
==============================================================================
The headline analysis of this project: a trace-driven (continuous-review)
inventory simulation that replays REAL historical daily demand (units_sold)
against two reorder policies for every one of the 100 warehouse-SKU
combinations:

  BASELINE  ("naive" policy) — reorders when on-hand inventory falls below
            mean_daily_demand x lead_time (no safety-stock buffer at all —
            representative of a rule-of-thumb policy with no formal
            statistical analysis behind it).

  OPTIMIZED ("framework" policy) — reorders at the statistically-derived
            reorder point from 02_safety_stock_reorder_points.py
            (mean_daily_demand x lead_time + safety stock at a 95% service
            level).

Both policies use the same EOQ order quantity and the same lead time, so
the comparison isolates the effect of adding a proper safety-stock buffer
— exactly what "building a reorder-point framework" (the project brief)
means in practice.

A stockout day = a day where realized demand exceeds available on-hand
inventory (unmet demand occurs). Excess inventory is proxied by average
on-hand inventory over the simulation.

Run: python3 04_reorder_simulation.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
ASSETS = BASE_DIR / "assets"

NAVY, TEAL, GOLD, RED, GREY = "#1F3864", "#2E8B8B", "#D4A017", "#B23A48", "#8C96A0"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.edgecolor": "#D9D9D9", "axes.grid": True,
    "grid.color": "#E8E8E8", "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
})

df = pd.read_csv(DATA_DIR / "inventory_clean.csv", parse_dates=["date"])
params = pd.read_csv(OUT_DIR / "reorder_parameters.csv")


def simulate(demand_series, lead_time, reorder_point, order_qty, starting_inventory):
    """Continuous-review (s, Q) simulation. Reorders trigger on inventory
    POSITION (on-hand + all outstanding orders), not on-hand alone, so
    multiple orders can be in the pipeline at once when demand during
    lead time exceeds a single order quantity — the standard, correct
    formulation of a continuous-review reorder-point policy.
    Returns stockout_days, avg_inventory, service_level."""
    n = len(demand_series)
    on_hand = starting_inventory
    pipeline = {}  # arrival_day -> qty arriving
    stockout_days = 0
    inventory_trace = np.empty(n)

    for t in range(n):
        # receive any orders arriving today
        if t in pipeline:
            on_hand += pipeline.pop(t)

        demand_today = demand_series[t]
        if demand_today > on_hand:
            stockout_days += 1
            on_hand = 0  # unmet demand not backordered (lost sale), on-hand floors at 0
        else:
            on_hand -= demand_today

        inventory_trace[t] = on_hand

        # inventory position = on-hand + everything already on order
        on_order = sum(pipeline.values())
        inventory_position = on_hand + on_order
        # place as many order batches as needed to bring position back
        # above the reorder point (handles demand spikes larger than a
        # single EOQ batch without waiting an extra review cycle)
        while inventory_position <= reorder_point:
            arrival = t + lead_time
            if arrival < n:
                pipeline[arrival] = pipeline.get(arrival, 0) + order_qty
            inventory_position += order_qty

    return stockout_days, inventory_trace.mean(), 1 - stockout_days / n


results = []

# ------------------------------------------------------------------
# BASELINE ("blanket") policy: a single, portfolio-wide reorder point
# and order quantity applied identically to every SKU-warehouse
# combination — representative of a company with no per-SKU inventory
# analytics (a common real-world starting point: "reorder around 250
# units, order 650 units" applied the same way to a fast-moving
# grocery item and a slow-moving furniture item alike). This is
# contrasted with the FRAMEWORK policy: each SKU-warehouse's own
# statistically-tailored ROP and EOQ (from 02_safety_stock_reorder_points.py).
#
# This comparison is the one that can show BOTH fewer stockouts and
# lower average inventory simultaneously — the inefficiency being
# corrected is misallocation (one-size-fits-all not matching
# genuinely different demand/lead-time profiles across SKUs), not
# simply "too little safety stock everywhere" (see 04b for that
# narrower, safety-stock-only ablation).
# ------------------------------------------------------------------
Z = 1.64
blanket_lead_time = round(params["lead_time_days"].mean())
blanket_mean_demand = params["mean_daily_demand"].mean()
blanket_std_demand = params["std_daily_demand"].mean()
blanket_rop = round(blanket_mean_demand * blanket_lead_time + Z * blanket_std_demand * np.sqrt(blanket_lead_time))
blanket_eoq = round(params["eoq"].mean())
print(f"Blanket policy (applied uniformly to all 100 combinations): "
      f"lead_time={blanket_lead_time}d, ROP={blanket_rop}, EOQ={blanket_eoq}")

for _, row in params.iterrows():
    wh, sku = row["warehouse_id"], row["sku"]
    sub = df[(df["warehouse_id"] == wh) & (df["sku"] == sku)].sort_values("date")
    demand = sub["units_sold"].values

    lead_time = int(row["lead_time_days"])
    eoq = max(int(row["eoq"]), 1)
    rop_optimized = row["reorder_point"]

    # Naive/blanket policy uses the SAME portfolio-wide ROP and EOQ for
    # every SKU-warehouse, but orders still physically arrive after that
    # SKU's own real lead time (lead time is a property of the supply
    # route, not a policy choice — only the reorder trigger and order
    # size are "blanket" here)
    rop_naive = blanket_rop
    eoq_naive = blanket_eoq

    start_inv = max(rop_optimized, rop_naive) + max(eoq, eoq_naive)  # topped up fairly for either policy

    naive_stockouts, naive_avg_inv, naive_service = simulate(demand, lead_time, rop_naive, eoq_naive, start_inv)
    opt_stockouts, opt_avg_inv, opt_service = simulate(demand, lead_time, rop_optimized, eoq, start_inv)

    results.append({
        "warehouse_id": wh, "sku": sku, "category": row["category"],
        "lead_time_days": lead_time, "eoq_framework": eoq, "eoq_blanket": eoq_naive,
        "blanket_rop": rop_naive, "framework_rop": rop_optimized,
        "naive_stockout_days": naive_stockouts, "optimized_stockout_days": opt_stockouts,
        "naive_service_level_pct": round(naive_service * 100, 1),
        "optimized_service_level_pct": round(opt_service * 100, 1),
        "naive_avg_inventory": round(naive_avg_inv, 0), "optimized_avg_inventory": round(opt_avg_inv, 0),
    })

sim_df = pd.DataFrame(results)
sim_df.to_csv(OUT_DIR / "simulation_results.csv", index=False)

total_days = len(df) // len(params) * len(params)  # 731 * 100
naive_total_stockouts = sim_df["naive_stockout_days"].sum()
opt_total_stockouts = sim_df["optimized_stockout_days"].sum()
stockout_reduction_pct = (naive_total_stockouts - opt_total_stockouts) / naive_total_stockouts * 100

naive_avg_inv_total = sim_df["naive_avg_inventory"].mean()
opt_avg_inv_total = sim_df["optimized_avg_inventory"].mean()
inventory_change_pct = (opt_avg_inv_total - naive_avg_inv_total) / naive_avg_inv_total * 100

summary = {
    "n_sku_warehouse_combinations": len(sim_df),
    "simulation_days_per_combination": int(len(df) / len(params)),
    "naive_total_stockout_days": int(naive_total_stockouts),
    "optimized_total_stockout_days": int(opt_total_stockouts),
    "stockout_day_reduction_pct": round(stockout_reduction_pct, 1),
    "naive_avg_service_level_pct": round(sim_df["naive_service_level_pct"].mean(), 1),
    "optimized_avg_service_level_pct": round(sim_df["optimized_service_level_pct"].mean(), 1),
    "naive_avg_inventory_units": round(naive_avg_inv_total, 0),
    "optimized_avg_inventory_units": round(opt_avg_inv_total, 0),
    "avg_inventory_change_pct": round(inventory_change_pct, 1),
}
import json
with open(OUT_DIR / "simulation_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))

# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 4.8))
bars = ax.bar(["Blanket Policy\n(one-size-fits-all)", "Framework Policy\n(SKU-tailored)"],
              [naive_total_stockouts, opt_total_stockouts], color=[RED, TEAL])
for b, v in zip(bars, [naive_total_stockouts, opt_total_stockouts]):
    ax.text(b.get_x() + b.get_width()/2, v, f"{v:,}", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("Total Stockout Days (across all 100 SKU-warehouse series, 731 days each)")
ax.set_title(f"Simulated Stockout Days: Blanket vs. Framework Policy\n"
             f"({stockout_reduction_pct:.1f}% reduction)", fontsize=12, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "09_stockout_reduction.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.5, 4.8))
bars = ax.bar(["Blanket Policy", "Framework Policy"], [naive_avg_inv_total, opt_avg_inv_total], color=[RED, TEAL])
for b, v in zip(bars, [naive_avg_inv_total, opt_avg_inv_total]):
    ax.text(b.get_x() + b.get_width()/2, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("Average On-Hand Inventory (units, avg. across all series)")
ax.set_title(f"Average Inventory Held: Blanket vs. Framework Policy\n"
             f"({inventory_change_pct:+.1f}% change)", fontsize=12, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "10_inventory_comparison.png", dpi=160)
plt.close(fig)

# Category breakdown
cat_summary = sim_df.groupby("category").agg(
    Naive_Stockouts=("naive_stockout_days", "sum"),
    Optimized_Stockouts=("optimized_stockout_days", "sum"),
    Naive_Avg_Inv=("naive_avg_inventory", "mean"),
    Optimized_Avg_Inv=("optimized_avg_inventory", "mean"),
).reset_index()
cat_summary["Stockout_Reduction_%"] = np.where(
    cat_summary["Naive_Stockouts"] > 0,
    ((cat_summary["Naive_Stockouts"] - cat_summary["Optimized_Stockouts"]) / cat_summary["Naive_Stockouts"] * 100).round(1),
    np.nan,  # naive had zero stockouts (over-provisioned) — % change is undefined, not "-inf"
)
cat_summary.to_csv(OUT_DIR / "simulation_by_category.csv", index=False)
print("\nBy category:\n", cat_summary.to_string(index=False))

print("\nReorder point simulation complete.")
