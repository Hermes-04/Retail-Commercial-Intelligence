import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/processed/commercial_product_scope.csv")
OUTPUT_FILE = Path("data/processed/product_anomaly_audit.csv")

print("=" * 70)
print("PRODUCT ANOMALY & COMMERCIAL VALIDATION AUDIT")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

# ------------------------------------------------------------
# 1. NORMALISE NUMERIC FIELDS
# ------------------------------------------------------------

numeric_columns = [
    "NetRevenue",
    "GrossRevenue",
    "UnitsSold",
    "Orders",
    "ReturnValueRate"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)

df["Description"] = (
    df["Description"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# Only analyse products already inside the commercial universe
commercial = df[
    df["IsCommercialMerchandise"] == True
].copy()

# ------------------------------------------------------------
# 2. DERIVED COMMERCIAL METRICS
# ------------------------------------------------------------

commercial["RevenuePerOrder"] = np.where(
    commercial["Orders"] > 0,
    commercial["NetRevenue"] / commercial["Orders"],
    0
)

commercial["RevenuePerUnit"] = np.where(
    commercial["UnitsSold"] > 0,
    commercial["NetRevenue"] / commercial["UnitsSold"],
    0
)

commercial["ReturnValueRate"] = (
    commercial["ReturnValueRate"]
    .clip(lower=0)
)

# ------------------------------------------------------------
# 3. DESCRIPTION ANOMALIES
# ------------------------------------------------------------

suspicious_keywords = [
    "adjust",
    "adjustment",
    "damaged",
    "damage",
    "broken",
    "smashed",
    "wonky",
    "wrongly",
    "reverse",
    "website",
    "quick fix",
    "amazon",
    "cargo",
    "amendment",
    "mailout",
    "thrown away",
    "throw away",
    "unsaleable",
    "destroyed",
    "bad debt",
    "missing"
]

pattern = "|".join(suspicious_keywords)

commercial["DescriptionAnomaly"] = (
    commercial["Description"]
    .str.lower()
    .str.contains(
        pattern,
        regex=True,
        na=False
    )
)

# ------------------------------------------------------------
# 4. RETURN ANOMALIES
# ------------------------------------------------------------

commercial["ReturnAnomaly"] = (
    commercial["ReturnValueRate"] >= 0.30
)

# ------------------------------------------------------------
# 5. HIGH-REVENUE ANOMALIES
# ------------------------------------------------------------

revenue_threshold = commercial["NetRevenue"].quantile(0.95)

commercial["HighRevenueAnomaly"] = (
    (commercial["NetRevenue"] >= revenue_threshold)
    & commercial["DescriptionAnomaly"]
)

# ------------------------------------------------------------
# 6. HIGH VOLUME / LOW VALUE ANOMALIES
# ------------------------------------------------------------

unit_threshold = commercial["UnitsSold"].quantile(0.95)

commercial["HighVolumeLowValueAnomaly"] = (
    (commercial["UnitsSold"] >= unit_threshold)
    & (commercial["NetRevenue"] <= 0)
)

# ------------------------------------------------------------
# 7. EXTREME REVENUE-PER-ORDER ANOMALIES
# ------------------------------------------------------------

rpo_threshold = commercial["RevenuePerOrder"].quantile(0.99)

commercial["ExtremeRevenuePerOrder"] = (
    commercial["RevenuePerOrder"] >= rpo_threshold
)

# ------------------------------------------------------------
# 8. EXTREME REVENUE-PER-UNIT ANOMALIES
# ------------------------------------------------------------

rpu_threshold = commercial["RevenuePerUnit"].quantile(0.99)

commercial["ExtremeRevenuePerUnit"] = (
    commercial["RevenuePerUnit"] >= rpu_threshold
)

# ------------------------------------------------------------
# 9. OVERALL ANOMALY SCORE
# ------------------------------------------------------------

commercial["AnomalyScore"] = (
    commercial["DescriptionAnomaly"].astype(int)
    + commercial["ReturnAnomaly"].astype(int)
    + commercial["HighRevenueAnomaly"].astype(int)
    + commercial["HighVolumeLowValueAnomaly"].astype(int)
    + commercial["ExtremeRevenuePerOrder"].astype(int)
    + commercial["ExtremeRevenuePerUnit"].astype(int)
)

# ------------------------------------------------------------
# 10. ANOMALY CLASSIFICATION
# ------------------------------------------------------------

commercial["AnomalySeverity"] = np.select(

    [
        commercial["AnomalyScore"] >= 3,
        commercial["AnomalyScore"] == 2,
        commercial["AnomalyScore"] == 1
    ],

    [
        "Critical Review",
        "High Review",
        "Monitor"
    ],

    default="Normal"
)

# ------------------------------------------------------------
# 11. RECOMMENDED ACTION
# ------------------------------------------------------------

commercial["RecommendedAction"] = np.select(

    [
        commercial["AnomalySeverity"] == "Critical Review",
        commercial["AnomalySeverity"] == "High Review",
        commercial["DescriptionAnomaly"],
        commercial["ReturnAnomaly"]
    ],

    [
        "Validate product master and transaction history",
        "Investigate before executive reporting",
        "Validate product description / SKU mapping",
        "Investigate return behaviour"
    ],

    default="No immediate action"
)

# ------------------------------------------------------------
# 12. SORT BY BUSINESS IMPORTANCE
# ------------------------------------------------------------

commercial = commercial.sort_values(
    [
        "AnomalyScore",
        "NetRevenue"
    ],
    ascending=[
        False,
        False
    ]
)

# ------------------------------------------------------------
# 13. SAVE
# ------------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

commercial.to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# 14. EXECUTIVE SUMMARY
# ------------------------------------------------------------

print()
print("ANOMALY SUMMARY")
print("-" * 70)

print(
    commercial["AnomalySeverity"]
    .value_counts()
    .to_string()
)

print()
print(
    f"Commercial products audited: "
    f"{len(commercial):,}"
)

print(
    f"Products requiring investigation: "
    f"{(commercial['AnomalyScore'] > 0).sum():,}"
)

print()
print("ANOMALY TYPES")
print("-" * 70)

print(
    f"Description anomalies: "
    f"{commercial['DescriptionAnomaly'].sum():,}"
)

print(
    f"High return anomalies: "
    f"{commercial['ReturnAnomaly'].sum():,}"
)

print(
    f"High-revenue description anomalies: "
    f"{commercial['HighRevenueAnomaly'].sum():,}"
)

print(
    f"High-volume / low-value anomalies: "
    f"{commercial['HighVolumeLowValueAnomaly'].sum():,}"
)

print(
    f"Extreme revenue/order anomalies: "
    f"{commercial['ExtremeRevenuePerOrder'].sum():,}"
)

print(
    f"Extreme revenue/unit anomalies: "
    f"{commercial['ExtremeRevenuePerUnit'].sum():,}"
)

print()
print("TOP ANOMALIES BY BUSINESS IMPACT")
print("-" * 70)

top_anomalies = commercial[
    commercial["AnomalyScore"] > 0
].head(30)

print(
    top_anomalies[
        [
            "StockCode",
            "Description",
            "NetRevenue",
            "UnitsSold",
            "Orders",
            "ReturnValueRate",
            "RevenuePerOrder",
            "RevenuePerUnit",
            "AnomalyScore",
            "AnomalySeverity",
            "RecommendedAction"
        ]
    ].to_string(index=False)
)

print()
print("=" * 70)
print(f"OUTPUT SAVED: {OUTPUT_FILE}")
print("=" * 70)