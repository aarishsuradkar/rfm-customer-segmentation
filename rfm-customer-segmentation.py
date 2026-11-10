"""
RFM Customer Segmentation - Online Retail II (UCI / Kaggle)

How to run:
1. Put the dataset CSV file(s) in the same folder as this script (or use full paths).
   This version loads BOTH years (2009-10 and 2010-11) and combines them.
2. pip install pandas numpy openpyxl matplotlib
3. python rfm_segmentation.py   (or open in VS Code / Jupyter, each "# %%" is a cell)

Outputs (in ./output, ready to load into Power BI):
- rfm_segments.csv      one row per customer with R, F, M, scores and segment
- segment_summary.csv   customers and revenue per segment
- monthly_revenue.csv   revenue by month
- country_revenue.csv   revenue by country
"""

# %% 1. Imports and settings
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# List every data file you want to load. Use full paths if they are not in this folder,
# e.g. r"C:\Users\SCI\Downloads\archive\online_retail_09_10.csv"
DATA_FILES = [
    r"C:\Users\SCI\Downloads\archive\online_retail_09_10.csv",
    r"C:\Users\SCI\Downloads\archive\online_retail_10_11.csv",
]
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)


# %% 2. Load data
def load_file(path: str) -> pd.DataFrame:
    if path.endswith(".csv"):
        # utf-8-sig removes the hidden BOM character at the start of the file
        return pd.read_csv(path, encoding="utf-8-sig")
    sheets = pd.read_excel(path, sheet_name=None)   # Excel: combine all sheets
    return pd.concat(sheets.values(), ignore_index=True)


df = pd.concat([load_file(f) for f in DATA_FILES], ignore_index=True)
df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip()
print("Raw shape:", df.shape)
print(df.head())


# %% 3. Clean data
# Normalise column names (Kaggle and UCI versions differ slightly)
df = df.rename(columns={
    "InvoiceNo": "Invoice",
    "UnitPrice": "Price",
    "CustomerID": "Customer ID",
})
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed")

n_start = len(df)

df = df.dropna(subset=["Customer ID"])                         # need a customer to segment
df = df[~df["Invoice"].astype(str).str.startswith("C")]        # remove cancelled orders
df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]              # remove returns / bad prices
df = df.drop_duplicates()   # also removes the overlapping days (Dec 2010) present in both files
df["Customer ID"] = df["Customer ID"].astype(int)

df["TotalPrice"] = df["Quantity"] * df["Price"]

print(f"Rows: {n_start:,} -> {len(df):,} after cleaning")
print("Customers:", df["Customer ID"].nunique())
print("Date range:", df["InvoiceDate"].min().date(), "to", df["InvoiceDate"].max().date())


# %% 4. Calculate RFM metrics
# Snapshot date = one day after the last transaction in the data
snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df.groupby("Customer ID").agg(
    Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
    Frequency=("Invoice", "nunique"),
    Monetary=("TotalPrice", "sum"),
).reset_index()

print(rfm.describe())


# %% 5. Score each metric from 1 to 5
# Recency: lower days = better, so labels are reversed.
# Frequency: many customers share the same value, so rank first to avoid duplicate bin edges.
rfm["R_score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F_score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M_score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["RFM_Score"] = rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)


# %% 6. Assign segments (based on R and F scores)
def assign_segment(row) -> str:
    r, f = row["R_score"], row["F_score"]
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and f == 3:
        return "Potential Loyalists"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r == 3 and f <= 3:
        return "Need Attention"
    if r <= 2 and f >= 4:
        return "Cant Lose Them"
    if r <= 2 and f == 3:
        return "At Risk"
    if r <= 2 and f == 2:
        return "Hibernating"
    return "Lost"


rfm["Segment"] = rfm.apply(assign_segment, axis=1)


# %% 7. Segment summary and key insights
summary = rfm.groupby("Segment").agg(
    Customers=("Customer ID", "count"),
    Avg_Recency=("Recency", "mean"),
    Avg_Frequency=("Frequency", "mean"),
    Avg_Monetary=("Monetary", "mean"),
    Total_Revenue=("Monetary", "sum"),
).reset_index()

summary["Customer_%"] = (summary["Customers"] / summary["Customers"].sum() * 100).round(1)
summary["Revenue_%"] = (summary["Total_Revenue"] / summary["Total_Revenue"].sum() * 100).round(1)
summary = summary.sort_values("Total_Revenue", ascending=False).round(1)

print(summary.to_string(index=False))

# These are the numbers for your resume bullet:
champ = summary[summary["Segment"] == "Champions"]
if not champ.empty:
    print(
        f"\nChampions = {champ['Customer_%'].iloc[0]}% of customers "
        f"but {champ['Revenue_%'].iloc[0]}% of revenue"
    )
print(f"Total customers segmented: {len(rfm):,}")
print(f"Transactions analysed: {len(df):,}")


# %% 8. Quick charts (screenshots for your README)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

summary.sort_values("Customers").plot.barh(
    x="Segment", y="Customers", ax=axes[0], legend=False, color="#4C72B0"
)
axes[0].set_title("Customers per segment")

summary.sort_values("Total_Revenue").plot.barh(
    x="Segment", y="Total_Revenue", ax=axes[1], legend=False, color="#55A868"
)
axes[1].set_title("Revenue per segment")

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/segment_charts.png", dpi=150)
plt.close()   # close instead of show() so the script keeps running to the CSV export


# %% 9. Export for Power BI
df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

monthly = df.groupby("Month").agg(
    Revenue=("TotalPrice", "sum"),
    Orders=("Invoice", "nunique"),
    Customers=("Customer ID", "nunique"),
).reset_index()

country = df.groupby("Country").agg(
    Revenue=("TotalPrice", "sum"),
    Customers=("Customer ID", "nunique"),
).reset_index().sort_values("Revenue", ascending=False)

# Add each customer's country so Power BI can filter segments by country
cust_country = df.groupby("Customer ID")["Country"].agg(lambda x: x.mode().iloc[0]).reset_index()
rfm_export = rfm.merge(cust_country, on="Customer ID", how="left")

rfm_export.to_csv(f"{OUT_DIR}/rfm_segments.csv", index=False)
summary.to_csv(f"{OUT_DIR}/segment_summary.csv", index=False)
monthly.to_csv(f"{OUT_DIR}/monthly_revenue.csv", index=False)
country.to_csv(f"{OUT_DIR}/country_revenue.csv", index=False)

print(f"\nSaved 4 CSVs and 1 chart to ./{OUT_DIR}/")

# %% 10. Export high-value at-risk customers for the Make.com alert
alerts = rfm_export[rfm_export["Segment"].isin(["At Risk", "Cant Lose Them"])]
alerts = alerts.sort_values("Monetary", ascending=False).head(50)
alerts.to_csv(f"{OUT_DIR}/at_risk_alerts.csv", index=False)
print(f"Saved {len(alerts)} alert customers")