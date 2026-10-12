"""Build reproducible product-month and product-location-month CSVs.

Uses only Python's standard library. Source CSVs stay in the project root and
are never modified. Run from any directory with Python 3.10+:
    python src/product_radar/data/build_features.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed"
# Finished-goods decision scope. Corporate and production facilities are not
# included unless confirmed as finished-goods inventory locations.
IN_SCOPE_INVENTORY_LOCATION_IDS = {"LOC001", "LOC002", "LOC003"}


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(row: dict[str, str], field: str) -> float:
    value = row.get(field, "").strip()
    return float(value) if value else 0.0


def month_of(value: str) -> str:
    return value[:7]


def month_range(first: str, last: str) -> list[str]:
    year, month = map(int, first.split("-")[:2])
    end_year, end_month = map(int, last.split("-")[:2])
    result: list[str] = []
    while (year, month) <= (end_year, end_month):
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return result


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    products = read_csv("Product_Master.csv")
    sales = read_csv("Sales_Transactions.csv")
    inventory = read_csv("Inventory_History.csv")
    quality = read_csv("Quality.csv")
    locations = read_csv("Locations.csv")

    product_by_id = {row["Product_ID"]: row for row in products}
    location_ids = {row["Location_ID"] for row in locations}
    unknown_scope_ids = IN_SCOPE_INVENTORY_LOCATION_IDS - location_ids
    if unknown_scope_ids:
        raise ValueError(f"Inventory scope contains unknown location IDs: {sorted(unknown_scope_ids)}")
    if len(product_by_id) != len(products):
        raise ValueError("Product_Master.csv has duplicate Product_ID values")

    def validate_product(source_name: str, rows: list[dict[str, str]]) -> None:
        unknown = sorted({r["Product_ID"] for r in rows} - product_by_id.keys())
        if unknown:
            raise ValueError(f"{source_name} has unknown Product_ID values: {unknown[:5]}")

    for name, rows in (("Sales_Transactions.csv", sales),
                       ("Inventory_History.csv", inventory),
                       ("Quality.csv", quality)):
        validate_product(name, rows)

    months = month_range(
        min(month_of(row["Order_Date"]) for row in sales),
        max(month_of(row["Order_Date"]) for row in sales),
    )
    sales_by_key: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for row in sales:
        key = (row["Product_ID"], month_of(row["Order_Date"]))
        if row["Month_Key"] != key[1]:
            raise ValueError(f"Month_Key disagrees with Order_Date on Row_ID={row['Row_ID']}")
        agg = sales_by_key[key]
        agg["sales_row_count"] += 1
        agg["sales_units_on_rows"] += number(row, "Quantity")
        agg["gross_sales_egp"] += number(row, "Gross_Sales_EGP")
        agg["source_net_sales_egp"] += number(row, "Net_Sales_EGP")
        agg["estimated_cogs_egp"] += number(row, "Estimated_COGS_EGP")
        agg["estimated_gross_profit_egp"] += number(row, "Gross_Profit_EGP")
        agg["refund_value_egp"] += number(row, "Refund_Value_EGP")
        agg["returned_sales_row_count"] += row["Returned"].strip().lower() == "yes"
        agg["quality_related_return_row_count"] += (
            row["Quality_Related_Return"].strip().lower() == "yes"
        )
        agg["discount_value_egp"] += (
            number(row, "Gross_Sales_EGP") - number(row, "Net_Sales_EGP")
        )

    quality_by_key: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    quality_roots: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    quality_stages: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in quality:
        key = (row["Product_ID"], month_of(row["Inspection_Date"]))
        agg = quality_by_key[key]
        agg["inspection_count"] += 1
        agg["inspected_units"] += number(row, "Inspected_Qty")
        agg["rejected_units"] += number(row, "Rejected_Qty")
        agg["quality_estimated_loss_egp"] += number(row, "Estimated_Loss_EGP")
        rejected = number(row, "Rejected_Qty")
        quality_roots[key][row["Root_Cause"]] += rejected
        quality_stages[key][row["Stage"]] += rejected

    product_month: list[dict[str, object]] = []
    for product_id, product in product_by_id.items():
        for month in months:
            key = (product_id, month)
            s = sales_by_key.get(key, {})
            q = quality_by_key.get(key, {})
            rows = s.get("sales_row_count", 0.0)
            net = s.get("source_net_sales_egp", 0.0)
            gross = s.get("gross_sales_egp", 0.0)
            inspections = q.get("inspection_count", 0.0)
            inspected = q.get("inspected_units", 0.0)
            root_counts = quality_roots.get(key, Counter())
            stage_counts = quality_stages.get(key, Counter())
            top_root = max(root_counts.items(), key=lambda item: (item[1], item[0])) if root_counts else ("", 0)
            top_stage = max(stage_counts.items(), key=lambda item: (item[1], item[0])) if stage_counts else ("", 0)
            record: dict[str, object] = {
                "Month_Key": month,
                "Product_ID": product_id,
                "SKU": product["SKU"],
                "Product_Name": product["Product_Name"],
                "Brand": product["Brand"],
                "Product_Family": product["Product_Family"],
                "sales_row_count": int(rows),
                "sales_units_on_rows": round(s.get("sales_units_on_rows", 0.0), 2),
                "gross_sales_egp": round(gross, 2),
                "source_net_sales_egp": round(net, 2),
                "discount_value_egp": round(s.get("discount_value_egp", 0.0), 2),
                "estimated_cogs_egp": round(s.get("estimated_cogs_egp", 0.0), 2),
                "estimated_gross_profit_egp": round(
                    s.get("estimated_gross_profit_egp", 0.0), 2
                ),
                "estimated_gross_margin_pct": (
                    round(s.get("estimated_gross_profit_egp", 0.0) / net, 6)
                    if net else ""
                ),
                "returned_sales_row_count": int(s.get("returned_sales_row_count", 0.0)),
                "returned_sales_row_rate": (
                    round(s.get("returned_sales_row_count", 0.0) / rows, 6) if rows else ""
                ),
                "quality_related_return_row_count": int(
                    s.get("quality_related_return_row_count", 0.0)
                ),
                "refund_value_egp": round(s.get("refund_value_egp", 0.0), 2),
                "quality_inspection_count": int(inspections),
                "quality_inspected_units": int(inspected),
                "quality_rejected_units": int(q.get("rejected_units", 0.0)),
                "quality_rejection_rate": (
                    round(q.get("rejected_units", 0.0) / inspected, 6) if inspected else ""
                ),
                "quality_top_root_cause": top_root[0],
                "quality_top_root_cause_rejected_units": int(top_root[1]),
                "quality_top_inspection_stage": top_stage[0],
                "quality_top_stage_rejected_units": int(top_stage[1]),
                "quality_no_significant_issue_rejected_units": int(
                    root_counts.get("No significant issue", 0.0)
                ),
                "quality_unexplained_rejection_flag": root_counts.get(
                    "No significant issue", 0.0
                ) > 0,
                "quality_estimated_loss_egp": round(
                    q.get("quality_estimated_loss_egp", 0.0), 2
                ),
                "sales_coverage": "observed" if rows else "no_sales_rows",
                "quality_coverage": "observed" if inspections else "no_inspections",
                "returns_quality_link": "product-period association only; no transaction-to-inspection key",
            }
            product_month.append(record)

    inv_by_month: dict[str, set[str]] = defaultdict(set)
    inv_locations = {row["Location_ID"] for row in inventory}
    for row in inventory:
        if row["Location_ID"] in IN_SCOPE_INVENTORY_LOCATION_IDS:
            inv_by_month[month_of(row["Snapshot_Month"])].add(row["Location_ID"])

    product_location_month: list[dict[str, object]] = []
    for row in inventory:
        opening = number(row, "Opening_Stock")
        received = number(row, "Received_Qty")
        sold = number(row, "Sold_Qty")
        returned = number(row, "Returned_Qty")
        damaged = number(row, "Damaged_Qty")
        closing = number(row, "Closing_Stock")
        delta = closing - (opening + received - sold + returned - damaged)
        month = month_of(row["Snapshot_Month"])
        product = product_by_id[row["Product_ID"]]
        product_location_month.append({
            "Snapshot_Month": month,
            "Product_ID": row["Product_ID"],
            "SKU": product["SKU"],
            "Product_Name": product["Product_Name"],
            "Location_ID": row["Location_ID"],
            "Location_Name": row["Location_Name"],
            "Opening_Stock": row["Opening_Stock"],
            "Received_Qty": row["Received_Qty"],
            "Sold_Qty": row["Sold_Qty"],
            "Returned_Qty": row["Returned_Qty"],
            "Damaged_Qty": row["Damaged_Qty"],
            "Closing_Stock": row["Closing_Stock"],
            "Avg_Daily_Sales_90D": row["Avg_Daily_Sales_90D"],
            "Safety_Stock_Units": row["Safety_Stock_Units"],
            "Reorder_Point_Units": row["Reorder_Point_Units"],
            "Supplier_Lead_Time_Days": row["Supplier_Lead_Time_Days"],
            "Days_of_Cover": row["Days_of_Cover"],
            "Stockout_Days_In_Month": row["Stockout_Days_In_Month"],
            "inventory_flow_delta_units": round(delta, 2),
            "inventory_flow_balance_ok": abs(delta) <= 0.01,
            "inventory_location_coverage_count": len(inv_by_month[month]),
            "reference_location_count": len(IN_SCOPE_INVENTORY_LOCATION_IDS),
            "inventory_location_coverage_complete": (
                IN_SCOPE_INVENTORY_LOCATION_IDS.issubset(inv_locations)
            ),
            "inventory_location_in_decision_scope": (
                row["Location_ID"] in IN_SCOPE_INVENTORY_LOCATION_IDS
            ),
            "location_id_in_reference": row["Location_ID"] in location_ids,
            "days_of_cover_extreme_flag": number(row, "Days_of_Cover") > 365,
            "inventory_period_is_monthly_snapshot": True,
        })

    product_month_fields = list(product_month[0]) if product_month else []
    inventory_fields = list(product_location_month[0]) if product_location_month else []
    write_csv(OUTPUT / "product_month.csv", product_month, product_month_fields)
    write_csv(OUTPUT / "product_location_month.csv", product_location_month, inventory_fields)

    print(f"Wrote {len(product_month):,} product-month rows to {OUTPUT / 'product_month.csv'}")
    print(
        f"Wrote {len(product_location_month):,} product-location-month rows "
        f"to {OUTPUT / 'product_location_month.csv'}"
    )
    print(
        f"Months: {months[0]} through {months[-1]}; inventory scope coverage: "
        f"{len(IN_SCOPE_INVENTORY_LOCATION_IDS & inv_locations)} of "
        f"{len(IN_SCOPE_INVENTORY_LOCATION_IDS)} in-scope locations; "
        f"source locations: {len(inv_locations)} of {len(location_ids)} reference locations"
    )
    print(
        "Inventory flow mismatches: "
        f"{sum(not row['inventory_flow_balance_ok'] for row in product_location_month)}; "
        "extreme cover values (>365 days): "
        f"{sum(row['days_of_cover_extreme_flag'] for row in product_location_month)}"
    )


if __name__ == "__main__":
    main()
