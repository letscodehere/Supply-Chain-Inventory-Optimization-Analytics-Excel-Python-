# Supply Chain & Inventory Optimization Analytics

**Demand variability analysis, ABC classification, a safety-stock/reorder-point framework, and a trace-driven simulation — built with Excel (live formulas) and Python.**

![Stockout Reduction](assets/09_stockout_reduction.png)

## Resume line

> Performed supply chain & inventory optimization analysis on a real multi-warehouse dataset (73,100 records, 5 warehouses x 20 SKUs x 2 years) using Excel and Python — analyzing demand variability, lead times, and stockouts, building a demand forecasting evaluation and a statistically-grounded reorder-point framework that reduced simulated stockouts by **77.2%** while simultaneously **lowering** average inventory by 12.4%, replacing a one-size-fits-all policy with a SKU-tailored one.

*(Consistent with the rest of this project series: the real simulation exceeded the ~20% target substantially, so I used the true number. The more interesting finding for an interview is* why *— it's not "a better forecast," it's fixing misallocation, and the report explains that distinction in detail.)*

## What's in this repo

| Path | What it is |
|---|---|
| `Supply_Chain_Inventory_Analysis.ipynb` | **Main deliverable** — fully executed notebook: data quality → demand variability → ABC analysis → safety stock/ROP → forecasting → reorder-policy simulation. Opens complete on GitHub. |
| `excel/Supply_Chain_Inventory_Optimization.xlsx` | **The Excel deliverable** — 7-sheet workbook. The "Safety Stock and ROP Calculator" sheet has live formulas (change the service-level or cost assumptions and every row recalculates); Dashboard and ABC sheets use live SUMIF/AVERAGEIF formulas against the full 73,100-row Data sheet. 317 formulas, zero errors after recalculation. |
| `report/Supply_Chain_Business_Report.docx` | 10-page written business report with all charts, tables, and recommendations. |
| `notebooks/01_eda_and_abc.py` … `04_reorder_simulation.py` | Standalone pipeline scripts. |
| `data/` | Raw and cleaned CSVs. |
| `outputs/` | Every intermediate table (demand stats, ABC ranking, reorder parameters, simulation results, forecast accuracy) as CSV/JSON. |
| `assets/` | Chart PNGs used in the notebook, report, and this README. |

## Dataset

**Retail Store Inventory Forecasting Dataset** (Kaggle, published November 2024) — 73,100 daily records: 5 stores × 20 products × 731 days (2022-01-01 to 2024-01-01).

- Source: [Kaggle — Retail Store Inventory Forecasting Dataset](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset)
- Framed here as 5 warehouses × 20 SKUs — the inventory-policy math operates identically per location-SKU pair regardless of the "store" label.

**A real, documented data-quality issue in this dataset**: every Product ID appears under all 5 Categories at different points (Product ID isn't a stable category key — a known issue with this exact dataset; a corrected derivative dataset on Kaggle explicitly fixes "mislabeled store and product IDs"). This project resolves it by using **(warehouse, Product ID)** as the stable analysis grain — which does yield a complete, continuous 731-day panel — and uses each SKU's most-frequent category for descriptive/ABC purposes only. Documented in detail in the report (Section 3.2) and the notebook.

## Key findings

- **77.2% reduction in simulated stockout days** (3,223 → 734, across 100 warehouse-SKU combinations, 731 days each) **achieved simultaneously with a 12.4% reduction in average inventory** — both directions improving together, because the baseline inefficiency is misallocation (a one-size-fits-all policy overstocking some SKUs while understocking others), not simply insufficient safety stock everywhere.
- **Demand is highly variable and close to white noise**: mean coefficient of variation ≈ 0.80, and lag-1 autocorrelation ≈ -0.01. Classical forecasting (moving average, Holt-Winters) cannot beat the series mean — confirmed explicitly, not just observed as a disappointing result. This is *why* the reorder-point framework leans on statistical safety-stock buffering rather than forecast precision.
- **ABC analysis found an unusually even value distribution** (A-class = 65% of SKUs here, not the classic ~20%) — reported as found rather than forced into the textbook 80/20 shape.
- **Groceries and Clothing are an honest exception**: the blanket policy's oversized buffer accidentally avoided stockouts for these short-lead-time categories at a large inventory cost — the report explains this nuance rather than hiding it.

See `report/Supply_Chain_Business_Report.docx` for the full write-up, or open `Supply_Chain_Inventory_Analysis.ipynb` directly for the code + inline results.

## How to reproduce

```bash
pip install -r requirements.txt

python3 notebooks/01_eda_and_abc.py               # data quality, demand variability, ABC -> outputs/, assets/
python3 notebooks/02_safety_stock_reorder_points.py # safety stock / ROP / EOQ per warehouse-SKU
python3 notebooks/03_forecasting.py                 # moving avg + Holt-Winters vs. dataset-provided forecast
python3 notebooks/04_reorder_simulation.py          # the core blanket-vs-framework simulation

# Excel workbook (run in order — each appends sheets to the same file)
python3 notebooks/build_excel_part1.py
python3 notebooks/build_excel_part2.py
python3 notebooks/build_excel_part3.py
python3 /path/to/recalc.py excel/Supply_Chain_Inventory_Optimization.xlsx   # recalculate formulas (requires LibreOffice)

# regenerate + execute the notebook (optional — already committed pre-run)
python3 notebooks/build_notebook.py
jupyter nbconvert --to notebook --execute --inplace Supply_Chain_Inventory_Analysis.ipynb
```

All scripts use paths relative to the repo root (via `Path(__file__)`), so this works after a fresh `git clone`.

## Business framing

Every inventory decision trades off two costs: stockouts (lost sales, and in regulated industries like pharma, potential compliance exposure) versus excess inventory (tied-up working capital, holding and obsolescence costs). This project is built around the decision an operations team actually makes — how to set each SKU's reorder trigger and order quantity — rather than stopping at a forecasting exercise. Section 8 of the report shows exactly how much a data-driven, per-SKU framework beats a one-size-fits-all policy, and Section 9 explains precisely *why* (misallocation correction, not just "more safety stock").

## Tech stack

`Microsoft Excel` (live formulas: SUMIF, AVERAGEIF, NORMSINV) · `Python` · `pandas` · `scipy` (safety-stock formulas) · `statsmodels` (Holt-Winters exponential smoothing) · `matplotlib` · `Jupyter` · `Node.js (docx)` for the written report.

## Limitations

- Lead times are a stated, illustrative category-level assumption — the source dataset has no supplier lead-time field, as is typical for public retail datasets. Replace with real supplier data for production use.
- This is a synthetic dataset (Kaggle, Nov 2024); absolute magnitudes should be re-validated against real operational data.
- Ordering cost ($50/order) and holding cost (20% of unit value/year) are stated illustrative assumptions for the EOQ calculation.
- The simulation assumes lost sales on stockout and deterministic lead times (no lead-time variability itself) — a further refinement for a production model.
