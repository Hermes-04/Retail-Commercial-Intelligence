from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
OUTPUT_FILE = Path("data/processed/customer_rfm.csv")


def main():
    print("=" * 70)
    print("CUSTOMER RFM ANALYSIS")
    print("=" * 70)

    print("\nLoading cleaned transaction data...")

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["InvoiceDate"]
    )

    # Only identified customers and genuine commercial sales.
    sales = df[
        (df["IsRevenueEligible"] == True)
        & (df["CustomerID"].notna())
    ].copy()

    print(f"Revenue-eligible rows: {len(sales):,}")
    print(f"Unique customers: {sales['CustomerID'].nunique():,}")

    # Observation date = day after the latest observed transaction.
    observation_date = (
        sales["InvoiceDate"].max().normalize()
        + pd.Timedelta(days=1)
    )

    print(f"\nObservation date: {observation_date.date()}")

    # Customer-level aggregation.
    rfm = (
        sales.groupby("CustomerID")
        .agg(
            Recency=(
                "InvoiceDate",
                lambda x: (
                    observation_date - x.max().normalize()
                ).days,
            ),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("LineRevenue", "sum"),
            TotalUnits=("Quantity", "sum"),
            FirstPurchase=("InvoiceDate", "min"),
            LastPurchase=("InvoiceDate", "max"),
        )
        .reset_index()
    )

    # Customer lifetime in days.
    rfm["CustomerLifetimeDays"] = (
        rfm["LastPurchase"].dt.normalize()
        - rfm["FirstPurchase"].dt.normalize()
    ).dt.days

    # Average order value.
    rfm["AverageOrderValue"] = (
        rfm["Monetary"] / rfm["Frequency"]
    )

    # RFM scores.
    # Recency: lower is better.
    rfm["R_Score"] = pd.qcut(
        rfm["Recency"],
        5,
        labels=[5, 4, 3, 2, 1],
        duplicates="drop",
    )

    # Frequency: higher is better.
    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
    )

    # Monetary: higher is better.
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5],
    )

    rfm["R_Score"] = rfm["R_Score"].astype(int)
    rfm["F_Score"] = rfm["F_Score"].astype(int)
    rfm["M_Score"] = rfm["M_Score"].astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )

    rfm["RFM_Total"] = (
        rfm["R_Score"]
        + rfm["F_Score"]
        + rfm["M_Score"]
    )

    # Business-oriented segmentation.
    def segment(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"

        if r >= 4 and f >= 3:
            return "Loyal Customers"

        if r >= 4 and f <= 2:
            return "New / Promising"

        if r == 3 and f >= 3:
            return "Potential Loyalists"

        if r <= 2 and f >= 4 and m >= 4:
            return "At Risk High Value"

        if r <= 2 and f >= 3:
            return "At Risk"

        if r <= 2 and f <= 2:
            return "Hibernating"

        return "Needs Attention"

    rfm["Segment"] = rfm.apply(segment, axis=1)

    # Save.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    rfm.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("RFM SUMMARY")
    print("=" * 70)

    print(f"\nCustomers analyzed: {len(rfm):,}")

    print("\nSegment distribution:")
    print(
        rfm["Segment"]
        .value_counts()
        .to_string()
    )

    print("\nSegment revenue:")
    segment_revenue = (
        rfm.groupby("Segment")["Monetary"]
        .sum()
        .sort_values(ascending=False)
    )

    print(segment_revenue.to_string())

    print("\nTop 15 customers by monetary value:")
    print(
        rfm[
            [
                "CustomerID",
                "Recency",
                "Frequency",
                "Monetary",
                "AverageOrderValue",
                "Segment",
            ]
        ]
        .sort_values("Monetary", ascending=False)
        .head(15)
        .to_string(index=False)
    )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("RFM ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
