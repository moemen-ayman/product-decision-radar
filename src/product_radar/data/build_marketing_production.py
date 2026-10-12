"""Build reproducible marketing and production analysis tables.

Marketing is grouped by campaign start month, product, and platform. Production
orders are grouped by completion month; print batches use print month. Machine
downtime is only grouped by month and business area because no product key is
available. All source files remain unchanged.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed"


def read_csv(name: str) -> list[dict[str, str]]:
    with (SOURCE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def num(row: dict[str, str], field: str) -> float:
    value = row.get(field, "").strip()
    return float(value) if value else 0.0


def month_of(value: str) -> str:
    return value[:7] if value else "Unknown"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_product_keys(name: str, rows: list[dict[str, str]], products: set[str]) -> None:
    unknown = sorted({row["Product_ID"] for row in rows} - products)
    if unknown:
        raise ValueError(f"{name} has unknown Product_ID values: {unknown[:5]}")


def main() -> None:
    catalog_rows = read_csv("Product_Master.csv")
    catalog = {row["Product_ID"]: row for row in catalog_rows}
    if len(catalog) != len(catalog_rows):
        raise ValueError("Product_Master.csv has duplicate Product_ID values")
    product_ids = set(catalog)

    marketing = read_csv("Marketing.csv")
    production = read_csv("Production_Orders.csv")
    printing = read_csv("Printing_Batches.csv")
    downtime = read_csv("Machine_Downtime.csv")
    for name, rows in (("Marketing.csv", marketing),
                       ("Production_Orders.csv", production),
                       ("Printing_Batches.csv", printing)):
        validate_product_keys(name, rows, product_ids)

    def ensure_unique(name: str, rows: list[dict[str, str]], key: str) -> None:
        values = [row[key] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"{name} has duplicate {key} values")

    ensure_unique("Marketing.csv", marketing, "Campaign_ID")
    ensure_unique("Production_Orders.csv", production, "Production_Order_ID")
    ensure_unique("Printing_Batches.csv", printing, "Print_Batch_ID")
    ensure_unique("Machine_Downtime.csv", downtime, "Downtime_ID")

    # Campaign performance measures are cohort-reported by campaign start month.
    marketing_groups: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    campaign_names: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in marketing:
        key = (month_of(row["Start_Date"]), row["Product_ID"], row["Platform"])
        agg = marketing_groups[key]
        agg["campaign_count"] += 1
        for field in ("Spend_EGP", "Impressions", "Clicks", "Landing_Page_Sessions",
                      "Orders_Attributed", "Attributed_Revenue_EGP"):
            agg[field.lower()] += num(row, field)
        campaign_names[key].append(row["Campaign_Name"])

    marketing_rows: list[dict[str, object]] = []
    for (month, product_id, platform), agg in sorted(marketing_groups.items()):
        product = catalog[product_id]
        spend = agg["spend_egp"]
        impressions = agg["impressions"]
        clicks = agg["clicks"]
        sessions = agg["landing_page_sessions"]
        orders = agg["orders_attributed"]
        revenue = agg["attributed_revenue_egp"]
        marketing_rows.append({
            "Campaign_Start_Month": month,
            "Product_ID": product_id,
            "SKU": product["SKU"],
            "Product_Name": product["Product_Name"],
            "Brand": product["Brand"],
            "Product_Family": product["Product_Family"],
            "Platform": platform,
            "Campaign_Count": int(agg["campaign_count"]),
            "Campaign_Names": " | ".join(campaign_names[(month, product_id, platform)]),
            "Spend_EGP": round(spend, 2),
            "Impressions": int(impressions),
            "Clicks": int(clicks),
            "Landing_Page_Sessions": int(sessions),
            "Orders_Attributed": int(orders),
            "Attributed_Revenue_EGP": round(revenue, 2),
            "Attributed_ROAS": round(revenue / spend, 4) if spend else "",
            "Click_Through_Rate": round(clicks / impressions, 6) if impressions else "",
            "Session_Conversion_Rate": round(orders / sessions, 6) if sessions else "",
            "Attribution_Grain": "campaign start-month cohort; campaign performance may span later months",
        })

    # Production output is assigned to the actual completion month. Pending
    # records without completion dates are kept in an explicit Unknown month.
    production_groups: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    bottlenecks: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    bottleneck_rows: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for row in production:
        month = month_of(row["Completion_Date"])
        key = (month, row["Product_ID"])
        agg = production_groups[key]
        agg["order_count"] += 1
        agg["planned_qty"] += num(row, "Planned_Qty")
        agg["produced_qty"] += num(row, "Produced_Qty")
        agg["good_qty"] += num(row, "Good_Qty")
        agg["rejected_qty"] += num(row, "Rejected_Qty")
        agg["efficiency_pct_sum"] += num(row, "Efficiency_Pct")
        agg["delay_days_sum"] += num(row, "Delay_Days")
        agg["late_order_count"] += num(row, "Delay_Days") > 0
        agg["overtime_hours"] += num(row, "Overtime_Hours")
        if row["Start_Date"] and row["Completion_Date"]:
            agg["lead_time_days_sum"] += (
                date.fromisoformat(row["Completion_Date"])
                - date.fromisoformat(row["Start_Date"])
            ).days
            agg["completed_with_dates"] += 1
        bottleneck = row["Primary_Bottleneck"].strip()
        if bottleneck and bottleneck.lower() != "none":
            bottlenecks[key][bottleneck] += 1
            by_stage = bottleneck_rows[(month, row["Product_ID"], bottleneck)]
            by_stage["order_count"] += 1
            by_stage["delay_days"] += num(row, "Delay_Days")
            by_stage["overtime_hours"] += num(row, "Overtime_Hours")

    production_rows: list[dict[str, object]] = []
    for (month, product_id), agg in sorted(production_groups.items()):
        product = catalog[product_id]
        orders = int(agg["order_count"])
        planned = agg["planned_qty"]
        produced = agg["produced_qty"]
        good = agg["good_qty"]
        bottleneck_counts = bottlenecks[(month, product_id)]
        top_bottleneck = bottleneck_counts.most_common(1)[0] if bottleneck_counts else ("None reported", 0)
        production_rows.append({
            "Completion_Month": month,
            "Product_ID": product_id,
            "SKU": product["SKU"],
            "Product_Name": product["Product_Name"],
            "Brand": product["Brand"],
            "Product_Family": product["Product_Family"],
            "Completed_Order_Count": orders,
            "Planned_Qty": int(planned),
            "Produced_Qty": int(produced),
            "Good_Qty": int(good),
            "Rejected_Qty": int(agg["rejected_qty"]),
            "Plan_Fulfillment_Rate": round(produced / planned, 6) if planned else "",
            "Good_Unit_Yield": round(good / produced, 6) if produced else "",
            "Average_Reported_Efficiency_Pct": round(agg["efficiency_pct_sum"] / orders, 2) if orders else "",
            "Late_Order_Count": int(agg["late_order_count"]),
            "Late_Order_Rate": round(agg["late_order_count"] / orders, 6) if orders else "",
            "Average_Delay_Days": round(agg["delay_days_sum"] / orders, 2) if orders else "",
            "Overtime_Hours": round(agg["overtime_hours"], 2),
            "Orders_With_Reported_Bottleneck": sum(bottleneck_counts.values()),
            "Leading_Bottleneck": top_bottleneck[0],
            "Leading_Bottleneck_Order_Count": top_bottleneck[1],
            "Average_Order_Lead_Time_Days": round(
                agg["lead_time_days_sum"] / agg["completed_with_dates"], 2
            ) if agg["completed_with_dates"] else "",
            "Production_Grain": "order completion month; aggregated to product",
        })

    bottleneck_month_rows: list[dict[str, object]] = []
    for (month, product_id, stage), agg in sorted(bottleneck_rows.items()):
        product = catalog[product_id]
        bottleneck_month_rows.append({
            "Completion_Month": month,
            "Product_ID": product_id,
            "Product_Name": product["Product_Name"],
            "Bottleneck_Area": stage,
            "Affected_Order_Count": int(agg["order_count"]),
            "Associated_Delay_Days": int(agg["delay_days"]),
            "Associated_Overtime_Hours": round(agg["overtime_hours"], 2),
            "Interpretation": "reported order bottleneck; operational cause is not independently verified",
        })

    printing_groups: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    print_defects: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in printing:
        key = (month_of(row["Print_Date"]), row["Product_ID"])
        agg = printing_groups[key]
        agg["batch_count"] += 1
        for field in ("Planned_Qty", "Printed_Qty", "Good_Qty", "Rejected_Qty",
                      "Reprint_Qty", "Ink_or_Consumable_Cost_EGP", "Rework_Cost_EGP"):
            agg[field.lower()] += num(row, field)
        defect = row["Defect_Type"].strip()
        if defect and defect.lower() != "none":
            print_defects[key][defect] += num(row, "Rejected_Qty")

    printing_rows: list[dict[str, object]] = []
    for (month, product_id), agg in sorted(printing_groups.items()):
        product = catalog[product_id]
        batches = int(agg["batch_count"])
        printed = agg["printed_qty"]
        defects = print_defects[(month, product_id)]
        leading_defect = defects.most_common(1)[0] if defects else ("None reported", 0)
        printing_rows.append({
            "Print_Month": month,
            "Product_ID": product_id,
            "SKU": product["SKU"],
            "Product_Name": product["Product_Name"],
            "Brand": product["Brand"],
            "Product_Family": product["Product_Family"],
            "Print_Batch_Count": batches,
            "Planned_Qty": int(agg["planned_qty"]),
            "Printed_Qty": int(printed),
            "Good_Qty": int(agg["good_qty"]),
            "Rejected_Qty": int(agg["rejected_qty"]),
            "Reprint_Qty": int(agg["reprint_qty"]),
            "Print_Good_Yield": round(agg["good_qty"] / printed, 6) if printed else "",
            "Reported_Consumable_Cost_EGP": round(agg["ink_or_consumable_cost_egp"], 2),
            "Reported_Rework_Cost_EGP": round(agg["rework_cost_egp"], 2),
            "Leading_Reported_Defect": leading_defect[0],
            "Leading_Defect_Rejected_Units": int(leading_defect[1]),
            "Print_Grain": "print date month; batch-level product aggregate",
        })

    # Downtime is machine/area-level only; it cannot be attributed to products.
    downtime_groups: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    downtime_reasons: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in downtime:
        key = (month_of(row["Date"]), row["Business_Area"])
        agg = downtime_groups[key]
        agg["event_count"] += 1
        agg["downtime_hours"] += num(row, "Downtime_Hours")
        if row["Planned"].strip().lower() == "yes":
            agg["planned_event_count"] += 1
            agg["planned_downtime_hours"] += num(row, "Downtime_Hours")
        else:
            agg["unplanned_event_count"] += 1
            agg["unplanned_downtime_hours"] += num(row, "Downtime_Hours")
        downtime_reasons[key][row["Reason"]] += num(row, "Downtime_Hours")

    downtime_rows: list[dict[str, object]] = []
    for (month, area), agg in sorted(downtime_groups.items()):
        top_reason = downtime_reasons[(month, area)].most_common(1)[0]
        downtime_rows.append({
            "Downtime_Month": month,
            "Business_Area": area,
            "Downtime_Event_Count": int(agg["event_count"]),
            "Planned_Event_Count": int(agg["planned_event_count"]),
            "Unplanned_Event_Count": int(agg["unplanned_event_count"]),
            "Downtime_Hours": round(agg["downtime_hours"], 2),
            "Planned_Downtime_Hours": round(agg["planned_downtime_hours"], 2),
            "Unplanned_Downtime_Hours": round(agg["unplanned_downtime_hours"], 2),
            "Leading_Reason_By_Hours": top_reason[0],
            "Leading_Reason_Hours": round(top_reason[1], 2),
            "Product_Attribution": "unavailable; source downtime has no Product_ID",
        })

    outputs = {
        "product_marketing_month.csv": marketing_rows,
        "product_production_month.csv": production_rows,
        "product_production_bottlenecks_month.csv": bottleneck_month_rows,
        "product_printing_month.csv": printing_rows,
        "operations_downtime_month.csv": downtime_rows,
    }
    for name, rows in outputs.items():
        write_csv(OUTPUT / name, rows)
        print(f"Wrote {len(rows):,} rows to {OUTPUT / name}")
    print(
        "Marketing attribution is grouped by campaign start month; production by completion month; "
        "downtime remains area-level because no product key is supplied."
    )


if __name__ == "__main__":
    main()
