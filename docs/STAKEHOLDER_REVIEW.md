# Interim decisions and stakeholder review

**Decision date:** 11 October 2026  
**Status:** Five interim decisions selected and applied to the prototype outputs. They are project defaults for this modeled/anonymized dataset, not audited financial policy or live operational instructions.  
**Evidence caveat:** Source records describe modeled/anonymized operations. They do not establish actual company performance or physical on-hand inventory.

## Decisions selected and applied

| # | Topic | Selected interim decision | Applied effect |
|---|---|---|---|
| 1 | Refunds | Keep source `Net_Sales_EGP` and `Refund_Value_EGP` as separate measures. Do not subtract refunds again or assign them to a financial recognition month without a finance-approved rule. | Product sales, estimated margin and action rules continue to use source net sales; refund totals remain separately visible. This avoids double-subtracting an amount whose accounting period is unknown. |
| 2 | Inventory mismatches | Treat flow-balance failures as data/operations verification signals only. Do not derive automatic purchase or transfer quantities from the mismatched movements. | The 147 rows remain flagged (141 LOC003, three LOC001, three LOC002); stockout and mismatch combinations continue to recommend verifying records first. |
| 3 | LOC004 and LOC005 | Exclude LOC004 Head Office and LOC005 Production Hub from finished-goods stock decision scope unless the business confirms finished-goods holdings and provides inventory records. | Scope is LOC001 Retail, LOC002 Online, LOC003 Wholesale. Current extract covers all 3/3 in-scope sites. Missing LOC004/LOC005 records are not interpreted as zero stock. |
| 4 | Cover above 365 days | Preserve the supplied value and flag it for denominator/stock review. It cannot trigger markdown or clearance by itself. | Existing possible-excess rule still requires cover >120 days plus stock at least 3x local three-month sales (or positive stock and no local sales). Extreme cover remains a separate warning. |
| 5 | Six reviewed actions | Keep all six as preliminary review actions; no threshold change is justified by this small, modeled sample. | P002 verify stock and movements; P048 verify stock and margin before replenishment; P023 review excess stock and seasonality; P013 review cost and price; P030 review return reasons and product fit; P052 investigate quality. |

## Evidence reviewed

### Sales and refunds

- `Net_Sales_EGP` matches `Gross_Sales_EGP × (1 - Discount_Pct)` in the source; `Refund_Value_EGP` is a distinct field.
- There are 8,543 returned rows. Source net sales for these rows total EGP 10,066,834.31 and refunds total EGP 9,427,005.55.
- Refund equals source net sales in 6,397 returned rows and is lower in 2,146. The source does not establish recognized-revenue treatment or whether the refund belongs in order month or refund month.
- This prototype therefore reports refunds separately. Finance should define accounting treatment before using the output as a financial ledger or realized-sales statement.

### Inventory balance and scope

- `Sold_Qty` matches transaction `Quantity` aggregated by product/location/month for all 6,372 inventory rows.
- There are 147 flow equation mismatches: 141 at LOC003, three at LOC001, and three at LOC002. All 147 have zero closing stock and a negative theoretical balance before the recorded zero; the largest single-row delta is 2,108 units. The pre-floor theoretical balances sum to -15,704 units across the exception rows.
- This pattern is consistent with sales exceeding modeled supply before closing stock is floored at zero, but it does not prove how the records were generated. The 15,704-unit sum is a diagnostic arithmetic total, not confirmed lost sales, shrinkage, or a physical stock shortage. Keep the rows as verification flags; do not turn them into order/transfer quantities.
- The exceptions persist through the history: seven remain in the September 2026 snapshot (446 units of summed negative theoretical balance), after a peak of 11 rows / 3,144 units in July 2026. Reconcile receipt/return timing and the source's zero-flooring convention with the inventory owner before reclassifying or correcting them.
- Location reference data identifies LOC004 as Head Office and LOC005 as Factory / Production. They are out of finished-goods scope by this interim decision; no missing records are filled with zero.

### Days of cover

- Source `Days_of_Cover` agrees with `Closing_Stock ÷ Avg_Daily_Sales_90D` within 0.05 days across all 6,372 rows.
- Cover exceeds 365 days in 939/6,372 records, including 23 rows in the latest September 2026 snapshot. The minimum daily-sales denominator is 0.04 units.
- Keep source values, flag >365, and inspect the denominator/count. Such a flag alone does not recommend markdown or clearance.

## Six action examples retained

| Product | Retained action | Evidence and guard |
|---|---|---|
| P002 | Verify stock and inventory movements | Historical stockout/low stock plus movement deltas of +1 and +83 units; verify current stock and records before replenishment. |
| P048 | Verify stock and margin before replenishment | Historical stockout, +153-unit delta, and 0.8% estimated margin; resolve records and economics before any order. |
| P023 | Review excess stock and seasonality | Potential excess across covered sites with extreme supplied cover; review counts, demand denominator, and season plan. No automatic markdown. |
| P013 | Review cost and price | -0.8% weighted estimated margin and negative estimated profit in two of three months. |
| P030 | Review return reasons and product fit | Returned-row rate 10.7% over 233 rows versus 5.0% portfolio rate; review fit/reasons without assuming a defect. |
| P052 | Investigate quality | 3.59% rejection over 3,009 inspected units versus 2.40% portfolio rate; 26 unexplained rejects remain visible and excess stock is secondary evidence. |

The six cases are a desk review only. They support retaining the current lead actions, not claiming that rules are business-approved or validated on live operations.

## Project references

- Data audit: `docs/DATA_AUDIT.md`
- Example review: `docs/EXAMPLE_REVIEW.md`
- Metric definitions: `docs/METRIC_RULES.md`
- Decision rules: `docs/DECISION_RULES.md`
- Feature builder: `src/product_radar/data/build_features.py`
- Rule engine: `src/product_radar/decisions/rules.py`
