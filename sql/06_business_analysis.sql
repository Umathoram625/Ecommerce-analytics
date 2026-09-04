-- ==============================================================================
-- PROJECT: E-Commerce Sales Analytics Portfolio Project
-- SCRIPT: 06_business_analysis.sql
-- DATABASE: superstore.db (SQLite 3.30+)
-- TABLE: superstore_sales (9,994 validated records)
-- DESCRIPTION: Comprehensive suite of 25 enterprise SQL business queries
-- ==============================================================================


-- ==============================================================================
-- SECTION 1: CORE BUSINESS KPIS | Overall Executive Business KPIs
-- ==============================================================================
-- Query 01: Core Executive KPIs
-- Business Question: What are the aggregate baseline commercial KPIs for the enterprise?
SELECT 
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity) AS total_quantity_sold,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS average_order_value,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS average_discount_pct,
    ROUND(AVG(shipping_days), 2) AS average_shipping_days
FROM superstore_sales;


-- ==============================================================================
-- SECTION 2: TIME-BASED ANALYSIS | Annual Sales and Profit Performance
-- ==============================================================================
-- Query 02: Annual Sales and Profit
SELECT 
    year,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM superstore_sales
GROUP BY year
ORDER BY year ASC;


-- ==============================================================================
-- SECTION 2: TIME-BASED ANALYSIS | Year-over-Year (YoY) Sales and Profit Growth
-- ==============================================================================
-- Query 03: Year-over-Year (YoY) Growth using Window LAG()
WITH yearly_summary AS (
    SELECT 
        year,
        ROUND(SUM(sales), 2) AS annual_sales,
        ROUND(SUM(profit), 2) AS annual_profit
    FROM superstore_sales
    GROUP BY year
)
SELECT 
    year,
    annual_sales,
    LAG(annual_sales, 1) OVER (ORDER BY year) AS prior_year_sales,
    ROUND(((annual_sales - LAG(annual_sales, 1) OVER (ORDER BY year)) / LAG(annual_sales, 1) OVER (ORDER BY year)) * 100, 2) AS yoy_sales_growth_pct,
    annual_profit,
    LAG(annual_profit, 1) OVER (ORDER BY year) AS prior_year_profit,
    ROUND(((annual_profit - LAG(annual_profit, 1) OVER (ORDER BY year)) / LAG(annual_profit, 1) OVER (ORDER BY year)) * 100, 2) AS yoy_profit_growth_pct
FROM yearly_summary
ORDER BY year ASC;


-- ==============================================================================
-- SECTION 2: TIME-BASED ANALYSIS | Monthly Revenue, Profit, and Order Volume
-- ==============================================================================
-- Query 04: Monthly Sales and Profit Trend
SELECT 
    year_month,
    year,
    month,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS monthly_sales,
    ROUND(SUM(profit), 2) AS monthly_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM superstore_sales
GROUP BY year_month, year, month
ORDER BY year_month ASC;


-- ==============================================================================
-- SECTION 2: TIME-BASED ANALYSIS | Quarterly Sales and Profit Breakdown
-- ==============================================================================
-- Query 05: Quarterly Performance Breakdown
SELECT 
    year,
    quarter,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(sales), 2) AS quarterly_sales,
    ROUND(SUM(profit), 2) AS quarterly_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM superstore_sales
GROUP BY year, quarter
ORDER BY year ASC, quarter ASC;


-- ==============================================================================
-- SECTION 2: TIME-BASED ANALYSIS | Aggregated Monthly Seasonality Pattern
-- ==============================================================================
-- Query 06: Aggregated Monthly Seasonality
SELECT 
    month AS month_number,
    month_name AS month,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS cumulative_sales,
    ROUND(SUM(profit), 2) AS cumulative_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM superstore_sales
GROUP BY month, month_name
ORDER BY month ASC;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Sales and Profit by Category
-- ==============================================================================
-- Query 07: Sales and Profit by Category
SELECT 
    category,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND((SUM(sales) / (SELECT SUM(sales) FROM superstore_sales)) * 100, 2) AS revenue_share_pct,
    ROUND((SUM(profit) / (SELECT SUM(profit) FROM superstore_sales)) * 100, 2) AS profit_share_pct
FROM superstore_sales
GROUP BY category
ORDER BY total_sales DESC;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Sub-Category Sales, Profit, and Profit Margin
-- ==============================================================================
-- Query 08: Sub-Category Profitability Matrix
SELECT 
    category,
    sub_category,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    DENSE_RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
FROM superstore_sales
GROUP BY category, sub_category
ORDER BY total_profit DESC;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Top 10 Products by Sales Revenue
-- ==============================================================================
-- Query 09: Top 10 Products by Sales (DENSE_RANK)
WITH ranked_products AS (
    SELECT 
        product_name,
        category,
        sub_category,
        SUM(quantity) AS total_quantity,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        DENSE_RANK() OVER (ORDER BY SUM(sales) DESC) AS sales_rank
    FROM superstore_sales
    GROUP BY product_name, category, sub_category
)
SELECT * FROM ranked_products WHERE sales_rank <= 10;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Top 10 Products by Net Profit
-- ==============================================================================
-- Query 10: Top 10 Products by Profit (DENSE_RANK)
WITH ranked_products AS (
    SELECT 
        product_name,
        category,
        sub_category,
        SUM(quantity) AS total_quantity,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        DENSE_RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
    FROM superstore_sales
    GROUP BY product_name, category, sub_category
)
SELECT * FROM ranked_products WHERE profit_rank <= 10;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Bottom 10 Products by Profit (Highest Loss Leaders)
-- ==============================================================================
-- Query 11: Bottom 10 Products by Profit (Loss Leaders)
WITH ranked_products AS (
    SELECT 
        product_name,
        category,
        sub_category,
        SUM(quantity) AS total_quantity,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_loss,
        ROUND(AVG(discount) * 100, 2) AS avg_discount_pct,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        DENSE_RANK() OVER (ORDER BY SUM(profit) ASC) AS loss_rank
    FROM superstore_sales
    GROUP BY product_name, category, sub_category
    HAVING SUM(profit) < 0
)
SELECT * FROM ranked_products WHERE loss_rank <= 10;


-- ==============================================================================
-- SECTION 3: PRODUCT & CATEGORY ANALYSIS | Products with High Sales (> $3,000) but Negative Profit
-- ==============================================================================
-- Query 12: High Sales (> $3,000) but Negative Profit Products
SELECT 
    product_name,
    category,
    sub_category,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_loss,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    COUNT(row_id) AS transaction_count
FROM superstore_sales
GROUP BY product_name, category, sub_category
HAVING SUM(sales) > 3000 AND SUM(profit) < 0
ORDER BY total_loss ASC;


-- ==============================================================================
-- SECTION 4: CUSTOMER ANALYSIS | Top 10 Customers by Revenue Spend
-- ==============================================================================
-- Query 13: Top 10 Customers by Sales (RANK)
WITH customer_ranks AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS units_purchased,
        ROUND(SUM(sales), 2) AS total_spend,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        RANK() OVER (ORDER BY SUM(sales) DESC) AS sales_rank
    FROM superstore_sales
    GROUP BY customer_id, customer_name, segment
)
SELECT * FROM customer_ranks WHERE sales_rank <= 10;


-- ==============================================================================
-- SECTION 4: CUSTOMER ANALYSIS | Top 10 Customers by Net Profit Contribution
-- ==============================================================================
-- Query 14: Top 10 Customers by Profit Contribution
WITH customer_ranks AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(SUM(sales), 2) AS total_spend,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
    FROM superstore_sales
    GROUP BY customer_id, customer_name, segment
)
SELECT * FROM customer_ranks WHERE profit_rank <= 10;


-- ==============================================================================
-- SECTION 4: CUSTOMER ANALYSIS | Customer Revenue Concentration (Pareto 80/20 Distribution)
-- ==============================================================================
-- Query 15: Customer Spend Concentration & Pareto Analysis
WITH customer_totals AS (
    SELECT 
        customer_id,
        SUM(sales) AS customer_spend
    FROM superstore_sales
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT 
        customer_id,
        customer_spend,
        ROW_NUMBER() OVER (ORDER BY customer_spend DESC) AS customer_rank,
        COUNT(*) OVER () AS total_customers,
        SUM(customer_spend) OVER (ORDER BY customer_spend DESC) AS cumulative_sales,
        SUM(customer_spend) OVER () AS total_revenue
    FROM customer_totals
)
SELECT 
    customer_rank,
    ROUND((CAST(customer_rank AS REAL) / total_customers) * 100, 2) AS customer_percentile,
    ROUND(customer_spend, 2) AS customer_spend,
    ROUND(cumulative_sales, 2) AS cumulative_sales,
    ROUND((cumulative_sales / total_revenue) * 100, 2) AS cumulative_revenue_share_pct
FROM ranked_customers
WHERE customer_rank IN (
    CAST(total_customers * 0.05 AS INT),
    CAST(total_customers * 0.10 AS INT),
    CAST(total_customers * 0.20 AS INT),
    CAST(total_customers * 0.50 AS INT),
    total_customers
)
ORDER BY customer_rank ASC;


-- ==============================================================================
-- SECTION 5: REGIONAL & SEGMENT ANALYSIS | Regional Sales, Profit, and Margin Rankings
-- ==============================================================================
-- Query 16: Regional Performance Ranking
SELECT 
    region,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    DENSE_RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
FROM superstore_sales
GROUP BY region
ORDER BY profit_rank ASC;


-- ==============================================================================
-- SECTION 5: REGIONAL & SEGMENT ANALYSIS | Top 5 Profitable vs Bottom 5 Deficit States
-- ==============================================================================
-- Query 17: Top 5 and Bottom 5 States by Profit
WITH state_ranks AS (
    SELECT 
        state,
        region,
        COUNT(DISTINCT order_id) AS order_count,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
        ROUND(AVG(discount) * 100, 2) AS avg_discount_pct,
        ROW_NUMBER() OVER (ORDER BY SUM(profit) DESC) AS rank_top,
        ROW_NUMBER() OVER (ORDER BY SUM(profit) ASC) AS rank_bottom
    FROM superstore_sales
    GROUP BY state, region
)
SELECT 
    state,
    region,
    order_count,
    total_sales,
    total_profit,
    profit_margin_pct,
    avg_discount_pct,
    CASE 
        WHEN rank_top <= 5 THEN 'Top 5 Profitable'
        WHEN rank_bottom <= 5 THEN 'Bottom 5 Deficit'
    END AS state_group
FROM state_ranks
WHERE rank_top <= 5 OR rank_bottom <= 5
ORDER BY total_profit DESC;


-- ==============================================================================
-- SECTION 5: REGIONAL & SEGMENT ANALYSIS | Customer Segment Commercial Performance
-- ==============================================================================
-- Query 18: Customer Segment Performance
SELECT 
    segment,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS average_order_value
FROM superstore_sales
GROUP BY segment
ORDER BY total_sales DESC;


-- ==============================================================================
-- SECTION 5: REGIONAL & SEGMENT ANALYSIS | Shipping Duration and Profitability by Ship Mode
-- ==============================================================================
-- Query 19: Ship Mode Logistics and Profitability
SELECT 
    ship_mode,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(AVG(shipping_days), 2) AS avg_shipping_days,
    MIN(shipping_days) AS min_shipping_days,
    MAX(shipping_days) AS max_shipping_days,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct
FROM superstore_sales
GROUP BY ship_mode
ORDER BY avg_shipping_days ASC;


-- ==============================================================================
-- SECTION 6: DISCOUNT & PROFITABILITY | Profitability Analysis across Discount Bands
-- ==============================================================================
-- Query 20: Performance Across Discount Bands
WITH discount_banded AS (
    SELECT 
        CASE 
            WHEN discount = 0.00 THEN '0%'
            WHEN discount > 0.00 AND discount <= 0.10 THEN '>0%-10%'
            WHEN discount > 0.10 AND discount <= 0.20 THEN '>10%-20%'
            WHEN discount > 0.20 AND discount <= 0.30 THEN '>20%-30%'
            WHEN discount > 0.30 AND discount <= 0.40 THEN '>30%-40%'
            WHEN discount > 0.40 THEN '>40%'
            ELSE 'Other'
        END AS discount_band,
        sales,
        profit,
        discount
    FROM superstore_sales
)
SELECT 
    discount_band,
    COUNT(*) AS transaction_count,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM discount_banded
GROUP BY discount_band
ORDER BY 
    CASE discount_band
        WHEN '0%' THEN 1
        WHEN '>0%-10%' THEN 2
        WHEN '>10%-20%' THEN 3
        WHEN '>20%-30%' THEN 4
        WHEN '>30%-40%' THEN 5
        WHEN '>40%' THEN 6
        ELSE 7
    END;


-- ==============================================================================
-- SECTION 7: ADVANCED SQL ANALYTICS | Cumulative Running Total of Sales and Profit
-- ==============================================================================
-- Query 21: Cumulative Running Totals over Time
WITH monthly_metrics AS (
    SELECT 
        year_month,
        SUM(sales) AS monthly_sales,
        SUM(profit) AS monthly_profit
    FROM superstore_sales
    GROUP BY year_month
)
SELECT 
    year_month,
    ROUND(monthly_sales, 2) AS monthly_sales,
    ROUND(SUM(monthly_sales) OVER (ORDER BY year_month ASC), 2) AS running_total_sales,
    ROUND(monthly_profit, 2) AS monthly_profit,
    ROUND(SUM(monthly_profit) OVER (ORDER BY year_month ASC), 2) AS running_total_profit
FROM monthly_metrics
ORDER BY year_month ASC;


-- ==============================================================================
-- SECTION 7: ADVANCED SQL ANALYTICS | Sub-Category Revenue Contribution to Parent Category
-- ==============================================================================
-- Query 22: Sub-Category Contribution to Parent Category (Window Partition)
WITH subcat_totals AS (
    SELECT 
        category,
        sub_category,
        SUM(sales) AS subcat_sales
    FROM superstore_sales
    GROUP BY category, sub_category
)
SELECT 
    category,
    sub_category,
    ROUND(subcat_sales, 2) AS subcat_sales,
    ROUND(SUM(subcat_sales) OVER (PARTITION BY category), 2) AS category_total_sales,
    ROUND((subcat_sales / SUM(subcat_sales) OVER (PARTITION BY category)) * 100, 2) AS subcat_share_pct
FROM subcat_totals
ORDER BY category, subcat_share_pct DESC;


-- ==============================================================================
-- SECTION 7: ADVANCED SQL ANALYTICS | Customer Purchase Frequency Cohorts
-- ==============================================================================
-- Query 23: Customer Repeat Purchase Cohorts
WITH customer_orders AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT order_id) AS order_frequency
    FROM superstore_sales
    GROUP BY customer_id
)
SELECT 
    CASE 
        WHEN order_frequency = 1 THEN '1 Order (One-Time Buyer)'
        WHEN order_frequency BETWEEN 2 AND 4 THEN '2-4 Orders (Occasional)'
        WHEN order_frequency BETWEEN 5 AND 9 THEN '5-9 Orders (Frequent)'
        ELSE '10+ Orders (Power Buyer)'
    END AS buyer_cohort,
    COUNT(customer_id) AS customer_count,
    ROUND((CAST(COUNT(customer_id) AS REAL) / (SELECT COUNT(*) FROM customer_orders)) * 100, 2) AS customer_pct
FROM customer_orders
GROUP BY buyer_cohort
ORDER BY customer_count DESC;


-- ==============================================================================
-- SECTION 7: ADVANCED SQL ANALYTICS | 3-Month Moving Average Revenue Trend
-- ==============================================================================
-- Query 24: 3-Month Moving Average Revenue
WITH monthly_data AS (
    SELECT 
        year_month,
        ROUND(SUM(sales), 2) AS monthly_sales
    FROM superstore_sales
    GROUP BY year_month
)
SELECT 
    year_month,
    monthly_sales,
    ROUND(AVG(monthly_sales) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg_sales
FROM monthly_data
ORDER BY year_month ASC;


-- ==============================================================================
-- SECTION 7: ADVANCED SQL ANALYTICS | Detailed Loss-Making States Breakdown (All Deficit States)
-- ==============================================================================
-- Query 25: Complete Audit of Loss-Making States
SELECT 
    state,
    region,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS net_profit_loss,
    ROUND((SUM(profit) / SUM(sales)) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM superstore_sales
GROUP BY state, region
HAVING SUM(profit) < 0
ORDER BY net_profit_loss ASC;
