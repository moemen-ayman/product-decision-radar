# Marketing and production analysis

**Status:** Descriptive dashboard context built from modeled/anonymized source records. These measures do not create or change product purchase, transfer, markdown, or promotion actions.

## Output tables

| Output | Grain | Source and date assignment |
|---|---|---|
| `data/processed/product_marketing_month.csv` | Campaign start month × product × platform | `Marketing.csv`; a campaign's reported results are assigned to its start-month cohort even when it runs into later months. |
| `data/processed/product_production_month.csv` | Order completion month × product | `Production_Orders.csv`; grouped by actual completion month. Orders without a completion date use `Unknown`. |
| `data/processed/product_production_bottlenecks_month.csv` | Completion month × product × reported bottleneck area | `Production_Orders.csv`; `None` entries are omitted. |
| `data/processed/product_printing_month.csv` | Print month × product | `Printing_Batches.csv`; output, rejects, reprints, and reported costs are summed. |
| `data/processed/operations_downtime_month.csv` | Downtime month × business area | `Machine_Downtime.csv`; no product-level join is possible because the source has no `Product_ID`. |

## Measures and limits

### Marketing

- Spend, impressions, clicks, sessions, attributed orders, and attributed revenue are summed from campaign rows.
- Attributed ROAS = attributed revenue / reported campaign spend. This is not margin, profit, or incremental lift.
- Click-through rate = clicks / impressions. Session conversion rate = attributed orders / landing-page sessions.
- Campaign performance does not join to sales transactions: the sales extract has no campaign ID. Report attribution as directional; do not claim campaign causality.
- Reporting windows select campaign start-month cohorts. A campaign's outcomes may cover later months, and campaigns begun before the window are not included.
- The campaign records are modeled. Products without campaign rows have unavailable campaign evidence, not a measured real-world zero.

### Production orders

- Planned, produced, good, rejected units and overtime are summed by completion month and product.
- Plan fulfillment = produced units / planned units. Good-unit yield = good units / produced units.
- Late-order rate = orders with `Delay_Days > 0` / completed orders. Average reported efficiency and lead time are order-level averages, not rated capacity commitments.
- Order lead time = calendar days between `Start_Date` and `Completion_Date`, averaged over orders with both dates.
- Bottleneck area is counted as reported in `Primary_Bottleneck`; related delay and overtime remain descriptive. No causal attribution is inferred.

### Printing and downtime

- Print good-unit yield = good print units / printed units. Reprint quantity and reported consumable/rework costs are displayed separately.
- Downtime totals distinguish planned and unplanned events and hours by production area and month.
- Downtime cannot be allocated to an individual product, campaign, or order with the available keys. It appears as factory-wide context only.

## Rebuild

Run after the core feature-table builder and before opening the dashboard:

```powershell
python .\src\product_radar\data\build_marketing_production.py
```

The app expects all five output files above in `data/processed/`.
