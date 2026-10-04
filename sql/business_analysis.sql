-- Corrected business-analysis queries for the real Olist dataset.

-- 1. Dataset size
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN order_status <> 'canceled' THEN 1 ELSE 0 END) AS non_canceled_orders
FROM orders;

-- 2. Revenue by category
SELECT
    COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN category_translation ct
  ON ct.product_category_name = p.product_category_name
WHERE o.order_status <> 'canceled'
GROUP BY category
ORDER BY revenue DESC;

-- 3. Monthly revenue
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS month,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status <> 'canceled'
GROUP BY month
ORDER BY month;

-- 4. Revenue by customer state
SELECT
    c.customer_state AS state,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status <> 'canceled'
GROUP BY c.customer_state
ORDER BY revenue DESC;

-- 5. Payment value mix
-- Payment value is preferred over order counts because one order can
-- use multiple payment methods.
SELECT
    payment_type,
    ROUND(SUM(payment_value), 2) AS payment_value
FROM payments p
JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status <> 'canceled'
GROUP BY payment_type
ORDER BY payment_value DESC;

-- 6. Repeat-customer rate
-- customer_unique_id is the customer-level identifier.
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status <> 'canceled'
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS repeat_customer_pct
FROM customer_orders;

-- 7. Top sellers
SELECT
    oi.seller_id,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status <> 'canceled'
GROUP BY oi.seller_id
ORDER BY revenue DESC
LIMIT 10;

-- 8. Core-period month-over-month revenue growth.
-- Sparse edge periods are excluded from the headline trend.
WITH monthly AS (
    SELECT
        strftime('%Y-%m', o.order_purchase_timestamp) AS month,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status <> 'canceled'
    GROUP BY month
),
core AS (
    SELECT *
    FROM monthly
    WHERE month >= '2017-01'
      AND month <= '2018-08'
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0),
        2
    ) AS mom_growth_pct
FROM core
ORDER BY month;
