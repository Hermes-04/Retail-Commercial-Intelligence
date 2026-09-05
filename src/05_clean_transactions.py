from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/online_retail_II.xlsx")
OUTPUT_FILE = Path("data/processed/transactions_clean.csv")


def load_data():
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)

    frames = []

    for sheet_name, df in sheets.items():
        df["SourceYear"] = sheet_name
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def standardize_columns(df):
    df = df.rename(
        columns={
            "Invoice": "InvoiceNo",
            "StockCode": "StockCode",
            "Description": "Description",
            "Quantity": "Quantity",
            "InvoiceDate": "InvoiceDate",
            "Price": "UnitPrice",
            "Customer ID": "CustomerID",
            "Country": "Country",
        }
    )

    return df


def classify_transactions(df):
    invoice = df["InvoiceNo"].astype(str).str.strip()

    df["InvoicePrefix"] = invoice.str[0]

    df["IsCancellation"] = invoice.str.startswith("C")
    df["IsAccountingAdjustment"] = invoice.str.startswith("A")

    df["LineRevenue"] = df["Quantity"] * df["UnitPrice"]

    # Classification priority is deliberate.
    df["TransactionType"] = "Other"

    # Accounting adjustments
    df.loc[
        df["IsAccountingAdjustment"],
        "TransactionType"
    ] = "Accounting Adjustment"

    # Cancellations / returns
    df.loc[
        df["IsCancellation"] & (df["Quantity"] < 0),
        "TransactionType"
    ] = "Cancellation / Return"

    # Operational adjustments / write-offs
    df.loc[
        (~df["IsCancellation"])
        & (~df["IsAccountingAdjustment"])
        & (df["Quantity"] < 0)
        & (df["UnitPrice"] == 0),
        "TransactionType"
    ] = "Operational Adjustment"

    # Zero-price transactions
    df.loc[
        (df["Quantity"] > 0)
        & (df["UnitPrice"] == 0),
        "TransactionType"
    ] = "Zero-Price Transaction"

    # Negative-price adjustments
    df.loc[
        (~df["IsAccountingAdjustment"])
        & (df["UnitPrice"] < 0),
        "TransactionType"
    ] = "Negative Price Adjustment"

    # Normal commercial sales
    df.loc[
        (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
        & (~df["IsAccountingAdjustment"])
        & (~df["IsCancellation"]),
        "TransactionType"
    ] = "Normal Sale"

    return df


def create_analytical_flags(df):
    df["IsCustomerIdentified"] = df["CustomerID"].notna()

    df["IsCommercialSale"] = (
        df["TransactionType"] == "Normal Sale"
    )

    df["IsReturn"] = (
        df["TransactionType"] == "Cancellation / Return"
    )

    df["IsRevenueEligible"] = df["IsCommercialSale"]

    return df


def clean_data(df):
    # Remove exact duplicate records.
    before = len(df)

    df = df.drop_duplicates().copy()

    duplicates_removed = before - len(df)

    print(f"Duplicate rows removed: {duplicates_removed:,}")

    # Standardize data types.
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["Description"] = df["Description"].astype("string")
    df["Country"] = df["Country"].astype("string")

    # Keep raw transaction history but remove rows that cannot
    # represent a meaningful transaction event.
    df = df[df["TransactionType"] != "Other"].copy()

    return df


def main():
    print("=" * 70)
    print("ONLINE RETAIL II — TRANSACTION CLEANING PIPELINE")
    print("=" * 70)

    print("\nLoading raw workbook...")
    df = load_data()

    print(f"Raw rows loaded: {len(df):,}")

    df = standardize_columns(df)
    df = classify_transactions(df)
    df = create_analytical_flags(df)
    df = clean_data(df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("CLEANING SUMMARY")
    print("=" * 70)

    print(f"\nFinal rows: {len(df):,}")

    print("\nTransaction types:")
    print(
        df["TransactionType"]
        .value_counts()
        .to_string()
    )

    print("\nRevenue-eligible rows:")
    print(
        f"{df['IsRevenueEligible'].sum():,}"
    )

    print("\nCustomer-identified rows:")
    print(
        f"{df['IsCustomerIdentified'].sum():,}"
    )

    print("\nDate range:")
    print(
        f"{df['InvoiceDate'].min()} → "
        f"{df['InvoiceDate'].max()}"
    )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("CLEANING PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()