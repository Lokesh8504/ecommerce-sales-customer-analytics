from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "analytics.db"

st.set_page_config(
    page_title="E-Commerce Analytics | Lokesh Jangid",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top right, #19234a 0, #0b1020 38%, #080c18 100%); color: #edf2ff; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1450px; }
.hero { padding: 1.4rem 1.6rem; border:1px solid rgba(255,255,255,.08); background: linear-gradient(135deg, rgba(23,33,58,.96), rgba(15,22,40,.96)); border-radius: 22px; box-shadow:0 14px 45px rgba(0,0,0,.22); }
.hero h1 { font-size: 2rem; margin:0; color:#fff; }
.hero p { color:#9ca9c8; margin:.45rem 0 0; }
.kpi { padding: 1rem 1.1rem; border-radius: 18px; background:linear-gradient(145deg,#152039,#10192d); border:1px solid rgba(255,255,255,.07); }
.kpi-label { color:#9ca9c8; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { color:#fff; font-size:1.65rem; font-weight:800; margin-top:.2rem; }
.section { margin-top: 1.4rem; margin-bottom:.7rem; font-size:1.2rem; font-weight:800; color:#fff; }
.small { color:#9ca9c8; font-size:.86rem; }
[data-testid="stSidebar"] { background: #09101e; border-right:1px solid rgba(255,255,255,.06); }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "analytics.db not found. Run: python src\\data_pipeline.py"
        )

    con = sqlite3.connect(DB_PATH)

    orders = pd.read_sql_query("SELECT * FROM orders", con)
    items = pd.read_sql_query("""
        SELECT
            oi.*,
            p.product_category_name,
            ct.product_category_name_english
        FROM order_items oi
        LEFT JOIN products p ON p.product_id = oi.product_id
        LEFT JOIN category_translation ct
          ON ct.product_category_name = p.product_category_name
    """, con)
    customers = pd.read_sql_query("SELECT * FROM customers", con)
    payments = pd.read_sql_query("SELECT * FROM payments", con)
    reviews = pd.read_sql_query("SELECT * FROM reviews", con)

    con.close()

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )

    items["category"] = (
        items["product_category_name_english"]
        .fillna(items["product_category_name"])
        .fillna("Unknown")
    )
    items["line_revenue"] = (
        items["price"].astype(float) +
        items["freight_value"].astype(float)
    )

    return orders, items, customers, payments, reviews


orders, items, customers, payments, reviews = load_data()

# Customer-level identity is important:
# customer_id identifies an order/customer record;
# customer_unique_id represents the underlying customer across orders.
customer_lookup = customers[
    ["customer_id", "customer_unique_id", "customer_state", "customer_city"]
].drop_duplicates("customer_id")

base = (
    orders
    .merge(customer_lookup, on="customer_id", how="left")
    .merge(
        items[
            [
                "order_id",
                "category",
                "price",
                "freight_value",
                "line_revenue",
                "seller_id",
            ]
        ],
        on="order_id",
        how="left",
    )
)
base["month"] = base["order_purchase_timestamp"].dt.to_period("M").astype(str)

with st.sidebar:
    st.markdown("## 🎛️ Analytics Controls")

    min_date = orders["order_purchase_timestamp"].min().date()
    max_date = orders["order_purchase_timestamp"].max().date()

    date_range = st.date_input(
        "Order date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    states = sorted(customers["customer_state"].dropna().unique())
    selected_states = st.multiselect(
        "Customer state",
        states,
        default=states,
    )

    categories = sorted(items["category"].dropna().unique())
    selected_categories = st.multiselect(
        "Category",
        categories,
        default=categories,
    )

    st.markdown("---")
    st.caption(
        "Dashboard calculations use non-canceled orders with available "
        "order-item revenue records."
    )

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    (base["order_purchase_timestamp"].dt.date >= start_date) &
    (base["order_purchase_timestamp"].dt.date <= end_date) &
    (base["order_status"] != "canceled")
)

if selected_states:
    mask &= base["customer_state"].isin(selected_states)

if selected_categories:
    mask &= base["category"].isin(selected_categories)

filtered = base.loc[mask].copy()

# Revenue-bearing order set.
sales_order_ids = filtered["order_id"].dropna().unique()

total_revenue = filtered["line_revenue"].sum()
sales_orders = len(sales_order_ids)
aov = total_revenue / sales_orders if sales_orders else 0

# Correct repeat-customer calculation using customer_unique_id.
active_customer_orders = (
    orders[
        (orders["order_status"] != "canceled") &
        (orders["order_purchase_timestamp"].dt.date >= start_date) &
        (orders["order_purchase_timestamp"].dt.date <= end_date)
    ]
    .merge(
        customer_lookup[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )
)

if selected_states:
    active_customer_orders = active_customer_orders.merge(
        customer_lookup[["customer_id", "customer_state"]],
        on=["customer_id", "customer_state"] if "customer_state" in active_customer_orders.columns else ["customer_id"],
        how="left",
    ) if False else active_customer_orders

# Apply the state filter using the customer lookup.
if selected_states:
    eligible_customer_ids = set(
        customer_lookup.loc[
            customer_lookup["customer_state"].isin(selected_states),
            "customer_id",
        ]
    )
    active_customer_orders = active_customer_orders[
        active_customer_orders["customer_id"].isin(eligible_customer_ids)
    ]

customer_order_counts = (
    active_customer_orders.groupby("customer_unique_id")["order_id"]
    .nunique()
)

customer_count = len(customer_order_counts)
repeat_customers = int((customer_order_counts > 1).sum())
repeat_rate = (
    repeat_customers / customer_count * 100 if customer_count else 0
)

review_orders = reviews[reviews["order_id"].isin(sales_order_ids)]
avg_review = review_orders["review_score"].mean() if not review_orders.empty else 0

st.markdown("""
<div class="hero">
  <h1>📊 E-Commerce Sales & Customer Analytics</h1>
  <p>Python • SQL • Pandas • Interactive Business Intelligence</p>
  <p>Analyze revenue, customers, categories, geography and payments through an end-to-end analytics workflow.</p>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
kpis = [
    ("Revenue", f"₹{total_revenue:,.0f}"),
    ("Orders with Sales", f"{sales_orders:,}"),
    ("Average Order Value", f"₹{aov:,.2f}"),
    ("Repeat Customer Rate", f"{repeat_rate:.2f}%"),
]
for col, (label, value) in zip(cols, kpis):
    col.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div></div>',
        unsafe_allow_html=True,
    )

st.caption(
    f"Dataset coverage: {orders['order_purchase_timestamp'].min().date()} "
    f"to {orders['order_purchase_timestamp'].max().date()}."
)

tab1, tab2, tab3 = st.tabs(
    ["📈 Executive Dashboard", "🧠 Business Insights", "🔎 Data Quality"]
)

with tab1:
    st.markdown('<div class="section">Sales performance</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    monthly = (
        filtered.groupby("month", as_index=False)
        .agg(
            revenue=("line_revenue", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values("month")
    )

    # Edge periods in this public dataset are sparse. Use the core period
    # for the main trend so tiny edge months do not distort the chart.
    core_monthly = monthly[
        (monthly["month"] >= "2017-01") &
        (monthly["month"] <= "2018-08")
    ].copy()

    fig = px.line(
        core_monthly,
        x="month",
        y="revenue",
        markers=True,
        title="Monthly Revenue — Core Analysis Period",
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    c1.plotly_chart(fig, use_container_width=True)
    c1.caption(
        "The dashboard excludes sparse edge periods from the main trend chart "
        "to avoid misleading MoM spikes."
    )

    cat = (
        filtered.groupby("category", as_index=False)["line_revenue"]
        .sum()
        .sort_values("line_revenue", ascending=False)
        .head(10)
    )
    fig2 = px.bar(
        cat,
        x="line_revenue",
        y="category",
        orientation="h",
        title="Top Categories by Revenue",
        text_auto=".2s",
    )
    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    c2.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    state = (
        filtered.groupby("customer_state", as_index=False)
        .agg(
            revenue=("line_revenue", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
        .head(10)
    )

    fig3 = px.bar(
        state,
        x="customer_state",
        y="revenue",
        title="Revenue by Customer State",
        text_auto=".2s",
    )
    fig3.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    c3.plotly_chart(fig3, use_container_width=True)

    # Payment mix by payment value is more meaningful than summing order
    # counts because one order may use multiple payment methods.
    pay = (
        payments[payments["order_id"].isin(sales_order_ids)]
        .groupby("payment_type", as_index=False)["payment_value"]
        .sum()
        .sort_values("payment_value", ascending=False)
    )

    fig4 = px.pie(
        pay,
        names="payment_type",
        values="payment_value",
        hole=.58,
        title="Payment Value Mix",
    )
    fig4.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    c4.plotly_chart(fig4, use_container_width=True)

with tab2:
    st.markdown(
        '<div class="section">Business questions & insights</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    q1.metric("Unique Cities", f"{customers['customer_city'].nunique():,}")

    orders_2017 = int(
        (orders["order_purchase_timestamp"].dt.year == 2017).sum()
    )
    q2.metric("Orders in 2017", f"{orders_2017:,}")
    q3.metric("Repeat Customers", f"{repeat_customers:,}")

    insight_df = (
        filtered.groupby("category", as_index=False)
        .agg(
            revenue=("line_revenue", "sum"),
            avg_price=("price", "mean"),
            orders=("order_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
        .head(8)
    )

    if not insight_df.empty:
        insight_df["revenue_share"] = (
            insight_df["revenue"] / insight_df["revenue"].sum() * 100
        )

    st.dataframe(
        insight_df.style.format(
            {
                "revenue": "₹{:,.0f}",
                "avg_price": "₹{:,.2f}",
                "revenue_share": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    top_cat = (
        insight_df.iloc[0]["category"]
        if not insight_df.empty
        else "the leading category"
    )
    top_state = (
        state.iloc[0]["customer_state"]
        if not state.empty
        else "the leading state"
    )

    st.info(
        f"In the selected slice, **{top_cat}** is the strongest revenue category "
        f"and **{top_state}** is the leading customer state. The repeat-customer "
        f"rate is **{repeat_rate:.2f}%**, calculated using customer-level identity "
        f"rather than order-level IDs."
    )

with tab3:
    st.markdown('<div class="section">Data quality checks</div>', unsafe_allow_html=True)

    checks = []
    for name, df in [
        ("orders", orders),
        ("order_items", items),
        ("customers", customers),
        ("payments", payments),
        ("reviews", reviews),
    ]:
        checks.append(
            {
                "table": name,
                "rows": len(df),
                "duplicate_rows": int(df.duplicated().sum()),
                "missing_cells": int(df.isna().sum().sum()),
            }
        )

    dq = pd.DataFrame(checks)
    st.dataframe(dq, use_container_width=True, hide_index=True)

    unavailable_orders = int(
        (
            (orders["order_status"] == "unavailable")
        ).sum()
    )

    st.caption(
        f"The source data contains {unavailable_orders:,} orders marked "
        "'unavailable'. Orders without item-level rows are not included "
        "in revenue calculations because there is no sales-line value to aggregate."
    )
