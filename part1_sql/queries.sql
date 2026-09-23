-- ============================================================================
-- Meesho Reseller Growth & Alert Intelligence Pipeline - Part 1 SQL Queries
-- Database Target: data/meesho_reseller.db
-- File: part1_sql/queries.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Question 1: Monthly revenue by category
-- GROUP BY month, category, computing revenue = ROUND(SUM(quantity * unit_price), 2)
-- plus n_orders = COUNT(*).
-- Export target: part1_sql/output/monthly_category_revenue.csv
-- ----------------------------------------------------------------------------
SELECT 
    month,
    category,
    ROUND(SUM(quantity * unit_price), 2) AS revenue,
    COUNT(*) AS n_orders
FROM orders
GROUP BY 
    CASE month 
        WHEN 'April' THEN 1 
        WHEN 'May' THEN 2 
        WHEN 'June' THEN 3 
    END,
    month,
    category;

-- ----------------------------------------------------------------------------
-- Question 2: Region-wise total revenue and order count
-- JOIN orders to resellers on reseller_id, GROUP BY region.
-- ----------------------------------------------------------------------------
SELECT 
    r.region,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS total_revenue,
    COUNT(o.order_id) AS order_count
FROM resellers r
JOIN orders o ON r.reseller_id = o.reseller_id
GROUP BY r.region
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- Question 3: Top resellers by total spend (> 50,000)
-- JOIN, GROUP BY reseller_id, HAVING total_spend > 50000,
-- ordered by spend descending, LIMIT 5.
-- ----------------------------------------------------------------------------
SELECT 
    r.reseller_id,
    r.reseller_name,
    ROUND(SUM(o.quantity * o.unit_price), 2) AS total_spend
FROM resellers r
JOIN orders o ON r.reseller_id = o.reseller_id
GROUP BY r.reseller_id, r.reseller_name
HAVING total_spend > 50000
ORDER BY total_spend DESC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- Question 4: Resellers who have never placed an order
-- Part 4A: Identification using LEFT JOIN ... WHERE o.order_id IS NULL
-- ----------------------------------------------------------------------------
SELECT 
    r.reseller_id,
    r.reseller_name,
    r.region
FROM resellers r
LEFT JOIN orders o ON r.reseller_id = o.reseller_id
WHERE o.order_id IS NULL;

-- ----------------------------------------------------------------------------
-- Question 4B: Demonstration of why COUNT(*) cannot be used to test for zero-match
-- in a LEFT JOIN.
-- Grouping the LEFT JOIN result by reseller_id reports:
--   COUNT(*) = 1 (counts the single row with NULL order attributes)
--   COUNT(o.order_id) = 0 (ignores NULLs in the specified column)
-- ----------------------------------------------------------------------------
SELECT 
    r.reseller_id,
    r.reseller_name,
    COUNT(*) AS count_star,
    COUNT(o.order_id) AS count_order_id
FROM resellers r
LEFT JOIN orders o ON r.reseller_id = o.reseller_id
WHERE r.reseller_id = 'RS024'
GROUP BY r.reseller_id, r.reseller_name;

-- ----------------------------------------------------------------------------
-- Question 5: Average Order Value (AOV) for June, Delivered orders only
-- SUM(quantity * unit_price) / COUNT(*) restricted to:
--   month = 'June' AND status = 'Delivered'
-- ----------------------------------------------------------------------------
SELECT 
    ROUND(SUM(quantity * unit_price) / COUNT(*), 2) AS june_delivered_aov
FROM orders
WHERE month = 'June' AND status = 'Delivered';
