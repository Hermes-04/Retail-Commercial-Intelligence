-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- SQL ANALYTICS LAYER
-- ============================================================

-- NOTE:
-- This SQL layer is designed for DuckDB.
-- It reads the validated transaction dataset generated
-- by the Python data pipeline.

-- ============================================================
-- 1. CREATE ANALYTICAL BASE TABLE
-- ============================================================

CREATE OR REPLACE TABLE transactions AS
SELECT *
FROM read_csv_auto(
    'data/processed/transactions_clean.csv',
    header = true
);

-- ============================================================
-- 2. DATA QUALITY KPI
-- ============================================================

SELECT
    COUNT(*) AS total_transaction_rows,
    COUNT(DISTINCT InvoiceNo) AS unique_invoices,
    COUNT(DISTINCT StockCode) AS unique_products,
    COUNT(DISTINCT CustomerID) AS identified_customers,
    COUNT(DISTINCT Country) AS countries
FROM transactions;


-- ============================================================
-- 3. COMMERCIAL REVENUE KPIs
-- ============================================================

SELECT
    ROUND(
        SUM(CASE
            WHEN IsRevenueEligible = true
            THEN LineRevenue
            ELSE 0
        END), 2
    ) AS gross_sales_revenue,

    ROUND(
        SUM(CASE
            WHEN IsReturn = true
            THEN LineRevenue
            ELSE 0
        END), 2
    ) AS return_value,

    ROUND(
        SUM(CASE
            WHEN IsRevenueEligible = true
            THEN LineRevenue
            ELSE 0
        END)
        +
        SUM(CASE
            WHEN IsReturn = true
            THEN LineRevenue
            ELSE 0
        END), 2
    ) AS net_commercial_value

FROM transactions;


-- ============================================================
-- 4. MONTHLY REVENUE TREND
-- ============================================================

SELECT
    DATE_TRUNC('month', InvoiceDate) AS sales_month,

    ROUND(
        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS gross_revenue,

    ROUND(
        SUM(
            CASE
                WHEN IsReturn = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS return_value,

    ROUND(
        SUM(LineRevenue), 2
    ) AS net_revenue,

    COUNT(DISTINCT InvoiceNo) AS orders

FROM transactions

WHERE InvoiceDate IS NOT NULL

GROUP BY 1
ORDER BY 1;


-- ============================================================
-- 5. COUNTRY PERFORMANCE
-- ============================================================

SELECT
    Country,

    COUNT(DISTINCT InvoiceNo) AS orders,

    COUNT(DISTINCT CustomerID) AS customers,

    SUM(
        CASE
            WHEN IsRevenueEligible = true
            THEN Quantity
            ELSE 0
        END
    ) AS units_sold,

    ROUND(
        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS gross_revenue,

    ROUND(
        SUM(LineRevenue), 2
    ) AS net_revenue

FROM transactions

GROUP BY Country

ORDER BY net_revenue DESC;


-- ============================================================
-- 6. PRODUCT PERFORMANCE
-- ============================================================

SELECT
    StockCode,

    MAX(Description) AS Description,

    SUM(
        CASE
            WHEN IsRevenueEligible = true
            THEN Quantity
            ELSE 0
        END
    ) AS units_sold,

    COUNT(
        DISTINCT CASE
            WHEN IsRevenueEligible = true
            THEN InvoiceNo
        END
    ) AS orders,

    ROUND(
        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS gross_revenue,

    ROUND(
        SUM(LineRevenue), 2
    ) AS net_revenue

FROM transactions

GROUP BY StockCode

ORDER BY net_revenue DESC

LIMIT 50;


-- ============================================================
-- 7. CUSTOMER VALUE
-- ============================================================

SELECT
    CustomerID,

    COUNT(
        DISTINCT CASE
            WHEN IsRevenueEligible = true
            THEN InvoiceNo
        END
    ) AS orders,

    SUM(
        CASE
            WHEN IsRevenueEligible = true
            THEN Quantity
            ELSE 0
        END
    ) AS units,

    ROUND(
        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS gross_revenue,

    ROUND(
        SUM(LineRevenue), 2
    ) AS net_revenue

FROM transactions

WHERE CustomerID IS NOT NULL

GROUP BY CustomerID

ORDER BY net_revenue DESC

LIMIT 50;


-- ============================================================
-- 8. CUSTOMER CONCENTRATION
-- ============================================================

WITH customer_revenue AS (

    SELECT
        CustomerID,

        SUM(LineRevenue) AS net_revenue

    FROM transactions

    WHERE
        CustomerID IS NOT NULL

    GROUP BY CustomerID

),

ranked AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            ORDER BY net_revenue DESC
        ) AS customer_rank,

        COUNT(*) OVER () AS total_customers,

        SUM(net_revenue) OVER () AS total_revenue

    FROM customer_revenue

)

SELECT

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN customer_rank <= CEIL(total_customers * 0.01)
                THEN net_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue),
        2
    ) AS top_1pct_revenue_share,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN customer_rank <= CEIL(total_customers * 0.05)
                THEN net_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue),
        2
    ) AS top_5pct_revenue_share,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN customer_rank <= CEIL(total_customers * 0.10)
                THEN net_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue),
        2
    ) AS top_10pct_revenue_share,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN customer_rank <= CEIL(total_customers * 0.20)
                THEN net_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue),
        2
    ) AS top_20pct_revenue_share

FROM ranked;


-- ============================================================
-- 9. RETURN RISK BY CUSTOMER
-- ============================================================

SELECT

    CustomerID,

    COUNT(
        DISTINCT CASE
            WHEN IsRevenueEligible = true
            THEN InvoiceNo
        END
    ) AS sales_orders,

    COUNT(
        DISTINCT CASE
            WHEN IsReturn = true
            THEN InvoiceNo
        END
    ) AS return_orders,

    ROUND(
        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS gross_sales,

    ROUND(
        SUM(
            CASE
                WHEN IsReturn = true
                THEN LineRevenue
                ELSE 0
            END
        ), 2
    ) AS return_value,

    ROUND(
        SUM(LineRevenue), 2
    ) AS net_revenue

FROM transactions

WHERE CustomerID IS NOT NULL

GROUP BY CustomerID

HAVING gross_sales > 0

ORDER BY return_value ASC;


-- ============================================================
-- 10. TRANSACTION TYPE DISTRIBUTION
-- ============================================================

SELECT

    TransactionType,

    COUNT(*) AS transaction_rows,

    COUNT(DISTINCT InvoiceNo) AS invoices,

    ROUND(
        SUM(LineRevenue), 2
    ) AS transaction_value

FROM transactions

GROUP BY TransactionType

ORDER BY transaction_value DESC;