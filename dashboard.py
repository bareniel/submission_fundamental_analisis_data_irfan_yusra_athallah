import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📦 E-Commerce Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .stMetric label { font-size: 0.8rem; color: #6c757d; }
    h1 { color: #1a1a2e; }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Load dari file lokal (main_data.csv di folder dashboard)
    local_path = os.path.join(os.path.dirname(__file__), "main_data.csv")
    if os.path.exists(local_path):
        df = pd.read_csv(local_path)
    else:
        file_id = "1nPZ72aIaqoFFInIY00Qjf4U7X51R7ooz"
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        df = pd.read_csv(url)

    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")
    df["year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["year"] = df["order_purchase_timestamp"].dt.year
    df["month"] = df["order_purchase_timestamp"].dt.month
    df["day_of_week"] = df["order_purchase_timestamp"].dt.day_name()
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["on_time"] = df["order_delivered_customer_date"] <= df["order_estimated_delivery_date"]
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shopping-cart.png", width=60)
    st.title("🔍 Filter Data")

    year_options = sorted(df["year"].unique())
    selected_years = st.multiselect("Tahun", year_options, default=year_options)

    status_options = sorted(df["order_status"].unique())
    selected_status = st.multiselect("Status Pesanan", status_options, default=status_options)

    price_min, price_max = float(df["price"].min()), float(df["price"].max())
    price_range = st.slider("Rentang Harga (R$)", price_min, price_max, (price_min, price_max))

    st.markdown("---")
    st.caption("📊 Data: Brazilian E-Commerce")
    st.caption(f"Total data: {len(df):,} baris")

# ── Apply Filters ─────────────────────────────────────────────────────────────
filtered = df[
    df["year"].isin(selected_years) &
    df["order_status"].isin(selected_status) &
    df["price"].between(price_range[0], price_range[1])
]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📦 Dashboard E-Commerce")
st.caption(f"Menampilkan **{len(filtered):,}** dari **{len(df):,}** pesanan · Periode: {filtered['order_purchase_timestamp'].min().strftime('%d %b %Y')} – {filtered['order_purchase_timestamp'].max().strftime('%d %b %Y')}")
st.markdown("---")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_revenue = filtered["price"].sum() + filtered["freight_value"].sum()
avg_order_value = filtered["price"].mean()
total_orders = filtered["order_id"].nunique()
avg_delivery = filtered.loc[filtered["delivery_days"] > 0, "delivery_days"].mean()
on_time_pct = filtered["on_time"].mean() * 100 if filtered["on_time"].notna().any() else 0

col1.metric("🛒 Total Pesanan", f"{total_orders:,}")
col2.metric("💰 Total Pendapatan", f"R$ {total_revenue:,.0f}")
col3.metric("🎯 Rata-rata Harga", f"R$ {avg_order_value:.2f}")
col4.metric("🚚 Rata-rata Pengiriman", f"{avg_delivery:.1f} hari")
col5.metric("✅ On-Time Delivery", f"{on_time_pct:.1f}%")

st.markdown("---")

# ── Row 1: Monthly Trend + Status Distribution ────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Tren Pesanan & Pendapatan per Bulan")
    monthly = (
        filtered.groupby("year_month")
        .agg(total_orders=("order_id", "count"), total_revenue=("price", "sum"))
        .reset_index()
    )
    fig_trend = go.Figure()
    # Warna seragam untuk bar
    fig_trend.add_trace(go.Bar(
        x=monthly["year_month"], y=monthly["total_orders"],
        name="Jumlah Pesanan", marker_color="#4361ee",
        yaxis="y1"
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["total_revenue"],
        name="Pendapatan (R$)", line=dict(color="#f72585", width=2.5),
        mode="lines+markers", yaxis="y2"
    ))
    fig_trend.update_layout(
        yaxis=dict(title="Jumlah Pesanan", showgrid=False),
        yaxis2=dict(title="Pendapatan (R$)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0), height=300,
        xaxis=dict(tickangle=-45, tickfont=dict(size=9))
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🏷️ Status Pesanan")
    status_counts = filtered["order_status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    colors = ["#4361ee", "#7209b7", "#f72585", "#4cc9f0", "#06d6a0", "#ffd166", "#ef476f"]
    fig_pie = px.pie(
        status_counts, names="Status", values="Count",
        color_discrete_sequence=colors, hole=0.45
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(
        showlegend=False, margin=dict(l=0, r=0, t=30, b=0), height=300,
        plot_bgcolor="white", paper_bgcolor="white"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Row 2: Price Distribution + Day of Week ────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("💵 Distribusi Harga Produk")
    price_data = filtered[filtered["price"] <= filtered["price"].quantile(0.95)]
    fig_hist = px.histogram(
        price_data, x="price", nbins=50,
        color_discrete_sequence=["#4361ee"],
        labels={"price": "Harga (R$)", "count": "Jumlah"},
    )
    fig_hist.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0), height=280,
        showlegend=False, bargap=0.05
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    st.subheader("📅 Pesanan per Hari dalam Seminggu")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_label = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_counts = filtered["day_of_week"].value_counts().reindex(day_order).fillna(0)
    # Gunakan warna seragam (bukan color scale) agar prinsip desain visualisasi terpenuhi
    fig_bar = go.Figure(go.Bar(
        x=day_label,
        y=day_counts.values,
        marker_color="#4361ee",
    ))
    fig_bar.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0), height=280,
        showlegend=False,
        xaxis_title="Hari",
        yaxis_title="Jumlah Pesanan"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Row 3: Delivery Days + Freight vs Price ────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("🚚 Distribusi Lama Pengiriman")
    delivery_data = filtered[
        (filtered["delivery_days"] > 0) & (filtered["delivery_days"] <= 60)
    ]["delivery_days"]
    fig_box = px.histogram(
        delivery_data, nbins=40,
        color_discrete_sequence=["#4361ee"],
        labels={"value": "Hari Pengiriman", "count": "Jumlah"},
    )
    fig_box.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0), height=280,
        showlegend=False, bargap=0.05,
        xaxis_title="Hari Pengiriman", yaxis_title="Jumlah Pesanan"
    )
    st.plotly_chart(fig_box, use_container_width=True)

with col_d:
    st.subheader("✈️ Ongkos Kirim vs Harga Produk")
    sample = filtered[filtered["price"] <= filtered["price"].quantile(0.95)].sample(
        min(3000, len(filtered)), random_state=42
    )
    fig_scatter = px.scatter(
        sample, x="price", y="freight_value",
        color="order_status",
        opacity=0.5, size_max=6,
        labels={"price": "Harga (R$)", "freight_value": "Ongkos Kirim (R$)", "order_status": "Status"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_scatter.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=0), height=280,
        legend=dict(orientation="h", y=-0.3, font_size=10)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Raw Data Preview ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🗄️ Lihat Data Mentah", expanded=False):
    st.dataframe(
        filtered[[
            "order_id", "order_status", "order_purchase_timestamp",
            "price", "freight_value", "delivery_days", "on_time"
        ]].head(500),
        use_container_width=True, height=300
    )
    st.caption(f"Menampilkan 500 baris pertama dari {len(filtered):,} total baris.")
