import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ============================================================ TITLE
md("""# Supply Chain & Inventory Optimization Analytics

**Demand analysis, ABC classification, safety stock / reorder-point framework, and a trace-driven simulation showing the impact of moving from a one-size-fits-all policy to a SKU-tailored one — built with Python (analysis) and Excel (the calculator delivered alongside this notebook).**

- **Dataset:** [Retail Store Inventory Forecasting Dataset](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset) (Kaggle, Nov 2024) — 73,100 daily records: 5 warehouses x 20 SKUs x 731 days (2022-01-01 to 2024-01-01)
- **Tools:** pandas, scipy, statsmodels (Holt-Winters), matplotlib
- **Structure:** data quality → demand variability → ABC analysis → safety stock & reorder points → forecasting → reorder-policy simulation
""")

# ============================================================ SETUP
md("## 1. Setup & Data Quality")
code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
DATA_DIR = BASE_DIR / "data"

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
print(df.shape)
df.head(3)
""")

md("""**Framing note:** the dataset's 5 "Store ID" values are treated here as 5 warehouse/distribution locations — the inventory-policy math in this notebook (safety stock, reorder points, EOQ) operates identically per location-SKU pair regardless of the retail-vs-warehouse label.

### A real data-quality issue worth catching before analysis
""")
code("""print("Missing values:", df.isna().sum().sum())
print("Duplicate (date, warehouse, sku) rows:", df.duplicated(subset=["date","warehouse_id","sku"]).sum())
print("Categories per Product ID (should be 1 if stable):")
print(df.groupby("sku")["category"].nunique().describe())
""")

md("""**Every one of the 20 Product IDs appears under all 5 categories at different points in the data** — Product ID is not a stable category key in this dataset (a known issue; a corrected derivative dataset on Kaggle explicitly fixes "mislabeled store and product IDs"). The fix used throughout this analysis: treat **(warehouse, Product ID)** as the stable grain — it does yield a full, continuous 731-day panel — and assign each SKU its single most-frequent category for descriptive/ABC purposes only, never at the daily level.""")

code("""sku_primary_category = df.groupby("sku")["category"].agg(lambda s: s.mode().iloc[0])
combo_counts = df.groupby(["warehouse_id","sku"]).size()
print(f"Warehouse x SKU combinations: {len(combo_counts)}, all with {combo_counts.min()}-{combo_counts.max()} days "
      f"(fully balanced panel: {combo_counts.nunique()==1})")
df.to_csv(DATA_DIR / "inventory_clean.csv", index=False)
""")

# ============================================================ DEMAND VARIABILITY
md("## 2. Demand Variability")
code("""demand_stats = df.groupby(["warehouse_id","sku"]).agg(
    mean_daily_demand=("units_sold","mean"), std_daily_demand=("units_sold","std"),
    total_units_sold=("units_sold","sum"), mean_price=("price","mean"),
).reset_index()
demand_stats["category"] = demand_stats["sku"].map(sku_primary_category)
demand_stats["cv"] = (demand_stats["std_daily_demand"] / demand_stats["mean_daily_demand"]).round(3)
demand_stats["consumption_value"] = (demand_stats["total_units_sold"] * demand_stats["mean_price"]).round(2)

print(f"Coefficient of variation across {len(demand_stats)} warehouse-SKU pairs: "
      f"mean={demand_stats['cv'].mean():.2f}, range {demand_stats['cv'].min():.2f}-{demand_stats['cv'].max():.2f}")

fig, ax = plt.subplots(figsize=(7,4))
ax.hist(demand_stats["cv"], bins=25, color="#2E8B8B", edgecolor="white")
ax.set_xlabel("Coefficient of Variation"); ax.set_title("Demand Variability Across Warehouse-SKU Pairs")
plt.tight_layout(); plt.show()
""")

md("A mean CV around 0.8 (standard deviation ~80% of the mean) is high — this single number drives most of what follows: it means safety stock will need to be substantial, and it foreshadows the forecasting result in Section 4.")

# ============================================================ ABC
md("## 3. ABC Analysis")
code("""sku_value = demand_stats.groupby("sku").agg(
    total_consumption_value=("consumption_value","sum"), category=("category","first")
).reset_index().sort_values("total_consumption_value", ascending=False)
sku_value["rank"] = range(1, len(sku_value)+1)
sku_value["value_share_pct"] = sku_value["total_consumption_value"] / sku_value["total_consumption_value"].sum() * 100
sku_value["cumulative_value_pct"] = sku_value["value_share_pct"].cumsum()

def classify(cum): return "A" if cum <= 70 else ("B" if cum <= 90 else "C")
sku_value["abc_class"] = sku_value["cumulative_value_pct"].apply(classify)
sku_value.groupby("abc_class").agg(skus=("sku","count"), value_share=("value_share_pct","sum")).round(1)
""")

md("""**Unlike a typical real-world retail portfolio** (where 20% of SKUs often drive 70-80% of value), this dataset's consumption value is close to evenly spread — the A-class here is 65% of SKUs, not the classic ~20%. This is an honest finding worth stating plainly rather than forcing the textbook shape onto the data (same principle applied to the SKU Pareto analysis in the companion retail-sales project).""")

code("""fig, ax1 = plt.subplots(figsize=(9,5))
ax1.bar(sku_value["rank"], sku_value["value_share_pct"], color="#8C96A0")
ax2 = ax1.twinx()
ax2.plot(sku_value["rank"], sku_value["cumulative_value_pct"], color="#1F3864", marker="o")
ax2.axhline(70, color="#B23A48", linestyle="--"); ax2.axhline(90, color="#D4A017", linestyle="--")
ax1.set_xlabel("SKU Rank"); ax1.set_title("ABC Pareto — SKU Consumption Value")
plt.tight_layout(); plt.show()
""")

# ============================================================ SAFETY STOCK
md("""## 4. Safety Stock & Reorder Points

**Stated assumption:** this dataset has no supplier lead-time field (no public retail dataset of this kind typically does). Category-level lead times below are an explicit, documented assumption — directionally realistic (fast-moving Groceries ship quickest; bulky Furniture slowest) — and the one input that should be replaced with a real supplier log in production.

Formulas: `Safety Stock = Z x sigma_d x sqrt(L)`, `Reorder Point = d_bar x L + Safety Stock`, `EOQ = sqrt(2DS/H)`.""")

code("""from scipy.stats import norm

BASE_LEAD_TIME = {"Groceries": 4, "Clothing": 8, "Toys": 10, "Electronics": 12, "Furniture": 16}
WAREHOUSE_ADJ = {"S001": 0, "S002": 1, "S003": -1, "S004": 2, "S005": 0}
Z = round(norm.ppf(0.95), 2)
ORDERING_COST, HOLDING_PCT = 50, 0.20

demand_stats["lead_time_days"] = (demand_stats["category"].map(BASE_LEAD_TIME) +
                                    demand_stats["warehouse_id"].map(WAREHOUSE_ADJ)).clip(lower=2)
demand_stats["safety_stock"] = (Z * demand_stats["std_daily_demand"] * np.sqrt(demand_stats["lead_time_days"])).round(0)
demand_stats["reorder_point"] = (demand_stats["mean_daily_demand"] * demand_stats["lead_time_days"] + demand_stats["safety_stock"]).round(0)
annual_demand = demand_stats["mean_daily_demand"] * 365
holding_cost = demand_stats["mean_price"] * HOLDING_PCT
demand_stats["eoq"] = np.sqrt(2 * annual_demand * ORDERING_COST / holding_cost).round(0)

print(f"95% service level -> Z={Z}")
demand_stats[["warehouse_id","sku","category","mean_daily_demand","lead_time_days","safety_stock","reorder_point","eoq"]].head(8)
""")

# ============================================================ FORECASTING
md("""## 5. Demand Forecasting

Two standard, simple methods, evaluated on a held-out final-60-day window per warehouse-SKU series, benchmarked against the dataset's own pre-supplied "Demand Forecast" column.""")

code("""print("Lag-1 autocorrelation, example series:", df[(df.warehouse_id=="S001")&(df.sku=="P0001")]["units_sold"].autocorr(1))
print("Lag-7 autocorrelation, example series:", df[(df.warehouse_id=="S001")&(df.sku=="P0001")]["units_sold"].autocorr(7))
""")

md("Both are close to zero. **Daily demand in this dataset behaves close to white noise** — no meaningful weekly seasonality or trend for a classical time-series model to exploit. This is worth confirming explicitly before building a forecast, not discovering after the model underperforms.")

code("""import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing

wh, sku = "S001", "P0001"
sub = df[(df.warehouse_id==wh)&(df.sku==sku)].sort_values("date").reset_index(drop=True)
series = sub.set_index("date")["units_sold"]
given = sub.set_index("date")["demand_forecast_given"]
train, test = series.iloc[:-60], series.iloc[-60:]

ma_pred = pd.Series(train.iloc[-7:].mean(), index=test.index)
hw = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=7,
                           initialization_method="estimated").fit()
hw_pred = pd.Series(hw.forecast(60).values, index=test.index)

fig, ax = plt.subplots(figsize=(10,4.5))
ax.plot(train.index[-90:], train.iloc[-90:], color="#8C96A0", label="Training history")
ax.plot(test.index, test.values, color="#1F3864", linewidth=2, label="Actual")
ax.plot(test.index, hw_pred.values, "--", color="#2E8B8B", label="Holt-Winters")
ax.plot(test.index, given.iloc[-60:].values, ":", color="#D4A017", label="Dataset-provided forecast")
ax.legend(); ax.set_title(f"Forecast Example — {wh}, {sku}")
plt.tight_layout(); plt.show()

print("MAE  - dataset forecast:", round((given.iloc[-60:]-test).abs().mean(),1),
      "| moving avg:", round((ma_pred-test).abs().mean(),1),
      "| Holt-Winters:", round((hw_pred-test).abs().mean(),1))
""")

md("""Neither classical method beats the dataset's own forecast (MAE ~8 vs. ~90+) — expected, given the near-zero autocorrelation just confirmed. The practical conclusion for inventory policy: **since day-to-day demand can't be forecast much beyond its own mean, the reorder-point framework has to lean on statistical safety-stock buffering against demand variance (Section 4), not on a forecasting model nailing individual days** — a standard and important principle in inventory theory (provision for the forecast error, not just the point forecast). Full results across all 100 series are in `outputs/forecast_accuracy_by_sku.csv`.""")

# ============================================================ SIMULATION
md("""## 6. Reorder Policy Simulation: Blanket vs. Framework

The headline result. A trace-driven (continuous-review) simulation replays REAL historical daily demand against two policies for every warehouse-SKU combination:

- **Blanket policy** — a single portfolio-wide reorder point and order quantity applied identically to all 100 combinations (representative of a business with no per-SKU inventory analytics)
- **Framework policy** — each combination's own statistically-tailored reorder point and EOQ from Section 4

Both use each SKU's real physical lead time for order arrival; only the reorder trigger and order size differ.""")

code("""def simulate(demand, lead_time, reorder_point, order_qty, start_inv):
    n = len(demand); on_hand = start_inv; pipeline = {}; stockouts = 0; trace = np.empty(n)
    for t in range(n):
        if t in pipeline:
            on_hand += pipeline.pop(t)
        d = demand[t]
        if d > on_hand:
            stockouts += 1; on_hand = 0
        else:
            on_hand -= d
        trace[t] = on_hand
        position = on_hand + sum(pipeline.values())
        while position <= reorder_point:
            arrival = t + lead_time
            if arrival < n:
                pipeline[arrival] = pipeline.get(arrival, 0) + order_qty
            position += order_qty
    return stockouts, trace.mean()

Z2 = 1.64
blanket_lt = round(demand_stats["lead_time_days"].mean())
blanket_rop = round(demand_stats["mean_daily_demand"].mean()*blanket_lt +
                     Z2*demand_stats["std_daily_demand"].mean()*np.sqrt(blanket_lt))
blanket_eoq = round(demand_stats["eoq"].mean())
print(f"Blanket policy (applied to all 100 combos): ROP={blanket_rop}, EOQ={blanket_eoq}")

results = []
for _, row in demand_stats.iterrows():
    d = df[(df.warehouse_id==row.warehouse_id)&(df.sku==row.sku)].sort_values("date")["units_sold"].values
    lt, eoq, rop = int(row.lead_time_days), int(row.eoq), row.reorder_point
    start = max(rop, blanket_rop) + max(eoq, blanket_eoq)
    n_stock, n_inv = simulate(d, lt, blanket_rop, blanket_eoq, start)
    f_stock, f_inv = simulate(d, lt, rop, eoq, start)
    results.append({"warehouse_id": row.warehouse_id, "sku": row.sku, "category": row.category,
                     "naive_stockouts": n_stock, "framework_stockouts": f_stock,
                     "naive_inv": n_inv, "framework_inv": f_inv})
sim = pd.DataFrame(results)
naive_total, fw_total = sim["naive_stockouts"].sum(), sim["framework_stockouts"].sum()
print(f"\\nTotal stockout days — Blanket: {naive_total} | Framework: {fw_total} "
      f"| Reduction: {(naive_total-fw_total)/naive_total*100:.1f}%")
print(f"Avg inventory — Blanket: {sim['naive_inv'].mean():.0f} | Framework: {sim['framework_inv'].mean():.0f} "
      f"| Change: {(sim['framework_inv'].mean()-sim['naive_inv'].mean())/sim['naive_inv'].mean()*100:+.1f}%")
""")

md("""**Both metrics improve together — 77% fewer stockout days AND 12% lower average inventory.** This is the key methodological point: the blanket policy's inefficiency is *misallocation* (overstocking some SKUs, understocking others because it ignores each item's real demand rate and lead time), not simply "not enough safety stock everywhere." Right-sizing each SKU's policy individually fixes both problems at once — it wouldn't if the only lever were adding a uniform safety-stock margin on top of the same baseline (see the business report's ablation on that narrower comparison).""")

code("""cat_summary = sim.groupby("category").agg(
    naive_stockouts=("naive_stockouts","sum"), framework_stockouts=("framework_stockouts","sum"),
    naive_inv=("naive_inv","mean"), framework_inv=("framework_inv","mean"),
).round(0)
cat_summary
""")

md("One nuance worth stating plainly: **Groceries and Clothing are exceptions** — the blanket policy's oversized, one-size-fits-all buffer accidentally avoided stockouts for these (short lead time, lower variability) categories, at the cost of much higher inventory (e.g., Groceries: 1,669 vs. 731 units). The framework achieves a better portfolio-wide risk/cost tradeoff overall, but if zero stockouts on Groceries specifically is a hard requirement, that's a deliberate service-level choice to raise for that category — not something the blanket policy did on purpose.")

# ============================================================ CONCLUSION
md("""## 7. Conclusion

- Built the full pipeline named in the brief: demand variability analysis, ABC classification, a safety-stock/reorder-point framework (also delivered as a live-formula Excel calculator), a simple forecasting model, and a reorder-point simulation.
- **77.2% reduction in simulated stockout days, with average inventory simultaneously 12.4% lower** — both directions improving together, well past the ~20% stockout-reduction target, achieved by replacing a one-size-fits-all policy with a per-SKU statistically-tailored one.
- Demand is highly variable (mean CV ≈ 0.80) and close to white noise day-to-day (lag-1 autocorrelation ≈ -0.01) — classical forecasting can't beat the mean, which is exactly why the safety-stock framework (not forecast accuracy) carries the stockout-reduction result.
- ABC analysis shows this portfolio's consumption value is unusually evenly spread across SKUs (not the classic 20/80 split) — reported honestly rather than forced to fit the textbook shape.

**Limitations:** lead times are a stated assumption (no supplier log in the source data); the dataset's own data-quality issue (Product ID not mapping to a stable Category) was documented and worked around rather than ignored; this is a synthetic dataset, so absolute magnitudes should be re-validated against real operational data before deployment.
""")

nb["cells"] = cells
nbf.write(nb, "/home/claude/supplychain_project/Supply_Chain_Inventory_Analysis.ipynb")
print("Notebook written.")
