from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/processed/transactions_clean.csv")
TAXONOMY_FILE = Path("data/processed/product_taxonomy.csv")
OUTPUT_FILE = Path("data/processed/product_associations.csv")


def main():
    print("=" * 70)
    print("PRODUCT BASKET & ASSOCIATION ANALYSIS")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)
    taxonomy = pd.read_csv(TAXONOMY_FILE)

    # ------------------------------------------------------------
    # Keep genuine merchandise sales only.
    # ------------------------------------------------------------

    sales = df[
        (df["IsRevenueEligible"] == True)
        & (df["InvoiceNo"].notna())
    ].copy()

    merchandise_codes = set(
        taxonomy.loc[
            taxonomy["CommercialProduct"] == True,
            "StockCode"
        ].astype(str)
    )

    sales["StockCode"] = sales["StockCode"].astype(str)

    sales = sales[
        sales["StockCode"].isin(merchandise_codes)
    ].copy()

    # Exclude cancellation-style invoices just in case.
    sales = sales[
        ~sales["InvoiceNo"].astype(str).str.startswith("C")
    ]

    # ------------------------------------------------------------
    # Remove duplicate product occurrences within an invoice.
    # ------------------------------------------------------------

    basket = (
        sales[
            ["InvoiceNo", "StockCode"]
        ]
        .drop_duplicates()
    )

    print(f"\nUnique orders: {basket['InvoiceNo'].nunique():,}")
    print(f"Unique products: {basket['StockCode'].nunique():,}")

    # Only multi-product baskets can produce associations.
    basket_sizes = (
        basket.groupby("InvoiceNo")["StockCode"]
        .nunique()
    )

    multi_item_orders = basket_sizes[
        basket_sizes >= 2
    ].index

    basket = basket[
        basket["InvoiceNo"].isin(multi_item_orders)
    ]

    print(
        f"Multi-product orders: "
        f"{basket['InvoiceNo'].nunique():,}"
    )

    # ------------------------------------------------------------
    # Product descriptions.
    # ------------------------------------------------------------

    descriptions = (
        taxonomy[
            ["StockCode", "Description"]
        ]
        .drop_duplicates("StockCode")
    )

    description_map = dict(
        zip(
            descriptions["StockCode"].astype(str),
            descriptions["Description"],
        )
    )

    # ------------------------------------------------------------
    # Product order counts.
    # ------------------------------------------------------------

    product_order_count = (
        basket.groupby("StockCode")["InvoiceNo"]
        .nunique()
    )

    total_orders = basket["InvoiceNo"].nunique()

    # ------------------------------------------------------------
    # Generate product pairs within each order.
    # ------------------------------------------------------------

    pairs = []

    for invoice, group in basket.groupby("InvoiceNo"):
        products = sorted(
            group["StockCode"].unique()
        )

        for i in range(len(products)):
            for j in range(i + 1, len(products)):
                pairs.append(
                    (
                        products[i],
                        products[j],
                    )
                )

    pair_df = pd.DataFrame(
        pairs,
        columns=["ProductA", "ProductB"],
    )

    print(
        f"Product pairs generated: "
        f"{len(pair_df):,}"
    )

    # ------------------------------------------------------------
    # Pair support.
    # ------------------------------------------------------------

    pair_counts = (
        pair_df
        .value_counts()
        .reset_index(name="PairOrders")
    )

    pair_counts["Support"] = (
        pair_counts["PairOrders"]
        / total_orders
    )

    # ------------------------------------------------------------
    # Confidence and lift.
    # ------------------------------------------------------------

    pair_counts["ProductAOrders"] = (
        pair_counts["ProductA"]
        .map(product_order_count)
    )

    pair_counts["ProductBOrders"] = (
        pair_counts["ProductB"]
        .map(product_order_count)
    )

    pair_counts["Confidence_A_to_B"] = (
        pair_counts["PairOrders"]
        / pair_counts["ProductAOrders"]
    )

    pair_counts["Confidence_B_to_A"] = (
        pair_counts["PairOrders"]
        / pair_counts["ProductBOrders"]
    )

    pair_counts["Lift"] = (
        pair_counts["PairOrders"]
        * total_orders
        / (
            pair_counts["ProductAOrders"]
            * pair_counts["ProductBOrders"]
        )
    )

    pair_counts["ProductA"] = (
        pair_counts["ProductA"].astype(str)
    )

    pair_counts["ProductB"] = (
        pair_counts["ProductB"].astype(str)
    )

    pair_counts["ProductA_Description"] = (
        pair_counts["ProductA"]
        .map(description_map)
    )

    pair_counts["ProductB_Description"] = (
        pair_counts["ProductB"]
        .map(description_map)
    )

    # ------------------------------------------------------------
    # Minimum thresholds.
    #
    # We require at least 20 shared orders so that
    # tiny/rare combinations don't dominate.
    # ------------------------------------------------------------

    associations = pair_counts[
        pair_counts["PairOrders"] >= 20
    ].copy()

    associations = associations.sort_values(
        ["Lift", "PairOrders"],
        ascending=[False, False],
    )

    # ------------------------------------------------------------
    # Save.
    # ------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    associations.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------------
    # Output.
    # ------------------------------------------------------------

    print("\nTOP ASSOCIATIONS BY LIFT")
    print("-" * 70)

    print(
        associations[
            [
                "ProductA",
                "ProductA_Description",
                "ProductB",
                "ProductB_Description",
                "PairOrders",
                "Support",
                "Confidence_A_to_B",
                "Confidence_B_to_A",
                "Lift",
            ]
        ]
        .head(25)
        .to_string(index=False)
    )

    print("\nTOP ASSOCIATIONS BY FREQUENCY")
    print("-" * 70)

    print(
        associations
        .sort_values(
            "PairOrders",
            ascending=False
        )
        [
            [
                "ProductA_Description",
                "ProductB_Description",
                "PairOrders",
                "Support",
                "Lift",
            ]
        ]
        .head(25)
        .to_string(index=False)
    )

    print(
        f"\nAssociations retained: "
        f"{len(associations):,}"
    )

    print(f"Saved to: {OUTPUT_FILE}")

    print("\n" + "=" * 70)
    print("BASKET ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()