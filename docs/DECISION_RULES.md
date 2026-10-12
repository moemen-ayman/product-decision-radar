# Provisional product decision rules

**Status:** implemented as a reviewable prototype using the interim project decisions recorded in `docs/STAKEHOLDER_REVIEW.md`; thresholds remain provisional and are not approved company-wide policy.  
**Current source window:** sales July-September 2026; quality April-September 2026; inventory snapshot September 2026. Dates recalculate from the latest available source period when regenerated.

## Rules

| Signal | Implemented trigger | Meaning / guard |
|---|---|---|
| Historical availability risk | Any location has positive stockout days, or closing stock at/below reorder point and supplied cover at or below 14 days | Historical snapshot signal only; check current stock before ordering |
| Inventory flow mismatch | Absolute stock-flow delta exceeds 0.01 units | Keep as a visible data issue; if availability is also flagged, lead action is to verify stock and movement records |
| Negative estimated economics | Weighted estimated gross margin is negative, or estimated gross profit is negative in at least 2 of the last 3 months | Review cost, discount, and price; do not directly prescribe a markdown or discontinuation |
| Low-margin guard | Weighted estimated gross margin below 5% | Surface before any supply, promotion, or clearance decision |
| Elevated returned-row rate | At least 50 sales rows and returned-row rate above 2x the period portfolio rate | Row rate, not unit rate; show reasons and quality-related flags separately |
| Elevated quality rejection | At least 500 inspected units and rejected-unit rate above 1.25x the portfolio rate | Show inspected units, leading cause and stage, estimated loss, and any rejected units labeled `No significant issue` |
| Possible excess stock | In any location, cover exceeds 120 days and closing stock is at least 3x local sales units for the latest 3-month sales period (positive stock with zero local sales also qualifies) | Review seasonal status, count, and cover denominator; no automatic markdown |
| Extreme cover | Supplied cover exceeds 365 days | A separate data/denominator warning, not sufficient by itself for a clearance action |

For elevated returns and quality rejection, the generated evidence states the product rate, portfolio baseline, multiple of the baseline, configured trigger multiple, and required minimum sample size. If the portfolio baseline is zero, the evidence explains that the comparison multiple is undefined and reports the zero baseline.

Thresholds as currently configured: return sample >=50 rows and >2x portfolio rate; margin guard <5%; negative margin in >=2 of 3 months; quality sample >=500 units and >1.25x portfolio rate; excess cover >120 days with stock >=3x local quarterly sales; availability low-cover threshold <=14 days; stock-flow tolerance 0.01 units.

## Action selection

All triggered signals remain in the output. One lead action is selected for list sorting:

1. Availability plus inventory mismatch and low margin -> verify stock and margin before supply.
2. Availability plus inventory mismatch -> verify stock and movement records.
3. Negative estimated economics -> review cost and price.
4. Availability plus low margin -> review margin before a supply decision.
5. Availability -> review historical availability.
6. Elevated quality rejection -> investigate quality.
7. Elevated returned-row rate -> review return reasons and product fit.
8. Possible excess -> review excess and season.
9. Low margin alone -> review margin.
10. Inventory mismatch alone -> verify inventory balance.
11. Extreme cover alone -> verify cover inputs.
12. No trigger -> monitor; no action currently.

The priority label communicates review order, not business authorization. The prototype intentionally does not recommend a specific transfer, purchase quantity, markdown percentage, promotion budget, or discontinuation.

## Location and evidence rules

- Local sales are compared with inventory only within the same product and location. LOC001 is retail, LOC002 online, and LOC003 wholesale.
- Finished-goods stock scope is LOC001-LOC003. LOC004 (head office) and LOC005 (production hub) are excluded unless in-scope finished-goods records are supplied. Coverage completeness is measured against the three chosen locations, not all reference contexts.
- No cross-location transfer is generated because there is no confirmed operational rule saying which channel/location pairs can exchange stock.
- Stock and cover evidence always identifies the snapshot month. The current latest snapshot is September 2026; the output must not call it live availability.
- Product-level sales and inspections are period associations. No inspection is linked to a specific return transaction.
- The output has one row per product, including products with no triggered signal, with thresholds and source periods attached.
- Source net sales and refund value remain separate; no refund is subtracted again. Stock mismatches remain verification signals only. Cover above 365 days is a review/data warning and never creates a markdown action by itself.

## Generation

Run the feature builder first, then the decision rules:

```powershell
python .\src\product_radar\data\build_features.py
python .\src\product_radar\decisions\rules.py
```

The second command writes `data/processed/product_actions.csv` with a lead action, all signal codes, English evidence, per-location stock evidence, period coverage, counts, rates, estimates, and the threshold configuration.
