from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
OUTPUT_FILE = Path("data/processed/product_taxonomy.csv")


def classify_product(stock_code, description):
    code = str(stock_code).strip().upper()
    desc = str(description).strip().upper()

    if code in {"M", "AMAZONFEE", "BANK CHARGES", "D"}:
        return "Fees / Adjustments"

    if code in {"POST", "DOT"}:
        return "Logistics / Postage"

    if code in {"S"} or "SAMPLE" in desc:
        return "Samples"

    if "MANUAL" in desc:
        return "Fees / Adjustments"

    return "Merchandise"


def main():
    print("=" * 70)
    print("PRODUCT TAXONOMY")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    sales = df[
        df["IsRevenueEligible"] == True
    ].copy()

    descriptions = (
        sales.dropna(subset=["Description"])
        .groupby("StockCode")["Description"]
        .agg(lambda x: x.value_counts().index[0])
        .rename("Description")
    )

    products = (
        sales.groupby("StockCode")
        .agg(
            GrossRevenue=("LineRevenue", "sum"),
            UnitsSold=("Quantity", "sum"),
            SalesLines=("InvoiceNo", "count"),
            SalesOrders=("InvoiceNo", "nunique"),
        )
        .join(descriptions)
        .reset_index()
    )

    products["ProductCategory"] = products.apply(
        lambda row: classify_product(
            row["StockCode"],
            row["Description"],
        ),
        axis=1,
    )

    products["CommercialProduct"] = (
        products["ProductCategory"] == "Merchandise"
    )

    products["RevenueShare"] = (
        products["GrossRevenue"]
        / products["GrossRevenue"].sum()
        * 100
    )

    products = products.sort_values(
        "GrossRevenue",
        ascending=False,
    )

    products.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nPRODUCT CATEGORY DISTRIBUTION")
    print("-" * 70)

    print(
        products["ProductCategory"]
        .value_counts()
        .to_string()
    )

    print("\nREVENUE BY PRODUCT CATEGORY")
    print("-" * 70)

    category_summary = (
        products.groupby("ProductCategory")
        .agg(
            Products=("StockCode", "count"),
            Revenue=("GrossRevenue", "sum"),
            Units=("UnitsSold", "sum"),
        )
        .sort_values("Revenue", ascending=False)
    )

    category_summary["RevenueShare"] = (
        category_summary["Revenue"]
        / products["GrossRevenue"].sum()
        * 100
    )

    print(category_summary.to_string())

    print("\nTOP 20 GENUINE MERCHANDISE PRODUCTS")
    print("-" * 70)

    merchandise = products[
        products["CommercialProduct"]
    ]

    print(
        merchandise[
            [
                "StockCode",
                "Description",
                "GrossRevenue",
                "UnitsSold",
                "SalesOrders",
                "RevenueShare",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nCOMMERCIAL PRODUCT UNIVERSE")
    print("-" * 70)

    print(
        f"Genuine merchandise products: "
        f"{len(merchandise):,}"
    )

    print(
        f"Merchandise revenue: "
        f"£{merchandise['GrossRevenue'].sum():,.2f}"
    )

    print(
        f"Merchandise revenue share: "
        f"{merchandise['GrossRevenue'].sum() / products['GrossRevenue'].sum() * 100:.2f}%"
    )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("PRODUCT TAXONOMY COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()