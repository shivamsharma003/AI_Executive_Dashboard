
import pandas as pd
import numpy as np


def calculate_kpis(df):
    """Calculate all business KPIs from cleaned Superstore dataframe."""

    total_revenue = df["Revenue"].sum()
    total_profit = df["Profit"].sum()
    profit_margin = round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0
    total_orders = df["Order_ID"].nunique()
    total_units = int(df["Quantity"].sum())

    # ── Monthly revenue & profit trend ───────────────────────────────────────
    df = df.copy()
    df["Month"] = df["Order_Date"].dt.to_period("M")
    monthly = df.groupby("Month")["Revenue"].sum().reset_index()
    monthly["Month_str"] = monthly["Month"].astype(str)
    monthly = monthly.sort_values("Month")

    monthly_profit = df.groupby("Month")["Profit"].sum().reset_index()
    monthly_profit["Month_str"] = monthly_profit["Month"].astype(str)

    # Month-over-Month growth
    if len(monthly) >= 2:
        last = monthly["Revenue"].iloc[-1]
        prev = monthly["Revenue"].iloc[-2]
        growth = round(((last - prev) / prev * 100), 2) if prev > 0 else 0
    else:
        growth = 0

    # ── Region performance ────────────────────────────────────────────────────
    region_rev = df.groupby("Region")["Revenue"].sum()
    region_profit = df.groupby("Region")["Profit"].sum()
    top_region = region_rev.idxmax()
    worst_region = region_rev.idxmin()

    # ── Top 10 products by revenue ────────────────────────────────────────────
    top_products = (
        df.groupby("Product")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    # ── Category breakdown ────────────────────────────────────────────────────
    category_rev = df.groupby("Category")["Revenue"].sum().reset_index()
    category_profit = df.groupby("Category").agg(
        Revenue=("Revenue", "sum"),
        Profit=("Profit", "sum")
    ).reset_index()
    category_profit["Margin"] = (category_profit["Profit"] / category_profit["Revenue"] * 100).round(2)

    # ── Sub-Category breakdown (Superstore-specific) ──────────────────────────
    sub_cat_perf = None
    if "Sub_Category" in df.columns:
        sub_cat_perf = (
            df.groupby("Sub_Category")
            .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )
        sub_cat_perf["Margin"] = (sub_cat_perf["Profit"] / sub_cat_perf["Revenue"] * 100).round(2)

    # ── Segment breakdown (Superstore-specific) ───────────────────────────────
    segment_perf = None
    if "Segment" in df.columns:
        segment_perf = (
            df.groupby("Segment")
            .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
            .reset_index()
        )

    # ── Avg order value ───────────────────────────────────────────────────────
    order_values = df.groupby("Order_ID")["Revenue"].sum()
    avg_order_value = order_values.mean()

    # ── Avg discount (Superstore-specific) ────────────────────────────────────
    avg_discount = df["Discount"].mean() * 100 if "Discount" in df.columns else None

    # ── Avg days to ship ─────────────────────────────────────────────────────
    avg_ship_days = df["Days_to_Ship"].mean() if "Days_to_Ship" in df.columns else None

    # ── Top states by revenue ─────────────────────────────────────────────────
    top_states = None
    if "State" in df.columns:
        top_states = (
            df.groupby("State")["Revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

    # ── Yearly performance ────────────────────────────────────────────────────
    df["Year"] = df["Order_Date"].dt.year
    yearly = df.groupby("Year").agg(
        Revenue=("Revenue", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "nunique")
    ).reset_index()

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "profit_margin": profit_margin,
        "total_orders": total_orders,
        "total_units": total_units,
        "monthly_growth": growth,
        "avg_order_value": avg_order_value,
        "avg_discount": avg_discount,
        "avg_ship_days": avg_ship_days,
        "top_region": top_region,
        "worst_region": worst_region,
        "monthly_revenue": monthly,
        "monthly_profit": monthly_profit,
        "region_revenue": region_rev.reset_index(),
        "region_profit": region_profit.reset_index(),
        "top_products": top_products,
        "category_revenue": category_rev,
        "category_profit": category_profit,
        "sub_category": sub_cat_perf,
        "segment": segment_perf,
        "top_states": top_states,
        "yearly": yearly,
    }


def build_summary_text(kpis):
    """Convert KPIs into readable text for AI prompt."""
    top5 = ", ".join(kpis["top_products"]["Product"].head(5).tolist()) if len(kpis["top_products"]) > 0 else "N/A"

    lines = [
        f"Total Revenue: ${kpis['total_revenue']:,.0f}",
        f"Total Profit: ${kpis['total_profit']:,.0f}",
        f"Profit Margin: {kpis['profit_margin']}%",
        f"Total Orders: {kpis['total_orders']:,}",
        f"Total Units Sold: {kpis['total_units']:,}",
        f"Average Order Value: ${kpis['avg_order_value']:,.2f}",
        f"Month-over-Month Revenue Growth: {kpis['monthly_growth']}%",
        f"Top Performing Region: {kpis['top_region']}",
        f"Worst Performing Region: {kpis['worst_region']}",
        f"Top 5 Products by Revenue: {top5}",
    ]

    if kpis["avg_discount"] is not None:
        lines.append(f"Average Discount Given: {kpis['avg_discount']:.1f}%")

    if kpis["avg_ship_days"] is not None:
        lines.append(f"Average Days to Ship: {kpis['avg_ship_days']:.1f} days")

    if kpis["segment"] is not None:
        seg_summary = "; ".join(
            f"{row['Segment']} (${row['Revenue']:,.0f})"
            for _, row in kpis["segment"].iterrows()
        )
        lines.append(f"Revenue by Segment: {seg_summary}")

    if kpis["sub_category"] is not None:
        top3_sub = kpis["sub_category"].head(3)
        sub_summary = "; ".join(
            f"{row['Sub_Category']} (${row['Revenue']:,.0f}, margin {row['Margin']}%)"
            for _, row in top3_sub.iterrows()
        )
        lines.append(f"Top 3 Sub-Categories: {sub_summary}")

    cat_summary = "; ".join(
        f"{row['Category']} (${row['Revenue']:,.0f})"
        for _, row in kpis["category_revenue"].iterrows()
    )
    lines.append(f"Revenue by Category: {cat_summary}")

    if len(kpis["yearly"]) > 0:
        yearly_summary = "; ".join(
            f"{int(row['Year'])}: ${row['Revenue']:,.0f} revenue, ${row['Profit']:,.0f} profit"
            for _, row in kpis["yearly"].iterrows()
        )
        lines.append(f"Yearly Performance: {yearly_summary}")

    return "\n".join(lines)
