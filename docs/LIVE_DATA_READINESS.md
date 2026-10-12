# Live data readiness specification

**Status:** Requirements prepared; no live company data has been provided or validated.  
**Purpose:** Define what must be supplied and checked before replacing the modeled/anonymized prototype data.

## Current prototype review

**Reviewed:** 11 October 2026  
**Result:** The existing modeled/anonymized project extracts passed the 9 documented automated integrity checks for the current prototype. These checks cover source-to-summary totals, keys, inventory balance flags, product coverage, and generated action signals (see `tests/test_data_integrity.py` and the run instructions in `README.md`). This result validates consistency of the supplied prototype files only. It does not validate live company data, business definitions, threshold performance, or stakeholder approval. No live source files were present for intake.

**Next intake status:** Not started; awaiting approved operational extracts, source ownership/details, and the business definitions below. The go-live checklist remains open.

## Intake rules

- Preserve the current modeled files unchanged. Store a dated, access-controlled copy of any approved operational extract separately; do not overwrite `data/raw/` until source ownership, access, and rollback are agreed.
- Provide the export date, source system, business owner, currency, units, timezone, refresh schedule, and whether the extract is a full history or an incremental delta.
- Include stable IDs and complete definitions for every field used by a displayed metric or rule. Send a data dictionary when source labels differ from the mappings below.
- Exclude customer names, contact details, addresses, and other customer-level fields. Product-level decisions do not require identifiable customer data.
- Include enough history to calculate recent sales and returns (at least 6 months), inspect seasonality (preferably 24–36 months), and compare at least 6 months of quality data. Inventory must include dated snapshots and movement fields for the same period if flow reconciliation is expected.

## Required source extracts

| Extract | Required grain and key | Required fields / definitions | Acceptance checks |
|---|---|---|---|
| Product master | One row per product; stable `Product_ID` | SKU, product name, brand, family/category, active status; season where relevant | Product ID is present and unique; child extracts use known products; status and season codes are documented. |
| Sales transactions | One row per sales line; stable row/line ID | Order date, product ID, quantity and unit meaning, gross sales, discount and whether it is a fraction or percent, net sales, currency, channel, returned flag, refund amount/date/reason; cost and profit fields with source and estimate/audit status | Unique line ID; dates parse; percentages have documented units; sales arithmetic reconciles; returns and refunds have a confirmed business definition; product keys match. |
| Inventory history | One row per product × location × snapshot month | Snapshot month, product ID, location ID, opening/closing stock, received, sold, returned, damaged quantities, stockout days, reorder point, safety stock, average daily sales window, days of cover | Unique product-location-month key; units are consistent; movement equation is checked and exceptions retained; locations reconcile to the approved finished-goods scope. |
| Location reference | One row per location; stable `Location_ID` | Name, location type, finished-goods inclusion, operating context | IDs are unique; every inventory location resolves; business owner confirms whether LOC004 and LOC005 hold finished goods and belong in scope. |
| Quality inspections | One row per inspection record; stable `QC_ID` | Product, inspection date, stage, inspected/passed/rejected quantities, defect/root cause, estimated or actual loss, lot/order link where available | Unique inspection ID; passed + rejected equals inspected; taxonomy is documented; no transaction-level sales linkage is inferred without a real key. |
| Marketing campaigns (optional context) | One row per campaign × product × platform if fields vary by product/platform | Campaign ID, product, platform, start/end dates, spend, attributed orders/revenue, discount, attribution window/method | Stable campaign key and clear attribution method/window; no causal lift claim unless there is a suitable design and sales linkage. |
| Production orders (optional context) | One row per production order | Order ID, product, planned/completed dates and quantities, good/rejected quantities, delay, efficiency, bottleneck | Unique order key; quantities and completion-date definitions are documented; planned capacity is not inferred from historical orders. |
| Printing batches / downtime (optional context) | One row per print batch; one row per downtime event | Stable event ID, product key for print, print date, quantities/reprints/defects; area and downtime dates/hours/reason for downtime | Keep grains separate. Downtime remains factory/area context unless the source has a trustworthy product/order key. |

## Business definitions to confirm before live use

Record the answer, decision owner, and effective date for each item in `docs/STAKEHOLDER_REVIEW.md` or the approval logs:

1. Does `Net_Sales` already reflect returned sales? In which month should refunds be recognized, and can refund value differ from the original sale?
2. Does returned quantity mean original units sold or units retained after returns? This determines whether a unit-based return rate is valid.
3. Which locations contain finished goods, and may stock be transferred among their different operating contexts?
4. What do each of the inventory receipt, return, damage, and sold movement fields include? How are negative theoretical balances handled?
5. How is average daily demand calculated for days of cover, especially at zero or near-zero demand?
6. Which cost and quality-loss values are audited actuals versus estimates?
7. What minimum volume or evidence coverage is sufficient for each rule, and who may approve a threshold change?

## Go-live review checklist

- [ ] Source owner, export date, refresh cadence, history window, currency, and quantity units recorded.
- [ ] Approved source files retained separately from the prototype data, with access control and integrity hashes.
- [ ] Schema, date, missingness, uniqueness, key coverage, and reference values pass review.
- [ ] Sales and quality aggregates reconcile to source totals by period; no raw many-to-many join multiplies counts.
- [ ] Inventory balance exceptions are quantified and dispositioned; in-scope locations are explicitly approved.
- [ ] Finance and operations answer the business-definition questions above.
- [ ] Product examples are checked by business users and logged as Correct / Needs change / Evidence insufficient.
- [ ] Thresholds, recommendations, and output wording receive explicit owner approval before operational use.
- [ ] At least one refresh is reproduced from the approved extracts and reviewed against the dashboard and regression checks.

## Boundary

This specification does not connect to a source system, change the current data paths, or claim that any live data is available. The existing application and processed outputs continue to use the project files until a reviewed source mapping and controlled intake change are implemented.
