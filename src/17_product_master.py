import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/processed/product_quality.csv")
OUTPUT_FILE = Path("data/processed/product_master.csv")

print("=" * 70)
print("VALIDATED PRODUCT MASTER")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

# ------------------------------------------------------------
# 1. NORMALISE FIELDS
# ------------------------------------------------------------

df["Description"] = (
    df["Description"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["NetRevenue"] = pd.to_numeric(
    df["NetRevenue"],
    errors="coerce"
).fillna(0)

df["GrossRevenue"] = pd.to_numeric(
    df["GrossRevenue"],
    errors="coerce"
).fillna(0)

df["UnitsSold"] = pd.to_numeric(
    df["UnitsSold"],
    errors="coerce"
).fillna(0)

df["Orders"] = pd.to_numeric(
    df["Orders"],
    errors="coerce"
).fillna(0)

df["ReturnValueRate"] = pd.to_numeric(
    df["ReturnValueRate"],
    errors="coerce"
).fillna(0)

# ------------------------------------------------------------
# 2. DATA QUALITY CLASSIFICATION
# ------------------------------------------------------------

operational_pattern = (
    r"adjust|damaged|damage|broken|smashed|wonky|"
    r"wrongly marked|reverse|website fixed|quick fix|"
    r"amazon|cargo order|amendment|thrown away|throw away|"
    r"unsaleable|destroyed|bad debt"
)

df["IsOperationalRecord"] = (
    df["Description"]
    .str.lower()
    .str.contains(
        operational_pattern,
        regex=True,
        na=False
    )
)

df["IsMissingDescription"] = (
    df["Description"].eq("")
)

# ------------------------------------------------------------
# 3. COMMERCIAL ACTIVITY
# ------------------------------------------------------------

df["HasCommercialActivity"] = (
    (df["GrossRevenue"] > 0) |
    (df["UnitsSold"] > 0) |
    (df["Orders"] > 0)
)

# ------------------------------------------------------------
# 4. PRODUCT MASTER STATUS
# ------------------------------------------------------------

conditions = [

    # Operational records
    df["IsOperationalRecord"],

    # Missing product master data
    (
        df["IsMissingDescription"] &
        ~df["HasCommercialActivity"]
    ),

    # Missing description but commercially active
    (
        df["IsMissingDescription"] &
        df["HasCommercialActivity"]
    ),

    # No commercial activity
    (
        ~df["HasCommercialActivity"]
    ),

    # Valid active product
    (
        ~df["IsOperationalRecord"] &
        ~df["IsMissingDescription"] &
        df["HasCommercialActivity"]
    )
]

choices = [
    "Operational / Adjustment",
    "Inactive / Unmapped",
    "Master Data Incomplete",
    "Inactive / No Activity",
    "Validated Commercial Product"
]

df["ProductMasterStatus"] = np.select(
    conditions,
    choices,
    default="Review Required"
)

# ------------------------------------------------------------
# 5. COMMERCIAL PRIORITY
# ------------------------------------------------------------

df["CommercialPriority"] = np.select(

    [
        df["ProductMasterStatus"]
        .eq("Validated Commercial Product") &
        (df["NetRevenue"] > 100000),

        df["ProductMasterStatus"]
        .eq("Validated Commercial Product") &
        (df["NetRevenue"] > 25000),

        df["ProductMasterStatus"]
        .eq("Validated Commercial Product") &
        (df["NetRevenue"] > 5000),

        df["ProductMasterStatus"]
        .eq("Validated Commercial Product")
    ],

    [
        "Tier 1 - Strategic",
        "Tier 2 - High Value",
        "Tier 3 - Established",
        "Tier 4 - Long Tail"
    ],

    default="Not Applicable"
)

# ------------------------------------------------------------
# 6. RETURN RISK FLAG
# ------------------------------------------------------------

df["ReturnRiskFlag"] = np.select(

    [
        (
            df["ProductMasterStatus"]
            .eq("Validated Commercial Product") &
            (df["ReturnValueRate"] >= 0.30)
        ),

        (
            df["ProductMasterStatus"]
            .eq("Validated Commercial Product") &
            (df["ReturnValueRate"] >= 0.15)
        ),

        (
            df["ProductMasterStatus"]
            .eq("Validated Commercial Product") &
            (df["ReturnValueRate"] >= 0.05)
        )
    ],

    [
        "Critical",
        "High",
        "Moderate"
    ],

    default="Low / Not Applicable"
)

# ------------------------------------------------------------
# 7. FINAL ANALYTICAL FLAG
# ------------------------------------------------------------

df["IncludeInExecutiveAnalytics"] = (
    df["ProductMasterStatus"]
    .eq("Validated Commercial Product")
)

# ------------------------------------------------------------
# 8. SORT
# ------------------------------------------------------------

df = df.sort_values(
    ["IncludeInExecutiveAnalytics", "NetRevenue"],
    ascending=[False, False]
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
print("PRODUCT MASTER STATUS")
print("-" * 70)

print(
    df["ProductMasterStatus"]
    .value_counts()
    .to_string()
)

print()
print("COMMERCIAL PRIORITY")
print("-" * 70)

print(
    df["CommercialPriority"]
    .value_counts()
    .to_string()
)

print()
print("RETURN RISK")
print("-" * 70)

print(
    df["ReturnRiskFlag"]
    .value_counts()
    .to_string()
)

print()
print("EXECUTIVE ANALYTICS ELIGIBILITY")
print("-" * 70)

print(
    df["IncludeInExecutiveAnalytics"]
    .value_counts()
    .to_string()
)

print()
print("TOP VALIDATED COMMERCIAL PRODUCTS")
print("-" * 70)

top_products = df[
    df["IncludeInExecutiveAnalytics"]
].head(20)

print(
    top_products[
        [
            "StockCode",
            "Description",
            "NetRevenue",
            "UnitsSold",
            "Orders",
            "ReturnValueRate",
            "CommercialPriority",
            "ReturnRiskFlag"
        ]
    ].to_string(index=False)
)

print()
print("=" * 70)
print(f"OUTPUT SAVED: {OUTPUT_FILE}")
print("=" * 70)