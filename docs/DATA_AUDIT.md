# Data audit - Product Decision Radar

**Status:** first-pass, read-only audit of supplied CSV sources  
**Scope:** product master, sales, inventory, quality, locations, marketing, and production orders  
**Coverage:** October 2023 to September 2026 unless noted  
**Interpretation:** the data dictionary classifies operational records as modeled/anonymized training data. Treat calculated results as prototype evidence, not audited company performance.

## Summary

- The core product key is complete and matches the 59-row product master in sales (180,000 rows), inventory (6,372 rows), quality (9,000 rows), marketing (420 rows), and production orders (2,500 rows). No unknown location IDs were found in sales or inventory.
- Sales, inventory, and quality each have complete monthly coverage across 36 months. Inventory has exactly 59 products x 3 locations x 36 months, with no duplicate product-location-month keys.
- Two material caveats must be visible in any analysis: inventory flow balances fail for 147 rows (mostly LOC003), and the source omits LOC004 Head Office and LOC005 Production Hub. The interim finished-goods decision scope is LOC001-LOC003, so the extract covers all 3/3 in-scope locations; absence of LOC004/LOC005 records does not imply zero stock there.
- Sales discounts and margins are stored as fractions (for example, `0.20` means 20%). Returns are flagged consistently. The supplied estimated profit can be negative for 4,876 sales rows; preserve these values rather than treating them as data errors.
- Product-level links support a product-month analysis, but sales returns cannot be attributed to individual quality inspections. Avoid implying a defect caused a specific transaction return.
- Marketing, production orders, printing batches, and downtime are now summarized in separate grain-appropriate tables. Campaign results have no campaign key in sales transactions and are descriptive attribution only; machine downtime has no product key and stays at area level.

## File checks

| Source | Rows | Key / grain check | Missing or notable fields | Date coverage |
|---|---:|---|---|---|
| `data/raw/Product_Master.csv` | 59 | `Product_ID` unique; no blanks | No missing fields | Static catalog |
| `data/raw/Sales_Transactions.csv` | 180,000 | `Row_ID` unique; all `Product_ID` values match master | `Return_Date` blank on 171,457 non-return rows; expected | 2023-10-01 to 2026-09-30 |
| `data/raw/Inventory_History.csv` | 6,372 | Unique `Product_ID` + `Location_ID` + `Snapshot_Month`; 177 rows per month | Three locations represented | 2023-10 to 2026-09 |
| `data/raw/Quality.csv` | 9,000 | `QC_ID` unique; all products match master | No missing fields | 2023-10-01 to 2026-09-30 |
| `data/raw/Locations.csv` | 5 | `Location_ID` unique | Inventory and sales use only 3 IDs | Static reference |
| `data/raw/Marketing.csv` | 420 | `Campaign_ID` unique; product IDs match | Product is a repeated campaign dimension, not a unique key | Campaign start dates 2023-10 to 2026-09 |
| `data/raw/Production_Orders.csv` | 2,500 | `Production_Order_ID` unique; product IDs match | Product repeats by order, as expected | Orders present within analysis window |

No fully duplicated rows were detected in these sources. `Sales_Transactions.csv` has one unique `Invoice_ID` per row in this extract; treat the supplied row as the sales record grain unless a business owner confirms invoice semantics.

## Findings that affect metric definitions

### Sales and returns

- `Month_Key` matches the first seven characters of `Order_Date` for all 180,000 rows.
- `Net_Sales_EGP = Gross_Sales_EGP * (1 - Discount_Pct)` reconciles for every row when `Discount_Pct` is treated as a fraction, not divided by 100.
- `Gross_Profit_EGP = Net_Sales_EGP - Estimated_COGS_EGP` reconciles for every row. `Gross_Margin_Pct` reconciles to `Gross_Profit_EGP / Net_Sales_EGP` when stored as a fraction.
- 8,543 rows are marked `Returned=Yes`; each has a return date, a return reason other than `No return`, and a positive refund. 2,457 returned rows are marked quality-related, and none are marked quality-related without also being returned.
- Recommended descriptive rates: returned sales-row rate = returned rows / sales rows; quality-related returned-row rate = quality-related returned rows / sales rows. If calculating units or refund exposure, use the relevant quantity/refund denominators and name them explicitly; do not label a row rate as a unit return rate.
- `Estimated_COGS_EGP` and `Gross_Profit_EGP` are modeled estimates. Negative estimated gross profit occurs in 4,876 rows (~2.71%); this may reflect discounts/estimated costs and should not be clipped to zero.

### Inventory

- The supplied row grain is one product, location, and monthly snapshot. Use `Snapshot_Month` for month joins; there is no `Month_Key` column in this file.
- Monthly stock-flow expectation is `Opening_Stock + Received_Qty - Sold_Qty + Returned_Qty - Damaged_Qty = Closing_Stock`. This differs by more than 0.01 units in 147 rows (2.3%); 141 are at LOC003. All 147 rows have zero recorded closing stock and a negative pre-floor theoretical balance, totaling -15,704 units; the largest single-row absolute discrepancy is 2,108 units. This arithmetic total is not evidence of actual lost sales, shrinkage, or physical shortage. Investigate before using flow components for reconciliation or attributing changes. Snapshot measures can still be displayed with a data-quality flag.
- `Days_of_Cover` reaches 21,175 days. Preserve the source value and flag values above 365 for denominator/stock review; an extreme-cover flag alone is not a markdown/clearance trigger.
- Inventory contains LOC001-LOC003. The interim finished-goods scope is retail, online, and wholesale. LOC004 Head Office and LOC005 Factory / Production are excluded unless finished-goods holdings are confirmed and corresponding records are supplied.

### Quality and cross-source joins

- For all 9,000 inspection records, `Passed_Qty + Rejected_Qty = Inspected_Qty`.
- Product ID is a valid shared key, but quality records are inspections at stages and dates while sales returns have no inspection/lot/transaction key. Aggregate quality and return evidence separately at product-month or product-period level and explain that association is not causation.

### Marketing and production additions

- The campaign extract contains 420 rows across 58 products and five platforms. The sales extract has no campaign identifier, so campaign-attributed orders/revenue cannot be reconciled to transactions; campaign measures are not causal lift or profit.
- Campaigns are grouped by `Start_Date` month and product/platform. Reported campaign outcomes can span beyond that cohort month.
- The production-order extract contains 2,500 orders across all 59 products; completion dates are populated. Orders are grouped by completion month and product to summarize planned/produced/good/rejected quantities, delays, efficiency, overtime, and reported bottlenecks.
- Printing batches contain a product key and are grouped independently by print month and product. Do not join raw print batches to raw orders before aggregation.
- The downtime extract contains 2,800 events and no `Product_ID`. It is summarized by month and business area as factory-wide context only; do not attribute it to a particular product/order.
- Aggregated campaign measures reconcile to all 420 source campaigns; production aggregates retain all 2,500 orders, printing aggregates retain all 1,900 batches, and area/month downtime totals reconcile to all 2,800 events. Numeric sums match their respective sources after aggregation.

## Safe first-pass metric contracts

These definitions follow the supplied fields and should be made explicit in the application:

1. **Net sales (EGP):** sum of source `Net_Sales_EGP` for the selected `Month_Key`, including returned rows only as represented by the source. Keep `Refund_Value_EGP` separate and do not subtract it again; financial recognition and month assignment need finance confirmation before accounting use.
2. **Estimated gross profit (EGP):** sum `Gross_Profit_EGP`; label as estimated.
3. **Estimated gross margin:** sum gross profit / sum net sales for the period (weighted margin), rather than averaging row-level margin. Define behavior when net sales are zero.
4. **Returned-row rate:** count of `Returned=Yes` / count of sales rows. Call this a row rate; use quantity-based rate only if the business confirms what quantity represents for returned records.
5. **Inventory days of cover:** use the supplied snapshot value by product/location/month; show its timestamp and flag values above 365 days. Do not calculate markdown from the extreme-cover warning alone.
6. **Stockout signal:** use `Stockout_Days_In_Month` from the monthly snapshot and state that it is historical, not live availability.
7. **Campaign performance:** use source-attributed fields; group by campaign start month, product, and platform. ROAS is attributed revenue / spend, not profit or causal lift.
8. **Production:** group orders by completion month/product and print batches by print month/product. Downtime remains month/area because the source lacks a product key.

## Remaining source/business questions

- Confirm if `Net_Sales_EGP` is before or after refund accounting and whether returned `Quantity` is original sold quantity or net retained quantity.
- Confirm the meaning of inventory receipt/return flows and investigate the LOC003 reconciliation pattern.
- Confirm the near-zero-demand convention for days of cover and whether extreme values indicate a data-generation artifact; meanwhile retain supplied values and flag >365 days.
- Keep monthly sales/quality aggregates separate from location-month inventory until joining on the shared product and month keys; aggregate each source to the intended grain first to prevent row multiplication.

## First feature-table version

The reproducible builder is `src/product_radar/data/build_features.py`; metric definitions are in `docs/METRIC_RULES.md`. It produces `data/processed/product_month.csv` (2,124 product-month rows) and `data/processed/product_location_month.csv` (6,372 product-location-month rows). It retains source periods and coverage flags, preserves inventory flow deltas and extreme cover values, and reports leading inspection root cause/stage plus unexplained rejects.

Reconciliation after generation: all product-month and inventory keys are unique; all 180,000 sales rows are represented; net sales, estimated gross profit, refunds, inspected units, and rejected units sum exactly to their source totals (currency values within CSV rounding); all 147 inventory flow exceptions are retained and flagged. This is a first-pass analytical output, not a production dashboard or a final business policy.

Representative modeled examples and rule conflicts are documented in `docs/EXAMPLE_REVIEW.md`. Interim decisions are recorded in `docs/STAKEHOLDER_REVIEW.md`; marketing and production definitions and limitations are in `docs/MARKETING_PRODUCTION_RULES.md`. The rule engine produces `data/processed/product_actions.csv` with 59 product rows, evidence, conflicting signals, thresholds, and reporting periods. Before operational use, confirm return semantics, investigate inventory reconciliation, validate seasonal context, and approve the provisional triggers.
