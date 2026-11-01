# 🏪 Superstore AI Executive Dashboard v3.0

Upload the Kaggle Superstore CSV → Auto cleaning → Full KPI analysis → AI executive report

## 🚀 Run in 3 steps

```bash
pip install -r requirements.txt
```

Your Groq API key is already set in `.env`. To use your own:
```
GROQ_API_KEY=your_key_here
```
Get a free key at: https://console.groq.com

```bash
streamlit run app.py
```

## ✨ What it does

1. Upload the Kaggle Superstore CSV (Sample - Superstore.csv)
2. Auto-maps Superstore columns → standard names (e.g. `Sales` → `Revenue`, `Product Name` → `Product`)
3. Full data cleaning: duplicates, nulls, bad dates, negative values, type coercion
4. Adds derived columns: `Profit_Margin_Pct`, `Days_to_Ship`
5. Calculates 10+ KPIs automatically
6. Draws 8 interactive charts (revenue trend, region, categories, sub-categories, segments, states, profit, YoY)
7. Year-over-Year summary table
8. AI writes executive report — no API key input needed by user
9. Download cleaned CSV + executive report

## 📋 Superstore CSV Columns (auto-mapped)

| Kaggle Column   | Internal Name   |
|-----------------|-----------------|
| Order ID        | Order_ID        |
| Order Date      | Order_Date      |
| Ship Date       | Ship_Date       |
| Ship Mode       | Ship_Mode       |
| Customer Name   | Customer_Name   |
| Segment         | Segment         |
| Region          | Region          |
| State           | State           |
| Category        | Category        |
| Sub-Category    | Sub_Category    |
| Product Name    | Product         |
| Sales           | Revenue         |
| Quantity        | Quantity        |
| Discount        | Discount        |
| Profit          | Profit          |

## 📦 Dataset
Download from: https://www.kaggle.com/datasets/vivek468/superstore-dataset-final
