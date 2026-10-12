"""English, explainable product decision dashboard."""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

SIGNAL_LABELS = {
    "historical_availability_risk": "Historical stockout / low cover",
    "inventory_flow_mismatch": "Inventory movement mismatch",
    "negative_estimated_economics": "Negative estimated profitability",
    "low_margin_guard": "Low margin",
    "elevated_return_row_rate": "Elevated returns",
    "elevated_quality_rejection_rate": "Elevated quality rejection",
    "possible_excess_stock": "Possible excess stock",
    "extreme_days_of_cover": "Unusual days of cover",
}

FAMILY_LABELS = {
    "Pajamas/Homewear": "Pajamas / Homewear",
    "Kids Sets": "Kids' Sets",
    "T-Shirts": "T-Shirts",
    "Sweatshirts": "Sweatshirts",
}
RETURN_REASON_LABELS = {
    "Size / fit": "Size / fit",
    "Print issue": "Print issue",
    "Fabric / stitching": "Fabric / stitching",
    "Color / appearance": "Color / appearance",
    "Changed mind": "Changed mind",
    "Delivery issue": "Delivery issue",
}
QUALITY_CAUSE_LABELS = {
    "Curing temperature": "Curing temperature",
    "Operator method": "Operator method",
    "Pattern / measurement": "Pattern / measurement",
    "No significant issue": "No significant issue",
    "Process variation": "Process variation",
    "Machine calibration": "Machine calibration",
    "Handling / packing": "Handling / packing",
    "Material variation": "Material variation",
}
QUALITY_STAGE_LABELS = {
    "Fabric": "Fabric",
    "Final": "Final inspection",
    "Sewing": "Sewing",
    "Finishing": "Finishing",
    "Cutting": "Cutting",
    "Printing": "Printing",
}
LOCATION_LABELS = {
    "Retail Store": "Retail Store",
    "Digital Store": "Digital Store",
    "B2B / Wholesale": "B2B / Wholesale",
}


st.set_page_config(
    page_title="Product Decision Radar",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      html, body, [data-testid="stAppViewContainer"] {
        font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      }
      [data-testid="stMainBlockContainer"] {
        direction: ltr;
        text-align: left;
        max-width: 1500px;
        padding-top: 1.5rem;
      }
      [data-testid="stMarkdownContainer"], label, h1, h2, h3, p {
        direction: ltr;
        text-align: left;
      }
      [data-testid="stMetric"] {
        direction: ltr;
        text-align: left;
        background: #ffffff;
        border: 1px solid #e6ecef;
        border-radius: 14px;
        padding: 14px 16px;
      }
      [data-testid="stSidebar"] {
        border-right: 1px solid #e6ecef;
      }
      .hero {
        border-radius: 18px;
        padding: 24px 28px;
        margin: 0 0 18px 0;
        color: #f6fbfa;
        background: linear-gradient(115deg, #123a4a 0%, #17645f 58%, #278477 100%);
      }
      .hero h1 { color: #ffffff; margin: 0 0 6px 0; font-size: 2rem; }
      .hero p { color: #d9eeeb; margin: 0; font-size: 1rem; }
      .eyebrow {
        color: #a9ddd5;
        font-size: .8rem;
        font-weight: 700;
        letter-spacing: .05em;
        margin-bottom: 8px;
      }
      .evidence-card {
        background: #ffffff;
        border: 1px solid #e6ecef;
        border-left: 4px solid #1f7a70;
        border-radius: 12px;
        padding: 16px 18px;
        margin: 8px 0 16px 0;
        line-height: 1.8;
      }
      .small-note { color: #647582; font-size: .88rem; }
      div[data-testid="stDataFrame"] { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_data() -> tuple[pd.DataFrame, ...]:
    required = [
        PROCESSED / "product_actions.csv",
        PROCESSED / "product_month.csv",
        PROCESSED / "product_location_month.csv",
        PROCESSED / "product_marketing_month.csv",
        PROCESSED / "product_production_month.csv",
        PROCESSED / "product_production_bottlenecks_month.csv",
        PROCESSED / "product_printing_month.csv",
        PROCESSED / "operations_downtime_month.csv",
    ]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Analysis files are missing: " + ", ".join(missing)
            + ". Run the feature builder and decision rules as described in README.md."
        )
    frames = [
        pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
        for path in required
    ]
    return tuple(frames)


def numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    for column in columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def format_egp(value: object, decimals: int = 0) -> str:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return "—"
    return f"EGP {number:,.{decimals}f}"


def format_percent(value: object) -> str:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return "—"
    return f"{number:.1%}"


def label_signals(value: str) -> str:
    if not value or value == "none":
        return "No signal"
    return ", ".join(SIGNAL_LABELS.get(code, code) for code in value.split(";") if code)


def style_figure(fig, height: int = 320):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=12, t=48, b=18),
        font=dict(family="Segoe UI, Tahoma, Arial, sans-serif", size=13, color="#243947"),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e9eef0", zerolinecolor="#dce5e8")
    return fig


try:
    (
        actions,
        product_month,
        product_location_month,
        marketing_month,
        production_month,
        production_bottlenecks,
        printing_month,
        downtime_month,
    ) = load_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

actions = numeric(
    actions,
    [
        "Sales_Rows_3M", "Sales_Units_On_Rows_3M", "Source_Net_Sales_EGP_3M",
        "Estimated_Gross_Profit_EGP_3M", "Estimated_Gross_Margin_3M",
        "Returned_Rows_3M", "Returned_Row_Rate_3M", "Inspected_Units_6M",
        "Rejected_Units_6M", "Quality_Rejection_Rate_6M",
    ],
)
product_month = numeric(
    product_month,
    [
        "sales_row_count", "source_net_sales_egp", "estimated_gross_profit_egp",
        "refund_value_egp",
        "estimated_gross_margin_pct", "returned_sales_row_count",
        "returned_sales_row_rate", "quality_inspected_units", "quality_rejected_units",
        "quality_rejection_rate", "quality_estimated_loss_egp",
    ],
)
product_location_month = numeric(
    product_location_month,
    [
        "Closing_Stock", "Days_of_Cover", "Reorder_Point_Units",
        "Stockout_Days_In_Month", "inventory_flow_delta_units",
    ],
)
marketing_month = numeric(
    marketing_month,
    ["Campaign_Count", "Spend_EGP", "Impressions", "Clicks", "Landing_Page_Sessions",
     "Orders_Attributed", "Attributed_Revenue_EGP", "Attributed_ROAS", "Click_Through_Rate",
     "Session_Conversion_Rate"],
)
production_month = numeric(
    production_month,
    ["Completed_Order_Count", "Planned_Qty", "Produced_Qty", "Good_Qty", "Rejected_Qty",
     "Plan_Fulfillment_Rate", "Good_Unit_Yield", "Average_Reported_Efficiency_Pct",
     "Late_Order_Count", "Late_Order_Rate", "Average_Delay_Days", "Overtime_Hours",
     "Orders_With_Reported_Bottleneck", "Average_Order_Lead_Time_Days"],
)
production_bottlenecks = numeric(
    production_bottlenecks,
    ["Affected_Order_Count", "Associated_Delay_Days", "Associated_Overtime_Hours"],
)
printing_month = numeric(
    printing_month,
    ["Print_Batch_Count", "Planned_Qty", "Printed_Qty", "Good_Qty", "Rejected_Qty",
     "Reprint_Qty", "Print_Good_Yield", "Reported_Consumable_Cost_EGP",
     "Reported_Rework_Cost_EGP", "Leading_Defect_Rejected_Units"],
)
downtime_month = numeric(
    downtime_month,
    ["Downtime_Event_Count", "Planned_Event_Count", "Unplanned_Event_Count", "Downtime_Hours",
     "Planned_Downtime_Hours", "Unplanned_Downtime_Hours", "Leading_Reason_Hours"],
)

months = sorted(product_month["Month_Key"].unique())
latest_sales_month = months[-1] if months else "Unavailable"
latest_inventory_month = (
    sorted(product_location_month["Snapshot_Month"].unique())[-1]
    if not product_location_month.empty else "Unavailable"
)
selected_brand = "All"
selected_family = "All"
selected_priority = "All"
selected_report_window = "Latest 3 months"
query = ""

with st.sidebar:
    st.markdown("### Product Radar")
    page = st.radio(
        "Navigation",
        ["Priorities", "Product details", "Marketing & production", "Rule calibration", "Case review"],
        label_visibility="collapsed",
    )
    st.divider()

    if page not in {"Rule calibration", "Case review"}:
        brands = ["All"] + sorted(actions["Brand"].dropna().unique().tolist()) if "Brand" in actions else ["All"]
        families = ["All"] + sorted(actions["Product_Family"].dropna().unique().tolist()) if "Product_Family" in actions else ["All"]
        selected_brand = st.selectbox("Brand", brands)
        family_options = {FAMILY_LABELS.get(value, value): value for value in families if value != "All"}
        selected_family_label = st.selectbox("Product family", ["All", *family_options])
        selected_family = family_options.get(selected_family_label, "All")
        priority_options = ["All"] + sorted(actions["Priority"].dropna().unique().tolist())
        selected_priority = st.selectbox("Review priority", priority_options)
        query = st.text_input("Search products", placeholder="Product name or ID")
        if page == "Priorities":
            report_windows = ["Latest month", "Latest 3 months", "Latest 6 months", "All available months"]
            selected_report_window = st.selectbox(
                "Sales context period",
                report_windows,
                index=1,
                help="Changes the sales context and metrics on this page. Suggested actions retain the rule periods shown in their evidence.",
            )
        st.divider()
        st.caption(f"Latest sales: {latest_sales_month}")
        st.caption(f"Latest inventory snapshot: {latest_inventory_month}")

filtered_actions = actions.copy()
if selected_brand != "All" and "Brand" in filtered_actions:
    filtered_actions = filtered_actions[filtered_actions["Brand"] == selected_brand]
if selected_family != "All" and "Product_Family" in filtered_actions:
    filtered_actions = filtered_actions[filtered_actions["Product_Family"] == selected_family]
if selected_priority != "All":
    filtered_actions = filtered_actions[filtered_actions["Priority"] == selected_priority]
if query.strip():
    q = query.strip().casefold()
    match = (
        filtered_actions["Product_ID"].astype(str).str.casefold().str.contains(q, regex=False, na=False)
        | filtered_actions["Product_Name"].astype(str).str.casefold().str.contains(q, regex=False, na=False)
        | filtered_actions["SKU"].astype(str).str.casefold().str.contains(q, regex=False, na=False)
    )
    filtered_actions = filtered_actions[match]

if page not in {"Rule calibration", "Case review"}:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Decision support · Explainable signals</div>
          <h1>Product Decision Radar</h1>
          <p>Start with the suggested action, then review the evidence and trends before deciding.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "Prototype based on training / modeled operating data. Sales through "
        f"{latest_sales_month}; inventory is a monthly snapshot through {latest_inventory_month}. "
        "Balances are not live, and thresholds remain subject to review."
    )
    st.caption(
        "Finished-goods inventory scope: Retail, Online, and Wholesale (LOC001–LOC003). "
        "Head Office and Production Hub are excluded. Source net sales and reported refunds are shown separately."
    )


def overview() -> None:
    st.subheader("Priority actions")
    st.caption(
        "Actions are ranked using provisional rules. Conflicting signals remain visible; "
        "historical inventory must be verified before replenishment or transfer. The sales context period below does not change rule windows or the latest inventory snapshot."
    )

    view = filtered_actions.copy()
    window_sizes = {
        "Latest month": 1,
        "Latest 3 months": 3,
        "Latest 6 months": 6,
    }
    report_months = months[-window_sizes[selected_report_window]:] if selected_report_window in window_sizes else months
    report_sales = product_month[product_month["Month_Key"].isin(report_months)]
    period_by_product = (
        report_sales.groupby("Product_ID", as_index=False)
        .agg(
            Period_Sales_EGP=("source_net_sales_egp", "sum"),
            Period_Gross_Profit_EGP=("estimated_gross_profit_egp", "sum"),
            Period_Sales_Rows=("sales_row_count", "sum"),
        )
    )
    period_by_product["Period_Estimated_Margin"] = period_by_product[
        "Period_Gross_Profit_EGP"
    ].div(
        period_by_product["Period_Sales_EGP"].where(
            period_by_product["Period_Sales_EGP"] != 0
        )
    )
    view = view.merge(period_by_product, on="Product_ID", how="left")
    view[["Period_Sales_EGP", "Period_Gross_Profit_EGP", "Period_Sales_Rows"]] = view[
        ["Period_Sales_EGP", "Period_Gross_Profit_EGP", "Period_Sales_Rows"]
    ].fillna(0)

    review_count = int((view["Primary_Action"] != "Monitor - No action currently").sum())
    availability_count = int(view["Signals"].str.contains("historical_availability_risk", regex=False).sum())
    mismatch_count = int(view["Signals"].str.contains("inventory_flow_mismatch", regex=False).sum())
    quality_count = int(view["Signals"].str.contains("elevated_quality_rejection_rate", regex=False).sum())
    period_sales_total = float(report_sales["source_net_sales_egp"].sum())
    period_profit_total = float(report_sales["estimated_gross_profit_egp"].sum())
    period_margin = period_profit_total / period_sales_total if period_sales_total else None
    st.caption(
        f"Sales context: {report_months[0]} to {report_months[-1]} · "
        f"{int(report_sales['sales_row_count'].sum()):,} sales rows"
        if report_months else "No sales months are available."
    )
    with st.container(horizontal=True):
        st.metric("Products in view", f"{len(view):,}", border=True)
        st.metric("Need review", f"{review_count:,}", border=True)
        st.metric("Historical availability signals", f"{availability_count:,}", border=True)
        st.metric(
            "Elevated quality signals",
            f"{quality_count:,}",
            help=f"{mismatch_count} products also have inventory-balance discrepancies",
            border=True,
        )
        st.metric("Source net sales · selected period", format_egp(period_sales_total), border=True)
        st.metric("Weighted estimated margin · selected period", format_percent(period_margin), border=True)

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("#### Action list")
        display = view.copy()
        display["Signals"] = display["Signals"].map(label_signals)
        display["Period_Sales_EGP"] = display["Period_Sales_EGP"].map(format_egp)
        display["Period_Estimated_Margin"] = display["Period_Estimated_Margin"].map(format_percent)
        display = display.rename(
            columns={
                "Product_Name": "Product",
                "Product_ID": "Product ID",
                "Primary_Action": "Suggested action",
                "Priority": "Priority",
                "Period_Sales_EGP": "Sales · selected period",
                "Period_Estimated_Margin": "Estimated margin · selected period",
            }
        )
        columns = [
            "Product", "Product ID", "Suggested action", "Priority",
            "Sales · selected period", "Estimated margin · selected period", "Signals",
        ]
        st.dataframe(
            display[columns],
            width="stretch",
            height=480,
            hide_index=True,
        )
        st.download_button(
            "Download filtered list (CSV)",
            data=view.to_csv(index=False).encode("utf-8-sig"),
            file_name="product_actions_filtered.csv",
            mime="text/csv",
        )

    with right:
        st.markdown("#### Suggested action distribution")
        counts = (
            view.groupby("Primary_Action", as_index=False)
            .size()
            .rename(columns={"size": "Product count"})
            .sort_values("Product count", ascending=True)
        )
        if not counts.empty:
            fig = px.bar(
                counts,
                x="Product count",
                y="Primary_Action",
                orientation="h",
                text="Product count",
                color="Product count",
                color_continuous_scale=["#acd9d2", "#17645f"],
                labels={"Primary_Action": "Action", "Product count": "Product count"},
            )
            fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Product count")
            st.plotly_chart(style_figure(fig, max(320, 52 * len(counts))), width="stretch")
        st.markdown(
            "<div class='small-note'>Select a product on the details page to review sales trends, "
            "inventory by location, returns, and quality.</div>",
            unsafe_allow_html=True,
        )


def product_detail() -> None:
    st.subheader("Product details and evidence")
    product_options = sorted(actions["Product_ID"].unique().tolist())
    name_by_id = actions.set_index("Product_ID")["Product_Name"].to_dict()
    selected_product = st.selectbox(
        "Select a product",
        product_options,
        format_func=lambda value: f"{value} · {name_by_id.get(value, '')}",
    )
    action = actions.loc[actions["Product_ID"] == selected_product].iloc[0]
    product_inventory = product_location_month[
        (product_location_month["Product_ID"] == selected_product)
        & (product_location_month["Snapshot_Month"] == action["Inventory_Snapshot_Month"])
    ].copy()
    product_name = html.escape(str(action["Product_Name"]))
    sku = html.escape(str(action["SKU"]))
    st.markdown(f"### {product_name} <span class='small-note'>({selected_product} · {sku})</span>", unsafe_allow_html=True)
    evidence = html.escape(str(action["Evidence_English"]))
    action_name = html.escape(str(action["Primary_Action"]))
    st.markdown(
        f"<div class='evidence-card'><strong>Primary action: {action_name}</strong><br>"
        f"{evidence}<br><span class='small-note'>"
        f"Sales period: {html.escape(str(action['Sales_Period']))} · "
        f"Inventory snapshot: {html.escape(str(action['Inventory_Snapshot_Month']))} · "
        f"Quality period: {html.escape(str(action['Quality_Period']))}</span></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Evidence coverage: {int(float(action['Sales_Rows_3M'])):,} sales rows across 3 months · "
        f"{int(float(action['Inspected_Units_6M'])):,} units inspected across 6 months · "
        f"{len(product_inventory)} inventory location records in {action['Inventory_Snapshot_Month']}"
    )

    cols = st.columns(5)
    cols[0].metric(
        "Source net sales · 3 months",
        format_egp(action["Source_Net_Sales_EGP_3M"]),
        help="Source-provided after-discount sales. Reported refunds are not subtracted again.",
    )
    cols[1].metric("Reported refunds · 3 months", format_egp(action["Reported_Refund_Value_EGP_3M"]))
    cols[2].metric("Estimated gross profit · 3 months", format_egp(action["Estimated_Gross_Profit_EGP_3M"]))
    cols[3].metric("Weighted estimated margin", format_percent(action["Estimated_Gross_Margin_3M"]))
    cols[4].metric("Returned-row rate", format_percent(action["Returned_Row_Rate_3M"]))
    return_reasons_raw = str(action["Leading_Return_Reasons_3M"]).strip()
    return_reasons = ", ".join(
        f"{RETURN_REASON_LABELS.get(reason.rsplit(' (', 1)[0], reason.rsplit(' (', 1)[0])} ({reason.rsplit(' (', 1)[1]}"
        if " (" in reason else RETURN_REASON_LABELS.get(reason, reason)
        for reason in return_reasons_raw.split("; ") if reason
    ) or "No returns recorded in this period"
    st.caption(
        f"Leading return reasons in the last 3 months: {return_reasons} · "
        f"Rows tagged as quality-related: {int(float(action['Quality_Related_Return_Rows_3M']))}"
    )

    trend_months = st.select_slider(
        "Monthly trend window",
        options=[3, 6, 12, 24, 36],
        value=12,
        format_func=lambda value: f"Last {value} months",
    )
    product_history = product_month[product_month["Product_ID"] == selected_product].sort_values("Month_Key").tail(trend_months)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Net sales")
        fig = px.line(
            product_history,
            x="Month_Key",
            y="source_net_sales_egp",
            markers=True,
            labels={"Month_Key": "Month", "source_net_sales_egp": "EGP"},
        )
        fig.update_traces(line_color="#17645f", hovertemplate="%{x}<br>EGP %{y:,.0f}<extra></extra>")
        fig.update_layout(xaxis_title="Month", yaxis_title="EGP")
        st.plotly_chart(style_figure(fig), width="stretch")
    with c2:
        st.markdown("#### Estimated gross profit")
        fig = px.bar(
            product_history,
            x="Month_Key",
            y="estimated_gross_profit_egp",
            labels={"Month_Key": "Month", "estimated_gross_profit_egp": "EGP"},
            color="estimated_gross_profit_egp",
            color_continuous_scale=["#c95f56", "#d9e9e6", "#17645f"],
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Month", yaxis_title="EGP")
        st.plotly_chart(style_figure(fig), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Margin and returns")
        margin_history = product_history[product_history["estimated_gross_margin_pct"].notna()]
        fig = px.line(
            margin_history,
            x="Month_Key",
            y="estimated_gross_margin_pct",
            markers=True,
            labels={"Month_Key": "Month", "estimated_gross_margin_pct": "Margin"},
        )
        fig.update_traces(line_color="#b27025", hovertemplate="%{x}<br>%{y:.1%}<extra></extra>")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_figure(fig), width="stretch")
    with c4:
        st.markdown("#### Quality rejection rate")
        quality_history = product_history[product_history["quality_rejection_rate"].notna()]
        if not quality_history.empty:
            fig = px.line(
                quality_history,
                x="Month_Key",
                y="quality_rejection_rate",
                markers=True,
                labels={"Month_Key": "Month", "quality_rejection_rate": "Rejection rate"},
            )
            fig.update_traces(line_color="#8a587d", hovertemplate="%{x}<br>%{y:.1%}<extra></extra>")
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(style_figure(fig), width="stretch")
        else:
            st.info("No quality inspection records for this product in the selected trend window.")

    st.markdown("#### Inventory by location")
    inventory_history = product_inventory
    if inventory_history.empty:
        st.info("No inventory snapshot is available for this product.")
    else:
        inventory_history["Location_Name_Display"] = inventory_history["Location_Name"].map(
            lambda value: LOCATION_LABELS.get(value, value)
        )
        stock_chart = px.bar(
            inventory_history,
            x="Location_ID",
            y="Closing_Stock",
            color="Location_ID",
            text="Closing_Stock",
            labels={"Location_ID": "Location", "Closing_Stock": "Closing stock"},
            hover_data=["Location_Name_Display", "Days_of_Cover", "Stockout_Days_In_Month"],
        )
        stock_chart.update_layout(showlegend=False, xaxis_title="Location", yaxis_title="Units")
        st.plotly_chart(style_figure(stock_chart, 300), width="stretch")
        inventory_display = inventory_history[
            [
                "Location_ID", "Location_Name", "Closing_Stock", "Days_of_Cover",
                "Reorder_Point_Units", "Stockout_Days_In_Month",
                "inventory_flow_delta_units", "inventory_flow_balance_ok",
            ]
        ].rename(
            columns={
                "Location_ID": "Location ID",
                "Location_Name": "Location",
                "Closing_Stock": "Closing stock",
                "Days_of_Cover": "Source days of cover",
                "Reorder_Point_Units": "Reorder point",
                "Stockout_Days_In_Month": "Stockout days this month",
                "inventory_flow_delta_units": "Movement balance difference",
                "inventory_flow_balance_ok": "Movements balanced?",
            }
        )
        inventory_display["Location"] = inventory_display["Location"].map(
            lambda value: LOCATION_LABELS.get(value, value)
        )
        inventory_display["Movements balanced?"] = inventory_display["Movements balanced?"].map(
            {True: "Yes", False: "No", "True": "Yes", "False": "No"}
        ).fillna("Unavailable")
        st.dataframe(inventory_display, width="stretch", hide_index=True)

    quality_summary_cols = st.columns(3)
    quality_summary_cols[0].metric("Units inspected · 6 months", f"{int(float(action['Inspected_Units_6M'])):,}")
    quality_summary_cols[1].metric("Units rejected · 6 months", f"{int(float(action['Rejected_Units_6M'])):,}")
    quality_summary_cols[2].metric("Estimated quality loss", format_egp(action["Estimated_Quality_Loss_EGP_6M"]))

    st.caption(
        f"Leading cause: {QUALITY_CAUSE_LABELS.get(action['Leading_Root_Cause_6M'], action['Leading_Root_Cause_6M']) or 'Unavailable'} "
        f"({action['Leading_Root_Cause_Rejected_Units_6M']} units) · leading stage: "
        f"{QUALITY_STAGE_LABELS.get(action['Leading_Stage_6M'], action['Leading_Stage_6M']) or 'Unavailable'} ({action['Leading_Stage_Rejected_Units_6M']} units) · "
        f"Rejected units with unexplained classification: {action['Unexplained_Rejected_Units_6M']}"
    )
    st.caption(
        "Net sales, profit, cost of goods, and quality loss are estimates or source fields. "
        "Quality and returns are compared by product and period only; inspections are not linked to individual returns."
    )


def marketing_production() -> None:
    st.subheader("Marketing & production")
    month_columns = [
        marketing_month["Campaign_Start_Month"],
        production_month["Completion_Month"],
        printing_month["Print_Month"],
        downtime_month["Downtime_Month"],
    ]
    available_months = sorted({month for column in month_columns for month in column if month != "Unknown"})
    if not available_months:
        st.info("No marketing or production period data is available.")
        return

    filter_cols = st.columns([1.6, 1])
    product_options = ["All products", *sorted(actions["Product_ID"].unique().tolist())]
    product_names = actions.set_index("Product_ID")["Product_Name"].to_dict()
    selected_scope = filter_cols[0].selectbox(
        "Product scope",
        product_options,
        format_func=lambda value: (
            "All products" if value == "All products"
            else f"{value} · {product_names.get(value, '')}"
        ),
        key="marketing_production_product_scope",
    )
    month_window = filter_cols[1].select_slider(
        "Reporting window",
        options=[3, 6, 12, 24, 36],
        value=12,
        format_func=lambda value: f"Last {value} months",
        key="marketing_production_month_window",
    )
    window_months = set(available_months[-month_window:])
    first_month, last_month = min(window_months), max(window_months)

    def select_scope(frame: pd.DataFrame, month_field: str) -> pd.DataFrame:
        selected = frame[frame[month_field].isin(window_months)].copy()
        if selected_scope != "All products" and "Product_ID" in selected:
            selected = selected[selected["Product_ID"] == selected_scope]
        return selected

    marketing_view = select_scope(marketing_month, "Campaign_Start_Month")
    production_view = select_scope(production_month, "Completion_Month")
    bottleneck_view = select_scope(production_bottlenecks, "Completion_Month")
    printing_view = select_scope(printing_month, "Print_Month")
    downtime_view = downtime_month[downtime_month["Downtime_Month"].isin(window_months)].copy()
    st.caption(
        f"Reporting window: {first_month} to {last_month}. Select a product or review the full portfolio."
    )

    marketing_tab, production_tab, printing_tab = st.tabs(
        ["Marketing", "Production orders", "Printing & downtime"]
    )

    with marketing_tab:
        st.markdown("#### Campaign performance")
        st.caption(
            "Campaigns are grouped by start month, while attributed outcomes may span the full campaign. "
            "Attributed revenue and ROAS are directional source metrics, not incremental sales or profit."
        )
        if marketing_view.empty:
            st.info("No campaign records are available for this selection and period.")
        else:
            spend = marketing_view["Spend_EGP"].sum()
            attributed_revenue = marketing_view["Attributed_Revenue_EGP"].sum()
            attributed_orders = marketing_view["Orders_Attributed"].sum()
            impressions = marketing_view["Impressions"].sum()
            sessions = marketing_view["Landing_Page_Sessions"].sum()
            with st.container(horizontal=True):
                st.metric("Campaigns", f"{int(marketing_view['Campaign_Count'].sum()):,}", border=True)
                st.metric("Reported spend", format_egp(spend), border=True)
                st.metric("Attributed revenue", format_egp(attributed_revenue), border=True)
                st.metric(
                    "Attributed ROAS",
                    f"{attributed_revenue / spend:.2f}x" if spend else "—",
                    help="Attributed revenue divided by reported campaign spend. It is not profit or causal lift.",
                    border=True,
                )
                st.metric("Attributed orders", f"{int(attributed_orders):,}", border=True)

            channel_summary = (
                marketing_view.groupby("Platform", as_index=False)
                .agg(
                    Campaigns=("Campaign_Count", "sum"),
                    Spend_EGP=("Spend_EGP", "sum"),
                    Attributed_Revenue_EGP=("Attributed_Revenue_EGP", "sum"),
                    Attributed_Orders=("Orders_Attributed", "sum"),
                    Impressions=("Impressions", "sum"),
                    Clicks=("Clicks", "sum"),
                    Landing_Page_Sessions=("Landing_Page_Sessions", "sum"),
                )
            )
            channel_summary["Attributed ROAS"] = channel_summary.apply(
                lambda row: row["Attributed_Revenue_EGP"] / row["Spend_EGP"]
                if row["Spend_EGP"] else pd.NA,
                axis=1,
            )
            channel_summary["Click-through rate"] = channel_summary.apply(
                lambda row: row["Clicks"] / row["Impressions"] if row["Impressions"] else pd.NA,
                axis=1,
            )
            channel_summary["Session conversion rate"] = channel_summary.apply(
                lambda row: row["Attributed_Orders"] / row["Landing_Page_Sessions"]
                if row["Landing_Page_Sessions"] else pd.NA,
                axis=1,
            )
            st.markdown("##### Platform comparison")
            st.dataframe(
                channel_summary.rename(columns={
                    "Spend_EGP": "Spend (EGP)",
                    "Attributed_Revenue_EGP": "Attributed revenue (EGP)",
                    "Attributed_Orders": "Attributed orders",
                }),
                hide_index=True,
                alt="Campaign performance totals and response rates by platform",
            )

            monthly_campaigns = (
                marketing_view.groupby(["Campaign_Start_Month", "Platform"], as_index=False)
                .agg(Spend_EGP=("Spend_EGP", "sum"), Attributed_Revenue_EGP=("Attributed_Revenue_EGP", "sum"))
            )
            spend_col, revenue_col = st.columns(2)
            with spend_col:
                spend_chart = px.line(
                    monthly_campaigns,
                    x="Campaign_Start_Month",
                    y="Spend_EGP",
                    color="Platform",
                    markers=True,
                    labels={"Campaign_Start_Month": "Campaign start month", "Spend_EGP": "Spend (EGP)"},
                )
                st.plotly_chart(
                    style_figure(spend_chart),
                    width="stretch",
                    alt="Reported campaign spend by start month and platform",
                )
            with revenue_col:
                revenue_chart = px.line(
                    monthly_campaigns,
                    x="Campaign_Start_Month",
                    y="Attributed_Revenue_EGP",
                    color="Platform",
                    markers=True,
                    labels={
                        "Campaign_Start_Month": "Campaign start month",
                        "Attributed_Revenue_EGP": "Attributed revenue (EGP)",
                    },
                )
                st.plotly_chart(
                    style_figure(revenue_chart),
                    width="stretch",
                    alt="Campaign-attributed revenue by start month and platform",
                )

            st.markdown("##### Highest attributed campaign groups")
            top_campaigns = marketing_view.sort_values("Attributed_Revenue_EGP", ascending=False).head(15)
            st.dataframe(
                top_campaigns[[
                    "Campaign_Start_Month", "Product_ID", "Product_Name", "Platform", "Campaign_Names",
                    "Campaign_Count", "Spend_EGP", "Attributed_Revenue_EGP", "Attributed_ROAS",
                ]].rename(columns={
                    "Campaign_Start_Month": "Start month",
                    "Product_ID": "Product ID",
                    "Product_Name": "Product",
                    "Campaign_Names": "Campaign name(s)",
                    "Campaign_Count": "Campaigns",
                    "Spend_EGP": "Spend (EGP)",
                    "Attributed_Revenue_EGP": "Attributed revenue (EGP)",
                    "Attributed_ROAS": "Attributed ROAS",
                }),
                hide_index=True,
                alt="Campaign groups ranked by their reported attributed revenue",
            )

    with production_tab:
        st.markdown("#### Completed production orders")
        st.caption("Orders are grouped by completion month. Reported bottlenecks and efficiency are operational fields, not audited capacity commitments.")
        if production_view.empty:
            st.info("No completed production orders are available for this selection and period.")
        else:
            planned = production_view["Planned_Qty"].sum()
            produced = production_view["Produced_Qty"].sum()
            good = production_view["Good_Qty"].sum()
            order_count = production_view["Completed_Order_Count"].sum()
            late_orders = production_view["Late_Order_Count"].sum()
            with st.container(horizontal=True):
                st.metric("Completed orders", f"{int(order_count):,}", border=True)
                st.metric("Good units", f"{int(good):,}", border=True)
                st.metric("Plan fulfillment", format_percent(produced / planned if planned else None), border=True)
                st.metric("Good-unit yield", format_percent(good / produced if produced else None), border=True)
                st.metric("Late orders", f"{int(late_orders):,} ({late_orders / order_count:.1%})" if order_count else "—", border=True)

            production_trend = (
                production_view.groupby("Completion_Month", as_index=False)
                .agg(Produced_Qty=("Produced_Qty", "sum"), Good_Qty=("Good_Qty", "sum"))
            )
            production_chart_data = production_trend.melt(
                id_vars="Completion_Month", var_name="Measure", value_name="Units"
            )
            production_chart_data["Measure"] = production_chart_data["Measure"].map({
                "Produced_Qty": "Produced units",
                "Good_Qty": "Good units",
            })
            production_chart = px.line(
                production_chart_data,
                x="Completion_Month",
                y="Units",
                color="Measure",
                markers=True,
                labels={"Completion_Month": "Completion month"},
            )
            st.plotly_chart(
                style_figure(production_chart),
                width="stretch",
                alt="Produced and good units by production completion month",
            )

            bottleneck_summary = (
                bottleneck_view.groupby("Bottleneck_Area", as_index=False)
                .agg(
                    Affected_Orders=("Affected_Order_Count", "sum"),
                    Associated_Delay_Days=("Associated_Delay_Days", "sum"),
                    Associated_Overtime_Hours=("Associated_Overtime_Hours", "sum"),
                )
                .sort_values("Affected_Orders", ascending=False)
            )
            if not bottleneck_summary.empty:
                st.markdown("##### Reported production bottlenecks")
                st.dataframe(
                    bottleneck_summary,
                    hide_index=True,
                    alt="Reported bottleneck order counts, delay, and overtime by production area",
                )
            st.markdown("##### Monthly production evidence")
            production_display = production_view.sort_values("Completion_Month", ascending=False).rename(columns={
                "Completion_Month": "Completion month",
                "Product_ID": "Product ID",
                "Product_Name": "Product",
                "Completed_Order_Count": "Completed orders",
                "Planned_Qty": "Planned units",
                "Produced_Qty": "Produced units",
                "Good_Qty": "Good units",
                "Rejected_Qty": "Rejected units",
                "Plan_Fulfillment_Rate": "Plan fulfillment",
                "Good_Unit_Yield": "Good-unit yield",
                "Average_Reported_Efficiency_Pct": "Average reported efficiency (%)",
                "Late_Order_Count": "Late orders",
                "Late_Order_Rate": "Late-order rate",
                "Average_Delay_Days": "Average delay (days)",
                "Overtime_Hours": "Overtime hours",
                "Leading_Bottleneck": "Leading reported bottleneck",
                "Average_Order_Lead_Time_Days": "Average order lead time (days)",
            })
            production_columns = [
                "Completion month", "Product ID", "Product", "Completed orders", "Planned units",
                "Produced units", "Good units", "Rejected units", "Plan fulfillment", "Good-unit yield",
                "Average reported efficiency (%)", "Late orders", "Late-order rate", "Average delay (days)",
                "Overtime hours", "Leading reported bottleneck", "Average order lead time (days)",
            ]
            st.dataframe(
                production_display[production_columns],
                hide_index=True,
                alt="Monthly product-level production outcomes and delay indicators",
            )

    with printing_tab:
        st.markdown("#### Printing batches")
        st.caption("Printing batches are grouped by print month and product; recorded consumable and rework costs are source fields.")
        if printing_view.empty:
            st.info("No printing batches are available for this selection and period.")
        else:
            printed = printing_view["Printed_Qty"].sum()
            good_printed = printing_view["Good_Qty"].sum()
            with st.container(horizontal=True):
                st.metric("Print batches", f"{int(printing_view['Print_Batch_Count'].sum()):,}", border=True)
                st.metric("Printed units", f"{int(printed):,}", border=True)
                st.metric("Print good-unit yield", format_percent(good_printed / printed if printed else None), border=True)
                st.metric("Reprint units", f"{int(printing_view['Reprint_Qty'].sum()):,}", border=True)
            print_trend = (
                printing_view.groupby("Print_Month", as_index=False)
                .agg(Printed_Qty=("Printed_Qty", "sum"), Good_Qty=("Good_Qty", "sum"))
            )
            print_chart_data = print_trend.melt(
                id_vars="Print_Month", var_name="Measure", value_name="Units"
            )
            print_chart_data["Measure"] = print_chart_data["Measure"].map({
                "Printed_Qty": "Printed units",
                "Good_Qty": "Good units",
            })
            print_chart = px.line(
                print_chart_data,
                x="Print_Month",
                y="Units",
                color="Measure",
                markers=True,
                labels={"Print_Month": "Print month"},
            )
            st.plotly_chart(
                style_figure(print_chart),
                width="stretch",
                alt="Printed and good units by print month",
            )
            st.dataframe(
                printing_view.sort_values("Print_Month", ascending=False).rename(columns={
                    "Print_Month": "Print month",
                    "Product_ID": "Product ID",
                    "Product_Name": "Product",
                    "Print_Batch_Count": "Batches",
                    "Planned_Qty": "Planned units",
                    "Printed_Qty": "Printed units",
                    "Good_Qty": "Good units",
                    "Rejected_Qty": "Rejected units",
                    "Reprint_Qty": "Reprint units",
                    "Print_Good_Yield": "Good-unit yield",
                    "Reported_Consumable_Cost_EGP": "Consumable cost (EGP)",
                    "Reported_Rework_Cost_EGP": "Rework cost (EGP)",
                    "Leading_Reported_Defect": "Leading reported defect",
                })[[
                    "Print month", "Product ID", "Product", "Batches", "Planned units", "Printed units",
                    "Good units", "Rejected units", "Reprint units", "Good-unit yield",
                    "Consumable cost (EGP)", "Rework cost (EGP)", "Leading reported defect",
                ]],
                hide_index=True,
                alt="Monthly product-level printing output, quality, reprints, and reported costs",
            )

        st.markdown("#### Factory downtime by area")
        st.caption("Downtime is plant/area-level context. The source has no Product ID, so it is not attributed to the selected product.")
        if downtime_view.empty:
            st.info("No downtime records are available in this period.")
        else:
            downtime_hours = downtime_view["Downtime_Hours"].sum()
            unplanned_hours = downtime_view["Unplanned_Downtime_Hours"].sum()
            with st.container(horizontal=True):
                st.metric("Downtime hours", f"{downtime_hours:,.1f}", border=True)
                st.metric("Unplanned downtime hours", f"{unplanned_hours:,.1f}", border=True)
                st.metric("Downtime events", f"{int(downtime_view['Downtime_Event_Count'].sum()):,}", border=True)
            downtime_trend = (
                downtime_view.groupby(["Downtime_Month", "Business_Area"], as_index=False)
                .agg(Unplanned_Downtime_Hours=("Unplanned_Downtime_Hours", "sum"))
            )
            downtime_chart = px.line(
                downtime_trend,
                x="Downtime_Month",
                y="Unplanned_Downtime_Hours",
                color="Business_Area",
                markers=True,
                labels={"Downtime_Month": "Month", "Unplanned_Downtime_Hours": "Unplanned downtime (hours)"},
            )
            st.plotly_chart(
                style_figure(downtime_chart),
                width="stretch",
                alt="Unplanned factory downtime by production area and month",
            )


def rule_calibration() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">GOVERNANCE REVIEW</div>
          <h1>Rule calibration</h1>
          <p>Current decision thresholds, portfolio sensitivity, and the proposed interim position.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Quantitative desk review complete. Thresholds are still provisional and require business-owner approval. "
        "No rule changes have been applied."
    )
    st.markdown("### Portfolio sensitivity")
    calibration = pd.DataFrame(
        [
            {"Rule": "Low estimated margin", "Current threshold": "Below 5%", "Products flagged under alternatives": "0%: 1 · 3%: 2 · 5%: 3 · 8%: 6 · 10%: 12", "Proposed position": "Keep 5% as an early review guard."},
            {"Rule": "Elevated returns", "Current threshold": ">2× portfolio rate; minimum 50 sales rows", "Products flagged under alternatives": "1.5×: 2 · 2×: 1 · 2.5×: 0 · 3×: 0", "Proposed position": "Keep 2× and the 50-row minimum."},
            {"Rule": "Quality rejection", "Current threshold": ">1.25× portfolio rate; minimum 500 inspected units", "Products flagged under alternatives": "1×: 28–29 · 1.25×: 3 · 1.5×: 0 · 2×: 0", "Proposed position": "Keep 1.25× and the 500-unit minimum."},
            {"Rule": "Possible excess stock", "Current threshold": ">120 cover days and stock ≥3× local 3-month sales", "Products flagged under alternatives": "Stock multiple 2×: 20 · 3×: 17 · 4×: 15", "Proposed position": "Keep 120 days and 3×; >365 days remains a verification warning."},
            {"Rule": "Historical availability risk", "Current threshold": "Stockout days >0, or low stock with cover ≤14 days", "Products flagged under alternatives": "7 days: 25 · 14 days: 31 · 21 days: 34", "Proposed position": "Keep 14 days provisionally; label the signal historical."},
        ]
    )
    st.dataframe(
        calibration,
        hide_index=True,
        width="stretch",
        alt="Current decision thresholds, sensitivity counts, and proposed interim positions",
    )
    with st.container(border=True):
        st.markdown("### What the current data says")
        st.markdown(
            "- Review covers **59 products** in the project’s modeled/anonymized data. It measures threshold sensitivity, not business outcome accuracy.\n"
            "- Portfolio baselines: **5.02% returned sales rows** and **2.40% quality rejection rate**.\n"
            "- The current return signal is P030: **233 sales rows**, with a **10.73%** returned-row rate.\n"
            "- The current quality signals are P015, P035, and P052. Lowering the threshold to the portfolio baseline would flag 28–29 products.\n"
            "- Signals are review prompts. They do not authorize purchasing, transfers, markdowns, or promotions."
        )
    st.markdown("### Approval status")
    st.warning(
        "Pending business-owner review: confirm the interim thresholds or record a requested change. "
        "Until that review is recorded, the application continues to use the existing provisional rules."
    )
    st.markdown(
        "Approval form to complete: `docs/THRESHOLD_APPROVAL_LOG.md`. "
        "Detailed methodology and recommendation: `docs/RULE_CALIBRATION_REVIEW.md`."
    )


def case_review() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">STAKEHOLDER REVIEW</div>
          <h1>Case review</h1>
          <p>Walk through six representative product cases and record whether each suggested action fits the business.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "These are modeled/anonymized records. Inventory evidence refers to the September 2026 snapshot, not live stock. "
        "Record stakeholder outcomes in `docs/CASE_REVIEW_LOG.md`."
    )
    case_ids = ["P002", "P048", "P023", "P013", "P030", "P052"]
    cases = actions[actions["Product_ID"].astype(str).isin(case_ids)].set_index("Product_ID")
    for product_id in case_ids:
        if product_id not in cases.index:
            st.warning(f"{product_id} is not present in the current product action file.")
            continue
        row = cases.loc[product_id]
        with st.expander(f"{product_id} · {row['Product_Name']} — {row['Primary_Action']}", expanded=False):
            st.markdown(f"**Priority:** {row['Priority']}")
            st.markdown(f"**Signals:** {label_signals(str(row['Signals']))}")
            st.markdown(f"**Evidence:** {row['Evidence_English']}")
            if str(row.get("Location_Evidence", "")):
                st.markdown(f"**Location evidence:** {row['Location_Evidence']}")
            st.caption("Review outcome: pending stakeholder review")
    st.markdown("Record the outcome, requested changes, reviewer, and date in `docs/CASE_REVIEW_LOG.md`.")
    st.markdown("Detailed desk review: `docs/EXAMPLE_REVIEW.md`.")


if page == "Priorities":
    overview()
elif page == "Product details":
    product_detail()
elif page == "Rule calibration":
    rule_calibration()
elif page == "Case review":
    case_review()
else:
    marketing_production()
