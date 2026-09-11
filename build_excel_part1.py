import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

DATA_DIR = "/home/claude/supplychain_project/data"
OUT_DIR = "/home/claude/supplychain_project/outputs"
XLSX_PATH = "/home/claude/supplychain_project/excel/Supply_Chain_Inventory_Optimization.xlsx"

NAVY, TEAL, GOLD, RED = "1F3864", "2E8B8B", "D4A017", "B23A48"
LIGHT, YELLOW, WHITE = "EDF1F7", "FFF2CC", "FFFFFF"

HEADER_FONT = Font(name="Arial", bold=True, color=WHITE, size=11)
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
TITLE_FONT = Font(name="Arial", bold=True, color=NAVY, size=18)
SUBTITLE_FONT = Font(name="Arial", italic=True, color="595959", size=10)
KPI_LABEL_FONT = Font(name="Arial", bold=True, color="595959", size=9)
KPI_VALUE_FONT = Font(name="Arial", bold=True, color=NAVY, size=16)
BODY_FONT = Font(name="Arial", size=10)
NOTE_FONT = Font(name="Arial", italic=True, size=9, color="808080")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
KPI_FILL = PatternFill("solid", fgColor=LIGHT)
COMPUTED_FILL = PatternFill("solid", fgColor=YELLOW)

data = pd.read_csv(f"{DATA_DIR}/inventory_clean.csv")
abc = pd.read_csv(f"{OUT_DIR}/abc_analysis.csv")
abc_summary = pd.read_csv(f"{OUT_DIR}/abc_summary.csv")
reorder = pd.read_csv(f"{OUT_DIR}/reorder_parameters.csv")
sim = pd.read_csv(f"{OUT_DIR}/simulation_results.csv")
sim_cat = pd.read_csv(f"{OUT_DIR}/simulation_by_category.csv")
import json
with open(f"{OUT_DIR}/simulation_summary.json") as f:
    sim_summary = json.load(f)
forecast_summary = pd.read_csv(f"{OUT_DIR}/forecast_accuracy_summary.csv", index_col=0)

N_ROWS = len(data)
LAST_ROW = N_ROWS + 1
DS = "'Data'"
COL = {name: get_column_letter(i + 1) for i, name in enumerate(data.columns)}

wb = Workbook()
wb.remove(wb.active)


def style_header_row(ws, row, ncols, start_col=1):
    for c in range(start_col, start_col + ncols):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def fast_write_large_df(ws, df, start_row=1):
    ws.append(list(df.columns))
    for row in df.itertuples(index=False):
        ws.append(row)
    style_header_row(ws, start_row, len(df.columns))


def write_small_table(ws, df, start_row, start_col=1, table_name=None):
    for j, col in enumerate(df.columns):
        ws.cell(row=start_row, column=start_col + j, value=col)
    style_header_row(ws, start_row, len(df.columns), start_col)
    r0 = start_row + 1
    for i, row in enumerate(df.itertuples(index=False)):
        for j, val in enumerate(row):
            cell = ws.cell(row=r0 + i, column=start_col + j, value=val)
            cell.font = BODY_FONT
            cell.border = BORDER
    end_row = r0 + len(df) - 1
    if len(df) > 0:
        end_col_letter = get_column_letter(start_col + len(df.columns) - 1)
        start_col_letter = get_column_letter(start_col)
        ref = f"{start_col_letter}{start_row}:{end_col_letter}{end_row}"
        tbl = Table(displayName=table_name, ref=ref)
        tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tbl)
    return end_row


def autosize(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def kpi_card(ws, row, col, label, value, is_computed=False, number_format=None):
    lbl_cell = ws.cell(row=row, column=col, value=label)
    lbl_cell.font = KPI_LABEL_FONT
    val_cell = ws.cell(row=row + 1, column=col, value=value)
    val_cell.font = KPI_VALUE_FONT
    if number_format:
        val_cell.number_format = number_format
    for rr in (row, row + 1):
        c = ws.cell(row=rr, column=col)
        c.fill = COMPUTED_FILL if is_computed else KPI_FILL
        c.border = BORDER
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)
    ws.merge_cells(start_row=row + 1, start_column=col, end_row=row + 1, end_column=col + 1)


# ====================================================================
# SHEET 1 — Read Me
# ====================================================================
ws = wb.create_sheet("Read Me")
ws["B2"] = "Supply Chain & Inventory Optimization Analytics"
ws["B2"].font = TITLE_FONT
ws["B3"] = "Excel Companion Workbook"
ws["B3"].font = SUBTITLE_FONT

rows_info = [
    ("Dataset", "Retail Store Inventory Forecasting Dataset (Kaggle, Nov 2024) - 73,100 daily "
                "records: 5 warehouses x 20 SKUs x 731 days (2022-01-01 to 2024-01-01)."),
    ("Source", "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset"),
    ("Reproducible download", "A GitHub-hosted mirror of the identical file was used for a scripted "
                               "download. See README.md and notebooks/."),
    ("", ""),
    ("Data-quality note", "Every Product ID in this dataset appears under all 5 Categories at "
                           "different points (Product ID is not a stable category key - a known issue "
                           "in this dataset, since fixed in a derivative Kaggle dataset). Resolved here "
                           "by using (Warehouse, Product ID) as the stable analysis grain and assigning "
                           "each SKU its single most-frequent category for descriptive/ABC purposes only."),
    ("", ""),
    ("Sheet guide", ""),
    ("Data", "The cleaned, full 73,100-row dataset. Every formula in this workbook reads from here."),
    ("Dashboard", "Top-line KPIs and category breakdowns. White cells are live formulas; yellow "
                  "cells are values computed in Python (ABC ranks, safety stock, simulation results) "
                  "because they require ranking/cumulative logic or a multi-day simulation loop that "
                  "is impractical as a native Excel formula at this scale."),
    ("ABC Analysis", "SKU consumption-value ranking and A/B/C classification - precomputed in Python "
                     "(cumulative ranking across 20 SKUs), with a Pareto chart."),
    ("Safety Stock and ROP Calculator", "The core 'using Excel' deliverable - live formulas computing "
                                          "Safety Stock, Reorder Point, and EOQ per warehouse-SKU from "
                                          "editable assumption cells (lead time, service level, costs). "
                                          "Change any assumption and every row recalculates."),
    ("Simulation Results", "Before/after comparison of a one-size-fits-all 'blanket' reorder policy "
                            "vs. the SKU-tailored framework, precomputed in Python (a 731-day "
                            "day-by-day inventory simulation isn't practical as a spreadsheet formula) "
                            "- see notebooks/04_reorder_simulation.py for the full logic."),
]
r = 5
for label, text in rows_info:
    ws.cell(row=r, column=2, value=label).font = Font(name="Arial", bold=True, size=10, color=NAVY)
    c = ws.cell(row=r, column=3, value=text)
    c.font = BODY_FONT
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 42 if text else 8
    r += 1

autosize(ws, {"A": 3, "B": 26, "C": 100})
ws.sheet_view.showGridLines = False

# ====================================================================
# SHEET 2 — Data
# ====================================================================
ws_data = wb.create_sheet("Data")
fast_write_large_df(ws_data, data)
ws_data.freeze_panes = "A2"
autosize(ws_data, {get_column_letter(i + 1): 13 for i in range(len(data.columns))})
print("Data sheet written.")

# ====================================================================
# SHEET 3 — Dashboard
# ====================================================================
ws = wb.create_sheet("Dashboard")
ws.sheet_view.showGridLines = False
ws["B2"] = "Supply Chain & Inventory Optimization Dashboard"
ws["B2"].font = TITLE_FONT
ws["B3"] = "5 Warehouses | 20 SKUs | 2022-2024"
ws["B3"].font = SUBTITLE_FONT

sold_rng = f"{DS}!${COL['units_sold']}$2:${COL['units_sold']}${LAST_ROW}"
wh_rng = f"{DS}!${COL['warehouse_id']}$2:${COL['warehouse_id']}${LAST_ROW}"
sku_rng = f"{DS}!${COL['sku']}$2:${COL['sku']}${LAST_ROW}"
price_rng = f"{DS}!${COL['price']}$2:${COL['price']}${LAST_ROW}"

kpi_card(ws, 5, 2, "TOTAL UNITS SOLD", f"=SUM({sold_rng})", number_format='#,##0')
kpi_card(ws, 5, 4, "WAREHOUSES", 5, is_computed=True, number_format='0')
kpi_card(ws, 5, 6, "SKUs TRACKED", 20, is_computed=True, number_format='0')
kpi_card(ws, 5, 8, "DAYS OF HISTORY", 731, is_computed=True, number_format='0')

kpi_card(ws, 8, 2, "STOCKOUT DAYS REDUCTION\n(framework vs. blanket policy)",
         sim_summary["stockout_day_reduction_pct"] / 100, is_computed=True, number_format='0.0%')
kpi_card(ws, 8, 4, "AVG. INVENTORY CHANGE\n(framework vs. blanket policy)",
         sim_summary["avg_inventory_change_pct"] / 100, is_computed=True, number_format='+0.0%;-0.0%')
kpi_card(ws, 8, 6, "FRAMEWORK SERVICE LEVEL",
         sim_summary["optimized_avg_service_level_pct"] / 100, is_computed=True, number_format='0.0%')
kpi_card(ws, 8, 8, "BLANKET SERVICE LEVEL",
         sim_summary["naive_avg_service_level_pct"] / 100, is_computed=True, number_format='0.0%')

ws.cell(row=11, column=2, value=(
    "White cells = live formulas (recalculate if 'Data' changes). Yellow cells = values computed "
    "in Python — distinct counts, ABC ranks, and simulation results (see Read Me)."
)).font = NOTE_FONT

# Category breakdown (live SUMIF formulas)
cat_rng = f"{DS}!${COL['category']}$2:${COL['category']}${LAST_ROW}"
categories = sorted(data["category"].unique().tolist())
row0 = 13
ws.cell(row=row0, column=2, value="Units Sold by Category").font = Font(name="Arial", bold=True, size=12, color=NAVY)
hdr = ["Category", "Units Sold", "Avg. Price", "Est. Revenue"]
for j, h in enumerate(hdr):
    ws.cell(row=row0 + 1, column=2 + j, value=h)
style_header_row(ws, row0 + 1, len(hdr), 2)
for i, cat in enumerate(categories):
    rr = row0 + 2 + i
    ws.cell(row=rr, column=2, value=cat).font = BODY_FONT
    units_cell = ws.cell(row=rr, column=3, value=f"=SUMIF({cat_rng},$B{rr},{sold_rng})")
    units_cell.number_format = '#,##0'
    price_cell = ws.cell(row=rr, column=4, value=f"=AVERAGEIF({cat_rng},$B{rr},{price_rng})")
    price_cell.number_format = '$#,##0.00'
    rev_cell = ws.cell(row=rr, column=5, value=f"=C{rr}*D{rr}")
    rev_cell.number_format = '$#,##0'
    for cc in range(2, 6):
        ws.cell(row=rr, column=cc).border = BORDER

row_after_cat = row0 + 2 + len(categories)
autosize(ws, {"A": 2, "B": 22, "C": 14, "D": 14, "E": 16, "F": 4, "G": 20, "H": 20})

chart1 = BarChart()
chart1.type = "col"
chart1.title = "Units Sold by Category"
data_ref = Reference(ws, min_col=3, min_row=row0 + 1, max_row=row_after_cat - 1)
cats_ref = Reference(ws, min_col=2, min_row=row0 + 2, max_row=row_after_cat - 1)
chart1.add_data(data_ref, titles_from_data=True)
chart1.set_categories(cats_ref)
chart1.height, chart1.width = 9, 16
ws.add_chart(chart1, "B" + str(row_after_cat + 2))

wb.save(XLSX_PATH)
print("Dashboard sheet written. Saved:", XLSX_PATH)
