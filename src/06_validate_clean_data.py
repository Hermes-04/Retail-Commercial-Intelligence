from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")


def main():
    print("=" * 70)
    print("CLEAN TRANSACTION DATA — VALIDATION")
    print("=" * 70)

    print("\nLoading processed dataset...")

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["InvoiceDate"]
    )

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\n" + "-" * 70)
    print("1. DUPLICATE VALIDATION")
    print("-" * 70)

    duplicates = df.duplicated().sum()

    print(f"Duplicate rows: {duplicates:,}")

    print("\n" + "-" * 70)
    print("2. TRANSACTION TYPE VALIDATION")
    print("-" * 70)

    print(df["TransactionType"].value_counts().to_string())

    print("\n" + "-" * 70)
    print("3. REVENUE ELIGIBILITY VALIDATION")
    print("-" * 70)

    revenue_rows = df[df["IsRevenueEligible"]]

    invalid_revenue = revenue_rows[
        (revenue_rows["Quantity"] <= 0)
        | (revenue_rows["UnitPrice"] <= 0)
    ]

    print(f"Revenue-eligible rows: {len(revenue_rows):,}")
    print(f"Invalid revenue rows:   {len(invalid_revenue):,}")

    print("\n" + "-" * 70)
    print("4. RETURN VALIDATION")
    print("-" * 70)

    returns = df[df["IsReturn"]]

    invalid_returns = returns[
        returns["Quantity"] >= 0
    ]

    print(f"Return rows: {len(returns):,}")
    print(f"Invalid return rows: {len(invalid_returns):,}")

    print("\n" + "-" * 70)
    print("5. ACCOUNTING ADJUSTMENT VALIDATION")
    print("-" * 70)

    accounting = df[
        df["TransactionType"] == "Accounting Adjustment"
    ]

    print(f"Accounting adjustment rows: {len(accounting):,}")
    print(
        f"Included in revenue-eligible rows: "
        f"{accounting['IsRevenueEligible'].sum():,}"
    )

    print("\n" + "-" * 70)
    print("6. PRICE VALIDATION")
    print("-" * 70)

    print(
        f"Negative prices: {(df['UnitPrice'] < 0).sum():,}"
    )

    print(
        f"Zero prices:     {(df['UnitPrice'] == 0).sum():,}"
    )

    print(
        f"Positive prices: {(df['UnitPrice'] > 0).sum():,}"
    )

    print("\n" + "-" * 70)
    print("7. QUANTITY VALIDATION")
    print("-" * 70)

    print(
        f"Negative quantities: {(df['Quantity'] < 0).sum():,}"
    )

    print(
        f"Zero quantities:     {(df['Quantity'] == 0).sum():,}"
    )

    print(
        f"Positive quantities: {(df['Quantity'] > 0).sum():,}"
    )

    print("\n" + "-" * 70)
    print("8. CUSTOMER ID VALIDATION")
    print("-" * 70)

    print(
        f"Customer IDs present: "
        f"{df['CustomerID'].notna().sum():,}"
    )

    print(
        f"Customer IDs missing: "
        f"{df['CustomerID'].isna().sum():,}"
    )

    print(
        f"Unique customers: "
        f"{df['CustomerID'].nunique():,}"
    )

    print("\n" + "-" * 70)
    print("9. DATE VALIDATION")
    print("-" * 70)

    print(f"Minimum date: {df['InvoiceDate'].min()}")
    print(f"Maximum date: {df['InvoiceDate'].max()}")
    print(
        f"Missing dates: "
        f"{df['InvoiceDate'].isna().sum():,}"
    )

    print("\n" + "-" * 70)
    print("10. FINANCIAL VALIDATION")
    print("-" * 70)

    sales = df[df["IsRevenueEligible"]]

    print(
        f"Gross sales revenue: "
        f"£{sales['LineRevenue'].sum():,.2f}"
    )

    returns_value = df.loc[
        df["IsReturn"],
        "LineRevenue"
    ].sum()

    print(
        f"Return/cancellation value: "
        f"£{returns_value:,.2f}"
    )

    print(
        f"Net commercial value: "
        f"£{sales['LineRevenue'].sum() + returns_value:,.2f}"
    )

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()