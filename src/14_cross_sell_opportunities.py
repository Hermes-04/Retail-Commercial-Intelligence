import pandas as pd
from pathlib import Path

print("=" * 70)
print("EXECUTIVE CROSS-SELL OPPORTUNITY ANALYSIS")
print("=" * 70)

INPUT = Path("data/processed/product_associations.csv")
OUTPUT = Path("data/processed/executive_cross_sell_opportunities.csv")

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# 1. Remove statistically interesting but commercially weak
#    associations
# ---------------------------------------------------------

df = df[
    (df["PairOrders"] >= 50) &
    (df["Lift"] >= 10) &
    (df["Confidence_A_to_B"] >= 0.60)
].copy()

# ---------------------------------------------------------
# 2. Classify association type
# ---------------------------------------------------------

def classify_association(row):
    a = str(row["ProductA_Description"]).upper()
    b = str(row["ProductB_Description"]).upper()

    complementary_pairs = [
        ("BICYCLE", "PUNCTURE"),
        ("PUNCTURE", "BICYCLE"),
        ("FORK", "TROWEL"),
        ("TROWEL", "FORK"),
        ("CUP", "PLATE"),
        ("PLATE", "CUP"),
        ("FRAME", "FRAME"),
    ]

    for x, y in complementary_pairs:
        if x in a and y in b:
            return "Complementary Cross-Sell"

    coordinated_terms = [
        "CUP", "PLATE", "BOWL", "JUG",
        "TEACUP", "TEA PLATE",
        "TROWEL", "FORK", "CUTLERY"
    ]

    if any(term in a for term in coordinated_terms) and any(
        term in b for term in coordinated_terms
    ):
        return "Coordinated Set"

    # Detect obvious same-family / variant relationships
    family_keywords = [
        "JUMBO BAG",
        "LUNCH BAG",
        "CHILDRENS",
        "KIDS",
        "HERB MARKER",
        "EGG COSY",
        "RAIN MAC",
        "TEA PLATE",
        "TEACUP",
        "CHARLOTTE BAG"
    ]

    if any(term in a for term in family_keywords) and any(
        term in b for term in family_keywords
    ):
        return "Variant / Product Family"

    return "Cross-Sell"


df["AssociationType"] = df.apply(classify_association, axis=1)

# ---------------------------------------------------------
# 3. Executive ranking score
#
# Balance:
#   - order volume
#   - lift
#   - confidence
#
# Log transformation prevents extremely high lift from
# overwhelming commercially scalable relationships.
# ---------------------------------------------------------

import numpy as np

df["ExecutiveScore"] = (
    np.log1p(df["PairOrders"])
    * np.log1p(df["Lift"])
    * df["Confidence_A_to_B"]
)

# Strategic weighting by business type
type_multiplier = {
    "Complementary Cross-Sell": 1.35,
    "Coordinated Set": 1.20,
    "Cross-Sell": 1.00,
    "Variant / Product Family": 0.75
}

df["ExecutiveScore"] = (
    df["ExecutiveScore"]
    * df["AssociationType"].map(type_multiplier)
)

# ---------------------------------------------------------
# 4. Remove variant-heavy associations from the executive
#    recommendation layer
# ---------------------------------------------------------

executive = df[
    df["AssociationType"] != "Variant / Product Family"
].copy()

# ---------------------------------------------------------
# 5. Business opportunity classification
# ---------------------------------------------------------

def opportunity_type(row):
    if row["AssociationType"] == "Complementary Cross-Sell":
        return "Accessory / Complementary Recommendation"

    if row["AssociationType"] == "Coordinated Set":
        return "Bundle / Set Recommendation"

    return "Cross-Sell Recommendation"


executive["CommercialAction"] = executive.apply(
    opportunity_type,
    axis=1
)

# ---------------------------------------------------------
# 6. Rank
# ---------------------------------------------------------

executive = executive.sort_values(
    ["ExecutiveScore", "PairOrders", "Lift"],
    ascending=[False, False, False]
).reset_index(drop=True)

executive["ExecutiveRank"] = range(1, len(executive) + 1)

# ---------------------------------------------------------
# 7. Business recommendation
# ---------------------------------------------------------

def recommendation(row):

    if row["AssociationType"] == "Complementary Cross-Sell":
        return (
            "Use as a targeted accessory recommendation "
            "or checkout cross-sell."
        )

    if row["AssociationType"] == "Coordinated Set":
        return (
            "Evaluate bundled merchandising, coordinated "
            "product placement, or multi-item offers."
        )

    return (
        "Use as a personalized recommendation based "
        "on basket composition."
    )


executive["BusinessRecommendation"] = executive.apply(
    recommendation,
    axis=1
)

# ---------------------------------------------------------
# 8. Keep the executive output focused
# ---------------------------------------------------------

columns = [
    "ExecutiveRank",
    "ProductA",
    "ProductA_Description",
    "ProductB",
    "ProductB_Description",
    "AssociationType",
    "CommercialAction",
    "PairOrders",
    "Support",
    "Confidence_A_to_B",
    "Confidence_B_to_A",
    "Lift",
    "ExecutiveScore",
    "BusinessRecommendation"
]

executive = executive[columns]

# Top 50 only
executive_top50 = executive.head(50).copy()

# ---------------------------------------------------------
# 9. Save
# ---------------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
executive_top50.to_csv(OUTPUT, index=False)

# ---------------------------------------------------------
# 10. Executive output
# ---------------------------------------------------------

print()
print("TOP 50 EXECUTIVE CROSS-SELL OPPORTUNITIES")
print("-" * 70)

print(
    executive_top50[
        [
            "ExecutiveRank",
            "ProductA_Description",
            "ProductB_Description",
            "AssociationType",
            "PairOrders",
            "Confidence_A_to_B",
            "Lift"
        ]
    ].head(25).to_string(index=False)
)

print()
print("OPPORTUNITY TYPE DISTRIBUTION")
print("-" * 70)

print(
    executive_top50["AssociationType"]
    .value_counts()
    .to_string()
)

print()
print("COMMERCIAL ACTION DISTRIBUTION")
print("-" * 70)

print(
    executive_top50["CommercialAction"]
    .value_counts()
    .to_string()
)

print()
print(f"Filtered associations: {len(df):,}")
print(f"Executive opportunities: {len(executive):,}")
print(f"Top opportunities exported: {len(executive_top50):,}")
print(f"Output saved to: {OUTPUT}")

print()
print("=" * 70)
print("EXECUTIVE CROSS-SELL ANALYSIS COMPLETE")
print("=" * 70)