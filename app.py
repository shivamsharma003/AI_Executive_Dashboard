import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_cleaning import load_raw, clean_data
from utils.data_processing import calculate_kpis, build_summary_text
from utils.ai_insights import generate_insights

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Executive Insight Dashboard ",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }

    .kpi-card {
        background: linear-gradient(135deg, #1e2130, #252a3d);
        border: 1px solid #2e3450;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .kpi-label {
        color: #8892b0;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .kpi-value { color: #ccd6f6; font-size: 24px; font-weight: 700; }
    .kpi-value.green { color: #64ffda; }
    .kpi-value.red { color: #ff6b6b; }
    .kpi-value.yellow { color: #ffd166; }
    .kpi-icon { font-size: 20px; margin-bottom: 4px; }

    .section-title {
        color: #ccd6f6;
        font-size: 18px;
        font-weight: 700;
        border-left: 4px solid #64ffda;
        padding-left: 10px;
        margin: 28px 0 14px 0;
    }

    .clean-card {
        background: #1a1f35;
        border: 1px solid #2e3450;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 8px;
        color: #a8b2d8;
        font-size: 14px;
    }

    .insight-box {
        background: linear-gradient(135deg, #1a1f35, #1e2540);
        border: 1px solid #64ffda33;
        border-radius: 12px;
        padding: 24px 28px;
        color: #a8b2d8;
        line-height: 1.9;
        font-size: 15px;
    }

    .info-badge {
        background: #1a2744;
        border: 1px solid #2e4a80;
        border-radius: 8px;
        padding: 8px 14px;
        color: #7b9fd4;
        font-size: 12px;
        display: inline-block;
        margin: 2px 4px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

PLOT_BG = "#1a1f35"
FONT_COLOR = "#8892b0"
GRID_COLOR = "#2e3450"
COLORS = ["#64ffda", "#7b7fff", "#ff6b9d", "#ffd166", "#06d6a0",
          "#f72585", "#4cc9f0", "#fb8500", "#a8dadc", "#e9c46a"]


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📂 Upload Your Data")
    st.markdown(
        "Upload any raw sales CSV — the app will clean it automatically.")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Drop your CSV file here",
        type=["csv"]
    )

    st.markdown("---")
    st.markdown("### 📋 Required Columns")
    detected_cols = [
        "Order ID / Order_ID",
        "Order Date / Order_Date",
        "Ship Date / Ship_Date",
        "Ship Mode", "Customer Name",
        "Segment", "Region", "State",
        "Category", "Sub-Category",
        "Product Name → Product",
        "Sales → Revenue",
        "Quantity", "Discount", "Profit"
    ]
    for c in detected_cols:
        st.markdown(f"• `{c}`")

    st.markdown("---")
    st.markdown("**AI Superstore Dashboard** v3.0")
    st.markdown("Superstore data + AI insights")


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 8px 0 4px 0'>
    <h1 style='color:#ccd6f6; font-size:34px; font-weight:800; margin:0'>
        🏪 AI Executive Insight Dashboard 
    </h1>
    <p style='color:#8892b0; font-size:14px; margin-top:6px'>
        Upload raw data → Auto cleaning → KPI analysis → AI-generated executive report
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
raw_df = None

if uploaded_file:
    try:
        raw_df = load_raw(uploaded_file)
        st.success(
            f"✅ **{uploaded_file.name}** uploaded — {len(raw_df):,} raw rows detected")
    except ValueError as e:
        st.error(f"❌ {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Could not read file: {e}")
        st.stop()
else:
    st.markdown("""
    <div style='text-align:center; padding:80px 20px; color:#8892b0'>
        <div style='font-size:56px; margin-bottom:16px'>📂</div>
        <h3 style='color:#ccd6f6'>No Data Uploaded</h3>
        <p>Upload a CSV from the sidebar or check "Use sample raw data"</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — RAW DATA PREVIEW WITH ISSUE SCAN
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗂️ Step 1 — Raw Data (Before Cleaning)</div>',
            unsafe_allow_html=True)

total_nulls = raw_df.isna().sum().sum()
total_dups = raw_df.duplicated().sum()
# Use already-mapped column name
_date_col = "Order_Date" if "Order_Date" in raw_df.columns else "Order Date"
bad_dates_raw = pd.to_datetime(raw_df[_date_col], errors="coerce").isna().sum()
_rev_col = "Revenue" if "Revenue" in raw_df.columns else "Sales"
neg_sales_raw = (pd.to_numeric(raw_df[_rev_col], errors="coerce") < 0).sum()


null_per_col = raw_df.isna().sum()
null_cols = null_per_col[null_per_col > 0]
if len(null_cols) > 0:
    with st.expander(f"🔍 Null breakdown by column ({len(null_cols)} columns affected)"):
        null_df = null_cols.reset_index()
        null_df.columns = ["Column", "Null Count"]
        null_df["% of rows"] = (
            null_df["Null Count"] / len(raw_df) * 100).round(2).astype(str) + "%"
        st.dataframe(null_df, use_container_width=True, hide_index=True)

st.markdown("**Raw Data Table** — scroll to spot issues:")
st.dataframe(raw_df, use_container_width=True, height=280)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — DATA CLEANING
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🧹 Step 2 — Data Cleaning Report</div>',
            unsafe_allow_html=True)

with st.spinner("Cleaning your Superstore data..."):
    cleaned_df, report = clean_data(raw_df.copy())

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>🗑️</div>
        <div style='color:#ff6b6b;font-size:20px;font-weight:700'>{report['duplicates_removed']}</div>
        <div>Duplicates Removed</div></div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>🪪</div>
        <div style='color:#ff6b6b;font-size:20px;font-weight:700'>{report['missing_order_ids_removed']}</div>
        <div>Bad Order IDs Dropped</div></div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>📅</div>
        <div style='color:#ffd166;font-size:20px;font-weight:700'>{report['invalid_dates_removed']}</div>
        <div>Bad Dates Removed</div></div>""", unsafe_allow_html=True)

with c4:
    total_filled = (report['missing_revenue_filled'] +
                    report['missing_profit_filled'] + report['missing_quantity_filled'])
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>🔧</div>
        <div style='color:#ffd166;font-size:20px;font-weight:700'>{total_filled}</div>
        <div>Nulls Imputed (median)</div></div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>⛔</div>
        <div style='color:#ff6b6b;font-size:20px;font-weight:700'>{report.get('negative_revenue_removed', 0)}</div>
        <div>Negative Sales Dropped</div></div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""<div class="clean-card">
        <div style='font-size:22px'>✅</div>
        <div style='color:#64ffda;font-size:20px;font-weight:700'>{report['final_rows']:,}</div>
        <div>Clean Rows Ready</div></div>""", unsafe_allow_html=True)

st.markdown("#### 📊 Before vs After")
ba1, ba2, ba3, ba4 = st.columns(4)
with ba1:
    st.metric("Rows Before", f"{report['original_rows']:,}")
with ba2:
    removed = report['original_rows'] - report['final_rows']
    st.metric("Rows After",
              f"{report['final_rows']:,}", delta=f"-{removed} issues removed")
with ba3:
    new_cols = [c for c in ["Profit_Margin_Pct",
                            "Days_to_Ship"] if c in cleaned_df.columns]
    st.metric("Derived Columns Added", len(new_cols),
              help=", ".join(new_cols) if new_cols else "none")
with ba4:
    pct_clean = round(report['final_rows'] / report['original_rows'] * 100, 1)
    st.metric("Data Retained", f"{pct_clean}%")

with st.expander("📋 Full cleaning log — what was done to each column"):
    log_items = [
        ("Sales / Revenue", "Missing → Filled",
         report['missing_revenue_filled'],           "Imputed with column median"),
        ("Profit",          "Missing → Filled",
         report['missing_profit_filled'],            "Imputed with column median"),
        ("Quantity",        "Missing → Filled",
         report['missing_quantity_filled'],          "Imputed with column median"),
        ("Order ID",        "Rows Dropped",
         report['missing_order_ids_removed'],        "Rows with null Order ID removed"),
        ("Order Date",      "Rows Dropped",
         report['invalid_dates_removed'],            "Unparseable dates removed"),
        ("Region",          "Rows Dropped",
         report['missing_regions_removed'],          "Blank/null regions removed"),
        ("Sales / Revenue", "Rows Dropped",
         report.get('negative_revenue_removed', 0), "Negative sales removed"),
        ("All columns",     "Rows Dropped",
         report['duplicates_removed'],               "Exact duplicate rows removed"),
    ]
    log_df = pd.DataFrame(log_items, columns=[
                          "Column", "Action", "Count", "Details"])
    log_df["Status"] = log_df["Count"].apply(
        lambda x: "✅ Nothing to fix" if x == 0 else "🔧 Fixed")
    st.dataframe(log_df, use_container_width=True, hide_index=True)

tab_raw, tab_clean = st.tabs(["🔴 Raw Data (dirty)", "🟢 Cleaned Data"])

with tab_raw:
    st.markdown(
        f"**{report['original_rows']:,} rows** — unprocessed, may contain issues")
    st.dataframe(raw_df, use_container_width=True, height=260)

with tab_clean:
    st.markdown(
        f"**{report['final_rows']:,} rows** — fully cleaned and enriched")
    st.dataframe(cleaned_df, use_container_width=True, height=260)
    csv_clean = cleaned_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Cleaned Dataset",
        data=csv_clean,
        file_name="superstore_cleaned.csv",
        mime="text/csv"
    )


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — KPIs
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Step 3 — Key Performance Indicators</div>',
            unsafe_allow_html=True)

kpis = calculate_kpis(cleaned_df)

# Row 1 — Core KPIs
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">💰</div>
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value green">${kpis['total_revenue']:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    pc = "green" if kpis['total_profit'] > 0 else "red"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">📊</div>
        <div class="kpi-label">Total Profit</div>
        <div class="kpi-value {pc}">${kpis['total_profit']:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    mc = "green" if kpis['profit_margin'] >= 10 else "red"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">📉</div>
        <div class="kpi-label">Profit Margin</div>
        <div class="kpi-value {mc}">{kpis['profit_margin']}%</div>
    </div>""", unsafe_allow_html=True)

with k4:
    gc = "green" if kpis['monthly_growth'] >= 0 else "red"
    gi = "📈" if kpis['monthly_growth'] >= 0 else "📉"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{gi}</div>
        <div class="kpi-label">MoM Growth</div>
        <div class="kpi-value {gc}">{kpis['monthly_growth']:+.1f}%</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">📦</div>
        <div class="kpi-label">Total Orders</div>
        <div class="kpi-value">{kpis['total_orders']:,}</div>
    </div>""", unsafe_allow_html=True)

# Row 2 — Operational KPIs
r1, r2, r3, r4, r5 = st.columns(5)

with r1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">🏆</div>
        <div class="kpi-label">Top Region</div>
        <div class="kpi-value green" style="font-size:18px">{kpis['top_region']}</div>
    </div>""", unsafe_allow_html=True)

with r2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">⚠️</div>
        <div class="kpi-label">Worst Region</div>
        <div class="kpi-value red" style="font-size:18px">{kpis['worst_region']}</div>
    </div>""", unsafe_allow_html=True)

with r3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">🛒</div>
        <div class="kpi-label">Units Sold</div>
        <div class="kpi-value">{kpis['total_units']:,}</div>
    </div>""", unsafe_allow_html=True)

with r4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">🧾</div>
        <div class="kpi-label">Avg Order Value</div>
        <div class="kpi-value yellow">${kpis['avg_order_value']:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with r5:
    if kpis['avg_discount'] is not None:
        dc = "red" if kpis['avg_discount'] > 20 else "yellow"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🏷️</div>
            <div class="kpi-label">Avg Discount</div>
            <div class="kpi-value {dc}">{kpis['avg_discount']:.1f}%</div>
        </div>""", unsafe_allow_html=True)
    elif kpis['avg_ship_days'] is not None:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🚚</div>
            <div class="kpi-label">Avg Ship Days</div>
            <div class="kpi-value">{kpis['avg_ship_days']:.1f}d</div>
        </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — CHARTS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Step 4 — Visual Analytics</div>',
            unsafe_allow_html=True)

# ── Row 1: Monthly Revenue Trend + Region Revenue ────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("##### 📈 Monthly Revenue Trend")
    monthly = kpis["monthly_revenue"]
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=monthly["Month_str"], y=monthly["Revenue"],
        mode="lines+markers",
        line=dict(color="#64ffda", width=3),
        marker=dict(size=7, color="#64ffda"),
        fill="tozeroy", fillcolor="rgba(100,255,218,0.07)"
    ))
    fig1.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR, tickangle=-45),
        yaxis=dict(gridcolor=GRID_COLOR, tickprefix="$"),
        margin=dict(l=10, r=10, t=10, b=10), height=300, showlegend=False
    )
    st.plotly_chart(fig1, use_container_width=True)

with ch2:
    st.markdown("##### 🌍 Region-wise Revenue vs Profit")
    reg_rev = kpis["region_revenue"].rename(columns={"Revenue": "Revenue"})
    reg_prof = kpis["region_profit"].rename(columns={"Profit": "Profit"})
    reg_combined = reg_rev.merge(reg_prof, on="Region")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Revenue", x=reg_combined["Region"], y=reg_combined["Revenue"],
        marker_color="#64ffda"
    ))
    fig2.add_trace(go.Bar(
        name="Profit", x=reg_combined["Region"], y=reg_combined["Profit"],
        marker_color="#7b7fff"
    ))
    fig2.update_layout(
        barmode="group",
        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, tickprefix="$"),
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        legend=dict(font=dict(color="#8892b0"))
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Top 10 Products + Category Donut ─────────────────────────────────
ch3, ch4 = st.columns(2)

with ch3:
    st.markdown("##### 🏅 Top 10 Products by Revenue")
    tp = kpis["top_products"].sort_values("Revenue", ascending=True)
    # Truncate long product names
    tp["Product_Short"] = tp["Product"].apply(
        lambda x: x[:35] + "…" if len(x) > 35 else x)
    fig3 = go.Figure(go.Bar(
        x=tp["Revenue"], y=tp["Product_Short"], orientation="h",
        marker=dict(color=COLORS * 2),
        text=[f"${v:,.0f}" for v in tp["Revenue"]],
        textposition="outside", textfont=dict(color="#ccd6f6", size=11)
    ))
    fig3.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(size=10)),
        margin=dict(l=10, r=80, t=10, b=10), height=360, showlegend=False
    )
    st.plotly_chart(fig3, use_container_width=True)

with ch4:
    st.markdown("##### 🍩 Revenue by Category")
    cat = kpis["category_revenue"]
    fig4 = go.Figure(go.Pie(
        labels=cat["Category"], values=cat["Revenue"],
        hole=0.55, marker=dict(colors=COLORS[:len(cat)]),
        textinfo="label+percent", textfont=dict(color="#ccd6f6", size=13)
    ))
    fig4.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        margin=dict(l=10, r=10, t=10, b=10), height=360,
        legend=dict(font=dict(color="#8892b0"))
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Sub-Category + Segment (Superstore-specific) ─────────────────────
if kpis["sub_category"] is not None or kpis["segment"] is not None:
    ch5, ch6 = st.columns(2)

    if kpis["sub_category"] is not None:
        with ch5:
            st.markdown("##### 📂 Sub-Category Performance")
            sc = kpis["sub_category"].sort_values("Revenue", ascending=True)
            fig5 = go.Figure()
            fig5.add_trace(go.Bar(
                name="Revenue", x=sc["Revenue"], y=sc["Sub_Category"],
                orientation="h", marker_color="#64ffda"
            ))
            fig5.add_trace(go.Bar(
                name="Profit", x=sc["Profit"], y=sc["Sub_Category"],
                orientation="h", marker_color="#ff6b9d"
            ))
            fig5.update_layout(
                barmode="overlay",
                plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
                font=dict(color=FONT_COLOR),
                xaxis=dict(gridcolor=GRID_COLOR, tickprefix="$"),
                yaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(size=10)),
                margin=dict(l=10, r=10, t=10, b=10), height=360,
                legend=dict(font=dict(color="#8892b0"))
            )
            st.plotly_chart(fig5, use_container_width=True)

    if kpis["segment"] is not None:
        with ch6:
            st.markdown("##### 👥 Revenue by Customer Segment")
            seg = kpis["segment"]
            fig6 = go.Figure(go.Bar(
                x=seg["Segment"], y=seg["Revenue"],
                marker=dict(color=COLORS[:len(seg)]),
                text=[f"${v:,.0f}" for v in seg["Revenue"]],
                textposition="outside", textfont=dict(color="#ccd6f6")
            ))
            fig6.update_layout(
                plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
                font=dict(color=FONT_COLOR),
                xaxis=dict(gridcolor=GRID_COLOR),
                yaxis=dict(gridcolor=GRID_COLOR, tickprefix="$"),
                margin=dict(l=10, r=10, t=30, b=10), height=360, showlegend=False
            )
            st.plotly_chart(fig6, use_container_width=True)

# ── Row 4: Top States + Monthly Profit Trend ─────────────────────────────────
ch7, ch8 = st.columns(2)

if kpis["top_states"] is not None:
    with ch7:
        st.markdown("##### 🗺️ Top 10 States by Revenue")
        ts = kpis["top_states"].sort_values("Revenue", ascending=True)
        fig7 = go.Figure(go.Bar(
            x=ts["Revenue"], y=ts["State"], orientation="h",
            marker=dict(color=ts["Revenue"], colorscale=[
                        [0, "#7b7fff"], [1, "#64ffda"]], showscale=False),
            text=[f"${v:,.0f}" for v in ts["Revenue"]],
            textposition="outside", textfont=dict(color="#ccd6f6", size=11)
        ))
        fig7.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color=FONT_COLOR),
            xaxis=dict(gridcolor=GRID_COLOR),
            yaxis=dict(gridcolor=GRID_COLOR),
            margin=dict(l=10, r=80, t=10, b=10), height=360, showlegend=False
        )
        st.plotly_chart(fig7, use_container_width=True)

with ch8:
    st.markdown("##### 💹 Monthly Profit Trend")
    mp = kpis["monthly_profit"]
    colors_mp = ["#64ffda" if v >= 0 else "#ff6b6b" for v in mp["Profit"]]
    fig8 = go.Figure(go.Bar(
        x=mp["Month_str"], y=mp["Profit"],
        marker_color=colors_mp,
    ))
    fig8.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR, tickangle=-45),
        yaxis=dict(gridcolor=GRID_COLOR, tickprefix="$"),
        margin=dict(l=10, r=10, t=10, b=10), height=360, showlegend=False
    )
    st.plotly_chart(fig8, use_container_width=True)

# ── Yearly summary table ──────────────────────────────────────────────────────
st.markdown("##### 📅 Year-over-Year Summary")
yearly = kpis["yearly"].copy()
yearly["Revenue"] = yearly["Revenue"].apply(lambda x: f"${x:,.0f}")
yearly["Profit"] = yearly["Profit"].apply(lambda x: f"${x:,.0f}")
yearly["Year"] = yearly["Year"].astype(int)
st.dataframe(yearly.rename(columns={"Year": "Year", "Revenue": "Revenue", "Profit": "Profit", "Orders": "Orders"}),
             use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — AI INSIGHTS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🤖 Step 5 — AI Executive Insight Report</div>',
            unsafe_allow_html=True)

summary_text = build_summary_text(kpis)

with st.expander("📋 View data summary sent to AI"):
    st.code(summary_text, language="text")

if st.button("🚀 Generate AI Executive Report", use_container_width=True, type="primary"):
    with st.spinner("AI is analyzing your Superstore data and writing the executive report..."):
        st.session_state["insight"] = generate_insights(summary_text)

elif "insight" not in st.session_state:
    with st.spinner("Generating initial AI insights..."):
        st.session_state["insight"] = generate_insights(summary_text)

if "insight" in st.session_state:
    st.markdown(f"""
    <div class="insight-box">
        {st.session_state['insight'].replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download Executive Report",
        data=st.session_state["insight"],
        file_name="superstore_executive_report.txt",
        mime="text/plain"
    )

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#4a5568; font-size:12px; padding:8px 0'>
     AI executive Dashboard • Auto Data Cleaning + Groq AI + Streamlit
</div>
""", unsafe_allow_html=True)
