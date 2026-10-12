"""Headless UI checks for the dashboard's sales-context period selector."""

from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "product_radar" / "app.py"
MONTHLY_DATA = ROOT / "data" / "processed" / "product_month.csv"


class DashboardPeriodFilterTests(unittest.TestCase):
    def test_period_changes_sales_context_without_changing_actions(self) -> None:
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)

        monthly = pd.read_csv(MONTHLY_DATA, encoding="utf-8-sig")
        months = sorted(monthly["Month_Key"].dropna().unique().tolist())
        periods = {
            "Latest month": months[-1:],
            "Latest 3 months": months[-3:],
            "Latest 6 months": months[-6:],
            "All available months": months,
        }
        selector = next(
            widget for widget in app.selectbox
            if widget.label == "Sales context period"
        )
        action_table = app.dataframe[0].value
        initial_actions = action_table["Suggested action"].tolist()

        for label, selected_months in periods.items():
            selector.select(label).run()
            self.assertFalse(app.exception)
            current_selector = next(
                widget for widget in app.selectbox
                if widget.label == "Sales context period"
            )
            self.assertEqual(current_selector.value, label)
            caption = next(
                item.value for item in app.caption
                if item.value.startswith("Sales context:")
            )
            self.assertIn(
                f"{selected_months[0]} to {selected_months[-1]}", caption
            )
            self.assertEqual(
                app.dataframe[0].value["Suggested action"].tolist(),
                initial_actions,
            )


if __name__ == "__main__":
    unittest.main()
