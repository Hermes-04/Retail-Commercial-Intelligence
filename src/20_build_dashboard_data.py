import duckdb
from pathlib import Path

OUTPUT_DIR = Path("data/dashboard")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()

try:
    # --------------------------------------------------------
    # Load core transaction data
    # --------------------------------------------------------

    con.execute("""
        CREATE OR REPLACE VIEW transactions AS
        SELECT *
        FROM read_csv_auto(
            'data/processed/transactions_clean.csv',
            header = true
        )
    """)

    # --------------------------------------------------------
    # 1. Executive KPI dataset
    # --------------------------------------------------------

    executive_kpis = con.execute("""
        SELECT

            COUNT(*) AS transaction_rows,

            COUNT(DISTINCT InvoiceNo) AS total_orders,

            COUNT(DISTINCT CASE
                WHEN IsCustomerIdentified = TRUE
                THEN CustomerID
            END) AS identified_customers,

            COUNT(DISTINCT StockCode) AS product_records,

            COUNT(DISTINCT Country) AS countries,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            ) AS gross_revenue,

            SUM(
                CASE
                    WHEN IsReturn = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            ) AS return_value,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            )
            +
            SUM(
                CASE
                    WHEN IsReturn = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            ) AS net_revenue,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN Quantity
                    ELSE 0
                END
            ) AS units_sold

        FROM transactions
    """).df()

    executive_kpis.to_csv(
        OUTPUT_DIR / "executive_kpis.csv",
        index=False
    )

    # --------------------------------------------------------
    # 2. Monthly performance
    # --------------------------------------------------------

    monthly = con.execute("""
        SELECT

            DATE_TRUNC(
                'month',
                CAST(InvoiceDate AS TIMESTAMP)
            ) AS month,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            )
            +
            SUM(
                CASE
                    WHEN IsReturn = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            ) AS net_revenue,

            COUNT(DISTINCT CASE
                WHEN IsRevenueEligible = TRUE
                THEN InvoiceNo
            END) AS orders,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN Quantity
                    ELSE 0
                END
            ) AS units_sold

        FROM transactions

        GROUP BY 1

        ORDER BY 1
    """).df()

    monthly.to_csv(
        OUTPUT_DIR / "monthly_performance.csv",
        index=False
    )

    # --------------------------------------------------------
    # 3. Country performance
    # --------------------------------------------------------

    country = con.execute("""
        SELECT

            Country,

            SUM(
                CASE
                    WHEN IsCommercialSale = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            )
            +
            SUM(
                CASE
                    WHEN IsReturn = TRUE
                    THEN LineRevenue
                    ELSE 0
                END
            ) AS net_revenue,

            COUNT(DISTINCT CASE
                WHEN IsRevenueEligible = TRUE
                THEN InvoiceNo
            END) AS orders,

            COUNT(DISTINCT CASE
                WHEN IsCustomerIdentified = TRUE
                THEN CustomerID
            END) AS customers

        FROM transactions

        GROUP BY Country

        ORDER BY net_revenue DESC
    """).df()

    country.to_csv(
        OUTPUT_DIR / "country_performance.csv",
        index=False
    )

    # --------------------------------------------------------
    # 4. Customer RFM
    # --------------------------------------------------------

    rfm = con.execute("""
        SELECT *
        FROM read_csv_auto(
            'data/processed/customer_rfm.csv',
            header = true
        )
    """).df()

    rfm.to_csv(
        OUTPUT_DIR / "customer_rfm_dashboard.csv",
        index=False
    )

    # --------------------------------------------------------
    # 5. High-value customers at risk
    # --------------------------------------------------------

    at_risk = rfm[
        rfm["Segment"] == "At Risk High Value"
    ].copy()

    at_risk = at_risk.sort_values(
        "Monetary",
        ascending=False
    )

    at_risk.to_csv(
        OUTPUT_DIR / "high_value_at_risk.csv",
        index=False
    )

    # --------------------------------------------------------
    # 6. Product intelligence
    # --------------------------------------------------------

    product_master = con.execute("""
        SELECT *
        FROM read_csv_auto(
            'data/processed/product_master.csv',
            header = true
        )
    """).df()

    product_master.to_csv(
        OUTPUT_DIR / "product_master_dashboard.csv",
        index=False
    )

    # --------------------------------------------------------
    # 7. Cross-sell opportunities
    # --------------------------------------------------------

    cross_sell = con.execute("""
        SELECT *
        FROM read_csv_auto(
            'data/processed/executive_cross_sell_opportunities.csv',
            header = true
        )
    """).df()

    cross_sell.to_csv(
        OUTPUT_DIR / "cross_sell_opportunities.csv",
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("=" * 70)
    print("DASHBOARD DATA BUILD COMPLETE")
    print("=" * 70)

    print()
    print(f"Executive KPI rows: {len(executive_kpis)}")
    print(f"Monthly rows: {len(monthly)}")
    print(f"Country rows: {len(country)}")
    print(f"RFM customers: {len(rfm)}")
    print(f"High-value at-risk customers: {len(at_risk)}")
    print(f"Products: {len(product_master)}")
    print(f"Cross-sell opportunities: {len(cross_sell)}")

    print()
    print("Output directory:")
    print(OUTPUT_DIR)

finally:
    con.close()