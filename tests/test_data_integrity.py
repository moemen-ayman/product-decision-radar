"""Regression checks for source-to-processed metrics and product joins.

Run from the project root with: python -m unittest discover -s tests -v
These checks read the existing files; they do not rebuild or modify outputs.
"""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.product_radar.data.build_features import (  # noqa: E402
    IN_SCOPE_INVENTORY_LOCATION_IDS,
    month_of,
    month_range,
)
from src.product_radar.decisions.rules import RULE_CONFIG, num, rate_vs_portfolio  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def as_float(row: dict[str, str], field: str) -> float:
    return float(row[field]) if row.get(field, "") else 0.0


class MetricHelperTests(unittest.TestCase):
    def test_month_range_includes_both_ends_and_crosses_year(self) -> None:
        self.assertEqual(month_range("2025-11", "2026-02"), [
            "2025-11", "2025-12", "2026-01", "2026-02",
        ])

    def test_month_of_uses_calendar_month(self) -> None:
        self.assertEqual(month_of("2026-09-30"), "2026-09")

    def test_blank_numeric_source_values_default_to_zero(self) -> None:
        self.assertEqual(num({"amount": ""}, "amount"), 0.0)

    def test_zero_portfolio_baseline_is_explained(self) -> None:
        explanation = rate_vs_portfolio(0.02, 0.0, 2.0)
        self.assertIn("portfolio baseline is 0.0%", explanation)
        self.assertIn("any positive rate exceeds", explanation)


class ProcessedDataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = ROOT / "data" / "raw"
        processed = ROOT / "data" / "processed"
        cls.products = read_csv(raw / "Product_Master.csv")
        cls.sales = read_csv(raw / "Sales_Transactions.csv")
        cls.quality = read_csv(raw / "Quality.csv")
        cls.locations = read_csv(raw / "Locations.csv")
        cls.inventory_source = read_csv(raw / "Inventory_History.csv")
        cls.product_month = read_csv(processed / "product_month.csv")
        cls.location_month = read_csv(processed / "product_location_month.csv")
        cls.actions = read_csv(processed / "product_actions.csv")

    def test_product_month_is_unique_and_complete(self) -> None:
        keys = [(r["Product_ID"], r["Month_Key"]) for r in self.product_month]
        self.assertEqual(len(keys), len(set(keys)))
        product_ids = {r["Product_ID"] for r in self.products}
        months = sorted({r["Month_Key"] for r in self.product_month})
        self.assertEqual(set(keys), {
            (product_id, month) for product_id in product_ids for month in months
        })

    def test_sales_metrics_reconcile_to_source_by_product_month(self) -> None:
        expected: dict[tuple[str, str], dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for row in self.sales:
            key = (row["Product_ID"], row["Month_Key"])
            expected[key]["rows"] += 1
            expected[key]["units"] += as_float(row, "Quantity")
            expected[key]["net"] += as_float(row, "Net_Sales_EGP")
            expected[key]["refunds"] += as_float(row, "Refund_Value_EGP")
            expected[key]["returned"] += row["Returned"].strip().lower() == "yes"

        for row in self.product_month:
            values = expected[(row["Product_ID"], row["Month_Key"])]
            self.assertEqual(int(row["sales_row_count"]), int(values["rows"]))
            self.assertEqual(int(row["returned_sales_row_count"]), int(values["returned"]))
            self.assertAlmostEqual(float(row["sales_units_on_rows"]), values["units"], places=2)
            self.assertAlmostEqual(float(row["source_net_sales_egp"]), values["net"], places=2)
            self.assertAlmostEqual(float(row["refund_value_egp"]), values["refunds"], places=2)

    def test_quality_metrics_reconcile_to_source_by_product_month(self) -> None:
        expected: dict[tuple[str, str], dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for row in self.quality:
            key = (row["Product_ID"], row["Inspection_Date"][:7])
            expected[key]["inspected"] += as_float(row, "Inspected_Qty")
            expected[key]["rejected"] += as_float(row, "Rejected_Qty")

        for row in self.product_month:
            values = expected[(row["Product_ID"], row["Month_Key"])]
            self.assertEqual(int(row["quality_inspected_units"]), int(values["inspected"]))
            self.assertEqual(int(row["quality_rejected_units"]), int(values["rejected"]))

    def test_inventory_keys_scope_and_balance_flags(self) -> None:
        keys = [(r["Product_ID"], r["Location_ID"], r["Snapshot_Month"])
                for r in self.location_month]
        self.assertEqual(len(keys), len(set(keys)))
        product_ids = {r["Product_ID"] for r in self.products}
        location_ids = {r["Location_ID"] for r in self.locations}
        self.assertTrue({r["Product_ID"] for r in self.location_month} <= product_ids)
        self.assertTrue({r["Location_ID"] for r in self.location_month} <= location_ids)

        for row in self.location_month:
            expected_scope = row["Location_ID"] in IN_SCOPE_INVENTORY_LOCATION_IDS
            self.assertEqual(row["inventory_location_in_decision_scope"] == "True", expected_scope)
            delta = (
                as_float(row, "Closing_Stock")
                - as_float(row, "Opening_Stock")
                - as_float(row, "Received_Qty")
                + as_float(row, "Sold_Qty")
                - as_float(row, "Returned_Qty")
                + as_float(row, "Damaged_Qty")
            )
            self.assertAlmostEqual(float(row["inventory_flow_delta_units"]), delta, places=2)
            self.assertEqual(row["inventory_flow_balance_ok"] == "True", abs(delta) <= 0.01)

    def test_product_actions_have_one_known_product_and_valid_signal_codes(self) -> None:
        product_ids = {r["Product_ID"] for r in self.products}
        action_ids = [r["Product_ID"] for r in self.actions]
        self.assertEqual(len(action_ids), len(set(action_ids)))
        self.assertEqual(set(action_ids), product_ids)
        allowed = {
            "historical_availability_risk", "inventory_flow_mismatch",
            "negative_estimated_economics", "low_margin_guard",
            "elevated_return_row_rate", "elevated_quality_rejection_rate",
            "possible_excess_stock", "extreme_days_of_cover", "none",
        }
        for row in self.actions:
            self.assertTrue(set(row["Signals"].split(";")) <= allowed)
            self.assertEqual(json.loads(row["Config_Thresholds"]), RULE_CONFIG)


if __name__ == "__main__":
    unittest.main()
