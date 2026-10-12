# Metric rules - first feature-table version

**Status:** interim project decisions applied on 11 October 2026; accounting/source semantics remain subject to owner validation.  
**Source data:** modeled/anonymized operating data plus a public product catalog. No output is an audited performance result.

## Product-month table

The grain is one product per calendar month. The builder makes every product-month in the sales date range, including months without sales or inspections. Counts identify whether evidence exists; a zero count means no source rows, not proof of zero underlying activity.

| Metric | First-pass rule | Important label |
|---|---|---|
| Sales rows | Count sales records for product and `Order_Date` month | One row per record in this extract; one unique invoice ID per row |
| Units on sales rows | Sum source `Quantity`, including rows marked returned | Do not call net units until return-quantity semantics are confirmed |
| Gross sales | Sum source `Gross_Sales_EGP` | Source-provided amount |
| Net sales | Sum source `Net_Sales_EGP` without subtracting `Refund_Value_EGP` again | After-discount source amount; refunds are a separate measure and are not double-subtracted |
| Discount value | Sum `Gross_Sales_EGP - Net_Sales_EGP` | Reconciles with the fractional discount field |
| Estimated COGS / gross profit | Sum source estimates | Always label as estimated |
| Estimated gross margin | Sum estimated gross profit / sum source net sales | Weighted period margin; blank if denominator is zero |
| Returned-row count/rate | Count `Returned=Yes`; divide by all sales rows | Row rate, not unit rate |
| Quality-related return rows | Count `Quality_Related_Return=Yes` | Report separately; not linked to specific inspections |
| Refund value | Sum `Refund_Value_EGP` | Shown separately; not deducted in this first-pass net sales metric |
| Quality rejection rate | Sum rejected units / sum inspected units in `Inspection_Date` month | Blank if no inspected units; estimated quality loss stays labeled estimated |
| Leading quality evidence | Root cause and inspection stage with the largest rejected-unit count | Show rejected units and inspection volume; preserve `No significant issue` as an unexplained-rejection flag |

## Product-location-month inventory table

The grain is one product, location, and `Snapshot_Month`. Closing stock, cover, reorder point, safety stock, lead time, and stockout days are retained as supplied. They represent monthly snapshots, not live availability.

- Reconciliation delta = `Closing_Stock - (Opening_Stock + Received_Qty - Sold_Qty + Returned_Qty - Damaged_Qty)`.
- `inventory_flow_balance_ok` is true only when the absolute delta is at most 0.01 units. Preserve the row and expose the delta when it fails.
- `days_of_cover_extreme_flag` is true above 365 days; preserve the original cover value and flag it rather than capping it.
- Finished-goods decision scope is LOC001 (retail), LOC002 (online), and LOC003 (wholesale). LOC004 (head office) and LOC005 (production hub) are excluded from finished-goods stock totals and coverage because the available references identify them as corporate/production contexts and provide no finished-goods stock rows.
- Coverage is reported against the three in-scope locations; the current source represents all 3/3. The source still has no LOC004/LOC005 rows, and should not be treated as evidence that those facilities hold zero inventory.

## Joining and interpretation safeguards

- Aggregate sales and quality independently to product-month before combining them. Never join raw transaction rows directly to inspection rows.
- Keep inventory at product-location-month; summarize it to product-month only in a separate view, preserving location counts and quality flags.
- Shared product/month keys show timing association only. They do not establish that a quality defect caused a return.
- Marketing attribution and production feasibility are not included in these first two tables. Add them only with explicit time-bucketing rules and keep attribution directional, not causal.

## Open confirmations

1. Finance should eventually confirm how source `Net_Sales_EGP`, `Refund_Value_EGP`, and returned-row `Quantity` map to recognized revenue and units; until then, keep source net sales and refunds separate.
2. Operations should investigate inventory movement mismatches, especially LOC003; the prototype only flags them and does not generate order/transfer quantities from them.
3. LOC004/LOC005 are excluded from finished-goods stock decisions unless the business confirms they hold such stock and supplies corresponding inventory records.
4. Preserve supplied days of cover and flag values above 365; inspect the demand denominator. This signal alone never triggers markdown/clearance.
