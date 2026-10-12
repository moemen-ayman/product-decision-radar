# Stakeholder case review log

Use the six example cases in the dashboard’s **Case review** page to record whether the suggested action is useful for the business. The internal desk assessment below summarizes the existing review in `docs/EXAMPLE_REVIEW.md`; it is not business-owner approval. Record stakeholder outcomes in the separate outcome column.

**Review date:** ____________________  
**Reviewer(s) and role(s):** ____________________  
**Business area(s):** ____________________

## Review outcomes

For each product, select **Correct**, **Needs change**, or **Evidence insufficient**. If a change is needed, record the requested action and the business rule or evidence that supports it. Do not leave a case marked “Correct” based only on the modeled-data desk review.

| Product | Current suggested action | Internal desk assessment | Stakeholder outcome (Correct / Needs change / Evidence insufficient) | Evidence/action to confirm with stakeholder | Reviewer and date |
|---|---|---|---|---|---|
| P002 | Verify stock and inventory movements | Supported by the historical stockout evidence; flow deltas are +1 at LOC002 and +83 at LOC003, so verify stock and movements first. | Pending | Confirm current stock and reconcile movements before any replenishment decision. |  |
| P048 | Verify stock and margin before replenishment | Supported as a verification-first action; LOC003 has a stockout signal and +153-unit flow delta, while estimated margin is 0.8%. | Pending | Validate inventory, cost, and price; margin conflict must be resolved before ordering. |  |
| P023 | Review excess stock and seasonality | Supported as a review prompt; 10,343 units across covered locations and extreme supplied cover; balances reconcile. | Pending | Confirm count, cover denominator, season, and next assortment plan before markdown. |  |
| P013 | Review cost and price | Supported by -0.8% estimated weighted margin and negative estimated profit in 2 of 3 months. | Pending | Validate estimated costs and discounts; do not treat the estimate as audited loss. |  |
| P030 | Review return reasons and product fit | Supported by 25/233 returned rows (10.7%); only 2 were tagged quality-related. | Pending | Review fit/listing and return reasons; do not infer a confirmed defect. |  |
| P052 | Investigate quality | Supported by 108/3,009 rejected units (3.59%) and 26 unexplained rejects; excess stock is also a secondary signal. | Pending | Confirm inspection taxonomy and root causes; keep quality distinct from returns. |  |

## Close-out

- Stakeholder decisions recorded: 0 / 6 (internal desk assessments are not counted as approvals)
- Rules or labels requested for change: ____________________
- Additional data required: ____________________
- Follow-up owner and date: ____________________

The cases come from modeled/anonymized project records. Inventory signals refer to the September 2026 snapshot and are not live stock. See `docs/EXAMPLE_REVIEW.md` for the detailed evidence and limitations for each case.
