import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/processed/product_master.csv")
OUTPUT_FILE = Path("data/processed/commercial_product_scope.csv")

print("=" * 70)
print("COMMERCIAL PRODUCT SCOPE")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

# ------------------------------------------------------------
# 1. IDENTIFY NON-MERCHANDISE PRODUCTS
# ------------------------------------------------------------

# Product master currently contains validated products plus
# operational / incomplete records.
#
# Logistics, postage, fees and adjustments are excluded from
# the executive merchandise universe using StockCode rules.

non_merchandise_codes = {
    "POST",
    "DOT",
    "AMAZONFEE",
    "BANK CHARGES",
    "D",
    "S",
    "M",
    "gift_0001_10",
    "gift_0001_20",
    "gift_0001_30",
    "gift_0001_40",
    "gift_0001_50",
    "gift_0001_60",
    "gift_0001_70",
    "gift_0001_80",
    "gift_0001_90",
    "gift_0001_100",
}

df["StockCode"] = df["StockCode"].astype(str).str.strip()

df["IsNonMerchandise"] = (
    df["StockCode"].isin(non_merchandise_codes)
)

# ------------------------------------------------------------
# 2. EXECUTIVE PRODUCT UNIVERSE
# ------------------------------------------------------------

df["IsCommercialMerchandise"] = (
    (df["ProductMasterStatus"] == "Validated Commercial Product")
    & (~df["IsNonMerchandise"])
)

df["ExecutiveScope"] = df["IsCommercialMerchandise"].map({
    True: "Included",
    False: "Excluded"
})

# ------------------------------------------------------------
# 3. EXCLUSION REASON
# ------------------------------------------------------------

def determine_exclusion(row):

    if row["IsCommercialMerchandise"]:
        return "Included"

    if row["ProductMasterStatus"] == "Operational / Adjustment":
        return "Operational / Adjustment"

    if row["ProductMasterStatus"] == "Master Data Incomplete":
        return "Missing Product Master Data"

    if row["IsNonMerchandise"]:
        return "Non-Merchandise / Logistics / Fee"

    return "Other Review"


df["ScopeReason"] = df.apply(
    determine_exclusion,
    axis=1
)

# ------------------------------------------------------------
# 4. COMMERCIAL PRODUCT DATASET
# ------------------------------------------------------------

commercial = df[
    df["IsCommercialMerchandise"]
].copy()

# ------------------------------------------------------------
# 5. REVENUE METRICS
# ------------------------------------------------------------

total_revenue = commercial["NetRevenue"].sum()

commercial["RevenueShare"] = (
    commercial["NetRevenue"] / total_revenue
)

commercial["RevenueRank"] = (
    commercial["NetRevenue"]
    .rank(
        method="first",
        ascending=False
    )
    .astype(int)
)

# ------------------------------------------------------------
# 6. EXECUTIVE PRODUCT TIERS
# ------------------------------------------------------------

commercial["ExecutiveProductTier"] = pd.cut(
    commercial["NetRevenue"],
    bins=[
        float("-inf"),
        5000,
        25000,
        100000,
        float("inf")
    ],
    labels=[
        "Tier 4 - Long Tail",
        "Tier 3 - Established",
        "Tier 2 - High Value",
        "Tier 1 - Strategic"
    ]
)

# ------------------------------------------------------------
# 7. WRITE METRICS BACK
# ------------------------------------------------------------

df["RevenueShare"] = 0.0
df["RevenueRank"] = 0
df["ExecutiveProductTier"] = "Not Applicable"

df.loc[
    commercial.index,
    "RevenueShare"
] = commercial["RevenueShare"]

df.loc[
    commercial.index,
    "RevenueRank"
] = commercial["RevenueRank"]

df.loc[
    commercial.index,
    "ExecutiveProductTier"
] = (
    commercial["ExecutiveProductTier"]
    .astype(str)
)

# ------------------------------------------------------------
# 8. SORT
# ------------------------------------------------------------

df = df.sort_values(
    [
        "IsCommercialMerchandise",
        "NetRevenue"
    ],
    ascending=[
        False,
        False
    ]
)

# ------------------------------------------------------------
# 9. SAVE
# ------------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# 10. EXECUTIVE SUMMARY
# ------------------------------------------------------------

print()
print("EXECUTIVE PRODUCT SCOPE")
print("-" * 70)

print(
    f"Total product records: "
    f"{len(df):,}"
)

print(
    f"Included commercial merchandise: "
    f"{df['IsCommercialMerchandise'].sum():,}"
)

print(
    f"Excluded records: "
    f"{(~df['IsCommercialMerchandise']).sum():,}"
)

print()
print("SCOPE REASONS")
print("-" * 70)

print(
    df["ScopeReason"]
    .value_counts()
    .to_string()
)

print()
print("COMMERCIAL PRODUCT TIERS")
print("-" * 70)

print(
    commercial["ExecutiveProductTier"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("COMMERCIAL MERCHANDISE KPIs")
print("-" * 70)

print(
    f"Net merchandise revenue: "
    f"£{total_revenue:,.2f}"
)

print(
    f"Units sold: "
    f"{commercial['UnitsSold'].sum():,.0f}"
)

print(
    f"Commercial product universe: "
    f"{len(commercial):,}"
)

print()
print("TOP 20 COMMERCIAL PRODUCTS")
print("-" * 70)

print(
    commercial[
        [
            "RevenueRank",
            "StockCode",
            "Description",
            "NetRevenue",
            "UnitsSold",
            "Orders",
            "RevenueShare",
            "ReturnValueRate",
            "ExecutiveProductTier"
        ]
    ]
    .sort_values("RevenueRank")
    .head(20)
    .to_string(index=False)
)

print()
print("=" * 70)
print(f"OUTPUT SAVED: {OUTPUT_FILE}")
print("=" * 70)