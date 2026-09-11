"""
Supply Chain & Inventory Optimization Analytics — Demand Forecasting
========================================================================
Builds two simple, standard forecasting approaches per SKU-warehouse
series and evaluates them on a held-out final-60-day test window,
benchmarked against the dataset's own pre-supplied "Demand Forecast"
column (a useful, already-present reference baseline).

Models:
  1. 7-day trailing moving average (naive baseline)
  2. Holt-Winters exponential smoothing with weekly seasonality
     (statsmodels) — the "simple forecasting model" referenced in the
     project brief

Run: python3 03_forecasting.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

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
TEST_DAYS = 60

combos = df[["warehouse_id", "sku"]].drop_duplicates().values.tolist()
results = []
example_plot_saved = False

for wh, sku in combos:
    sub = df[(df["warehouse_id"] == wh) & (df["sku"] == sku)].sort_values("date").reset_index(drop=True)
    series = sub.set_index("date")["units_sold"]
    given_forecast = sub.set_index("date")["demand_forecast_given"]

    train, test = series.iloc[:-TEST_DAYS], series.iloc[-TEST_DAYS:]
    given_test = given_forecast.iloc[-TEST_DAYS:]

    # 1. Moving average baseline: repeat the last 7-day trailing average
    ma_pred_value = train.iloc[-7:].mean()
    ma_pred = pd.Series(ma_pred_value, index=test.index)

    # 2. Holt-Winters exponential smoothing, weekly seasonality
    try:
        hw_model = ExponentialSmoothing(
            train, trend="add", seasonal="add", seasonal_periods=7, initialization_method="estimated"
        ).fit(optimized=True)
        hw_pred = hw_model.forecast(TEST_DAYS)
        hw_pred.index = test.index
    except Exception:
        hw_pred = ma_pred  # fallback, rare

    def mae(a, b): return float(np.mean(np.abs(a - b)))
    def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
    def mape(a, b): return float(np.mean(np.abs((a - b) / a.replace(0, np.nan))) * 100)

    results.append({
        "warehouse_id": wh, "sku": sku,
        "MAE_given": mae(test, given_test), "RMSE_given": rmse(test, given_test), "MAPE_given": mape(test, given_test),
        "MAE_moving_avg": mae(test, ma_pred), "RMSE_moving_avg": rmse(test, ma_pred), "MAPE_moving_avg": mape(test, ma_pred),
        "MAE_holt_winters": mae(test, hw_pred), "RMSE_holt_winters": rmse(test, hw_pred), "MAPE_holt_winters": mape(test, hw_pred),
    })

    if not example_plot_saved and wh == "S001" and sku == "P0001":
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(train.index[-90:], train.iloc[-90:], color=GREY, label="Training history (last 90 days)")
        ax.plot(test.index, test.values, color=NAVY, linewidth=2, label="Actual (test period)")
        ax.plot(test.index, hw_pred.values, color=TEAL, linewidth=2, linestyle="--", label="Holt-Winters forecast")
        ax.plot(test.index, given_test.values, color=GOLD, linewidth=1.5, linestyle=":", label="Dataset-provided forecast")
        ax.set_title(f"Demand Forecast Example — Warehouse {wh}, SKU {sku}", fontsize=13, fontweight="bold", color=NAVY, loc="left")
        ax.set_ylabel("Units Sold")
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(ASSETS / "07_forecast_example.png", dpi=160)
        plt.close(fig)
        example_plot_saved = True

results_df = pd.DataFrame(results)
results_df.to_csv(OUT_DIR / "forecast_accuracy_by_sku.csv", index=False)

summary = pd.DataFrame({
    "Dataset-Provided Forecast": [results_df["MAE_given"].mean(), results_df["RMSE_given"].mean(), results_df["MAPE_given"].mean()],
    "7-Day Moving Average": [results_df["MAE_moving_avg"].mean(), results_df["RMSE_moving_avg"].mean(), results_df["MAPE_moving_avg"].mean()],
    "Holt-Winters Exp. Smoothing": [results_df["MAE_holt_winters"].mean(), results_df["RMSE_holt_winters"].mean(), results_df["MAPE_holt_winters"].mean()],
}, index=["MAE", "RMSE", "MAPE %"]).round(2)
summary.to_csv(OUT_DIR / "forecast_accuracy_summary.csv")
print(summary.to_string())

# Chart: MAE comparison
fig, ax = plt.subplots(figsize=(8, 5))
methods = summary.columns.tolist()
mae_vals = summary.loc["MAE"].values
bars = ax.bar(methods, mae_vals, color=[GOLD, GREY, TEAL])
for b, v in zip(bars, mae_vals):
    ax.text(b.get_x() + b.get_width()/2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Mean Absolute Error (units)")
ax.set_title("Forecast Accuracy Comparison\n(60-day held-out test, avg. across 100 SKU-warehouse series)",
             fontsize=12, fontweight="bold", color=NAVY, loc="left")
ax.tick_params(axis="x", rotation=10)
fig.tight_layout()
fig.savefig(ASSETS / "08_forecast_accuracy_comparison.png", dpi=160)
plt.close(fig)

print("\nForecasting evaluation complete.")
