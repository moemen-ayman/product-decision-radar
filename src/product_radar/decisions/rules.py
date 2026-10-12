"""Explainable, provisional product action rules.

Run the feature builder first, then:
    python src/product_radar/decisions/rules.py

The thresholds below are review triggers, not approved purchasing or pricing
policy. Every output row keeps the evidence, coverage, period, and conflicts.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "processed"

# Provisional, visible review triggers. Tune with the business owner.
RULE_CONFIG = {
    "min_sales_rows_for_return_signal": 50,
    "return_rate_multiple_of_portfolio": 2.0,
    "low_margin_guard_fraction": 0.05,
    "negative_margin_months_for_review": 2,
    "min_inspected_units_for_quality_signal": 500,
    "quality_rate_multiple_of_portfolio": 1.25,
    "min_cover_days_for_excess_signal": 120,
    "stock_to_recent_local_sales_multiple": 3.0,
    "low_cover_days_for_availability_signal": 14,
    "inventory_balance_tolerance_units": 0.01,
}

RETURN_REASON_EN = {
    "Size / fit": "Size / fit",
    "Print issue": "Print issue",
    "Fabric / stitching": "Fabric / stitching",
    "Color / appearance": "Color / appearance",
    "Changed mind": "Changed mind",
    "Delivery issue": "Delivery issue",
}
QUALITY_CAUSE_EN = {
    "Curing temperature": "Curing temperature",
    "Operator method": "Operator method",
    "Pattern / measurement": "Pattern / measurement",
    "No significant issue": "No significant issue",
    "Process variation": "Process variation",
    "Machine calibration": "Machine calibration",
    "Handling / packing": "Handling / packing",
    "Material variation": "Material variation",
}
QUALITY_STAGE_EN = {
    "Fabric": "Fabric",
    "Final": "Final inspection",
    "Sewing": "Sewing",
    "Finishing": "Finishing",
    "Cutting": "Cutting",
    "Printing": "Printing",
}
LOCATION_TYPE_EN = {"Retail Store": "Retail Store", "Digital Store": "Digital Store", "B2B / Wholesale": "B2B / Wholesale"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def num(row: dict[str, str], field: str) -> float:
    value = row.get(field, "").strip()
    return float(value) if value else 0.0


def fmt(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}"


def rate_vs_portfolio(rate: float, portfolio_rate: float, trigger_multiple: float) -> str:
    if portfolio_rate > 0:
        ratio = rate / portfolio_rate
        return (
            f"{rate:.1%} ({ratio:.2f}x portfolio; portfolio {portfolio_rate:.1%}; "
            f"trigger >{trigger_multiple:.2f}x)"
        )
    return (
        f"{rate:.1%} (portfolio baseline is 0.0%; any positive rate exceeds "
        f"the >{trigger_multiple:.2f}x trigger)"
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    product_month = read_csv(DATA / "product_month.csv")
    inventory = read_csv(DATA / "product_location_month.csv")
    raw = ROOT / "data" / "raw"
    quality_source = read_csv(raw / "Quality.csv")
    sales_source = read_csv(raw / "Sales_Transactions.csv")
    locations = {row["Location_ID"]: row for row in read_csv(raw / "Locations.csv")}

    sales_months = sorted({row["Month_Key"] for row in product_month})
    latest_month = sales_months[-1]
    recent_sales_months = sales_months[-3:]
    recent_quality_months = sales_months[-6:]
    latest_inventory_month = max(row["Snapshot_Month"] for row in inventory)

    product_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in product_month:
        product_rows[row["Product_ID"]].append(row)

    sales_by_product_location: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    return_reasons_by_product: dict[str, Counter[str]] = defaultdict(Counter)
    quality_return_rows_by_product: dict[str, int] = defaultdict(int)
    for row in sales_source:
        if row["Month_Key"] in recent_sales_months:
            key = (row["Product_ID"], row["Location_ID"])
            sales_by_product_location[key]["units"] += num(row, "Quantity")
            sales_by_product_location[key]["rows"] += 1
            if row["Returned"].strip().lower() == "yes":
                return_reasons_by_product[row["Product_ID"]][row["Return_Reason"]] += 1
                if row["Quality_Related_Return"].strip().lower() == "yes":
                    quality_return_rows_by_product[row["Product_ID"]] += 1

    quality_by_product: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    quality_root_by_product: dict[str, Counter[str]] = defaultdict(Counter)
    quality_stage_by_product: dict[str, Counter[str]] = defaultdict(Counter)
    for row in quality_source:
        if row["Inspection_Date"][:7] not in recent_quality_months:
            continue
        pid = row["Product_ID"]
        rejected = num(row, "Rejected_Qty")
        quality_by_product[pid]["inspected"] += num(row, "Inspected_Qty")
        quality_by_product[pid]["rejected"] += rejected
        quality_by_product[pid]["loss"] += num(row, "Estimated_Loss_EGP")
        quality_root_by_product[pid][row["Root_Cause"]] += rejected
        quality_stage_by_product[pid][row["Stage"]] += rejected

    portfolio_rows = [
        row for row in product_month if row["Month_Key"] in recent_sales_months
    ]
    portfolio_sales_rows = sum(num(row, "sales_row_count") for row in portfolio_rows)
    portfolio_returned_rows = sum(
        num(row, "returned_sales_row_count") for row in portfolio_rows
    )
    portfolio_return_rate = (
        portfolio_returned_rows / portfolio_sales_rows if portfolio_sales_rows else 0.0
    )
    quality_inspected_total = sum(row["inspected"] for row in quality_by_product.values())
    quality_rejected_total = sum(row["rejected"] for row in quality_by_product.values())
    portfolio_quality_rate = (
        quality_rejected_total / quality_inspected_total if quality_inspected_total else 0.0
    )

    inventory_by_product: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inventory:
        if (
            row["Snapshot_Month"] == latest_inventory_month
            and row["Location_ID"] in {"LOC001", "LOC002", "LOC003"}
        ):
            inventory_by_product[row["Product_ID"]].append(row)

    products = sorted(product_rows)
    output: list[dict[str, object]] = []
    in_scope_location_ids = {"LOC001", "LOC002", "LOC003"}
    for pid in products:
        month_rows = product_rows[pid]
        period_rows = [row for row in month_rows if row["Month_Key"] in recent_sales_months]
        sales_rows = sum(num(row, "sales_row_count") for row in period_rows)
        sales_units = sum(num(row, "sales_units_on_rows") for row in period_rows)
        net_sales = sum(num(row, "source_net_sales_egp") for row in period_rows)
        gross_profit = sum(num(row, "estimated_gross_profit_egp") for row in period_rows)
        margin = gross_profit / net_sales if net_sales else 0.0
        returned_rows = sum(num(row, "returned_sales_row_count") for row in period_rows)
        return_rate = returned_rows / sales_rows if sales_rows else 0.0
        top_return_reasons = return_reasons_by_product[pid].most_common(3)
        quality_return_rows = quality_return_rows_by_product[pid]
        negative_months = sum(
            num(row, "source_net_sales_egp") > 0
            and num(row, "estimated_gross_profit_egp") < 0
            for row in period_rows
        )
        q = quality_by_product[pid]
        inspected = q["inspected"]
        rejected = q["rejected"]
        rejection_rate = rejected / inspected if inspected else 0.0
        top_root = max(quality_root_by_product[pid].items(), key=lambda item: (item[1], item[0])) if quality_root_by_product[pid] else ("", 0.0)
        top_stage = max(quality_stage_by_product[pid].items(), key=lambda item: (item[1], item[0])) if quality_stage_by_product[pid] else ("", 0.0)

        local_inventory = inventory_by_product.get(pid, [])
        stockout_locations: list[str] = []
        mismatch_locations: list[str] = []
        excess_locations: list[str] = []
        extreme_cover_locations: list[str] = []
        local_evidence: list[str] = []
        total_closing_stock = 0.0
        any_flow_mismatch = False
        for stock in local_inventory:
            location_id = stock["Location_ID"]
            location_type = locations.get(location_id, {}).get("Location_Type", "Unknown")
            location_type = LOCATION_TYPE_EN.get(location_type, location_type)
            closing = num(stock, "Closing_Stock")
            cover = num(stock, "Days_of_Cover")
            stockout_days = num(stock, "Stockout_Days_In_Month")
            reorder = num(stock, "Reorder_Point_Units")
            flow_delta = num(stock, "inventory_flow_delta_units")
            local_sales = sales_by_product_location[(pid, location_id)]["units"]
            total_closing_stock += closing
            has_stockout_signal = stockout_days > 0 or (
                closing <= reorder
                and cover <= RULE_CONFIG["low_cover_days_for_availability_signal"]
            )
            if has_stockout_signal:
                stockout_locations.append(location_id)
            if abs(flow_delta) > RULE_CONFIG["inventory_balance_tolerance_units"]:
                mismatch_locations.append(location_id)
                any_flow_mismatch = True
            if cover > 365:
                extreme_cover_locations.append(location_id)
            if (
                cover > RULE_CONFIG["min_cover_days_for_excess_signal"]
                and closing > 0
                and (local_sales == 0 or closing >= RULE_CONFIG["stock_to_recent_local_sales_multiple"] * local_sales)
            ):
                excess_locations.append(location_id)
            if has_stockout_signal or location_id in mismatch_locations or location_id in excess_locations or cover > 365:
                local_evidence.append(
                    f"{location_id} ({location_type}): closing={fmt(closing, 0)}, "
                    f"cover={fmt(cover)}, stockout_days={fmt(stockout_days, 0)}, "
                    f"3m_units={fmt(local_sales, 0)}, reorder={fmt(reorder, 0)}, "
                    f"flow_delta={fmt(flow_delta, 0)}"
                )

        availability_signal = bool(stockout_locations)
        mismatch_signal = bool(mismatch_locations)
        excess_signal = bool(excess_locations)
        extreme_cover_signal = bool(extreme_cover_locations)
        negative_margin_signal = margin < 0 or (
            negative_months >= RULE_CONFIG["negative_margin_months_for_review"]
        )
        low_margin_signal = (
            sales_rows > 0
            and net_sales > 0
            and margin < RULE_CONFIG["low_margin_guard_fraction"]
        )
        return_signal = (
            sales_rows >= RULE_CONFIG["min_sales_rows_for_return_signal"]
            and return_rate > portfolio_return_rate * RULE_CONFIG["return_rate_multiple_of_portfolio"]
        )
        quality_signal = (
            inspected >= RULE_CONFIG["min_inspected_units_for_quality_signal"]
            and rejection_rate > portfolio_quality_rate * RULE_CONFIG["quality_rate_multiple_of_portfolio"]
        )
        unexplained_rejects = quality_root_by_product[pid].get("No significant issue", 0.0)

        signal_codes: list[str] = []
        explanations: list[str] = []
        if availability_signal:
            signal_codes.append("historical_availability_risk")
            explanations.append(
                f"Historical stockout/low-cover signal at: {', '.join(stockout_locations)}. "
                "This is the September snapshot, not live inventory."
            )
        if mismatch_signal:
            signal_codes.append("inventory_flow_mismatch")
            explanations.append(
                f"Inventory movement differs from the balance equation by more than 0.01 units at: {', '.join(mismatch_locations)}."
            )
        if negative_margin_signal:
            signal_codes.append("negative_estimated_economics")
            explanations.append(
                f"Weighted estimated margin is {margin:.1%}; estimated gross profit is EGP {fmt(gross_profit, 0)}; "
                f"negative-profit months: {negative_months} of 3. Review cost and price before taking commercial action."
            )
        if low_margin_signal and not negative_margin_signal:
            signal_codes.append("low_margin_guard")
            explanations.append(
                f"Estimated margin of {margin:.1%} is below the provisional 5% review threshold; protect margin before supply, promotion, or markdown decisions."
            )
        if return_signal:
            signal_codes.append("elevated_return_row_rate")
            return_comparison = rate_vs_portfolio(
                return_rate,
                portfolio_return_rate,
                RULE_CONFIG["return_rate_multiple_of_portfolio"],
            )
            reason_detail = ", ".join(
                f"{RETURN_REASON_EN.get(reason, reason)} ({count})" for reason, count in top_return_reasons
            ) or "No return reasons recorded"
            explanations.append(
                f"Returned-row rate is {return_comparison} across {int(sales_rows)} sales rows "
                f"(minimum {RULE_CONFIG['min_sales_rows_for_return_signal']} required); leading reasons: {reason_detail}. "
                f"Only {quality_return_rows} rows are tagged as quality-related; do not assume returns indicate defects."
            )
        if quality_signal:
            signal_codes.append("elevated_quality_rejection_rate")
            quality_comparison = rate_vs_portfolio(
                rejection_rate,
                portfolio_quality_rate,
                RULE_CONFIG["quality_rate_multiple_of_portfolio"],
            )
            unexplained_detail = (
                f" {int(unexplained_rejects)} units are tagged 'No significant issue' and need interpretation."
                if unexplained_rejects else ""
            )
            explanations.append(
                f"Quality rejection rate is {quality_comparison} of {int(inspected):,} inspected units "
                f"(minimum {RULE_CONFIG['min_inspected_units_for_quality_signal']} required); leading cause: {QUALITY_CAUSE_EN.get(top_root[0], top_root[0])} "
                f"({int(top_root[1])} units), leading stage: {QUALITY_STAGE_EN.get(top_stage[0], top_stage[0])} ({int(top_stage[1])} units)."
                f"{unexplained_detail}"
            )
        if excess_signal:
            signal_codes.append("possible_excess_stock")
            explanations.append(
                f"Days of cover exceed {RULE_CONFIG['min_cover_days_for_excess_signal']} and location stock is "
                f"at least 3x local quarterly sales at: {', '.join(excess_locations)}; review seasonality and stock accuracy."
            )
        if extreme_cover_signal:
            signal_codes.append("extreme_days_of_cover")
            explanations.append(
                f"Days of cover exceed 365 at: {', '.join(extreme_cover_locations)}; check the demand denominator and stock value."
            )

        # Select one lead action while retaining every signal above.
        if availability_signal and mismatch_signal and low_margin_signal:
            primary_action = "Verify stock and margin before replenishment"
            priority = "High - Conflicting signals"
        elif availability_signal and mismatch_signal:
            primary_action = "Verify stock and inventory movements"
            priority = "High - Verification needed"
        elif negative_margin_signal:
            primary_action = "Review cost and price"
            priority = "High - Commercial review"
        elif availability_signal and low_margin_signal:
            primary_action = "Review margin before replenishment"
            priority = "High - Conflicting signals"
        elif availability_signal:
            primary_action = "Review historical availability"
            priority = "High - Historical signal"
        elif quality_signal:
            primary_action = "Investigate quality"
            priority = "Review"
        elif return_signal:
            primary_action = "Review return reasons and product fit"
            priority = "Review"
        elif excess_signal:
            primary_action = "Review excess stock and seasonality"
            priority = "Review"
        elif low_margin_signal:
            primary_action = "Review margin"
            priority = "Review"
        elif mismatch_signal:
            primary_action = "Verify inventory balance"
            priority = "Data review"
        elif extreme_cover_signal:
            primary_action = "Verify days of cover"
            priority = "Data review"
        else:
            primary_action = "Monitor - No action currently"
            priority = "Monitor"

        product = month_rows[0]
        output.append({
            "Product_ID": pid,
            "SKU": product["SKU"],
            "Product_Name": product["Product_Name"],
            "Brand": product["Brand"],
            "Product_Family": product["Product_Family"],
            "Primary_Action": primary_action,
            "Priority": priority,
            "Signals": ";".join(signal_codes) if signal_codes else "none",
            "Evidence_English": " ".join(explanations) if explanations else "No signals exceed the provisional review thresholds.",
            "Location_Evidence": " | ".join(local_evidence),
            "Sales_Period": f"{recent_sales_months[0]} to {recent_sales_months[-1]}",
            "Inventory_Snapshot_Month": latest_inventory_month,
            "Quality_Period": f"{recent_quality_months[0]} to {recent_quality_months[-1]}",
            "Sales_Rows_3M": int(sales_rows),
            "Sales_Units_On_Rows_3M": round(sales_units, 2),
            "Source_Net_Sales_EGP_3M": round(net_sales, 2),
            "Reported_Refund_Value_EGP_3M": round(
                sum(num(row, "refund_value_egp") for row in period_rows), 2
            ),
            "Estimated_Gross_Profit_EGP_3M": round(gross_profit, 2),
            "Estimated_Gross_Margin_3M": round(margin, 6) if net_sales else "",
            "Returned_Rows_3M": int(returned_rows),
            "Returned_Row_Rate_3M": round(return_rate, 6) if sales_rows else "",
            "Quality_Related_Return_Rows_3M": quality_return_rows,
            "Leading_Return_Reasons_3M": "; ".join(
                f"{reason} ({count})" for reason, count in top_return_reasons
            ),
            "Portfolio_Return_Row_Rate_3M": round(portfolio_return_rate, 6),
            "Inspected_Units_6M": int(inspected),
            "Rejected_Units_6M": int(rejected),
            "Estimated_Quality_Loss_EGP_6M": round(q["loss"], 2),
            "Quality_Rejection_Rate_6M": round(rejection_rate, 6) if inspected else "",
            "Portfolio_Quality_Rejection_Rate_6M": round(portfolio_quality_rate, 6),
            "Leading_Root_Cause_6M": top_root[0],
            "Leading_Root_Cause_Rejected_Units_6M": int(top_root[1]),
            "Leading_Stage_6M": top_stage[0],
            "Leading_Stage_Rejected_Units_6M": int(top_stage[1]),
            "Unexplained_Rejected_Units_6M": int(unexplained_rejects),
            "Closing_Stock_Units_In_Scope": round(total_closing_stock, 2),
            "Inventory_Locations_Covered": len({row["Location_ID"] for row in local_inventory}),
            "Inventory_Locations_In_Scope": len(in_scope_location_ids),
            "Inventory_Scope_Coverage_Complete": in_scope_location_ids.issubset(
                {row["Location_ID"] for row in local_inventory}
            ),
            "Inventory_Flow_Mismatch_Locations": ",".join(mismatch_locations),
            "Config_Thresholds": json.dumps(RULE_CONFIG, ensure_ascii=False, sort_keys=True),
        })

    priority_order = {"High - Verification needed": 0, "High - Commercial review": 1,
                      "High - Conflicting signals": 2, "High - Historical signal": 3,
                      "Review": 4, "Data review": 5, "Monitor": 6}
    output.sort(key=lambda row: (priority_order.get(str(row["Priority"]), 99),
                                 -len(str(row["Signals"]).split(";")),
                                 str(row["Product_ID"])))
    fields = list(output[0]) if output else []
    path = DATA / "product_actions.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    print(f"Wrote {len(output):,} product action rows to {path}")
    print(f"Sales period: {recent_sales_months[0]} to {recent_sales_months[-1]}; inventory snapshot: {latest_inventory_month}; quality period: {recent_quality_months[0]} to {recent_quality_months[-1]}")
    print("Primary actions:")
    for label, count in Counter(str(row["Primary_Action"]) for row in output).most_common():
        print(f"  {label}: {count}")
    print("Signals:")
    signal_counts = Counter(signal for row in output for signal in str(row["Signals"]).split(";") if signal != "none")
    for label, count in signal_counts.most_common():
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
