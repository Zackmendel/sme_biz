import os
import pandas as pd
import streamlit as st
from supabase import Client, create_client
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# Cache database hits so interactions don't spam Supabase
@st.cache_data(ttl=60)  # Caches data for 60 seconds
def get_sales_table(_supabase: Client, b_id: str):
    try:
        response = _supabase.table('sales').select('*').eq("business_id", b_id).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return []

@st.cache_data(ttl=60)
def get_product_list(_supabase: Client, b_id: str):
    try:
        response = _supabase.table("products").select("*").eq("business_id", b_id).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching product list: {e}")
        return []

@st.cache_data(ttl=60)
def get_purchases_table(_supabase: Client, b_id: str):
    try:
        response = _supabase.table("purchases").select("*").eq("business_id", b_id).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching purchases data: {e}")
        return []

def show_dashboard_metrics(supabase: Client, business_uuid: str):
    # Fetch raw data
    sales_data = get_sales_table(supabase, business_uuid)
    products_data = get_product_list(supabase, business_uuid)
    purchases_data = get_purchases_table(supabase, business_uuid)

    # Convert to DataFrames safely with column fallbacks if empty
    if sales_data:
        df_sales = pd.DataFrame(sales_data)
        df_sales["created_at"] = pd.to_datetime(df_sales["created_at"])
    else:
        df_sales = pd.DataFrame(columns=["id", "created_at", "total", "product_id", "customer_details", "discount", "item_name"])
        df_sales["created_at"] = pd.to_datetime(df_sales["created_at"])

    if purchases_data:
        df_purchases = pd.DataFrame(purchases_data)
        df_purchases["created_at"] = pd.to_datetime(df_purchases["created_at"])
    else:
        df_purchases = pd.DataFrame(columns=["id", "created_at", "total"])
        df_purchases["created_at"] = pd.to_datetime(df_purchases["created_at"])

    if products_data:
        df_products = pd.DataFrame(products_data)
    else:
        df_products = pd.DataFrame(columns=["id", "category"])

    # =================================================================
    # Metric Calculation
    # =================================================================
    if not df_sales.empty:
        total_sales = pd.to_numeric(df_sales["total"], errors="coerce").sum()
        transactions = df_sales["product_id"].count()
        customers = df_sales["customer_details"].nunique()
        total_discount = df_sales['discount'].sum()
        sales_by_item = df_sales['total'].groupby(df_sales['item_name']).sum()
        top_product = sales_by_item.idxmax() if not sales_by_item.empty else "N/A"
    else:
        total_sales = 0.0
        transactions = 0
        customers = 0
        total_discount = 0.0
        top_product = "N/A"

    if not df_purchases.empty:
        total_expenses = pd.to_numeric(df_purchases["total"], errors="coerce").sum()
    else:
        total_expenses = 0.0

    profit = total_sales - total_expenses
    profit_margin = (profit / total_sales * 100) if total_sales != 0 else 0.0

    # =================================================================
    # Dashboard UI
    # =================================================================
    st.title("Business Ledger Dashboard")

    col_1, col_2, col_3, col_4 = st.columns(4, border=True, gap="small")

    col_1.metric(label="Total Sales", value=f"₦{total_sales:,.2f}")
    col_2.metric(label="Total Expenses", value=f"₦{total_expenses:,.2f}")
    col_3.metric(label="Profit", value=f"₦{profit:,.2f}")
    col_4.metric(label="Profit Margin", value=f"{profit_margin:,.2f}%")

    col_5, col_6, col_7, col_8 = st.columns(4, border=True, gap="small")
    col_5.metric(label="Transactions", value=transactions)
    col_6.metric(label="Customers", value=customers)
    col_7.metric(label="Total Discount", value=f"₦{total_discount:,.2f}")
    col_8.metric(label="Top Selling Product", value=top_product)

    colx, colxx = st.columns([3, 1], gap="medium")

    st.markdown("""
        <style>
        div.stHorizontalBlock {
            background-color: transparent;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)

    with colx:
        # Create a sleek inline control row
        col_title, col_kv = st.columns([2, 1])
        with col_title:
            st.subheader("Financial Performance")

        with col_kv:
            time_frame = st.selectbox(
            label="Granularity",
            options=["Hour", "Day", "Week", "Month", "Year"],
            index=1,  # Default to "Day"
            label_visibility="collapsed",
            key="dashboard_granularity_selectbox"
        )

    # Map the human-readable selection to Pandas resampling offset aliases
    resample_map = {
        "Hour": "h",
        "Day": "D",
        "Week": "W",
        "Month": "ME",
        "Year": "YE"
    }
    offset = resample_map[time_frame]

    # =================================================================
    # 2. Advanced Data Resampling & Alignment
    # =================================================================
    # Resample Sales (Summing 'total' by chosen timeframe)
    sales_resampled = (
        df_sales.set_index("created_at")
        .resample(offset)["total"]
        .sum()
        .to_frame(name="Sales")
    )

    # Resample Expenses/Purchases
    purchases_resampled = (
        df_purchases.set_index("created_at")
        .resample(offset)["total"]
        .sum()
        .to_frame(name="Expenses")
    )

    # Outer join to align both timelines perfectly, replacing missing periods with 0
    df_metrics = sales_resampled.join(purchases_resampled, how="outer").fillna(0).reset_index()

    # =================================================================
    # 3. Premium Sleek Plotly UI Styling
    # =================================================================
    # Using graph_objects instead of express gives absolute design precision
    fig = go.Figure()

    # Sales Line (Dominant, clean theme color)
    fig.add_trace(go.Scatter(
        x=df_metrics["created_at"],
        y=df_metrics["Sales"],
        name="Sales",
        mode="lines",
        line=dict(color="#00D1B2", width=3, shape="spline"), # Spline makes lines smooth
        hovertemplate="<b>Sales</b>: ₦%{y:,.2f}<extra></extra>"
    ))

    # Expenses Line (Subdued accent color)
    fig.add_trace(go.Scatter(
        x=df_metrics["created_at"],
        y=df_metrics["Expenses"],
        name="Expenses",
        mode="lines",
        line=dict(color="#FF3860", width=2, dash="dash", shape="spline"), # Dashed for clear contrast
        hovertemplate="<b>Expenses</b>: ₦%{y:,.2f}<extra></extra>"
    ))

    # Complete UI layout overhaul
    fig.update_layout(
        hovermode="x unified", # Clean vertical hover bar card instead of messy dots
        paper_bgcolor="rgba(0,0,0,0)", # Transparent wrapper to match Streamlit's dark/light native theme
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=20, b=0), # Removes unnecessary padding waste
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="#E6E8EA",
            tickfont=dict(color="#848D95", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F0F2F5", # Soft grid lines that don't yell at the user
            showline=False,
            tickfont=dict(color="#848D95", size=11),
            tickprefix="₦"
        )
    )

    # Render the beautifully polished chart
    colx.plotly_chart(fig, width='stretch', config={"displayModeBar": False}) # Hides cluttery plotly toolbar

    # 1. Merge the dataframes on the matching keys
    # 'id' from products table maps to 'product_id' in the sales table
    df_merged = pd.merge(
        df_sales, 
        df_products, 
        left_on="product_id", 
        right_on="id", 
        how="inner"
    )

    # 2. Group by the product category and sum up the 'total' sales column
    df_category_sales = (
        df_merged.groupby("category")["total"]
        .sum()
        .reset_index(name="total_revenue")
        .sort_values(by="total_revenue", ascending=False)
    )

    # Check if we actually have data to display
    if df_category_sales.empty:
        st.info("No sales data available to display category breakdown.")
    else:
        # Premium, modern cohesive color palette
        sleek_colors = ["#00D1B2", "#2400FF", "#FF3860", "#FFDD57", "#1D8CF8", "#9B5DE5"]

        # Create the donut chart
        fig = px.pie(
            df_category_sales,
            values="total_revenue",
            names="category",
            hole=0.5,  # Turning it into a donut chart instantly makes it look sleeker
            color_discrete_sequence=sleek_colors
        )

        # Clean up layout, fonts, and hover labels
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Revenue: ₦%{value:,.2f}<br>Share: %{percent}<extra></extra>"
        )

        fig.update_layout(
            showlegend=False,  # Labels are already inside, removing the legend cuts clutter
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",  # Transparent background for system dark/light modes
            plot_bgcolor="rgba(0,0,0,0)",
            height=320
        )

        # Render UI elements
        st.subheader("Sales Breakdown by Category")
        colxx.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

    st.subheader("Sales Record Log")
    st.dataframe(df_sales, width='stretch')

    st.subheader("Inventory Product List")
    st.dataframe(df_products, width='stretch')

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Business Portal")
    load_dotenv()
    business_uuid = os.getenv("BUSINESS_ID")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

    if not supabase_url or not supabase_key:
        st.error("Missing Supabase credentials. Please check your .env file.")
        st.stop()

    supabase: Client = create_client(supabase_url, supabase_key)
    show_dashboard_metrics(supabase, business_uuid)