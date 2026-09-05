import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/processed/transactions_clean.csv")
OUTPUT_FILE = Path("data/processed/product_quality.csv")

print("=" * 70)
print("PRODUCT QUALITY & COMMERCIAL VALIDITY ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

# ------------------------------------------------------------
# 1. PRODUCT-LEVEL AGGREGATION
# ------------------------------------------------------------

product = (
    df.groupby("StockCode", dropna=False)
    .agg(
        Description=("Description", "first"),
        GrossRevenue=("LineRevenue", lambda x: x[df.loc[x.index, "IsRevenueEligible"]].sum()),
        NetRevenue=("LineRevenue", "sum"),
        UnitsSold=("Quantity", lambda x: x[df.loc[x.index, "IsRevenueEligible"]].sum()),
        SalesLines=("StockCode", "size"),
        Orders=("InvoiceNo", "nunique"),
        ReturnValue=("LineRevenue", lambda x: x[df.loc[x.index, "IsReturn"]].sum()),
        ReturnedUnits=("Quantity", lambda x: abs(x[df.loc[x.index, "IsReturn"]].sum())),
    )
    .reset_index()
)

# ------------------------------------------------------------
# 2. DESCRIPTION QUALITY FLAGS
# ------------------------------------------------------------

product["Description"] = (
    product["Description"]
    .fillna("")
    .astype(str)
    .str.strip()
)

text = product["Description"].str.lower()

dirty_keywords = [
    "damaged",
    "damage",
    "broken",
    "smashed",
    "wonky",
    "wrongly marked",
    "adjustment",
    "adjustment",
    "reverse",
    "website fixed",
    "quick fix",
    "amazon",
    "cargo order",
    "missing",
    "amendment",
    "thrown away",
    "throw away",
    "unsaleable",
    "destroyed",
    "bad debt",
]

pattern = "|".join(dirty_keywords)

product["DescriptionQualityFlag"] = np.where(
    product["Description"].eq(""),
    "Missing Description",
    np.where(
        text.str.contains(pattern, regex=True, na=False),
        "Operational / Dirty Description",
        "Commercial Description"
    )
)

# ------------------------------------------------------------
# 3. COMMERCIAL VALIDITY
# ------------------------------------------------------------

product["CommercialValidity"] = np.where(
    product["DescriptionQualityFlag"] == "Commercial Description",
    "Valid",
    "Review Required"
)

# ------------------------------------------------------------
# 4. RETURN RISK
# ------------------------------------------------------------

product["ReturnValueRate"] = np.where(
    product["GrossRevenue"] > 0,
    abs(product["ReturnValue"]) / product["GrossRevenue"],
    np.nan
)

product["ReturnValueRate"] = product["ReturnValueRate"].round(4)

product["ReturnRisk"] = pd.cut(
    product["ReturnValueRate"],
    bins=[-np.inf, 0.05, 0.15, 0.30, np.inf],
    labels=[
        "Low",
        "Moderate",
        "High",
        "Very High"
    ]
)

# ------------------------------------------------------------
# 5. COMMERCIAL PERFORMANCE SCORE
# ------------------------------------------------------------

valid_revenue = product.loc[
    product["CommercialValidity"] == "Valid",
    "NetRevenue"
]

revenue_rank = product["NetRevenue"].rank(
    method="average",
    pct=True
)

volume_rank = product["UnitsSold"].rank(
    method="average",
    pct=True
)

product["CommercialPerformanceScore"] = (
    0.70 * revenue_rank +
    0.30 * volume_rank
).round(4)

# ------------------------------------------------------------
# 6. STRATEGIC PRODUCT CLASSIFICATION
# ------------------------------------------------------------

conditions = [
    (
        (product["CommercialValidity"] == "Valid") &
        (product["NetRevenue"] > 0) &
        (product["ReturnValueRate"] < 0.05)
    ),

    (
        (product["CommercialValidity"] == "Valid") &
        (product["NetRevenue"] > 0) &
        (product["ReturnValueRate"] >= 0.05) &
        (product["ReturnValueRate"] < 0.15)
    ),

    (
        (product["CommercialValidity"] == "Valid") &
        (product["NetRevenue"] > 0) &
        (product["ReturnValueRate"] >= 0.15)
    ),
]

choices = [
    "Core Commercial Product",
    "Monitor Return Risk",
    "High Return Risk"
]

product["StrategicClassification"] = np.select(
    conditions,
    choices,
    default="Review / Operational"
)

# ------------------------------------------------------------
# 7. SAVE
# ------------------------------------------------------------

product = product.sort_values(
    "NetRevenue",
    ascending=False
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

product.to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# 8. EXECUTIVE SUMMARY
# ------------------------------------------------------------

print()
print("PRODUCT QUALITY SUMMARY")
print("-" * 70)

print(
    f"Total products analysed: "
    f"{len(product):,}"
)

print(
    f"Commercially valid products: "
    f"{(product['CommercialValidity'] == 'Valid').sum():,}"
)

print(
    f"Products requiring review: "
    f"{(product['CommercialValidity'] == 'Review Required').sum():,}"
)

print()
print("DESCRIPTION QUALITY")
print("-" * 70)

print(
    product["DescriptionQualityFlag"]
    .value_counts()
    .to_string()
)

print()
print("STRATEGIC CLASSIFICATION")
print("-" * 70)

print(
    product["StrategicClassification"]
    .value_counts()
    .to_string()
)

print()
print("TOP PRODUCTS REQUIRING REVIEW")
print("-" * 70)

review = product[
    product["CommercialValidity"] == "Review Required"
].head(15)

print(
    review[
        [
            "StockCode",
            "Description",
            "NetRevenue",
            "UnitsSold",
            "DescriptionQualityFlag"
        ]
    ].to_string(index=False)
)

print()
print("=" * 70)
print(f"OUTPUT SAVED: {OUTPUT_FILE}")
print("=" * 70)