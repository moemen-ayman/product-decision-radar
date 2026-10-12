# Product Decision Radar

An explainable product-review prototype for sales, inventory, returns, and quality signals, with marketing and production context. It shows the evidence behind each suggested action. The supplied operational records are modeled/anonymized training data; results are not audited company performance or approved operational recommendations.

## Project structure

```text
project/
  data/
    raw/                         # Original source files, preserved as received
      reference/                 # Source PDF references
    processed/                   # Rebuildable analytical tables and outputs
  docs/
    reference/                   # Project plan PDF
    PROJECT_CHECKLIST.md         # Requirements and completion status
    PROJECT_CLOSEOUT.md          # Completed work and remaining operational steps
    STAKEHOLDER_REVIEW.md        # Findings and decisions requiring business review
    DATA_AUDIT.md                # Data audit results
    LIVE_DATA_READINESS.md       # Requirements for approved operational data
    METRIC_RULES.md              # Provisional metric definitions
    MARKETING_PRODUCTION_RULES.md # Marketing/production definitions and attribution limits
    EXAMPLE_REVIEW.md            # Example cases and conflicting signals
    DECISION_RULES.md            # Recommendation and priority rules
    PRODUCT_DECISION_RADAR_PLAN.md
  src/product_radar/
    app.py                       # English dashboard for priorities, product details, marketing, and production
    data/build_features.py       # Builds product-month and product-location-month tables
    data/build_marketing_production.py # Builds marketing, production, printing, and downtime tables
    decisions/rules.py           # Applies decision rules and creates the action list
  tests/
    test_data_integrity.py       # Metric, join-key, and decision-output checks
  requirements.txt               # Dashboard dependencies
  .streamlit/config.toml         # Dashboard theme
  output/pdf/                    # Project plan copy and Arabic executive summary
  output/presentations/          # Editable presentation drafts
  outputs/<task-id>/             # Final Excel workbooks; see outputs/README.md
  tmp/                           # Temporary build files and previews; not deliverables
```

## Set up and run the dashboard

From the project root in PowerShell, create the virtual environment, install dependencies, and build the data tables:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\src\product_radar\data\build_features.py
.\.venv\Scripts\python.exe .\src\product_radar\data\build_marketing_production.py
.\.venv\Scripts\python.exe .\src\product_radar\decisions\rules.py
.\.venv\Scripts\python.exe -m streamlit run .\src\product_radar\app.py
```

The dashboard opens at `http://localhost:8501/`. Keep the terminal open while using it.

The first build creates:

- `data/processed/product_month.csv`: one row per product and month, with sales, estimated profit, returns, and quality.
- `data/processed/product_location_month.csv`: one row per product, location, and month, with inventory balances, cover, and movement-balance flags.

The second build creates five marketing and operations tables: campaigns by start month/product/platform, production orders by completion month, reported bottlenecks, printing by product/month, and factory downtime by area/month. Campaign metrics are directional; downtime cannot be attributed to a product because the source has no product key.

The third build creates `data/processed/product_actions.csv`, with one row per product, the lead action, concurrent signals, supporting evidence, measurement periods, and thresholds.

The English dashboard includes a ranked action list, filters for brand/category/priority/search and sales context, product details, marketing and production views, plus threshold and case-review pages. The sales-period selector updates sales and margin context only. Decision rules keep their fixed windows (three months for sales/returns and six months for quality), while inventory remains the latest available monthly snapshot.

Marketing is grouped by campaign start month, although results may extend into later months. Sales transactions do not have a campaign key, so attributed revenue and ROAS do not prove causal impact. Production orders are grouped by completion month. Factory downtime is shown by area because it has no product key. Source net sales and reported refunds remain separate. Finished-goods inventory scope is limited to LOC001–LOC003.

Rules and thresholds are provisional and configurable in `src/product_radar/decisions/rules.py`. Review `docs/DECISION_RULES.md` before using results as business decisions. Inventory data is a historical monthly snapshot, not live on-hand stock.

## Validate the current outputs

After rebuilding the processed tables, run the checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The checks compare sales and quality totals with source data, verify product/month/location keys and inventory balances, and validate product coverage and decision signals. They read the current files; they do not rebuild or modify them.

## Source-file integrity

The CSV files in `data/raw/` are preserved as received. The original assignment reference is in `data/raw/reference/`; the project plan is in `docs/reference/`. `data/SHA256SUMS.txt` contains SHA-256 checksums for source and reference files, so their integrity can be verified after copying or moving them.

The project plan also remains in `output/pdf/` as a legacy copy. It matches the reference copy in `docs/reference/` by checksum.

## Final deliverables

- Arabic executive summary: `output/pdf/Product_Decision_Radar_Executive_Summary_AR_2026-10-11.pdf`.
- Detailed Excel analysis: under `outputs/<task-id>/`; see `outputs/README.md` for the exact path.
- Presentation draft: `output/presentations/`; pending business-owner review and approval.
- Temporary build files and previews: under `tmp/`; these are not final deliverables.
