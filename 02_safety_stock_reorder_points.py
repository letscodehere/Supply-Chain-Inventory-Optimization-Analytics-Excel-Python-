"""
Supply Chain & Inventory Optimization Analytics — Safety Stock & Reorder Points
===================================================================================
The source dataset has no supplier lead-time field (no public retail
dataset of this kind typically does — lead time is operational/contractual
data, not point-of-sale data). Category-level lead times are therefore
a STATED, explicit assumption below, chosen to be directionally realistic
(perishable/fast-moving Groceries ship fastest; bulky Furniture slowest)
and are the one input in this analysis that should be replaced with a
real supplier lead-time log in a production deployment.

Formulas (standard inventory-theory, e.g. Silver/Pyke/Peterson):
    Safety Stock (SS) = Z x sigma_d x sqrt(L)
    Reorder Point (ROP) = (d_bar x L) + SS
    Economic Order Qty (EOQ) = sqrt(2 x D x S / H)
where d_bar = mean daily demand, sigma_d = std of daily demand, L = lead
time (days), Z = service-level z-score, D = annual demand, S = ordering
cost per order, H = annual holding cost per unit.

Run: python3 02_safety_stock_reorder_points.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
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

demand_stats = pd.read_csv(OUT_DIR / "demand_stats_by_sku_warehouse.csv")

# ----------------------------------------------------------------------
# STATED ASSUMPTION: category-level lead times (days), including a small
# amount of warehouse-level variation to reflect realistic distance-from-
# supplier effects. Documented explicitly here and in the report.
# ----------------------------------------------------------------------
BASE_LEAD_TIME_DAYS = {
    "Groceries": 4, "Clothing": 8, "Toys": 10, "Electronics": 12, "Furniture": 16,
}
WAREHOUSE_LEAD_TIME_ADJUSTMENT = {
    "S001": 0, "S002": 1, "S003": -1, "S004": 2, "S005": 0,
}  # days added/subtracted per warehouse (e.g., distance from central DC)
SERVICE_LEVEL = 0.95          # target cycle service level
Z = round(norm.ppf(SERVICE_LEVEL), 2)   # ~1.645
ORDERING_COST_PER_ORDER = 50  # GBP-equivalent, stated illustrative assumption
HOLDING_COST_PCT_OF_VALUE = 0.20  # 20% of unit value per year, stated illustrative assumption

demand_stats["lead_time_days"] = (
    demand_stats["category"].map(BASE_LEAD_TIME_DAYS) +
    demand_stats["warehouse_id"].map(WAREHOUSE_LEAD_TIME_ADJUSTMENT)
).clip(lower=2)

# ----------------------------------------------------------------------
# Safety stock, ROP, EOQ
# ----------------------------------------------------------------------
demand_stats["safety_stock"] = (
    Z * demand_stats["std_daily_demand"] * np.sqrt(demand_stats["lead_time_days"])
).round(0)
demand_stats["reorder_point"] = (
    demand_stats["mean_daily_demand"] * demand_stats["lead_time_days"] + demand_stats["safety_stock"]
).round(0)

annual_demand = demand_stats["mean_daily_demand"] * 365
holding_cost_per_unit = demand_stats["mean_price"] * HOLDING_COST_PCT_OF_VALUE
demand_stats["eoq"] = np.sqrt(
    2 * annual_demand * ORDERING_COST_PER_ORDER / holding_cost_per_unit
).round(0)

demand_stats.to_csv(OUT_DIR / "reorder_parameters.csv", index=False)
print(demand_stats[["warehouse_id", "sku", "category", "mean_daily_demand", "std_daily_demand",
                     "lead_time_days", "safety_stock", "reorder_point", "eoq"]].head(10).to_string(index=False))

print(f"\nService level target: {SERVICE_LEVEL*100:.0f}% (Z={Z})")
print(f"Lead time range applied: {demand_stats['lead_time_days'].min()}-{demand_stats['lead_time_days'].max()} days")
print(f"Mean safety stock: {demand_stats['safety_stock'].mean():.0f} units")
print(f"Mean reorder point: {demand_stats['reorder_point'].mean():.0f} units")

# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
lt_by_cat = demand_stats.groupby("category")["lead_time_days"].mean().sort_values()
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.barh(lt_by_cat.index, lt_by_cat.values, color=TEAL)
ax.set_xlabel("Assumed Lead Time (days)")
ax.set_title("Stated Lead-Time Assumption by Category", fontsize=13, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "05_lead_time_assumption.png", dpi=160)
plt.close(fig)

rop_by_cat = demand_stats.groupby("category").agg(
    Avg_Safety_Stock=("safety_stock", "mean"), Avg_ROP=("reorder_point", "mean")
).round(0).sort_values("Avg_ROP", ascending=False)
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(rop_by_cat))
width = 0.35
ax.bar(x - width/2, rop_by_cat["Avg_Safety_Stock"], width, label="Safety Stock", color=GOLD)
ax.bar(x + width/2, rop_by_cat["Avg_ROP"], width, label="Reorder Point", color=NAVY)
ax.set_xticks(x)
ax.set_xticklabels(rop_by_cat.index, rotation=15)
ax.set_ylabel("Units")
ax.set_title("Safety Stock & Reorder Point by Category (avg. across warehouses)",
             fontsize=12, fontweight="bold", color=NAVY, loc="left")
ax.legend()
fig.tight_layout()
fig.savefig(ASSETS / "06_safety_stock_rop_by_category.png", dpi=160)
plt.close(fig)

print("\nSafety stock / ROP / EOQ calculations complete.")
