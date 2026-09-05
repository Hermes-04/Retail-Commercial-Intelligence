from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/online_retail_II.xlsx")


def classify_transactions(df):
    invoice = df["Invoice"].astype(str)

    df["InvoicePrefix"] = invoice.str[0]

    df["LineRevenue"] = df["Quantity"] * df["Price"]

    conditions = [
        (invoice.str.startswith("A")),
        (invoice.str.startswith("C")) & (df["Quantity"] < 0),
        (df["Quantity"] < 0) & (df["Price"] == 0),
        (df["Quantity"] > 0) & (df["Price"] == 0),
        (df["Quantity"] > 0) & (df["Price"] > 0),
        (df["Price"] < 0),
    ]

    categories = [
        "Accounting Adjustment",
        "Cancellation / Return",
        "Operational Adjustment",
        "Zero-Price Transaction",
        "Normal Sale",
        "Negative Price Adjustment",
    ]

    df["TransactionType"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="string"
    )

    for condition, category in zip(conditions, categories):
        df.loc[condition & df["TransactionType"].isna(), "TransactionType"] = category

    df["TransactionType"] = df["TransactionType"].fillna("Other")

    return df


def profile_sheet(sheet_name, df):
    df = classify_transactions(df)

    print("\n" + "=" * 75)
    print(f"SHEET: {sheet_name}")
    print("=" * 75)

    print("\nBUSINESS SCALE")
    print("-" * 75)

    print(f"Rows:               {len(df):,}")
    print(f"Unique invoices:    {df['Invoice'].nunique():,}")
    print(f"Unique products:    {df['StockCode'].nunique():,}")
    print(f"Unique customers:   {df['Customer ID'].nunique():,}")
    print(f"Unique countries:   {df['Country'].nunique():,}")
    print(
        f"Date range:         "
        f"{df['InvoiceDate'].min()} → {df['InvoiceDate'].max()}"
    )

    print("\nTRANSACTION CLASSIFICATION")
    print("-" * 75)

    classification = (
        df.groupby("TransactionType")
        .agg(
            rows=("Invoice", "size"),
            unique_invoices=("Invoice", "nunique"),
            revenue=("LineRevenue", "sum"),
        )
        .sort_values("rows", ascending=False)
    )

    classification["row_pct"] = (
        classification["rows"] / len(df) * 100
    ).round(2)

    print(classification.to_string())

    print("\nCUSTOMER COVERAGE")
    print("-" * 75)

    customer_rows = df["Customer ID"].notna()

    print(f"Rows with Customer ID:    {customer_rows.sum():,}")
    print(f"Rows without Customer ID: {(~customer_rows).sum():,}")
    print(
        f"Customer coverage:        "
        f"{customer_rows.mean() * 100:.2f}%"
    )

    print("\nTOP PRODUCTS BY SALES REVENUE")
    print("-" * 75)

    sales = df[df["TransactionType"] == "Normal Sale"]

    product_sales = (
        sales.groupby("StockCode")["LineRevenue"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    print(product_sales.to_string())

    print("\nTOP COUNTRIES BY SALES REVENUE")
    print("-" * 75)

    country_sales = (
        sales.groupby("Country")["LineRevenue"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    print(country_sales.to_string())

    print("\nTOP CUSTOMERS BY SALES REVENUE")
    print("-" * 75)

    customer_sales = (
        sales.dropna(subset=["Customer ID"])
        .groupby("Customer ID")["LineRevenue"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )

    print(customer_sales.to_string())

    return df


def main():
    print("=" * 75)
    print("ONLINE RETAIL II — BUSINESS DATA PROFILE")
    print("=" * 75)

    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)

    for sheet_name, df in sheets.items():
        profile_sheet(sheet_name, df)

    print("\n" + "=" * 75)
    print("BUSINESS DATA PROFILE COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()