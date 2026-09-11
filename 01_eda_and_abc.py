"""
Supply Chain & Inventory Optimization Analytics — EDA & ABC Analysis
========================================================================
Dataset: "Retail Store Inventory Forecasting Dataset" (Kaggle, Nov 2024)
Source : https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset
73,100 daily records: 5 stores x 20 products x 731 days (2022-01-01 to
2024-01-01). Framed here as a 5-warehouse, 20-SKU supply chain network —
the inventory-policy math (Sections 2 onward) operates identically on a
per-location-per-SKU basis regardless of whether "Store ID" denotes a
retail store or a distribution warehouse.

Run: python3 01_eda_and_abc.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
ASSETS = BASE_DIR / "assets"
for d in (OUT_DIR, ASSETS):
    d.mkdir(exist_ok=True)

NAVY, TEAL, GOLD, RED, GREY = "#1F3864", "#2E8B8B", "#D4A017", "#B23A48", "#8C96A0"
PALETTE = [NAVY, TEAL, GOLD, RED, "#7FB3B0"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.edgecolor": "#D9D9D9", "axes.grid": True,
    "grid.color": "#E8E8E8", "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
})

RENAME = {
    "Store ID": "warehouse_id", "Product ID": "sku", "Category": "category",
    "Region": "region", "Inventory Level": "inventory_level", "Units Sold": "units_sold",
    "Units Ordered": "units_ordered", "Demand Forecast": "demand_forecast_given",
    "Price": "price", "Discount": "discount_pct", "Weather Condition": "weather",
    "Holiday/Promotion": "promotion", "Competitor Pricing": "competitor_price",
    "Seasonality": "season",
}

df = pd.read_csv(DATA_DIR / "retail_store_inventory.csv", parse_dates=["Date"])
df = df.rename(columns=RENAME).rename(columns={"Date": "date"})
df.to_csv(DATA_DIR / "inventory_clean.csv", index=False)

log = []
log.append(f"Loaded {len(df):,} rows: {df['warehouse_id'].nunique()} warehouses, "
            f"{df['sku'].nunique()} SKUs, {df['category'].nunique()} categories, "
            f"{df['date'].min().date()} to {df['date'].max().date()} "
            f"({(df['date'].max()-df['date'].min()).days + 1} days)")

# ----------------------------------------------------------------------
# Data quality checks (documented even though this dataset is clean —
# verifying that, not assuming it, is the point)
# ----------------------------------------------------------------------
n_missing = df.isna().sum().sum()
n_dupe = df.duplicated(subset=["date", "warehouse_id", "sku"]).sum()
n_neg = ((df["inventory_level"] < 0) | (df["units_sold"] < 0) | (df["units_ordered"] < 0)).sum()
combo_counts = df.groupby(["warehouse_id", "sku"]).size()
log.append(f"Missing values: {n_missing} | Duplicate (date, warehouse, SKU) rows: {n_dupe} | "
            f"Negative-value rows: {n_neg}")
log.append(f"Warehouse x SKU combinations: {len(combo_counts)}, each with "
            f"{combo_counts.min()}-{combo_counts.max()} daily records "
            f"(fully balanced panel: {combo_counts.nunique() == 1})")

# --- Known data-quality issue in this dataset: 'Product ID' does not map
# to a single stable Category. Every Product ID (P0001-P0020) appears
# under all 5 categories at different points in the data (confirmed by
# a since-published "corrected" derivative of this dataset that
# explicitly fixes "mislabeled store and product IDs"). The stable,
# continuous 731-day daily panel exists at the (warehouse, Product ID)
# grain; Category is NOT stable within that grain and is therefore used
# here only in an aggregated, descriptive sense (each SKU's single most
# frequent category), never as a daily-level field.
cat_instability = df.groupby("sku")["category"].nunique()
log.append(f"Data-quality issue: every one of the {len(cat_instability)} Product IDs appears "
            f"under all {cat_instability.max()} categories at different points in the data "
            f"(Product ID is not a stable category key). Resolved by using (warehouse, Product ID) "
            f"as the stable analysis grain (full 731-day continuous panel) and assigning each SKU "
            f"its single most-frequent category for descriptive/ABC grouping only.")
with open(DATA_DIR / "data_quality_log.txt", "w") as f:
    f.write("\n".join(f"- {l}" for l in log))
print("\n".join(log))

# ----------------------------------------------------------------------
# 1. Demand overview & variability — grain: (warehouse_id, sku)
# ----------------------------------------------------------------------
sku_primary_category = df.groupby("sku")["category"].agg(lambda s: s.mode().iloc[0])

demand_stats = df.groupby(["warehouse_id", "sku"]).agg(
    mean_daily_demand=("units_sold", "mean"),
    std_daily_demand=("units_sold", "std"),
    total_units_sold=("units_sold", "sum"),
    mean_price=("price", "mean"),
).reset_index()
demand_stats["category"] = demand_stats["sku"].map(sku_primary_category)
demand_stats["cv"] = (demand_stats["std_daily_demand"] / demand_stats["mean_daily_demand"]).round(3)
demand_stats["consumption_value"] = (demand_stats["total_units_sold"] * demand_stats["mean_price"]).round(2)
demand_stats.to_csv(OUT_DIR / "demand_stats_by_sku_warehouse.csv", index=False)

print(f"\nDemand coefficient of variation (CV) across {len(demand_stats)} SKU-warehouse pairs: "
      f"mean={demand_stats['cv'].mean():.2f}, min={demand_stats['cv'].min():.2f}, "
      f"max={demand_stats['cv'].max():.2f}")

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(demand_stats["cv"], bins=30, color=TEAL, edgecolor="white")
ax.axvline(demand_stats["cv"].mean(), color=RED, linestyle="--", label=f"Mean CV = {demand_stats['cv'].mean():.2f}")
ax.set_xlabel("Coefficient of Variation (std / mean daily demand)")
ax.set_ylabel("SKU-Warehouse Pairs")
ax.set_title("Demand Variability Across SKU-Warehouse Combinations", fontsize=13, fontweight="bold", color=NAVY, loc="left")
ax.legend()
fig.tight_layout()
fig.savefig(ASSETS / "01_demand_variability.png", dpi=160)
plt.close(fig)

# Demand variability by category
cat_cv = demand_stats.groupby("category")["cv"].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.bar(cat_cv.index, cat_cv.values, color=NAVY)
ax.set_ylabel("Mean Coefficient of Variation")
ax.set_title("Demand Variability by Product Category", fontsize=13, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "02_cv_by_category.png", dpi=160)
plt.close(fig)

# ----------------------------------------------------------------------
# 2. Overall demand trend (all warehouses, monthly)
# ----------------------------------------------------------------------
monthly = df.groupby(pd.Grouper(key="date", freq="MS")).agg(
    total_units_sold=("units_sold", "sum"), total_revenue=("units_sold", lambda s: None)
)
monthly["total_revenue"] = df.groupby(pd.Grouper(key="date", freq="MS")).apply(
    lambda g: (g["units_sold"] * g["price"]).sum(), include_groups=False
)
monthly = monthly.reset_index()
monthly.to_csv(OUT_DIR / "monthly_demand_trend.csv", index=False)

fig, ax1 = plt.subplots(figsize=(10, 4.2))
ax1.plot(monthly["date"], monthly["total_units_sold"], color=NAVY, linewidth=2.2)
ax1.fill_between(monthly["date"], monthly["total_units_sold"], color=NAVY, alpha=0.08)
ax1.set_ylabel("Total Units Sold (all warehouses)")
ax1.set_title("Monthly Demand Trend, 2022-2024", fontsize=13, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "03_monthly_demand_trend.png", dpi=160)
plt.close(fig)

# ----------------------------------------------------------------------
# 3. ABC Analysis (by consumption value = units sold x price, per SKU
#    aggregated across all warehouses — the standard ABC unit of analysis)
# ----------------------------------------------------------------------
sku_value = demand_stats.groupby("sku").agg(
    total_consumption_value=("consumption_value", "sum"),
    category=("category", "first"),
).reset_index().sort_values("total_consumption_value", ascending=False)
sku_value["rank"] = range(1, len(sku_value) + 1)
sku_value["value_share_pct"] = sku_value["total_consumption_value"] / sku_value["total_consumption_value"].sum() * 100
sku_value["cumulative_value_pct"] = sku_value["value_share_pct"].cumsum()
sku_value["sku_share_pct"] = sku_value["rank"] / len(sku_value) * 100


def classify_abc(cum_pct):
    if cum_pct <= 70:
        return "A"
    elif cum_pct <= 90:
        return "B"
    else:
        return "C"


sku_value["abc_class"] = sku_value["cumulative_value_pct"].apply(classify_abc)
sku_value.to_csv(OUT_DIR / "abc_analysis.csv", index=False)

abc_summary = sku_value.groupby("abc_class").agg(
    skus=("sku", "count"), total_value=("total_consumption_value", "sum")
).reset_index()
abc_summary["sku_share_pct"] = (abc_summary["skus"] / abc_summary["skus"].sum() * 100).round(1)
abc_summary["value_share_pct"] = (abc_summary["total_value"] / abc_summary["total_value"].sum() * 100).round(1)
abc_summary.to_csv(OUT_DIR / "abc_summary.csv", index=False)
print("\nABC summary:\n", abc_summary.to_string(index=False))

# ABC Pareto chart
fig, ax1 = plt.subplots(figsize=(9, 5))
colors = {"A": RED, "B": GOLD, "C": TEAL}
bar_colors = [colors[c] for c in sku_value["abc_class"]]
ax1.bar(sku_value["rank"], sku_value["value_share_pct"], color=bar_colors)
ax1.set_xlabel("SKU Rank (by consumption value)")
ax1.set_ylabel("Value Share % (bars)")
ax2 = ax1.twinx()
ax2.plot(sku_value["rank"], sku_value["cumulative_value_pct"], color=NAVY, marker="o", markersize=4, linewidth=2)
ax2.axhline(70, color=RED, linestyle="--", linewidth=1)
ax2.axhline(90, color=GOLD, linestyle="--", linewidth=1)
ax2.set_ylabel("Cumulative Value % (line)")
ax2.set_ylim(0, 105)
from matplotlib.patches import Patch
legend_elems = [Patch(facecolor=RED, label="A (top ~70% value)"),
                Patch(facecolor=GOLD, label="B (next ~20%)"),
                Patch(facecolor=TEAL, label="C (remaining ~10%)")]
ax1.legend(handles=legend_elems, loc="center right")
ax1.set_title("ABC Analysis: SKU Consumption Value (Pareto)", fontsize=13, fontweight="bold", color=NAVY, loc="left")
fig.tight_layout()
fig.savefig(ASSETS / "04_abc_pareto.png", dpi=160)
plt.close(fig)

print(f"\nEDA + ABC analysis complete. {len(sku_value)} SKUs classified: "
      f"A={abc_summary[abc_summary.abc_class=='A'].skus.values[0]}, "
      f"B={abc_summary[abc_summary.abc_class=='B'].skus.values[0]}, "
      f"C={abc_summary[abc_summary.abc_class=='C'].skus.values[0]}")
