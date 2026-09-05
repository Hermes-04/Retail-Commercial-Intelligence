-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- SQL PRODUCT INTELLIGENCE LAYER
-- ============================================================


-- ============================================================
-- 1. LOAD CLEAN TRANSACTIONS
-- ============================================================

CREATE OR REPLACE TABLE transactions AS
SELECT *
FROM read_csv_auto(
    'data/processed/transactions_clean.csv',
    header = true
);


-- ============================================================
-- 2. LOAD PRODUCT TAXONOMY
-- ============================================================

CREATE OR REPLACE TABLE product_taxonomy AS
SELECT *
FROM read_csv_auto(
    'data/processed/product_taxonomy.csv',
    header = true
);


-- ============================================================
-- 3. TOP MERCHANDISE PRODUCTS
-- ============================================================

SELECT

    t.StockCode,

    MAX(t.Description) AS Description,

    MAX(p.ProductCategory) AS ProductCategory,

    SUM(
        CASE
            WHEN t.IsRevenueEligible = true
            THEN t.Quantity
            ELSE 0
        END
    ) AS units_sold,

    COUNT(
        DISTINCT CASE
            WHEN t.IsRevenueEligible = true
            THEN t.InvoiceNo
        END
    ) AS orders,

    ROUND(
        SUM(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS gross_revenue,

    ROUND(
        SUM(t.LineRevenue),
        2
    ) AS net_revenue,

    ROUND(
        AVG(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.UnitPrice
            END
        ),
        2
    ) AS average_unit_price

FROM transactions t

INNER JOIN product_taxonomy p
    ON t.StockCode = p.StockCode

WHERE
    p.ProductCategory = 'Merchandise'

GROUP BY
    t.StockCode

HAVING
    gross_revenue > 0

ORDER BY
    net_revenue DESC

LIMIT 50;


-- ============================================================
-- 4. MERCHANDISE REVENUE CONCENTRATION
-- ============================================================

WITH product_revenue AS (

    SELECT

        t.StockCode,

        SUM(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.LineRevenue
                ELSE 0
            END
        ) AS revenue

    FROM transactions t

    INNER JOIN product_taxonomy p
        ON t.StockCode = p.StockCode

    WHERE
        p.ProductCategory = 'Merchandise'

    GROUP BY
        t.StockCode

),

ranked AS (

    SELECT

        *,

        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS product_rank,

        COUNT(*) OVER () AS total_products,

        SUM(revenue) OVER () AS total_revenue

    FROM product_revenue

)

SELECT

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN product_rank <= CEIL(total_products * 0.01)
                THEN revenue
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
                WHEN product_rank <= CEIL(total_products * 0.05)
                THEN revenue
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
                WHEN product_rank <= CEIL(total_products * 0.10)
                THEN revenue
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
                WHEN product_rank <= CEIL(total_products * 0.20)
                THEN revenue
                ELSE 0
            END
        )
        / MAX(total_revenue),
        2
    ) AS top_20pct_revenue_share

FROM ranked;


-- ============================================================
-- 5. PRODUCT RETURN RISK
-- ============================================================

SELECT

    t.StockCode,

    MAX(t.Description) AS Description,

    ROUND(
        SUM(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS gross_revenue,

    ROUND(
        SUM(
            CASE
                WHEN t.IsReturn = true
                THEN t.LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS return_value,

    ROUND(
        100.0 *
        ABS(
            SUM(
                CASE
                    WHEN t.IsReturn = true
                    THEN t.LineRevenue
                    ELSE 0
                END
            )
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN t.IsRevenueEligible = true
                    THEN t.LineRevenue
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS return_value_rate,

    SUM(
        CASE
            WHEN t.IsRevenueEligible = true
            THEN t.Quantity
            ELSE 0
        END
    ) AS units_sold,

    ABS(
        SUM(
            CASE
                WHEN t.IsReturn = true
                THEN t.Quantity
                ELSE 0
            END
        )
    ) AS returned_units

FROM transactions t

INNER JOIN product_taxonomy p
    ON t.StockCode = p.StockCode

WHERE
    p.ProductCategory = 'Merchandise'

GROUP BY
    t.StockCode

HAVING
    gross_revenue > 0

ORDER BY
    return_value_rate DESC

LIMIT 50;


-- ============================================================
-- 6. COMMERCIAL PERFORMANCE BY PRODUCT CATEGORY
-- ============================================================

SELECT

    p.ProductCategory,

    COUNT(DISTINCT t.StockCode) AS products,

    SUM(
        CASE
            WHEN t.IsRevenueEligible = true
            THEN t.Quantity
            ELSE 0
        END
    ) AS units_sold,

    ROUND(
        SUM(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS gross_revenue,

    ROUND(
        SUM(t.LineRevenue),
        2
    ) AS net_revenue

FROM transactions t

INNER JOIN product_taxonomy p
    ON t.StockCode = p.StockCode

GROUP BY
    p.ProductCategory

ORDER BY
    net_revenue DESC;


-- ============================================================
-- 7. MONTHLY MERCHANDISE PERFORMANCE
-- ============================================================

SELECT

    DATE_TRUNC(
        'month',
        t.InvoiceDate
    ) AS sales_month,

    ROUND(
        SUM(
            CASE
                WHEN t.IsRevenueEligible = true
                THEN t.LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS merchandise_revenue,

    SUM(
        CASE
            WHEN t.IsRevenueEligible = true
            THEN t.Quantity
            ELSE 0
        END
    ) AS units_sold

FROM transactions t

INNER JOIN product_taxonomy p
    ON t.StockCode = p.StockCode

WHERE
    p.ProductCategory = 'Merchandise'

    AND t.InvoiceDate IS NOT NULL

GROUP BY
    1

ORDER BY
    1;