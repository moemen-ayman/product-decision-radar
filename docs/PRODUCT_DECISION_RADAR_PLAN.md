# Product Decision Radar - Planning Notes

## Purpose

Build a decision-support prototype that recommends an action for each product, such as replenish, transfer, promote, markdown, investigate quality, or review for discontinuation. The first version should explain why it recommends an action and show the supporting evidence.

## Data reviewed

Source CSV files are preserved under `data/raw/`, with the HVIA task brief in `data/raw/reference/`. The Arabic plan is preserved under `docs/reference/`. The audit, reproducible feature tables, provisional explainable rules, and English dashboard are now in the project. Marketing and production context and stakeholder threshold review remain later phases.

| Data area | Files | Rows | Useful connection |
|---|---|---:|---|
| Product catalog | `data/raw/Product_Master.csv` | 59 | Product ID is the shared product key |
| Sales | `data/raw/Sales_Transactions.csv` | 180,000 | Product, date, channel, quantity, net sales, estimated COGS/profit/margin, returns and return reasons |
| Inventory | `data/raw/Inventory_History.csv` | 6,372 | Product x location x month; includes closing stock, cover, reorder point and stockout days |
| Quality | `data/raw/Quality.csv` | 9,000 | Product, inspection stage, defect/root cause and estimated loss |
| Marketing | `data/raw/Marketing.csv` | 420 | Product, platform, spend, attributed revenue and discount |
| Production | `data/raw/Production_Orders.csv` | 2,500 | Product, planned/actual/good quantity, efficiency, delays and bottleneck |
| Customers | `data/raw/Customers.csv` | 30,000 | Sales customer IDs all matched this customer master in the initial check |

The sales, inventory, quality, marketing and production records cover approximately October 2023 through September 2026. The data dictionary classifies most operational/customer data as modeled or anonymized training data. Product catalog facts are public/verified. Treat model outputs as prototype results, not verified company performance.

## Initial product scope

For the first usable version, focus on a monthly product action score using:

1. **Commercial performance:** net sales, units, gross profit, margin, discounts, and trend from `data/raw/Sales_Transactions.csv`.
2. **Stock position:** closing stock, days of cover, reorder point, and stockout days from the latest `data/raw/Inventory_History.csv` snapshot per product and location.
3. **Quality and returns:** return rate, quality-related return rate, return reasons, defect rate, root causes, and estimated quality loss from `data/raw/Sales_Transactions.csv` and `data/raw/Quality.csv`.
4. **Marketing context:** spend and attributed revenue by product/platform from `Marketing.csv`.
5. **Production feasibility:** good quantity, efficiency, delay and bottleneck context from `Production_Orders.csv` where it helps explain supply constraints.

Every recommendation must show its evidence, reporting period, confidence/coverage, and a plain-language explanation. A product should be allowed to receive more than one signal (for example, strong demand plus quality concerns); the app should surface conflicts instead of hiding them in one score.

## Suggested first action rules

- **Replenish / protect availability:** strong recent demand or repeated stockouts, with stock below a configurable reorder threshold.
- **Transfer / rebalance:** sufficient total stock but poor distribution across locations, paired with different local demand/cover.
- **Promote:** healthy margin and quality with weak demand or excess cover; verify campaign data before suggesting spend.
- **Markdown / clear excess:** sustained weak sales and excess cover, with a minimum margin floor so the recommendation does not create an unbounded loss.
- **Quality investigation:** elevated defect, quality-related return, or estimated quality loss; show the dominant defect stage/root cause.
- **Review / no action:** insufficient evidence, conflicting signals, or a product with too few observations.

These are decision rules to validate with users; they are not business policies inferred from the CSVs. Thresholds must be configurable and visible.

## Data limitations to handle explicitly

- `Marketing.csv` is modeled attribution data; it should be presented as directional demonstration data, not causal proof that a campaign caused sales.
- Sales return and quality inspection data share product IDs but do not provide a dependable transaction-to-inspection link. Do not claim a specific defect caused a specific customer's return.
- Inventory is monthly and location-level; it supports a monthly planning view, not live stock recommendations.
- Production orders identify products, but material consumption by order is not recorded. `Product_BOM.csv` describes modeled requirements, not actual consumption.
- The first pass found three inventory locations, while `data/raw/Locations.csv` describes five operating contexts. The absent entries are the head office and production hub; confirm whether these should hold finished-goods inventory before treating coverage as incomplete.
- Exclude customer-level targeting from the first version. It adds privacy/consent considerations and is not needed for product-level actions.
- Distinguish supplied estimates such as `Estimated_COGS_EGP` and `Estimated_Loss_EGP` from audited financial values.

## Proposed project structure

Keep supplied source files unchanged until the project layout is agreed. Then organize the app code separately from the source data:

```text
project/
  README.md
  pyproject.toml                 # or requirements.txt if preferred
  .gitignore
  data/
    raw/                         # original supplied CSVs, unchanged
    processed/                   # generated, reproducible tables; ignored by Git
  docs/
    PRODUCT_DECISION_RADAR_PLAN.md
    data_dictionary_notes.md
    decision_rules.md
  src/
    product_radar/
      app.py                     # dashboard entry point
      config.py                  # paths and visible thresholds
      data/
        load.py                  # read and validate source files
        checks.py                # schemas, keys, dates and reconciliation checks
      features/
        sales.py
        inventory.py
        quality.py
        marketing.py
        production.py
      decisions/
        rules.py                 # explainable action rules
        explanations.py          # evidence and reason text
      views/
        overview.py
        product_detail.py
  tests/
    test_data_checks.py
    test_features.py
    test_decisions.py
```

Suggested prototype stack: Python, Streamlit, pandas, and Plotly. Keep decision calculations in reusable modules separate from the dashboard so they can be checked independently and later reused in another interface.

## Work plan and checkpoints

1. **Confirm scope and action vocabulary:** agree which decisions the first version should make and who will use it.
2. **Inventory and validate data:** check schemas, duplicates, missing values, ranges, units, key coverage and monthly reconciliation; document exceptions.
3. **Define metrics and thresholds:** write the exact formulas, time windows, minimum evidence rules and margin/stock safeguards.
4. **Build the feature tables:** produce one product-month view and one product-location-month inventory view, retaining source period and coverage.
5. **Implement explainable rules:** create action labels, evidence, conflict handling and a no-recommendation state.
6. **Build the dashboard:** current English version is in `src/product_radar/app.py`; it includes the portfolio action list, filters, and product detail trends for sales, stock, returns, and quality.
7. **Validate examples with stakeholders:** review high/low margin, stockout, excess stock, high-return and insufficient-data cases; tune thresholds.
8. **Prepare the pitch:** demonstrate a few representative decisions, state assumptions and data limitations, and avoid presenting modeled results as actual savings.

## Definition of a successful prototype

- A user can filter products and reporting period, then see a ranked action list.
- Each action links to the underlying evidence and clearly states the rule that triggered it.
- The user can inspect a product's sales/profit, stock by location, returns/quality, and marketing context.
- Low-coverage or conflicting data produces an explicit review/no-action outcome.
- Core metrics reconcile to the supplied source rows for selected examples.
- The demo separates modeled data from public catalog facts and makes no unsupported savings claim.

## Decisions to settle before treating actions as business policy

- Which person is the primary user: executive, planning/inventory, merchandising, or a mixed judging audience?
- Which action types belong in the first release?
- What time window defines “recent” (for example, last 3 months versus last 6 months)?
- Should the first demo prioritize product-level decisions across the business or product-by-location inventory actions?
- Confirm Streamlit/Python as the preferred prototype stack.
