from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
OUTPUT_FILE = Path("data/processed/product_intelligence.csv")


def main():
    print("=" * 70)
    print("PRODUCT COMMERCIAL INTELLIGENCE")
    print("=" * 70)

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["InvoiceDate"]
    )

    # ------------------------------------------------------------
    # Sales
    # ------------------------------------------------------------

    sales = df[
        df["IsRevenueEligible"] == True
    ].copy()

    product_sales = (
        sales.groupby("StockCode")
        .agg(
            GrossRevenue=("LineRevenue", "sum"),
            UnitsSold=("Quantity", "sum"),
            SalesLines=("InvoiceNo", "count"),
            SalesOrders=("InvoiceNo", "nunique"),
            AvgUnitPrice=("UnitPrice", "mean"),
        )
    )

    # Most common product description.
    descriptions = (
        sales.dropna(subset=["Description"])
        .groupby("StockCode")["Description"]
        .agg(lambda x: x.value_counts().index[0])
        .rename("Description")
    )

    product_sales = product_sales.join(descriptions)

    # ------------------------------------------------------------
    # Returns
    # ------------------------------------------------------------

    returns = df[
        df["IsReturn"] == True
    ].copy()

    product_returns = (
        returns.groupby("StockCode")
        .agg(
            ReturnValue=("LineRevenue", "sum"),
            ReturnedUnits=("Quantity", lambda x: abs(x.sum())),
            ReturnLines=("InvoiceNo", "count"),
            ReturnOrders=("InvoiceNo", "nunique"),
        )
    )

    product = (
        product_sales
        .join(product_returns, how="left")
        .fillna(0)
    )

    # ------------------------------------------------------------
    # Commercial metrics
    # ------------------------------------------------------------

    product["NetRevenue"] = (
        product["GrossRevenue"]
        + product["ReturnValue"]
    )

    product["ReturnValueRate"] = (
        abs(product["ReturnValue"])
        / product["GrossRevenue"]
    )

    product["ReturnUnitRate"] = (
        product["ReturnedUnits"]
        / product["UnitsSold"]
    )

    product["RevenuePerUnit"] = (
        product["GrossRevenue"]
        / product["UnitsSold"]
    )

    product["RevenuePerOrder"] = (
        product["GrossRevenue"]
        / product["SalesOrders"]
    )

    # Revenue share.
    total_net_revenue = product["NetRevenue"].sum()

    product["RevenueShare"] = (
        product["NetRevenue"]
        / total_net_revenue
        * 100
    )

    # Rank.
    product["RevenueRank"] = (
        product["NetRevenue"]
        .rank(
            method="first",
            ascending=False
        )
        .astype(int)
    )

    product = product.sort_values(
        "NetRevenue",
        ascending=False
    )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    product.to_csv(
        OUTPUT_FILE,
        encoding="utf-8-sig"
    )

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    print("\nPRODUCT PORTFOLIO")
    print("-" * 70)

    print(f"Unique products with sales: {len(product):,}")

    print(
        f"Gross product revenue: "
        f"£{product['GrossRevenue'].sum():,.2f}"
    )

    print(
        f"Product returns: "
        f"£{product['ReturnValue'].sum():,.2f}"
    )

    print(
        f"Net product revenue: "
        f"£{product['NetRevenue'].sum():,.2f}"
    )

    print("\nTOP 20 PRODUCTS BY NET REVENUE")
    print("-" * 70)

    print(
        product[
            [
                "Description",
                "GrossRevenue",
                "ReturnValue",
                "NetRevenue",
                "UnitsSold",
                "ReturnValueRate",
                "RevenueShare",
            ]
        ]
        .head(20)
        .to_string()
    )

    print("\nTOP 20 PRODUCTS BY UNITS SOLD")
    print("-" * 70)

    print(
        product[
            [
                "Description",
                "UnitsSold",
                "GrossRevenue",
                "NetRevenue",
                "RevenuePerUnit",
            ]
        ]
        .sort_values(
            "UnitsSold",
            ascending=False
        )
        .head(20)
        .to_string()
    )

    print("\nTOP 20 PRODUCTS BY RETURN VALUE")
    print("-" * 70)

    print(
        product[
            [
                "Description",
                "GrossRevenue",
                "ReturnValue",
                "NetRevenue",
                "ReturnValueRate",
            ]
        ]
        .sort_values(
            "ReturnValue"
        )
        .head(20)
        .to_string()
    )

    print("\nREVENUE CONCENTRATION")
    print("-" * 70)

    for pct in [1, 5, 10, 20]:
        n = max(
            1,
            int(len(product) * pct / 100)
        )

        share = (
            product.head(n)["NetRevenue"].sum()
            / total_net_revenue
            * 100
        )

        print(
            f"Top {pct:>2}% of products: "
            f"{share:6.2f}% of net revenue"
        )

    print(f"\nSaved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("PRODUCT INTELLIGENCE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()