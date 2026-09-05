from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
OUTPUT_COHORT = Path("data/processed/customer_cohort_retention.csv")


def main():
    print("=" * 70)
    print("CUSTOMER COHORT & RETENTION ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["InvoiceDate"]
    )

    # Only genuine sales with identified customers.
    sales = df[
        (df["IsRevenueEligible"] == True)
        & (df["CustomerID"].notna())
    ].copy()

    sales["CustomerID"] = sales["CustomerID"].astype(int)

    # Month of each transaction.
    sales["PurchaseMonth"] = (
        sales["InvoiceDate"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # First purchase month = customer cohort.
    first_purchase = (
        sales.groupby("CustomerID")["PurchaseMonth"]
        .min()
        .rename("CohortMonth")
    )

    sales = sales.merge(
        first_purchase,
        on="CustomerID",
        how="left"
    )

    # Months since acquisition.
    sales["CohortIndex"] = (
        (
            sales["PurchaseMonth"].dt.year
            - sales["CohortMonth"].dt.year
        ) * 12
        + (
            sales["PurchaseMonth"].dt.month
            - sales["CohortMonth"].dt.month
        )
        + 1
    )

    # Number of unique active customers.
    cohort_counts = (
        sales.groupby(
            ["CohortMonth", "CohortIndex"]
        )["CustomerID"]
        .nunique()
        .reset_index(name="ActiveCustomers")
    )

    # Initial cohort size.
    cohort_size = (
        cohort_counts[
            cohort_counts["CohortIndex"] == 1
        ][
            ["CohortMonth", "ActiveCustomers"]
        ]
        .rename(
            columns={
                "ActiveCustomers": "CohortSize"
            }
        )
    )

    cohort_counts = cohort_counts.merge(
        cohort_size,
        on="CohortMonth",
        how="left"
    )

    cohort_counts["RetentionRate"] = (
        cohort_counts["ActiveCustomers"]
        / cohort_counts["CohortSize"]
        * 100
    )

    # Revenue by cohort/month.
    cohort_revenue = (
        sales.groupby(
            ["CohortMonth", "CohortIndex"]
        )["LineRevenue"]
        .sum()
        .reset_index(name="Revenue")
    )

    cohort = cohort_counts.merge(
        cohort_revenue,
        on=["CohortMonth", "CohortIndex"],
        how="left"
    )

    cohort = cohort.sort_values(
        ["CohortMonth", "CohortIndex"]
    )

    OUTPUT_COHORT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cohort.to_csv(
        OUTPUT_COHORT,
        index=False,
        encoding="utf-8-sig"
    )

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    print("\nCOHORT OVERVIEW")
    print("-" * 70)

    overview = (
        cohort[cohort["CohortIndex"] == 1]
        [
            [
                "CohortMonth",
                "CohortSize",
                "Revenue",
            ]
        ]
        .copy()
    )

    print(overview.to_string(index=False))

    print("\nRETENTION AT KEY LIFECYCLE MONTHS")
    print("-" * 70)

    for month in [1, 2, 3, 6, 12]:
        subset = cohort[
            cohort["CohortIndex"] == month
        ]

        if len(subset) == 0:
            continue

        weighted_retention = (
            subset["ActiveCustomers"].sum()
            / subset["CohortSize"].sum()
            * 100
        )

        print(
            f"Month {month:>2}: "
            f"{weighted_retention:6.2f}%"
        )

    print("\nBEST COHORTS BY 3-MONTH RETENTION")
    print("-" * 70)

    month_3 = cohort[
        cohort["CohortIndex"] == 3
    ].sort_values(
        "RetentionRate",
        ascending=False
    )

    print(
        month_3[
            [
                "CohortMonth",
                "CohortSize",
                "ActiveCustomers",
                "RetentionRate",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nLOWEST COHORTS BY 3-MONTH RETENTION")
    print("-" * 70)

    print(
        month_3[
            [
                "CohortMonth",
                "CohortSize",
                "ActiveCustomers",
                "RetentionRate",
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    print(f"\nSaved to: {OUTPUT_COHORT}")

    print("\n" + "=" * 70)
    print("COHORT RETENTION ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()