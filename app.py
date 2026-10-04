from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"

st.set_page_config(
    page_title="E-Commerce Analytics | Lokesh Jangid",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top right, #19234a 0, #0b1020 38%, #080c18 100%); color:#edf2ff; }
.block-container { padding-top:1.4rem; padding-bottom:2rem; max-width:1450px; }
.hero { padding:1.35rem 1.6rem; border:1px solid rgba(255,255,255,.08); background:linear-gradient(135deg,rgba(23,33,58,.96),rgba(15,22,40,.96)); border-radius:22px; }
.hero h1 { margin:0; font-size:2rem; color:#fff; }
.hero p { color:#9ca9c8; margin:.35rem 0 0; }
.kpi { padding:1rem 1.1rem; border-radius:18px; background:linear-gradient(145deg,#152039,#10192d); border:1px solid rgba(255,255,255,.07); }
.kpi-label { color:#9ca9c8; font-size:.76rem; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { color:#fff; font-size:1.65rem; font-weight:800; margin-top:.2rem; }
[data-testid="stSidebar"] { background:#09101e; border-right:1px solid rgba(255,255,255,.06); }
</style>
""", unsafe_allow_html=True)

def load_data():
    sales_path = PROCESSED / "tableau_sales.csv"

    if sales_path.exists():
        sales = pd.read_csv(sales_path)
        orders_path = PROCESSED / "tableau_orders.csv"
        customer_orders_path = PROCESSED / "tableau_customer_orders.csv"

        orders = (
            pd.read_csv(orders_path)
            if orders_path.exists()
            else sales.drop_duplicates("order_id").copy()
        )
        customer_orders = (
            pd.read_csv(customer_orders_path)
            if customer_orders_path.exists()
            else orders.copy()
        )
        mode = "processed"
    else:
        orders = pd.read_csv(SAMPLE / "orders.csv")
        items = pd.read_csv(SAMPLE / "order_items.csv")
        customers = pd.read_csv(SAMPLE / "customers.csv")
        products = pd.read_csv(SAMPLE / "products.csv")

        orders = orders[orders["order_status"] != "canceled"]
        sales = (
            orders.merge(
                customers[
                    ["customer_id", "customer_unique_id",
                     "customer_state", "customer_city"]
                ],
                on="customer_id",
                how="left",
            )
            .merge(
                items[["order_id", "product_id", "seller_id",
                       "price", "freight_value"]],
                on="order_id",
                how="inner",
            )
            .merge(
                products[["product_id", "product_category_name"]],
                on="product_id",
                how="left",
            )
        )
        sales["category"] = sales["product_category_name"].fillna("Unknown")
        sales["sales"] = sales["price"] + sales["freight_value"]
        sales["order_date"] = pd.to_datetime(
            sales["order_purchase_timestamp"], errors="coerce"
        )
        sales["year_month"] = sales["order_date"].dt.to_period("M").astype(str)
        sales["primary_payment_type"] = "Unknown"

        orders = sales[
            ["order_id", "order_date", "customer_unique_id",
             "customer_state", "customer_city"]
        ].drop_duplicates()
        customer_orders = orders.copy()
        mode = "sample"

    for df in (sales, orders, customer_orders):
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    return sales, orders, customer_orders, mode

@st.cache_data
def get_data():
    return load_data()

sales, orders, customer_orders, mode = get_data()

sales["category"] = sales["category"].fillna("Unknown")
sales["sales"] = pd.to_numeric(sales["sales"], errors="coerce").fillna(0)

min_date = sales["order_date"].min().date()
max_date = sales["order_date"].max().date()

with st.sidebar:
    st.markdown("## 🎛️ Analytics Controls")
    date_range = st.date_input(
        "Order date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    states = sorted(sales["customer_state"].dropna().unique())
    selected_states = st.multiselect("Customer state", states, default=states)

    categories = sorted(sales["category"].dropna().unique())
    selected_categories = st.multiselect(
        "Category", categories, default=categories
    )

    st.markdown("---")
    st.caption(
        "Live mode: processed public dataset"
        if mode == "processed"
        else "Preview mode: bundled sample data"
    )

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

sales_mask = (
    (sales["order_date"].dt.date >= start_date)
    & (sales["order_date"].dt.date <= end_date)
)
if selected_states:
    sales_mask &= sales["customer_state"].isin(selected_states)
if selected_categories:
    sales_mask &= sales["category"].isin(selected_categories)

filtered = sales.loc[sales_mask].copy()
filtered_order_ids = filtered["order_id"].unique()

revenue = filtered["sales"].sum()
orders_count = len(filtered_order_ids)
aov = revenue / orders_count if orders_count else 0

co = customer_orders.copy()
customer_mask = (
    (co["order_date"].dt.date >= start_date)
    & (co["order_date"].dt.date <= end_date)
)
if selected_states:
    customer_mask &= co["customer_state"].isin(selected_states)
co = co.loc[customer_mask]

counts = co.groupby("customer_unique_id")["order_id"].nunique()
repeat_rate = counts.gt(1).mean() * 100 if len(counts) else 0

st.markdown("""
<div class="hero">
<h1>📊 E-Commerce Sales & Customer Analytics</h1>
<p>Python • SQL • Pandas • Tableau • Streamlit</p>
<p>Interactive analysis of revenue, customers, categories, geography and payments.</p>
</div>
""", unsafe_allow_html=True)

cards = st.columns(4)
values = [
    ("Revenue", f"₹{revenue:,.0f}"),
    ("Orders with Sales", f"{orders_count:,}"),
    ("Average Order Value", f"₹{aov:,.2f}"),
    ("Repeat Customer Rate", f"{repeat_rate:.2f}%"),
]
for col, (label, value) in zip(cards, values):
    col.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div></div>',
        unsafe_allow_html=True,
    )

tab1, tab2, tab3 = st.tabs(
    ["📈 Executive Dashboard", "🧠 Business Insights", "🔎 Data Quality"]
)

with tab1:
    c1, c2 = st.columns(2)

    filtered["year_month"] = (
        filtered["order_date"].dt.to_period("M").astype(str)
    )
    monthly = (
        filtered.groupby("year_month", as_index=False)["sales"]
        .sum()
        .rename(columns={"year_month": "month", "sales": "revenue"})
    )
    core = monthly[
        (monthly["month"] >= "2017-01")
        & (monthly["month"] <= "2018-08")
    ]

    fig = px.line(
        core, x="month", y="revenue", markers=True,
        title="Monthly Revenue Trend"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    c1.plotly_chart(fig, use_container_width=True)

    cat = (
        filtered.groupby("category", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
        .head(10)
    )
    fig2 = px.bar(
        cat, x="sales", y="category", orientation="h",
        title="Revenue by Product Category", text_auto=".2s"
    )
    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    c2.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    state = (
        filtered.groupby("customer_state", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
        .head(10)
    )
    fig3 = px.bar(
        state, x="customer_state", y="sales",
        title="Revenue by Customer State", text_auto=".2s"
    )
    fig3.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    c3.plotly_chart(fig3, use_container_width=True)

    if "primary_payment_type" in filtered.columns and not filtered.empty:
        payment = (
            filtered.groupby("primary_payment_type", as_index=False)["sales"]
            .sum()
            .sort_values("sales", ascending=False)
        )
        payment = payment[payment["primary_payment_type"].notna()]
        if mode == "processed":
            fig4 = px.pie(
                payment,
                names="primary_payment_type",
                values="sales",
                hole=.58,
                title="Sales by Primary Payment Method",
            )
            fig4.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            c4.plotly_chart(fig4, use_container_width=True)
        else:
            c4.info(
                "Payment detail is available in the full processed-data version."
            )

with tab2:
    top = (
        filtered.groupby("category", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
        .head(8)
    )
    st.dataframe(top, use_container_width=True, hide_index=True)

    if not top.empty and not filtered.empty:
        top_state = (
            filtered.groupby("customer_state")["sales"]
            .sum()
            .idxmax()
        )
        st.info(
            f"Top revenue category: **{top.iloc[0]['category']}**. "
            f"Top customer state by revenue: **{top_state}**."
        )

with tab3:
    st.write(
        "Data mode:",
        "**Full processed dataset**" if mode == "processed"
        else "**Sample preview**",
    )
    st.metric("Sales rows", f"{len(sales):,}")
    st.metric("Orders with sales-line data", f"{sales['order_id'].nunique():,}")
    st.metric(
        "Unique customers",
        f"{customer_orders['customer_unique_id'].nunique():,}",
    )
