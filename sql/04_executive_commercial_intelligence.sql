-- ============================================================
-- EXECUTIVE COMMERCIAL INTELLIGENCE v2
-- Retail Commercial Intelligence
-- ============================================================


-- ============================================================
-- 1. LOAD CORE TRANSACTION DATA
-- ============================================================

CREATE OR REPLACE VIEW transactions AS
SELECT *
FROM read_csv_auto(
    'data/processed/transactions_clean.csv',
    header = true
);


-- ============================================================
-- 2. EXECUTIVE COMMERCIAL KPIs
-- ============================================================

SELECT

    COUNT(*) AS transaction_rows,

    COUNT(DISTINCT InvoiceNo) AS total_orders,

    COUNT(DISTINCT CASE
        WHEN IsCustomerIdentified = TRUE
        THEN CustomerID
    END) AS identified_customers,

    COUNT(DISTINCT StockCode) AS product_records,

    COUNT(DISTINCT Country) AS countries,

    ROUND(
        SUM(
            CASE
                WHEN IsCommercialSale = TRUE
                THEN LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS gross_revenue,

    ROUND(
        SUM(
            CASE
                WHEN IsReturn = TRUE
                THEN LineRevenue
                ELSE 0
            END
        ),
        2
    ) AS return_value,

    ROUND(
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
        ),
        2
    ) AS net_revenue,

    SUM(
        CASE
            WHEN IsCommercialSale = TRUE
            THEN Quantity
            ELSE 0
        END
    ) AS units_sold,

    ROUND(
        (
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
            )
        )
        /
        NULLIF(
            COUNT(DISTINCT CASE
                WHEN IsRevenueEligible = TRUE
                THEN InvoiceNo
            END),
            0
        ),
        2
    ) AS net_revenue_per_order

FROM transactions;


-- ============================================================
-- 3. CUSTOMER COMMERCIAL HEALTH
-- ============================================================

WITH customer_value AS (

    SELECT

        CustomerID,

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

        COUNT(DISTINCT CASE
            WHEN IsCommercialSale = TRUE
            THEN InvoiceNo
        END) AS orders

    FROM transactions

    WHERE IsCustomerIdentified = TRUE

    GROUP BY CustomerID
)

SELECT

    COUNT(*) AS customers,

    ROUND(
        AVG(net_revenue),
        2
    ) AS avg_customer_value,

    ROUND(
        SUM(net_revenue) /
        NULLIF(COUNT(*), 0),
        2
    ) AS revenue_per_customer,

    ROUND(
        AVG(orders),
        2
    ) AS average_orders_per_customer,

    ROUND(
        SUM(
            CASE
                WHEN orders > 1
                THEN 1
                ELSE 0
            END
        ) * 100.0 /
        COUNT(*),
        2
    ) AS repeat_customer_rate,

    ROUND(
        SUM(
            CASE
                WHEN return_value < 0
                THEN 1
                ELSE 0
            END
        ) * 100.0 /
        COUNT(*),
        2
    ) AS customers_with_returns

FROM customer_value;


-- ============================================================
-- 4. CUSTOMER REVENUE CONCENTRATION
-- ============================================================

WITH customer_value AS (

    SELECT

        CustomerID,

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
        ) AS net_revenue

    FROM transactions

    WHERE IsCustomerIdentified = TRUE

    GROUP BY CustomerID
),

ranked AS (

    SELECT

        CustomerID,
        net_revenue,

        ROW_NUMBER() OVER (
            ORDER BY net_revenue DESC
        ) AS revenue_rank,

        COUNT(*) OVER () AS customer_count

    FROM customer_value
)

SELECT

    ROUND(
        SUM(
            CASE
                WHEN revenue_rank <= CEIL(customer_count * 0.01)
                THEN net_revenue
                ELSE 0
            END
        ) * 100.0 /
        NULLIF(SUM(net_revenue), 0),
        2
    ) AS top_1pct_share,

    ROUND(
        SUM(
            CASE
                WHEN revenue_rank <= CEIL(customer_count * 0.05)
                THEN net_revenue
                ELSE 0
            END
        ) * 100.0 /
        NULLIF(SUM(net_revenue), 0),
        2
    ) AS top_5pct_share,

    ROUND(
        SUM(
            CASE
                WHEN revenue_rank <= CEIL(customer_count * 0.10)
                THEN net_revenue
                ELSE 0
            END
        ) * 100.0 /
        NULLIF(SUM(net_revenue), 0),
        2
    ) AS top_10pct_share,

    ROUND(
        SUM(
            CASE
                WHEN revenue_rank <= CEIL(customer_count * 0.20)
                THEN net_revenue
                ELSE 0
            END
        ) * 100.0 /
        NULLIF(SUM(net_revenue), 0),
        2
    ) AS top_20pct_share

FROM ranked;


-- ============================================================
-- 5. MONTHLY NET COMMERCIAL PERFORMANCE
-- ============================================================

SELECT

    DATE_TRUNC(
        'month',
        CAST(InvoiceDate AS TIMESTAMP)
    ) AS month,

    ROUND(
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
        ),
        2
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

ORDER BY 1;


-- ============================================================
-- 6. COUNTRY COMMERCIAL PERFORMANCE
-- ============================================================

SELECT

    Country,

    ROUND(
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
        ),
        2
    ) AS net_revenue,

    COUNT(DISTINCT CASE
        WHEN IsRevenueEligible = TRUE
        THEN InvoiceNo
    END) AS orders,

    COUNT(DISTINCT CASE
        WHEN IsCustomerIdentified = TRUE
        THEN CustomerID
    END) AS customers,

    ROUND(
        (
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
            )
        )
        /
        NULLIF(
            COUNT(DISTINCT CASE
                WHEN IsRevenueEligible = TRUE
                THEN InvoiceNo
            END),
            0
        ),
        2
    ) AS revenue_per_order

FROM transactions

GROUP BY Country

ORDER BY net_revenue DESC;


-- ============================================================
-- 7. VALIDATED RFM SEGMENT PERFORMANCE
-- ============================================================

SELECT

    Segment,

    COUNT(*) AS customers,

    ROUND(
        SUM(Monetary),
        2
    ) AS gross_revenue,

    ROUND(
        AVG(Monetary),
        2
    ) AS average_customer_value,

    ROUND(
        AVG(Frequency),
        2
    ) AS average_orders,

    ROUND(
        AVG(Recency),
        1
    ) AS average_recency_days

FROM read_csv_auto(
    'data/processed/customer_rfm.csv',
    header = true
)

GROUP BY Segment

ORDER BY gross_revenue DESC;


-- ============================================================
-- 8. HIGH-VALUE CUSTOMER RECOVERY OPPORTUNITY
-- ============================================================

SELECT

    COUNT(*) AS high_value_at_risk_customers,

    ROUND(
        SUM(Monetary),
        2
    ) AS recoverable_gross_revenue,

    ROUND(
        AVG(Monetary),
        2
    ) AS average_customer_value,

    ROUND(
        AVG(Recency),
        1
    ) AS average_days_since_purchase,

    ROUND(
        AVG(Frequency),
        2
    ) AS average_historical_orders

FROM read_csv_auto(
    'data/processed/customer_rfm.csv',
    header = true
)

WHERE Segment = 'At Risk High Value';


-- ============================================================
-- 9. REPEAT PURCHASE PERFORMANCE
-- ============================================================

WITH customer_orders AS (

    SELECT

        CustomerID,

        COUNT(
            DISTINCT CASE
                WHEN IsCommercialSale = TRUE
                THEN InvoiceNo
            END
        ) AS orders

    FROM transactions

    WHERE IsCustomerIdentified = TRUE

    GROUP BY CustomerID
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
            WHEN orders > 1
            THEN 1
            ELSE 0
        END
    ) AS repeat_customers,

    ROUND(
        SUM(
            CASE
                WHEN orders > 1
                THEN 1
                ELSE 0
            END
        ) * 100.0 /
        COUNT(*),
        2
    ) AS repeat_customer_rate

FROM customer_orders;


-- ============================================================
-- 10. EXECUTIVE COMMERCIAL OPPORTUNITY MATRIX
-- ============================================================

WITH customer_value AS (

    SELECT

        CustomerID,

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
        ) AS net_revenue

    FROM transactions

    WHERE IsCustomerIdentified = TRUE

    GROUP BY CustomerID
),

classified AS (

    SELECT

        CustomerID,

        net_revenue,

        CASE
            WHEN net_revenue >= 3000
                THEN 'High Value'
            ELSE 'Standard Value'
        END AS value_class

    FROM customer_value
)

SELECT

    value_class,

    COUNT(*) AS customers,

    ROUND(
        SUM(net_revenue),
        2
    ) AS net_revenue,

    ROUND(
        AVG(net_revenue),
        2
    ) AS average_customer_value

FROM classified

GROUP BY value_class

ORDER BY net_revenue DESC;