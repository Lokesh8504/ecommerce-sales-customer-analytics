-- MySQL 8+ version of the business-analysis questions.
-- Load the public Target/Olist dataset into MySQL first.
-- Table names expected:
-- customers, orders, order_items, payments, reviews, products, sellers

-- 1. Unique customer cities
SELECT COUNT(DISTINCT customer_city) AS unique_cities
FROM customers;

-- 2. Orders placed in 2017
SELECT COUNT(*) AS orders_2017
FROM orders
WHERE YEAR(order_purchase_timestamp) = 2017;

-- 3. Total sales per category
SELECT p.product_category_name,
       ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status <> 'canceled'
GROUP BY p.product_category_name
ORDER BY revenue DESC;

-- 4. Percentage of orders paid in installments
SELECT ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN payment_installments > 1 THEN order_id END)
    / COUNT(DISTINCT order_id), 2
) AS installment_order_pct
FROM payments;

-- 5. Customer count by state
SELECT c.customer_state, COUNT(*) AS customers
FROM customers c
GROUP BY c.customer_state
ORDER BY customers DESC;

-- 6. Monthly order count in 2018
SELECT DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
       COUNT(*) AS orders
FROM orders
WHERE YEAR(order_purchase_timestamp) = 2018
GROUP BY month
ORDER BY month;

-- 7. Revenue share by category
WITH category_sales AS (
    SELECT p.product_category_name AS category,
           SUM(oi.price + oi.freight_value) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_status <> 'canceled'
    GROUP BY category
)
SELECT category,
       ROUND(revenue,2) AS revenue,
       ROUND(100 * revenue / SUM(revenue) OVER (),2) AS revenue_share_pct
FROM category_sales
ORDER BY revenue DESC;

-- 8. Average products per order by city
SELECT c.customer_city,
       ROUND(AVG(x.items_per_order),2) AS avg_products_per_order
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN (
    SELECT order_id, COUNT(*) AS items_per_order
    FROM order_items
    GROUP BY order_id
) x ON x.order_id = o.order_id
GROUP BY c.customer_city
ORDER BY avg_products_per_order DESC;

-- 9. Product price vs purchase volume
SELECT p.product_category_name,
       ROUND(AVG(oi.price),2) AS avg_price,
       COUNT(*) AS units_sold
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status <> 'canceled'
GROUP BY p.product_category_name
ORDER BY units_sold DESC;

-- 10. Seller revenue ranking
SELECT seller_id,
       ROUND(SUM(price + freight_value),2) AS revenue,
       DENSE_RANK() OVER (ORDER BY SUM(price + freight_value) DESC) AS revenue_rank
FROM order_items
GROUP BY seller_id;

-- 11. Moving average of order values
WITH order_values AS (
    SELECT o.order_id,
           DATE(o.order_purchase_timestamp) AS order_date,
           SUM(oi.price + oi.freight_value) AS order_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status <> 'canceled'
    GROUP BY o.order_id, order_date
)
SELECT order_id, order_date, order_value,
       ROUND(
         AVG(order_value) OVER (
           ORDER BY order_date
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
         ), 2
       ) AS seven_order_moving_avg
FROM order_values
ORDER BY order_date;

-- 12. Cumulative monthly sales
WITH monthly_sales AS (
    SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
           SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status <> 'canceled'
    GROUP BY month
)
SELECT month,
       ROUND(revenue,2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month),2) AS cumulative_revenue
FROM monthly_sales
ORDER BY month;

-- 13. Month-over-month growth
WITH monthly_sales AS (
    SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
           SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status <> 'canceled'
    GROUP BY month
)
SELECT month,
       ROUND(revenue,2) AS revenue,
       ROUND(
          100 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / NULLIF(LAG(revenue) OVER (ORDER BY month),0), 2
       ) AS mom_growth_pct
FROM monthly_sales
ORDER BY month;

-- 14. Customer retention proxy
WITH customer_orders AS (
    SELECT customer_id,
           COUNT(DISTINCT order_id) AS orders_count
    FROM orders
    WHERE order_status <> 'canceled'
    GROUP BY customer_id
)
SELECT ROUND(
    100 * SUM(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END)
    / COUNT(*), 2
) AS repeat_customer_pct
FROM customer_orders;

-- 15. Top 3 customers by year
WITH customer_year AS (
    SELECT
        o.customer_id,
        YEAR(o.order_purchase_timestamp) AS order_year,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status <> 'canceled'
    GROUP BY o.customer_id, YEAR(o.order_purchase_timestamp)
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY order_year ORDER BY revenue DESC) AS rnk
    FROM customer_year
)
SELECT order_year, customer_id, ROUND(revenue,2) AS revenue, rnk
FROM ranked
WHERE rnk <= 3
ORDER BY order_year, rnk;
