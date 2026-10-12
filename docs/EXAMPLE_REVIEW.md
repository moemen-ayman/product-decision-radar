# Review of modeled data examples

**Review period:** sales July-September 2026; latest inventory snapshot September 2026; quality inspections April-September 2026.  
**Purpose:** inspect whether simple product action rules produce useful, explainable signals. These are modeled/anonymized operating records, and inventory is not live. Treat outcomes as prototype examples, not current company instructions.

## Portfolio reference points

- Across 18,397 sales rows in July-September 2026, 924 were marked returned: a 5.02% returned-row rate. This is a row rate, not a unit rate.
- Weighted estimated gross margin across those rows was 15.2%.
- Across 587,164 inspected units in April-September 2026, 14,088 units were rejected: a 2.40% rejection rate.
- Of those rejected units, 1,831 (13.0%) carry the root-cause label `No significant issue`. Keep these visible as unexplained rejected units; do not use that label as a corrective-action cause.

## Cases

| Case | Evidence in supplied data | Review result |
|---|---|---|
| Historical stockout, healthy economics: P002 | At the September snapshot, LOC002 ended at 0 units with 9 stockout days; LOC003 ended at 0 with 11 days. Its July-September sales were 2,912 units and 18.7% weighted estimated gross margin. LOC003's stock-flow delta is +83 units; LOC002's is +1 unit, beyond the strict 0.01 reconciliation tolerance. | Strong historical availability signal, but flag movement reconciliation and verify on-hand stock before a replenishment decision. Mark it as a September signal, not live inventory. |
| Stockout with a margin conflict: P048 | LOC003 ended September at 0 units, with 5 stockout days and 44.34 average daily units; the supplied reorder point is 366. The LOC003 flow delta is +153 units. Product sales were 4,523 units in July-September, but estimated gross margin was only 0.8%; July alone had an estimated loss of EGP 3,314. | Show both signals. Review cost/price and stock records before an order; never let a stockout rule override the margin safeguard. |
| Excess/seasonal stock candidate: P023 | September closing stock totaled 10,343 units across the three covered points; sales were 922 units in July-September and weighted estimated gross margin was 16.2%. All three stock-flow balances reconcile. LOC001 and LOC002 had 3,057 and 3,497 units with 5,879 and 6,725 supplied days of cover, respectively, while each sold 47 units in the period. Catalog season is Summer 2026. | Prioritize an excess-stock and seasonal assortment review. The extreme cover values are mathematically consistent with very low daily demand, but confirm stock counts and the next season's plan before markdown. No case for automatic transfer: the high-demand point is wholesale and already holds substantial inventory. |
| Negative estimated product economics: P013 | In July-September, net sales were EGP 605,817 and estimated gross profit was -EGP 4,786, for -0.8% weighted estimated margin. Two of three months were negative (July -EGP 5,422; August +EGP 1,659; September -EGP 1,023). The 324 sales rows had a 2.5% returned-row rate, below portfolio. | Route to cost/discount/price review. Do not recommend a promotion or markdown based on sales volume alone. Validate the estimated cost input before treating the loss as actual. |
| Elevated returns without a strong quality-return signal: P030 | 25 of 233 July-September sales rows were returned (10.7%, versus 5.02% portfolio). Only 2 of those rows were flagged quality-related. Recorded reasons include size/fit (9), changed mind (6), and color/appearance (6). | Flag for a product/fit and listing review. The return count is a row rate and the reason labels are descriptive; do not classify this as a confirmed manufacturing defect. |
| Elevated inspection rejects: P052 | In April-September, 108 of 3,009 inspected units were rejected (3.59%, versus 2.40% portfolio); estimated loss was EGP 21,873. Pattern/measurement was the leading root cause (43 rejected units), and Final was the stage with the most rejects (51). Another 26 rejects were labeled `No significant issue`. July-September sales had 5 returns in 104 rows, 2 flagged quality-related. | Quality investigation is warranted; show the leading cause and stage plus the unexplained count. Keep quality and returns as separate product-period evidence, with no claim that the inspections caused these returns. |

## Rule changes supported by the examples

1. **Show competing signals side by side.** P048 must display stockout and low margin together. A single summed priority score could hide the margin risk.
2. **Gate decisions on data quality and recency.** When the stock-flow balance fails, label the signal “verify stock” before using it for replenishment. Always show the latest available snapshot month and never call it live stock.
3. **Respect location types.** LOC001 is retail, LOC002 online, and LOC003 wholesale. A cross-location imbalance is only a transfer candidate after an operator confirms that movement between those contexts is appropriate. The head office and production hub are not in the inventory extract; confirm whether they are in scope.
4. **Keep the margin floor in front of commercial actions.** Negative estimated profit calls for economics review; low/near-zero estimated margin blocks promotion or markdown suggestions until reviewed.
5. **Use comparison and minimum evidence for returns.** P030 is more than twice the recent portfolio returned-row rate with 233 sales rows, but its low share of quality-related flags points to a broader product/fit review, not an automatic quality action.
6. **Quality rules need coverage and taxonomy checks.** Show inspected units, rejected units, rate, estimated loss, leading cause and stage, and unexplained rejects. A product-period correlation is not a transaction-level link.
7. **Season matters.** The latest snapshot is September 2026 and several examples are explicitly Summer 2026 or older. Review the current assortment and next-season plan before acting on old seasonal sales.

## Provisional review triggers to validate with users

These are candidate review triggers, not approved business policies:

- Availability review: any stockout days or closing stock at/below reorder point in the latest snapshot; elevate to “verify stock” if the flow balance fails or the snapshot is stale.
- Excess review: cover above 120 days plus low recent units, but only after checking absolute stock, seasonal status, and the cover denominator.
- Economics review: negative weighted estimated margin, especially if negative in at least two of the latest three months and there is adequate sales volume.
- Return review: returned-row rate above twice the period's portfolio rate, with at least 50 sales rows; show return reasons and quality-related share separately.
- Quality review: elevated rejected-unit rate with a visible inspected-unit count and minimum-volume threshold; show unexplained rejects separately.

The thresholds above identify records to inspect. They do not by themselves authorize purchasing, transfers, markdowns, campaigns, or discontinuation.

## Feature-table updates made from review

The product-month builder now includes leading rejected-unit root cause and inspection stage, plus counts and a flag for rejected units labeled `No significant issue`. Regenerate the outputs with:

```powershell
python .\src\product_radar\data\build_features.py
```

## Review of generated actions - 10 October 2026

Compared the six cases above with the current `data/processed/product_actions.csv`, its evidence fields, and the September 2026 location snapshots. This is an internal consistency review; it is not stakeholder approval.

| Product | Current generated action | Review finding |
|---|---|---|
| P002 | Verify stock and inventory movements | Correctly prioritizes the September stockout signal together with movement mismatches at LOC002 (+1 unit) and LOC003 (+83 units). Positive estimated margin (18.7%) does not indicate a margin conflict. Verify current stock and movement records before replenishment. |
| P048 | Verify stock and margin before replenishment | Correctly keeps the LOC003 stockout, +153-unit movement mismatch, and 0.8% estimated margin together. The margin is below the provisional 5% guard. Do not turn the availability signal into an order recommendation until stock records and economics are reviewed. |
| P023 | Review excess stock and seasonality | Correctly flags all three locations for excess and extreme supplied cover; the stock-flow balances reconcile. The 5,879-6,725 cover-day values at LOC001/LOC002 are extreme, so verify the cover denominator and season plan. Keep this as a review action, not an automatic markdown. |
| P013 | Review cost and price | Correctly flags -0.8% weighted estimated margin and negative estimated profit in 2 of 3 months. Review estimated cost, discounts, and price before any commercial action; do not present the estimate as audited loss. |
| P030 | Review return reasons and product fit | Correctly flags 25 returned rows out of 233 (10.7%) versus a 5.0% portfolio rate, while only 2 rows are tagged quality-related. This supports a fit/listing review, not a confirmed defect claim. |
| P052 | Investigate quality | Correctly flags 108 rejects from 3,009 inspected units (3.59%) versus 2.40% portfolio and preserves 26 unexplained rejects. Excess stock at LOC002 also remains visible as a secondary signal; the quality action must not hide the seasonal stock review. |

### Refinement review and implementation

1. **Implemented: show the threshold and comparison in the evidence text.** P030 is about 2.14x the 5.02% portfolio returned-row rate against a >2x trigger. P052 is about 1.50x the 2.40% portfolio rejection rate against a >1.25x trigger. Evidence also shows the configured minimum sample size; these examples remain consistent with their current actions.
2. **Keep availability actions verification-first when inventory movement fails.** P002 and P048 demonstrate why a stockout alone should not generate a purchase quantity while the related balance is unreconciled.
3. **Keep extreme cover and excess as review signals.** P023 supports showing supplied cover and stock quantity together, with a seasonal/count/denominator check before a markdown.
4. **Retain the current lead-action precedence for these examples.** P048 appropriately gives the margin guard visibility before replenishment; P052 keeps quality as the lead action while retaining the excess-stock signal.
5. **No threshold changes are recommended from these six modeled examples alone.** Confirm threshold performance and action wording with the intended users before treating them as business policy.
