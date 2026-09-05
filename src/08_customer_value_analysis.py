from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
RFM_FILE = Path("data/processed/customer_rfm.csv")
OUTPUT_FILE = Path("data/processed/customer_value_analysis.csv")


def main():
    print("=" * 70)
    print("CUSTOMER COMMERCIAL VALUE ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["InvoiceDate"]
    )

    rfm = pd.read_csv(RFM_FILE)

    # Customer-level sales
    sales = df[
        (df["IsRevenueEligible"] == True)
        & (df["CustomerID"].notna())
    ].copy()

    sales_value = (
        sales.groupby("CustomerID")
        .agg(
            GrossRevenue=("LineRevenue", "sum"),
            SalesOrders=("InvoiceNo", "nunique"),
            UnitsSold=("Quantity", "sum"),
        )
    )

    # Customer-level returns
    returns = df[
        (df["IsReturn"] == True)
        & (df["CustomerID"].notna())
    ].copy()

    return_value = (
        returns.groupby("CustomerID")
        .agg(
            ReturnValue=("LineRevenue", "sum"),
            ReturnOrders=("InvoiceNo", "nunique"),
            ReturnedUnits=("Quantity", lambda x: abs(x.sum())),
        )
    )

    # Combine
    customer_value = (
        sales_value
        .join(return_value, how="left")
        .fillna(0)
        .reset_index()
    )

    customer_value["NetRevenue"] = (
        customer_value["GrossRevenue"]
        + customer_value["ReturnValue"]
    )

    customer_value["ReturnRate"] = (
        customer_value["ReturnOrders"]
        / customer_value["SalesOrders"]
    )

    customer_value["ReturnValueRate"] = (
        abs(customer_value["ReturnValue"])
        / customer_value["GrossRevenue"]
    )

    # Merge RFM
    customer_value = customer_value.merge(
        rfm[
            [
                "CustomerID",
                "Recency",
                "Frequency",
                "Monetary",
                "Segment",
                "CustomerLifetimeDays",
                "AverageOrderValue",
            ]
        ],
        on="CustomerID",
        how="left",
    )

    # Revenue concentration
    customer_value = customer_value.sort_values(
        "NetRevenue",
        ascending=False
    ).reset_index(drop=True)

    total_net_revenue = customer_value["NetRevenue"].sum()

    customer_value["CumulativeNetRevenue"] = (
        customer_value["NetRevenue"].cumsum()
    )

    customer_value["CumulativeRevenuePct"] = (
        customer_value["CumulativeNetRevenue"]
        / total_net_revenue
        * 100
    )

    customer_value["RevenueRank"] = (
        customer_value.index + 1
    )

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    customer_value.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nCUSTOMER VALUE SUMMARY")
    print("-" * 70)

    print(f"Customers analyzed: {len(customer_value):,}")

    print(
        f"Gross revenue: "
        f"£{customer_value['GrossRevenue'].sum():,.2f}"
    )

    print(
        f"Returns: "
        f"£{customer_value['ReturnValue'].sum():,.2f}"
    )

    print(
        f"Net revenue: "
        f"£{customer_value['NetRevenue'].sum():,.2f}"
    )

    print("\nTop 15 customers by NET revenue:")

    print(
        customer_value[
            [
                "CustomerID",
                "GrossRevenue",
                "ReturnValue",
                "NetRevenue",
                "ReturnValueRate",
                "Segment",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    print("\nREVENUE CONCENTRATION")
    print("-" * 70)

    for pct in [1, 5, 10, 20]:
        n = max(
            1,
            int(len(customer_value) * pct / 100)
        )

        revenue_share = (
            customer_value.head(n)["NetRevenue"].sum()
            / total_net_revenue
            * 100
        )

        print(
            f"Top {pct:>2}% of customers: "
            f"{revenue_share:6.2f}% of net revenue"
        )

    print("\nHIGH-VALUE CUSTOMER RISK")
    print("-" * 70)

    high_value_risk = customer_value[
        customer_value["Segment"] == "At Risk High Value"
    ]

    print(
        f"At Risk High Value customers: "
        f"{len(high_value_risk):,}"
    )

    print(
        f"At Risk High Value net revenue: "
        f"£{high_value_risk['NetRevenue'].sum():,.2f}"
    )

    print(
        f"Average At Risk High Value revenue: "
        f"£{high_value_risk['NetRevenue'].mean():,.2f}"
    )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("CUSTOMER VALUE ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()