-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- SQL CUSTOMER INTELLIGENCE LAYER
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
-- 2. LOAD CUSTOMER RFM
-- ============================================================

CREATE OR REPLACE TABLE customer_rfm AS
SELECT *
FROM read_csv_auto(
    'data/processed/customer_rfm.csv',
    header = true
);


-- ============================================================
-- 3. CUSTOMER COMMERCIAL VALUE
-- ============================================================

SELECT

    t.CustomerID,

    COUNT(
        DISTINCT CASE
            WHEN t.IsRevenueEligible = true
            THEN t.InvoiceNo
        END
    ) AS orders,

    SUM(
        CASE
            WHEN t.IsRevenueEligible = true
            THEN t.LineRevenue
            ELSE 0
        END
    ) AS gross_revenue,

    SUM(
        CASE
            WHEN t.IsReturn = true
            THEN t.LineRevenue
            ELSE 0
        END
    ) AS return_value,

    ROUND(
        SUM(t.LineRevenue),
        2
    ) AS net_revenue,

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
        )
        /
        NULLIF(
            COUNT(
                DISTINCT CASE
                    WHEN t.IsRevenueEligible = true
                    THEN t.InvoiceNo
                END
            ),
            0
        ),
        2
    ) AS average_order_value

FROM transactions t

WHERE
    t.CustomerID IS NOT NULL

GROUP BY
    t.CustomerID

HAVING
    gross_revenue > 0

ORDER BY
    net_revenue DESC

LIMIT 50;


-- ============================================================
-- 4. CUSTOMER REVENUE CONCENTRATION
-- ============================================================

WITH customer_value AS (

    SELECT

        CustomerID,

        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        )
        +
        SUM(
            CASE
                WHEN IsReturn = true
                THEN LineRevenue
                ELSE 0
            END
        ) AS net_revenue

    FROM transactions

    WHERE
        CustomerID IS NOT NULL

    GROUP BY
        CustomerID

    HAVING
        net_revenue > 0

),

ranked AS (

    SELECT

        *,

        ROW_NUMBER() OVER (
            ORDER BY net_revenue DESC
        ) AS customer_rank,

        COUNT(*) OVER () AS total_customers,

        SUM(net_revenue) OVER () AS total_revenue

    FROM customer_value

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
-- 5. RFM SEGMENT PERFORMANCE
-- ============================================================

SELECT

    r.Segment,

    COUNT(*) AS customers,

    ROUND(
        SUM(r.Monetary),
        2
    ) AS gross_revenue,

    ROUND(
        AVG(r.Monetary),
        2
    ) AS average_customer_value,

    ROUND(
        AVG(r.Frequency),
        2
    ) AS average_orders,

    ROUND(
        AVG(r.Recency),
        1
    ) AS average_recency_days

FROM customer_rfm r

GROUP BY
    r.Segment

ORDER BY
    gross_revenue DESC;


-- ============================================================
-- 6. HIGH-VALUE AT-RISK CUSTOMERS
-- ============================================================

SELECT

    r.CustomerID,

    r.Segment,

    r.Recency,

    r.Frequency,

    ROUND(
        r.Monetary,
        2
    ) AS gross_revenue,

    ROUND(
        r.Monetary / NULLIF(r.Frequency, 0),
        2
    ) AS revenue_per_order

FROM customer_rfm r

WHERE
    r.Segment = 'At Risk High Value'

ORDER BY
    r.Monetary DESC

LIMIT 50;


-- ============================================================
-- 7. CUSTOMER RETURN RISK
-- ============================================================

SELECT

    t.CustomerID,

    COUNT(
        DISTINCT CASE
            WHEN t.IsRevenueEligible = true
            THEN t.InvoiceNo
        END
    ) AS sales_orders,

    COUNT(
        DISTINCT CASE
            WHEN t.IsReturn = true
            THEN t.InvoiceNo
        END
    ) AS return_orders,

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
        ABS(
            SUM(
                CASE
                    WHEN t.IsReturn = true
                    THEN t.LineRevenue
                    ELSE 0
                END
            )
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
    ) AS return_value_rate

FROM transactions t

WHERE
    t.CustomerID IS NOT NULL

GROUP BY
    t.CustomerID

HAVING
    gross_revenue > 0

ORDER BY
    return_value_rate DESC

LIMIT 50;


-- ============================================================
-- 8. CUSTOMER VALUE TIERS
-- ============================================================

WITH customer_value AS (

    SELECT

        CustomerID,

        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        )
        +
        SUM(
            CASE
                WHEN IsReturn = true
                THEN LineRevenue
                ELSE 0
            END
        ) AS net_revenue

    FROM transactions

    WHERE
        CustomerID IS NOT NULL

    GROUP BY
        CustomerID

    HAVING
        net_revenue > 0

),

tiered AS (

    SELECT

        *,

        NTILE(4) OVER (
            ORDER BY net_revenue
        ) AS value_quartile

    FROM customer_value

)

SELECT

    value_quartile,

    COUNT(*) AS customers,

    ROUND(
        SUM(net_revenue),
        2
    ) AS net_revenue,

    ROUND(
        AVG(net_revenue),
        2
    ) AS average_customer_value

FROM tiered

GROUP BY
    value_quartile

ORDER BY
    value_quartile DESC;


-- ============================================================
-- 9. REPEAT PURCHASE PERFORMANCE
-- ============================================================

WITH customer_orders AS (

    SELECT

        CustomerID,

        COUNT(
            DISTINCT CASE
                WHEN IsRevenueEligible = true
                THEN InvoiceNo
            END
        ) AS orders

    FROM transactions

    WHERE
        CustomerID IS NOT NULL

    GROUP BY
        CustomerID

)

SELECT

    COUNT(*) AS identified_customers,

    SUM(
        CASE
            WHEN orders = 1
            THEN 1
            ELSE 0
        END
    ) AS one_time_customers,

    SUM(
        CASE
            WHEN orders >= 2
            THEN 1
            ELSE 0
        END
    ) AS repeat_customers,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN orders >= 2
                THEN 1
                ELSE 0
            END
        )
        / COUNT(*),
        2
    ) AS repeat_customer_rate

FROM customer_orders;


-- ============================================================
-- 10. CUSTOMER VALUE × RETURN RISK
-- ============================================================

WITH customer_metrics AS (

    SELECT

        CustomerID,

        SUM(
            CASE
                WHEN IsRevenueEligible = true
                THEN LineRevenue
                ELSE 0
            END
        ) AS gross_revenue,

        SUM(
            CASE
                WHEN IsReturn = true
                THEN LineRevenue
                ELSE 0
            END
        ) AS return_value

    FROM transactions

    WHERE
        CustomerID IS NOT NULL

    GROUP BY
        CustomerID

    HAVING
        gross_revenue > 0

)

SELECT

    CASE
        WHEN gross_revenue >= 10000
        THEN 'High Value'
        ELSE 'Standard Value'
    END AS value_class,

    CASE
        WHEN ABS(return_value) / gross_revenue >= 0.30
        THEN 'High Return Risk'

        WHEN ABS(return_value) / gross_revenue >= 0.15
        THEN 'Moderate Return Risk'

        ELSE 'Low Return Risk'
    END AS return_risk_class,

    COUNT(*) AS customers,

    ROUND(
        SUM(gross_revenue + return_value),
        2
    ) AS net_revenue

FROM customer_metrics

GROUP BY
    value_class,
    return_risk_class

ORDER BY
    net_revenue DESC;