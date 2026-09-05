from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/customer_value_analysis.csv")
OUTPUT_FILE = Path("data/processed/customer_risk_analysis.csv")


def main():
    print("=" * 70)
    print("CUSTOMER VALUE & RETURN RISK ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    print(f"\nCustomers analyzed: {len(df):,}")

    # ------------------------------------------------------------
    # Commercial value tiers
    # ------------------------------------------------------------

    df["ValueTier"] = pd.qcut(
        df["NetRevenue"].rank(method="first"),
        4,
        labels=[
            "Low Value",
            "Mid Value",
            "High Value",
            "Very High Value",
        ],
    )

    # ------------------------------------------------------------
    # Return-risk tiers
    # ------------------------------------------------------------

    def return_risk(rate):
        if rate == 0:
            return "No Returns"
        elif rate < 0.05:
            return "Low Return Risk"
        elif rate < 0.15:
            return "Moderate Return Risk"
        elif rate < 0.30:
            return "High Return Risk"
        else:
            return "Very High Return Risk"

    df["ReturnRisk"] = df["ReturnValueRate"].apply(return_risk)

    # ------------------------------------------------------------
    # Strategic customer classification
    # ------------------------------------------------------------

    def strategic_class(row):
        value = row["ValueTier"]
        risk = row["ReturnRisk"]

        if value == "Very High Value" and risk in [
            "High Return Risk",
            "Very High Return Risk",
        ]:
            return "High Value / High Return Risk"

        if value == "Very High Value":
            return "Strategic High Value"

        if value == "High Value" and risk in [
            "High Return Risk",
            "Very High Return Risk",
        ]:
            return "High Value / Return Risk"

        if risk == "Very High Return Risk":
            return "Severe Return Risk"

        return "Standard"

    df["StrategicClass"] = df.apply(
        strategic_class,
        axis=1,
    )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    print("\nVALUE TIER DISTRIBUTION")
    print("-" * 70)

    print(
        df["ValueTier"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nRETURN RISK DISTRIBUTION")
    print("-" * 70)

    print(
        df["ReturnRisk"]
        .value_counts()
        .to_string()
    )

    print("\nSTRATEGIC CUSTOMER CLASSIFICATION")
    print("-" * 70)

    strategic = (
        df.groupby("StrategicClass")
        .agg(
            Customers=("CustomerID", "count"),
            NetRevenue=("NetRevenue", "sum"),
            GrossRevenue=("GrossRevenue", "sum"),
            ReturnValue=("ReturnValue", "sum"),
        )
        .sort_values("NetRevenue", ascending=False)
    )

    strategic["RevenueShare"] = (
        strategic["NetRevenue"]
        / df["NetRevenue"].sum()
        * 100
    )

    print(strategic.to_string())

    print("\nTOP 20 CUSTOMERS BY RETURN VALUE")
    print("-" * 70)

    print(
        df[
            [
                "CustomerID",
                "GrossRevenue",
                "ReturnValue",
                "NetRevenue",
                "ReturnValueRate",
                "ValueTier",
                "ReturnRisk",
                "StrategicClass",
            ]
        ]
        .sort_values("ReturnValue")
        .head(20)
        .to_string(index=False)
    )

    print("\nHIGH VALUE / HIGH RETURN RISK CUSTOMERS")
    print("-" * 70)

    high_risk = df[
        df["StrategicClass"]
        == "High Value / High Return Risk"
    ].sort_values(
        "NetRevenue",
        ascending=False,
    )

    print(f"Customers: {len(high_risk):,}")

    print(
        f"Net revenue: "
        f"£{high_risk['NetRevenue'].sum():,.2f}"
    )

    print(
        high_risk[
            [
                "CustomerID",
                "NetRevenue",
                "ReturnValue",
                "ReturnValueRate",
                "Segment",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("CUSTOMER RISK ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()