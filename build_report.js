const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, ImageRun, Header, Footer,
  PageNumber,
} = require("docx");

const ASSETS = "/home/claude/supplychain_project/assets";
const NAVY = "1F3864";
const TEAL = "2E8B8B";
const GOLD = "D4A017";
const RED = "B23A48";
const GREY = "595959";
const LIGHTGREY = "F2F2F2";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 } });
}
function body(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, size: 21, ...opts })],
    spacing: { after: 160 },
    alignment: AlignmentType.JUSTIFIED,
  });
}
function bullet(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, size: 21, ...opts })],
    bullet: { level: 0 },
    spacing: { after: 90 },
  });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 18, color: GREY })],
    spacing: { after: 260 },
    alignment: AlignmentType.CENTER,
  });
}
function tableCaption(num, text) {
  return new Paragraph({
    children: [new TextRun({ text: `Table ${num}. ${text}`, size: 19, bold: true, color: NAVY })],
    spacing: { before: 160, after: 100 },
  });
}
function image(file, width, height) {
  const data = fs.readFileSync(`${ASSETS}/${file}`);
  return new Paragraph({
    children: [new ImageRun({ data, transformation: { width, height }, type: "png" })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
  });
}
function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: NAVY, color: "auto" },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 19 })], alignment: AlignmentType.CENTER })],
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
  });
}
function dataTable(headers, rows, colWidths) {
  const headerRow = new TableRow({ children: headers.map((t, i) => headerCell(t, colWidths[i])), tableHeader: true });
  const bodyRows = rows.map((r, ridx) => new TableRow({
    children: r.map((val, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ridx % 2 === 0 ? "FFFFFF" : LIGHTGREY, color: "auto" },
      children: [new Paragraph({
        children: [new TextRun({ text: String(val), size: 19 })],
        alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
      })],
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
    })),
  }));
  return new Table({ rows: [headerRow, ...bodyRows], width: { size: colWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: colWidths });
}
function kpiRow(items) {
  const w = Math.floor(9360 / items.length);
  return new Table({
    columnWidths: items.map(() => w),
    width: { size: 9360, type: WidthType.DXA },
    rows: [new TableRow({
      children: items.map(([label, value]) => new TableCell({
        width: { size: w, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: "EDF1F7", color: "auto" },
        margins: { top: 160, bottom: 160, left: 120, right: 120 },
        children: [
          new Paragraph({ children: [new TextRun({ text: label, size: 15, bold: true, color: GREY })], alignment: AlignmentType.CENTER }),
          new Paragraph({ children: [new TextRun({ text: value, size: 27, bold: true, color: NAVY })], alignment: AlignmentType.CENTER, spacing: { before: 60 } }),
        ],
      })),
    })],
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        run: { size: 32, bold: true, color: NAVY, font: "Calibri" },
        paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { color: NAVY, space: 4, style: BorderStyle.SINGLE, size: 8 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        run: { size: 25, bold: true, color: TEAL, font: "Calibri" },
        paragraph: { spacing: { before: 260, after: 120 } } },
    ],
  },
  sections: [
    // ============================================================ COVER
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [
        new Paragraph({ text: "", spacing: { before: 1600 } }),
        new Paragraph({ children: [new TextRun({ text: "SUPPLY CHAIN & INVENTORY", bold: true, size: 52, color: NAVY })], alignment: AlignmentType.CENTER }),
        new Paragraph({ children: [new TextRun({ text: "OPTIMIZATION ANALYTICS", bold: true, size: 52, color: NAVY })], alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
        new Paragraph({ children: [new TextRun({ text: "Business Insights Report", size: 28, color: TEAL, italics: true })], alignment: AlignmentType.CENTER, spacing: { after: 720 } }),
        new Paragraph({ children: [new TextRun({ text: "Dataset: Retail Store Inventory Forecasting (Kaggle, Nov 2024)", size: 22, color: GREY })], alignment: AlignmentType.CENTER }),
        new Paragraph({ children: [new TextRun({ text: "5 Warehouses | 20 SKUs | 731 Days | Excel + Python", size: 22, color: GREY })], alignment: AlignmentType.CENTER, spacing: { after: 720 } }),
        image("09_stockout_reduction.png", 340, 251),
        new Paragraph({ text: "", spacing: { before: 500 } }),
        new Paragraph({ children: [new TextRun({ text: "Prepared using Microsoft Excel (live safety-stock/ROP formulas) and Python (pandas, scipy, statsmodels, matplotlib)", size: 18, color: GREY, italics: true })], alignment: AlignmentType.CENTER }),
        new Paragraph({ children: [new TextRun({ text: "Source data: Kaggle - Retail Store Inventory Forecasting Dataset", size: 18, color: GREY, italics: true })], alignment: AlignmentType.CENTER }),
      ],
    },
    // ============================================================ BODY
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
      headers: {
        default: new Header({ children: [new Paragraph({
          children: [new TextRun({ text: "Supply Chain & Inventory Optimization Analytics — Business Insights Report", size: 15, color: GREY })],
          border: { bottom: { color: "D9D9D9", space: 4, style: BorderStyle.SINGLE, size: 4 } },
        })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Page ", size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY })],
        })] }),
      },
      children: [
        // ---------------------------------------------------- EXEC SUMMARY
        h1("1. Executive Summary"),
        body("This report analyzes 731 days of daily demand across 5 warehouses and 20 SKUs (100 " +
          "warehouse-SKU combinations, 73,100 records) to build a statistically-grounded safety-stock " +
          "and reorder-point framework, and to quantify its impact against a one-size-fits-all baseline " +
          "policy using a trace-driven simulation replayed against real historical demand. The objective " +
          "is to translate demand variability and lead-time exposure into an inventory policy that " +
          "reduces stockouts without inflating carrying costs — the core operations-efficiency trade-off " +
          "behind every inventory management decision."),
        kpiRow([
          ["STOCKOUT DAY REDUCTION", "77.2%"],
          ["AVG. INVENTORY CHANGE", "-12.4%"],
          ["SERVICE LEVEL ACHIEVED", "99.0%"],
          ["WAREHOUSE-SKU PAIRS", "100"],
        ]),
        new Paragraph({ text: "", spacing: { after: 200 } }),
        h2("Headline findings"),
        bullet("Replacing a one-size-fits-all ('blanket') reorder policy with a SKU-tailored " +
          "statistical framework reduces simulated stockout days by 77.2% (3,223 to 734 days across " +
          "the 731-day, 100-combination simulation) while simultaneously LOWERING average inventory " +
          "by 12.4% — both directions improving together, well past the ~20% stockout-reduction target " +
          "originally set for this project."),
        bullet("Daily demand is highly variable (mean coefficient of variation \u2248 0.80 across all " +
          "warehouse-SKU pairs) and behaves close to statistical white noise day-to-day (lag-1 " +
          "autocorrelation \u2248 -0.01) \u2014 classical time-series forecasting cannot beat the series mean, " +
          "which is exactly why the reorder-point framework leans on statistical safety-stock " +
          "buffering rather than forecast precision to prevent stockouts."),
        bullet("ABC analysis shows this SKU portfolio's consumption value is unusually evenly spread " +
          "(the A-class covers 65% of SKUs here, not the classic ~20%) \u2014 reported as found rather " +
          "than forced into the textbook 80/20 shape."),
        bullet("The improvement is not uniform: Groceries and Clothing are exceptions where the " +
          "blanket policy's oversized buffer accidentally avoided stockouts at a large inventory cost " +
          "\u2014 an important nuance for how this framework should be communicated to stakeholders."),

        // ---------------------------------------------------- BUSINESS PROBLEM
        h1("2. Business Problem & Objective"),
        body("Inventory management sits on a permanent trade-off: too little stock causes stockouts " +
          "(lost sales, dissatisfied customers, and in regulated industries such as pharmaceuticals, " +
          "potential compliance exposure from unfulfilled orders); too much stock ties up working " +
          "capital and increases holding, obsolescence, and spoilage costs. A reorder-point framework " +
          "that accounts for each SKU's actual demand variability and supply lead time \u2014 rather than " +
          "a uniform rule applied across a whole catalog \u2014 is the standard operations-research answer " +
          "to this trade-off, and is exactly what this report builds and tests."),
        body("This analysis is framed around a decision a supply chain or operations team actually " +
          "makes: given a fixed catalog of SKUs across multiple stocking locations, how should each " +
          "one's reorder trigger and order quantity be set? Section 8's simulation directly compares " +
          "the answer this framework gives against the status quo of an undifferentiated policy."),

        // ---------------------------------------------------- DATA SOURCE
        h1("3. Data Source & Methodology"),
        h2("3.1 Dataset"),
        body("Kaggle \u2014 \u201cRetail Store Inventory Forecasting Dataset\u201d (published November 2024): " +
          "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset. " +
          "73,100 daily records spanning 5 stores, 20 products, and 5 categories from 2022-01-01 to " +
          "2024-01-01. A GitHub-hosted mirror of the identical file was used for a scripted, " +
          "reproducible download. The dataset's 5 stores are treated here as 5 warehouse/distribution " +
          "locations \u2014 the inventory-policy mathematics applies identically per location-SKU pair " +
          "regardless of that label."),
        h2("3.2 A data-quality issue worth documenting"),
        body("Every one of the 20 Product IDs in this dataset appears under all 5 Categories at " +
          "different points \u2014 Product ID is not a stable category key (a known issue with this " +
          "dataset; a corrected derivative dataset published later on Kaggle explicitly fixes " +
          "\u201cmislabeled store and product IDs\u201d). This is resolved here by using (warehouse, Product " +
          "ID) as the stable analysis grain \u2014 which does yield a complete, continuous 731-day daily " +
          "panel \u2014 and assigning each SKU its single most-frequent category for descriptive and ABC " +
          "purposes only, never at the daily level."),
        h2("3.3 Tools and approach"),
        dataTable(
          ["Stage", "Tool", "Purpose"],
          [
            ["Data quality & ABC analysis", "Python (pandas)", "Cleaning verification, demand variability, ABC classification"],
            ["Safety stock / ROP / EOQ", "Python (scipy) + Excel", "Statistical formulas; delivered as a live-formula Excel calculator"],
            ["Forecasting", "Python (statsmodels)", "Moving average and Holt-Winters exponential smoothing"],
            ["Reorder-policy simulation", "Python (pandas, numpy)", "731-day trace-driven simulation against real historical demand"],
            ["Visualization", "Python (matplotlib) + Excel", "All charts in this report and the Excel dashboard"],
          ],
          [3000, 2600, 3760],
        ),

        // ---------------------------------------------------- DEMAND VARIABILITY
        h1("4. Demand Variability"),
        image("01_demand_variability.png", 380, 245),
        figureCaption(1, "Coefficient of variation (std / mean daily demand) across all 100 warehouse-SKU pairs."),
        body("Demand variability is uniformly high across the portfolio: coefficient of variation " +
          "(CV) ranges from 0.67 to 0.92 with a mean of 0.80, meaning day-to-day demand routinely " +
          "swings by roughly 80% of its own average. This single statistic is the primary driver of " +
          "everything that follows \u2014 it is why safety stock needs to be substantial, and it foreshadows " +
          "the forecasting result in Section 6."),
        image("03_monthly_demand_trend.png", 460, 193),
        figureCaption(2, "Total monthly units sold across all warehouses, 2022-2024."),

        // ---------------------------------------------------- ABC
        h1("5. ABC Analysis"),
        body("SKUs were ranked by total consumption value (units sold \u00d7 average price, aggregated " +
          "across all warehouses) and classified using the standard cumulative-value cutoffs (A: top " +
          "\u224870% of value, B: next \u224820%, C: remaining \u224810%)."),
        tableCaption(1, "ABC classification summary."),
        dataTable(
          ["Class", "SKUs", "SKU Share", "Value Share"],
          [
            ["A", "13", "65.0%", "65.6%"],
            ["B", "4", "20.0%", "19.7%"],
            ["C", "3", "15.0%", "14.7%"],
          ],
          [1800, 2000, 2680, 2880],
        ),
        new Paragraph({ text: "", spacing: { after: 160 } }),
        image("04_abc_pareto.png", 460, 256),
        figureCaption(3, "ABC Pareto chart — SKU consumption value ranking."),
        body("This result is worth stating plainly rather than glossing over: unlike many real-world " +
          "retail portfolios, where roughly 20% of SKUs typically drive 70-80% of consumption value, " +
          "this dataset's value is spread nearly evenly across all 20 SKUs \u2014 the A-class needed 13 of " +
          "20 SKUs (65%) to reach 70% of value, not the classic handful. The standard ABC cutoffs are " +
          "still applied for methodological completeness, but the practical prioritization benefit of " +
          "ABC segmentation is more muted for this specific catalog than it would be for a typical " +
          "real-world SKU portfolio with genuine fast-mover/slow-mover concentration."),

        // ---------------------------------------------------- SAFETY STOCK
        h1("6. Safety Stock & Reorder Points"),
        body("The source dataset has no supplier lead-time field \u2014 unsurprising, since lead time is " +
          "operational/contractual data, not point-of-sale data, and is essentially never present in " +
          "public retail datasets of this kind. Category-level lead times below are therefore a " +
          "stated, explicit assumption, chosen to be directionally realistic and documented as the one " +
          "input that should be replaced with a real supplier log in a production deployment."),
        tableCaption(2, "Stated lead-time assumption by category (days), plus a small per-warehouse adjustment."),
        dataTable(
          ["Category", "Base Lead Time (days)", "Rationale"],
          [
            ["Groceries", "4", "Fast-moving, perishable, short supply chains"],
            ["Clothing", "8", "Moderate — seasonal batch production"],
            ["Toys", "10", "Moderate-to-long — often imported"],
            ["Electronics", "12", "Longer — complex component sourcing"],
            ["Furniture", "16", "Longest — bulky, made-to-order common"],
          ],
          [2400, 2800, 4160],
        ),
        new Paragraph({ text: "", spacing: { after: 160 } }),
        body("Safety stock and reorder points were computed using standard inventory theory: " +
          "Safety Stock = Z \u00d7 \u03c3d \u00d7 \u221aL, Reorder Point = (mean daily demand \u00d7 L) + Safety Stock, " +
          "targeting a 95% cycle service level (Z \u2248 1.645). Order quantities use the Economic Order " +
          "Quantity (EOQ) formula with stated illustrative cost assumptions ($50 ordering cost per " +
          "order, 20% annual holding cost as a share of unit value). All of this is delivered as live, " +
          "editable formulas in the accompanying Excel workbook \u2014 changing the service-level target " +
          "or cost assumptions recalculates every row instantly."),
        image("06_safety_stock_rop_by_category.png", 440, 248),
        figureCaption(4, "Average safety stock and reorder point by category, across warehouses."),

        // ---------------------------------------------------- FORECASTING
        h1("7. Demand Forecasting"),
        body("Two standard forecasting methods \u2014 a 7-day trailing moving average and Holt-Winters " +
          "exponential smoothing with weekly seasonality \u2014 were evaluated on a held-out final-60-day " +
          "window for every one of the 100 warehouse-SKU series, benchmarked against the dataset's own " +
          "pre-supplied \u201cDemand Forecast\u201d column."),
        image("07_forecast_example.png", 500, 225),
        figureCaption(5, "Forecast example, Warehouse S001 / SKU P0001. Both the trailing history and the test-period actuals swing wildly; Holt-Winters correctly reverts toward the mean rather than chasing noise."),
        tableCaption(3, "Forecast accuracy, 60-day held-out test (mean across 100 series)."),
        dataTable(
          ["Method", "MAE", "RMSE", "MAPE %"],
          [
            ["Dataset-Provided Forecast", "8.36", "10.03", "25.6%"],
            ["7-Day Moving Average", "93.43", "114.83", "330.9%"],
            ["Holt-Winters Exp. Smoothing", "89.10", "108.28", "329.2%"],
          ],
          [3600, 1920, 1920, 1920],
        ),
        new Paragraph({ text: "", spacing: { after: 160 } }),
        image("08_forecast_accuracy_comparison.png", 420, 262),
        figureCaption(6, "Forecast accuracy comparison (mean absolute error)."),
        body("Neither classical method comes close to the dataset's own forecast, and the reason is " +
          "identifiable rather than a modelling failure: daily demand in this dataset shows " +
          "essentially zero autocorrelation at every lag tested (1, 7, 14, and 30 days, all between " +
          "-0.02 and +0.02) \u2014 statistically indistinguishable from white noise around a stable mean. " +
          "No method that relies on historical patterns can outperform predicting the mean when the " +
          "series has no such patterns to find. This has a direct, important implication for inventory " +
          "policy: since day-to-day demand cannot be forecast with precision, the reorder-point " +
          "framework must lean on statistical safety-stock buffering against demand variance (Section " +
          "6) to prevent stockouts \u2014 not on a forecasting model correctly anticipating individual " +
          "days. This is standard, well-established inventory theory (provisioning for forecast error, " +
          "not just the point forecast), and this dataset is a clean illustration of exactly when and " +
          "why that principle matters."),

        // ---------------------------------------------------- SIMULATION
        h1("8. Reorder Policy Simulation: The Core Result"),
        body("A trace-driven, continuous-review inventory simulation replayed real historical daily " +
          "demand against two policies for all 100 warehouse-SKU combinations over the full 731-day " +
          "history:"),
        bullet("Blanket policy \u2014 a single portfolio-wide reorder point and order quantity applied " +
          "identically to every warehouse-SKU combination, representative of a business with no " +
          "per-SKU inventory analytics (e.g., \u201creorder around 1,929 units, order 672 units\u201d applied " +
          "the same way to a fast-moving grocery item and a slow-moving furniture item alike)"),
        bullet("Framework policy \u2014 each combination's own statistically-tailored reorder point and " +
          "EOQ from Section 6"),
        body("Both policies use each SKU's real physical lead time for order-arrival timing; only the " +
          "reorder trigger and order size differ between them, isolating the effect of moving from " +
          "one-size-fits-all to SKU-tailored parameters."),
        tableCaption(4, "Simulation results, aggregated across all 100 warehouse-SKU combinations."),
        dataTable(
          ["Metric", "Blanket Policy", "Framework Policy", "Change"],
          [
            ["Total stockout days", "3,223", "734", "-77.2%"],
            ["Average service level", "95.6%", "99.0%", "+3.4 pp"],
            ["Average on-hand inventory (units)", "1,036", "908", "-12.4%"],
          ],
          [3600, 1920, 1920, 1920],
        ),
        new Paragraph({ text: "", spacing: { after: 160 } }),
        image("09_stockout_reduction.png", 340, 251),
        figureCaption(7, "Total simulated stockout days: blanket vs. framework policy."),
        image("10_inventory_comparison.png", 340, 251),
        figureCaption(8, "Average on-hand inventory: blanket vs. framework policy."),
        body("Both metrics improve simultaneously \u2014 77.2% fewer stockout days and 12.4% lower average " +
          "inventory \u2014 which is the key methodological point of this analysis. The blanket policy's " +
          "inefficiency is misallocation: it ignores each SKU's real demand rate and lead time, so it " +
          "understocks fast-moving, long-lead-time items (causing stockouts) while overstocking slow, " +
          "short-lead-time items (causing excess inventory) at the same time. Right-sizing each " +
          "combination's policy individually corrects both problems at once. This is a materially " +
          "different \u2014 and more realistic \u2014 finding than would result from simply adding a uniform " +
          "safety-stock margin on top of an already-uniform baseline, which (as tested separately) " +
          "improves service level only by adding inventory, the classical safety-stock trade-off, " +
          "without the dual improvement shown here."),
        h2("A nuance worth stating plainly"),
        body("The improvement is not uniform across categories. Groceries and Clothing are exceptions: " +
          "the blanket policy's oversized, one-size-fits-all buffer \u2014 calibrated to the portfolio's " +
          "average lead time (10 days) \u2014 happened to massively over-provision these short-lead-time " +
          "(4 and 8 day), lower-variability categories, avoiding stockouts almost entirely but at a " +
          "large inventory cost (Groceries: 1,669 vs. 731 units under the framework). The framework " +
          "correctly right-sizes to each category's true, shorter lead time and carries less " +
          "inventory as a result, at the cost of a small number of stockouts it did not have before. " +
          "If zero stockouts on Groceries specifically is a hard business requirement, that is a " +
          "deliberate, adjustable service-level choice the framework makes explicit (simply raise the " +
          "target service level for that category) \u2014 not something the blanket policy achieved on " +
          "purpose."),

        // ---------------------------------------------------- RECOMMENDATIONS
        h1("9. Recommendations Summary"),
        bullet("Replace the one-size-fits-all reorder policy with the SKU-tailored framework " +
          "(Section 6, delivered as a live Excel calculator) \u2014 the simulation shows this reduces both " +
          "stockouts and excess inventory simultaneously, not a trade-off between them."),
        bullet("Prioritize obtaining real supplier lead-time data to replace the stated category-level " +
          "assumption used here \u2014 lead time is the single input in this analysis with the least " +
          "empirical grounding and the most direct effect on both safety stock and reorder point."),
        bullet("For Groceries and Clothing specifically, set an explicit, deliberate service-level " +
          "target (rather than inheriting one by accident from an oversized blanket buffer) \u2014 if " +
          "near-zero stockouts matter more than inventory cost for these categories, raise their " +
          "target service level above the portfolio default of 95%."),
        bullet("Do not invest heavily in forecast-accuracy improvement for this SKU portfolio \u2014 " +
          "demand's near-zero autocorrelation means the return on a more sophisticated forecasting " +
          "model is likely to be small; the safety-stock framework is where the leverage is."),
        bullet("Revisit the ABC classification's practical use given the unusually even value " +
          "distribution found here \u2014 a differentiated service-level policy by ABC class may add less " +
          "value for this specific catalog than it would for a more concentrated one."),

        // ---------------------------------------------------- LIMITATIONS
        h1("10. Limitations"),
        bullet("Lead times are a stated, illustrative assumption (category-level, with a small " +
          "warehouse adjustment) \u2014 the source dataset has no supplier lead-time field, as is typical " +
          "for public retail datasets. A production deployment should substitute real supplier data."),
        bullet("This is a synthetic dataset (Kaggle, Nov 2024); absolute demand levels, prices, and " +
          "the specific stockout/inventory magnitudes here should be re-validated against real " +
          "operational data before being used for an actual inventory decision."),
        bullet("The dataset's own data-quality issue \u2014 Product ID not mapping to a stable Category " +
          "\u2014 was documented and worked around by using (warehouse, Product ID) as the analysis grain; " +
          "Category is therefore descriptive only and not used at the daily level."),
        bullet("Ordering cost ($50/order) and holding cost (20% of unit value/year) used in the EOQ " +
          "calculation are stated illustrative assumptions, not measured figures \u2014 substitute a real " +
          "business's actual costs for a production estimate."),
        bullet("The simulation assumes lost sales on stockout (unmet demand is not backordered) and a " +
          "single supplier per SKU with deterministic lead time; real supply chains often have lead-" +
          "time variability itself, which would further increase the required safety stock."),

        // ---------------------------------------------------- CONCLUSION
        h1("11. Conclusion"),
        body("This analysis built a complete, evidence-based supply chain and inventory optimization " +
          "framework across 5 warehouses and 20 SKUs: demand variability analysis, ABC classification, " +
          "a statistically-grounded safety-stock and reorder-point framework (delivered as both a " +
          "Python pipeline and a live-formula Excel calculator), a forecasting evaluation that " +
          "correctly identified when classical time-series methods add little value, and a trace-" +
          "driven simulation quantifying the framework's real-world impact. The central finding \u2014 a " +
          "77.2% reduction in simulated stockout days achieved simultaneously with a 12.4% reduction " +
          "in average inventory \u2014 demonstrates that the right lever for this kind of operational " +
          "inefficiency is per-SKU statistical tailoring, not a uniform buffer, and provides a directly " +
          "actionable case for replacing one-size-fits-all inventory policies with a data-driven " +
          "framework."),

        // ---------------------------------------------------- APPENDIX
        h1("12. Appendix: Data Dictionary"),
        dataTable(
          ["Field", "Description"],
          [
            ["warehouse_id (Store ID)", "One of 5 stocking locations"],
            ["sku (Product ID)", "One of 20 products; see Section 3.2 for the category-stability caveat"],
            ["category", "Product category (5 total) \u2014 descriptive/ABC use only, see Section 3.2"],
            ["inventory_level", "Recorded on-hand inventory snapshot (not used as a running ledger \u2014 see notebooks/01_eda_and_abc.py)"],
            ["units_sold", "Realized daily demand \u2014 the primary series used throughout this analysis"],
            ["units_ordered", "Units replenished that day, per the source data"],
            ["demand_forecast_given", "The dataset's own pre-supplied forecast \u2014 used as a benchmark in Section 7"],
            ["price / discount_pct / competitor_price", "Pricing fields, used for consumption-value (ABC) calculation"],
            ["lead_time_days (derived)", "Stated category-level assumption \u2014 see Section 6"],
            ["safety_stock / reorder_point / eoq (derived)", "Computed per warehouse-SKU \u2014 see Section 6"],
          ],
          [3600, 5760],
        ),
      ],
    },
  ],
});

function figureCaption(num, text) { return caption(`Figure ${num}. ${text}`); }

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("/home/claude/supplychain_project/report/Supply_Chain_Business_Report.docx", buffer);
  console.log("Report written.");
});
