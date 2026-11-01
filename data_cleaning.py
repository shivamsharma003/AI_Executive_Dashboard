import pandas as pd
import numpy as np

# ── Superstore column mapping ─────────────────────────────────────────────────
# Kaggle Superstore columns → our standard names
COLUMN_MAP = {
    "Row ID":        "Row_ID",
    "Order ID":      "Order_ID",
    "Order Date":    "Order_Date",
    "Ship Date":     "Ship_Date",
    "Ship Mode":     "Ship_Mode",
    "Customer ID":   "Customer_ID",
    "Customer Name": "Customer_Name",
    "Segment":       "Segment",
    "Country":       "Country",
    "City":          "City",
    "State":         "State",
    "Postal Code":   "Postal_Code",
    "Region":        "Region",
    "Product ID":    "Product_ID",
    "Category":      "Category",
    "Sub-Category":  "Sub_Category",
    "Product Name":  "Product",
    "Sales":         "Revenue",
    "Quantity":      "Quantity",
    "Discount":      "Discount",
    "Profit":        "Profit",
}

REQUIRED_COLS = {
    "Order_ID", "Order_Date", "Region", "Product",
    "Category", "Quantity", "Revenue", "Profit"
}


def load_raw(file):
    """Read uploaded CSV and map Superstore columns to standard names."""
    df = pd.read_csv(file, encoding="latin-1")

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Apply column mapping where applicable
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df.rename(columns=rename, inplace=True)

    # Check required columns exist after mapping
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns after mapping: {', '.join(sorted(missing))}. "
            f"Found: {', '.join(df.columns.tolist())}"
        )
    return df


def clean_data(df):
    """
    Full data cleaning pipeline for Superstore (and generic) sales data.
    Returns: (cleaned_df, report_dict)
    """
    report = {}
    original_rows = len(df)

    # ── 1. Strip whitespace from column names ─────────────────────────────────
    df.columns = df.columns.str.strip()

    # ── 2. Remove fully empty rows ────────────────────────────────────────────
    df.dropna(how="all", inplace=True)

    # ── 3. Remove duplicate rows ──────────────────────────────────────────────
    before_dup = len(df)
    df.drop_duplicates(inplace=True)
    report["duplicates_removed"] = before_dup - len(df)

    # ── 4. Fix Order_ID ───────────────────────────────────────────────────────
    missing_ids = df["Order_ID"].isna().sum()
    df = df[df["Order_ID"].notna()]
    report["missing_order_ids_removed"] = int(missing_ids)

    # ── 5. Fix Order_Date ─────────────────────────────────────────────────────
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    invalid_dates = df["Order_Date"].isna().sum()
    df = df[df["Order_Date"].notna()]
    report["invalid_dates_removed"] = int(invalid_dates)

    # ── 6. Standardize text columns ───────────────────────────────────────────
    text_cols = ["Region", "Product", "Category", "Segment", "City", "State",
                 "Country", "Sub_Category", "Ship_Mode"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # ── 7. Remove rows with missing / blank Region ────────────────────────────
    bad_region_mask = df["Region"].isin(["Nan", "None", "", "Na"])
    report["missing_regions_removed"] = int(bad_region_mask.sum())
    df = df[~bad_region_mask]

    # ── 8. Fix numeric columns ────────────────────────────────────────────────
    for col in ["Revenue", "Profit", "Quantity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    missing_revenue = df["Revenue"].isna().sum()
    df["Revenue"] = df["Revenue"].fillna(df["Revenue"].median())
    report["missing_revenue_filled"] = int(missing_revenue)

    missing_profit = df["Profit"].isna().sum()
    df["Profit"] = df["Profit"].fillna(df["Profit"].median())
    report["missing_profit_filled"] = int(missing_profit)

    missing_qty = df["Quantity"].isna().sum()
    df["Quantity"] = df["Quantity"].fillna(df["Quantity"].median())
    report["missing_quantity_filled"] = int(missing_qty)

    # Discount column (Superstore-specific)
    if "Discount" in df.columns:
        df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce").fillna(0).clip(0, 1)

    # ── 9. Remove negative Revenue ────────────────────────────────────────────
    negative_rev = (df["Revenue"] < 0).sum()
    df = df[df["Revenue"] >= 0]
    report["negative_revenue_removed"] = int(negative_rev)

    # ── 10. Fix Quantity — must be positive integer ───────────────────────────
    df["Quantity"] = df["Quantity"].apply(lambda x: max(1, round(x)) if pd.notna(x) else 1).astype(int)

    # ── 11. Derived columns ───────────────────────────────────────────────────
    df["Profit_Margin_Pct"] = np.where(
        df["Revenue"] > 0,
        (df["Profit"] / df["Revenue"] * 100).round(2),
        0.0
    )

    if "Ship_Date" in df.columns:
        df["Ship_Date"] = pd.to_datetime(df["Ship_Date"], errors="coerce")
        df["Days_to_Ship"] = (df["Ship_Date"] - df["Order_Date"]).dt.days
        df["Days_to_Ship"] = df["Days_to_Ship"].clip(lower=0)

    # ── 12. Final stats ───────────────────────────────────────────────────────
    report["original_rows"] = original_rows
    report["final_rows"] = len(df)
    report["total_issues_fixed"] = original_rows - len(df)

    df.reset_index(drop=True, inplace=True)
    return df, report
