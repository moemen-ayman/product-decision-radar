# Threshold approval log

Use this page in the business-owner review to record the decision for each proposed interim threshold. The current application settings remain active until a decision is recorded and deliberately applied.

**Project:** Product Decision Radar  
**Review status:** Pending  
**Review meeting/date:** ____________________  
**Decision owner(s):** ____________________

## Internal recommendation (11 October 2026)

The sensitivity review covers 59 products in modeled/anonymized project data. Retain the current settings as **interim review triggers** until a business owner records a decision below. This is a documented recommendation, not policy approval or evidence of predictive accuracy.

| Rule | Recommendation | Evidence from sensitivity review | Limitation to resolve |
|---|---|---|---|
| Low estimated margin | Retain below 5% | Flags 3 products; below 8% flags 6 and below 10% flags 12 | Costs and margins are estimates; validate with Finance. |
| Elevated returns | Retain above 2× portfolio rate and at least 50 sales rows | Flags 1 product at 2×; 2 at 1.5× and none at 2.5× | This is a returned-row rate, not a unit rate; confirm refund/return definitions. |
| Quality rejection | Retain above 1.25× portfolio rate and at least 500 inspected units | Flags 3 products at 1.25×; 28–29 at baseline and none at 1.5× | Confirm inspection taxonomy and estimated versus actual loss. |
| Possible excess stock | Retain >120 days and stock ≥3× local three-month sales | Flags 17 products; changing the stock multiple to 2× flags 20 and 4× flags 15 | Confirm cover denominator, seasonal plan, stock counts, and approved locations. |
| Historical availability risk | Retain stockout-days trigger and provisional ≤14-day cover trigger | Flags 31 products at 14 days; 25 at 7 days and 34 at 21 days | September 2026 is a historical snapshot; confirm current stock and demand window. |

No rule has been changed in the application based on this desk review.

## Decisions

For each row, select one status and complete the requested threshold, reviewer, date, and rationale. Write “Approve current” or “Change” in the decision field. If evidence is insufficient, leave the rule provisional and note what evidence is needed.

| Rule | Current setting | Desk-review recommendation | Decision (Approve current / Change / Insufficient evidence) | Approved or requested setting | Reviewer and date | Rationale / follow-up |
|---|---|---|---|---|---|---|
| Low estimated margin | Below 5% (negative economics handled separately) | Keep 5% as an early review guard | Pending |  |  |  |
| Elevated returns | Above 2× portfolio returned-row rate; at least 50 sales rows | Keep 2× and 50 rows | Pending |  |  |  |
| Quality rejection | Above 1.25× portfolio rejection rate; at least 500 inspected units | Keep 1.25× and 500 units | Pending |  |  |  |
| Possible excess stock | Cover >120 days and stock ≥3× local three-month sales | Keep 120 days and 3× | Pending |  |  |  |
| Historical availability risk | Stockout days >0, or low stock with cover ≤14 days | Keep 14 days provisionally; preserve historical label | Pending |  |  |  |

## Review guardrails

- The sensitivity analysis uses 59 products from modeled/anonymized project data; it does not establish business outcome accuracy.
- Keep recommendations as human review prompts. Approval of a threshold does not authorize automatic purchase, transfer, markdown, or promotion quantities.
- Record financial, inventory-scope, and data-quality assumptions separately in `docs/STAKEHOLDER_REVIEW.md` if the discussion changes them.
- After approval, update `src/product_radar/decisions/rules.py`, regenerate processed outputs, and update this log with the applied date. Do not mark a decision approved before the owner records it.

## Evidence

See `docs/RULE_CALIBRATION_REVIEW.md` for threshold sensitivity counts, product examples, and limitations. Business owners should record a decision, reviewer, date, and rationale in the table above; all five decisions remain pending.
