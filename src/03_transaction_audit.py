from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/online_retail_II.xlsx")


def audit_sheet(sheet_name, df):
    print("\n" + "=" * 70)
    print(f"SHEET: {sheet_name}")
    print("=" * 70)

    # Basic transaction counts
    total_rows = len(df)
    negative_quantity = df["Quantity"] < 0
    zero_quantity = df["Quantity"] == 0
    negative_price = df["Price"] < 0
    zero_price = df["Price"] == 0

    print(f"\nTotal rows: {total_rows:,}")

    print("\nQuantity analysis:")
    print(f"  Negative quantity rows: {negative_quantity.sum():,}")
    print(f"  Zero quantity rows:     {zero_quantity.sum():,}")
    print(f"  Positive quantity rows: {(df['Quantity'] > 0).sum():,}")

    print("\nPrice analysis:")
    print(f"  Negative price rows: {negative_price.sum():,}")
    print(f"  Zero price rows:     {zero_price.sum():,}")
    print(f"  Positive price rows: {(df['Price'] > 0).sum():,}")

    # Invoice patterns
    invoice_text = df["Invoice"].astype(str)

    cancelled_invoice = invoice_text.str.startswith("C")

    print("\nInvoice analysis:")
    print(f"  Cancellation invoices: {cancelled_invoice.sum():,}")
    print(f"  Normal invoices:       {(~cancelled_invoice).sum():,}")

    print("\nCancellation invoice examples:")
    print(
        df.loc[
            cancelled_invoice,
            ["Invoice", "StockCode", "Description", "Quantity", "Price"]
        ].head(10).to_string(index=False)
    )

    # Revenue calculation
    df["LineRevenue"] = df["Quantity"] * df["Price"]

    print("\nFinancial impact:")
    print(f"  Gross transaction value: £{df['LineRevenue'].sum():,.2f}")
    print(
        f"  Positive-quantity revenue: "
        f"£{df.loc[df['Quantity'] > 0, 'LineRevenue'].sum():,.2f}"
    )
    print(
        f"  Negative-quantity value: "
        f"£{df.loc[df['Quantity'] < 0, 'LineRevenue'].sum():,.2f}"
    )
    print(
        f"  Negative-price value: "
        f"£{df.loc[df['Price'] < 0, 'LineRevenue'].sum():,.2f}"
    )

    # Top negative quantities
    print("\nLargest negative quantities:")
    print(
        df.loc[
            df["Quantity"] < 0,
            ["Invoice", "StockCode", "Description", "Quantity", "Price"]
        ]
        .sort_values("Quantity")
        .head(10)
        .to_string(index=False)
    )

    # Top negative prices
    print("\nLargest negative prices:")
    print(
        df.loc[
            df["Price"] < 0,
            ["Invoice", "StockCode", "Description", "Quantity", "Price"]
        ]
        .sort_values("Price")
        .head(10)
        .to_string(index=False)
    )

    # Customer coverage
    missing_customer = df["Customer ID"].isna()

    print("\nCustomer coverage:")
    print(f"  Rows with Customer ID:    {(~missing_customer).sum():,}")
    print(f"  Rows without Customer ID: {missing_customer.sum():,}")
    print(
        f"  Customer ID coverage: "
        f"{(~missing_customer).mean() * 100:.2f}%"
    )

    # Country coverage
    print("\nGeographic coverage:")
    print(f"  Unique countries: {df['Country'].nunique()}")

    print("\nTop 10 countries by transaction rows:")
    print(
        df["Country"]
        .value_counts()
        .head(10)
        .to_string()
    )


def main():
    print("=" * 70)
    print("ONLINE RETAIL II — TRANSACTION & FINANCIAL AUDIT")
    print("=" * 70)

    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)

    for sheet_name, df in sheets.items():
        audit_sheet(sheet_name, df)

    print("\n" + "=" * 70)
    print("TRANSACTION AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()