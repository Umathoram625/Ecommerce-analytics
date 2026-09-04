import sqlite3
import pandas as pd
import os

db_path = 'data/database/superstore.db'
conn = sqlite3.connect(db_path)

results_dir = 'sql/query_results'
os.makedirs(results_dir, exist_ok=True)

# Define all 25 SQL queries with business titles, categories, and code
queries = [
    # --- SECTION 1: CORE BUSINESS KPIs ---
    {
        "id": "q01_core_kpis",
        "section": "Section 1: Core Business KPIs",
        "title": "Overall Executive Business KPIs",
        "question": "What are the aggregate baseline commercial KPIs for the enterprise across all transactions?",
        "sql": """
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
"""
    },
    
    # --- SECTION 2: TIME-BASED ANALYSIS ---
    {
        "id": "q02_sales_profit_by_year",
        "section": "Section 2: Time-Based Analysis",
        "title": "Annual Sales and Profit Performance",
        "question": "What is the annual revenue, profit, and margin breakdown by calendar year?",
        "sql": """
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
"""
    },
    {
        "id": "q03_yoy_growth_analysis",
        "section": "Section 2: Time-Based Analysis",
        "title": "Year-over-Year (YoY) Sales and Profit Growth",
        "question": "What is the annual YoY percentage growth for revenue and net profit calculated using LAG()?",
        "sql": """
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
"""
    },
    {
        "id": "q04_monthly_sales_trend",
        "section": "Section 2: Time-Based Analysis",
        "title": "Monthly Revenue, Profit, and Order Volume",
        "question": "What is the monthly trajectory of revenue, profit, and order volume across all 48 months?",
        "sql": """
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
"""
    },
    {
        "id": "q05_quarterly_performance",
        "section": "Section 2: Time-Based Analysis",
        "title": "Quarterly Sales and Profit Breakdown",
        "question": "How do sales and profits fluctuate by calendar quarter across all years?",
        "sql": """
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
"""
    },
    {
        "id": "q06_seasonality_by_month",
        "section": "Section 2: Time-Based Analysis",
        "title": "Aggregated Monthly Seasonality Pattern",
        "question": "Which calendar months consistently generate the highest and lowest sales across the 4-year period?",
        "sql": """
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
"""
    },
    
    # --- SECTION 3: PRODUCT & CATEGORY ANALYSIS ---
    {
        "id": "q07_category_performance",
        "section": "Section 3: Product & Category Analysis",
        "title": "Sales and Profit by Category",
        "question": "What is the sales, profit, units sold, and profit margin contribution across major product categories?",
        "sql": """
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
"""
    },
    {
        "id": "q08_subcategory_performance",
        "section": "Section 3: Product & Category Analysis",
        "title": "Sub-Category Sales, Profit, and Profit Margin",
        "question": "How do individual sub-categories perform in sales, profit, and margin, ranked by net profit?",
        "sql": """
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
"""
    },
    {
        "id": "q09_top10_products_sales",
        "section": "Section 3: Product & Category Analysis",
        "title": "Top 10 Products by Sales Revenue",
        "question": "Which 10 individual products generated the highest gross revenue?",
        "sql": """
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
"""
    },
    {
        "id": "q10_top10_products_profit",
        "section": "Section 3: Product & Category Analysis",
        "title": "Top 10 Products by Net Profit",
        "question": "Which 10 products generated the highest cumulative net profit?",
        "sql": """
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
"""
    },
    {
        "id": "q11_bottom10_products_loss",
        "section": "Section 3: Product & Category Analysis",
        "title": "Bottom 10 Products by Profit (Highest Loss Leaders)",
        "question": "Which 10 products produced the largest cumulative financial losses?",
        "sql": """
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
"""
    },
    {
        "id": "q12_high_sales_negative_profit",
        "section": "Section 3: Product & Category Analysis",
        "title": "Products with High Sales (> $3,000) but Negative Profit",
        "question": "Which high-volume products generated substantial top-line revenue but operated at a cumulative net loss?",
        "sql": """
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
"""
    },
    
    # --- SECTION 4: CUSTOMER ANALYSIS ---
    {
        "id": "q13_top10_customers_sales",
        "section": "Section 4: Customer Analysis",
        "title": "Top 10 Customers by Revenue Spend",
        "question": "Who are the top 10 customers by cumulative revenue spend, and what is their net profitability?",
        "sql": """
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
"""
    },
    {
        "id": "q14_top10_customers_profit",
        "section": "Section 4: Customer Analysis",
        "title": "Top 10 Customers by Net Profit Contribution",
        "question": "Which 10 customer accounts generated the highest net profit contribution?",
        "sql": """
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
"""
    },
    {
        "id": "q15_customer_pareto_distribution",
        "section": "Section 4: Customer Analysis",
        "title": "Customer Revenue Concentration (Pareto 80/20 Distribution)",
        "question": "What proportion of total revenue is driven by top customer percentiles using cumulative window functions?",
        "sql": """
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
"""
    },
    
    # --- SECTION 5: REGIONAL & SEGMENT ANALYSIS ---
    {
        "id": "q16_regional_performance",
        "section": "Section 5: Regional & Segment Analysis",
        "title": "Regional Sales, Profit, and Margin Rankings",
        "question": "How do the 4 US regions rank in revenue, profit, and percentage margin using DENSE_RANK()?",
        "sql": """
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
"""
    },
    {
        "id": "q17_state_profitability_ranking",
        "section": "Section 5: Regional & Segment Analysis",
        "title": "Top 5 Profitable vs Bottom 5 Deficit States",
        "question": "Which states generate the highest profits, and which 5 states experience the largest cumulative losses?",
        "sql": """
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
"""
    },
    {
        "id": "q18_customer_segment_performance",
        "section": "Section 5: Regional & Segment Analysis",
        "title": "Customer Segment Commercial Performance",
        "question": "What is the revenue, profit, volume, and margin breakdown across Consumer, Corporate, and Home Office segments?",
        "sql": """
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
"""
    },
    {
        "id": "q19_ship_mode_performance",
        "section": "Section 5: Regional & Segment Analysis",
        "title": "Shipping Duration and Profitability by Ship Mode",
        "question": "What is the average transit duration, order volume, revenue, and profit margin across each fulfillment ship mode?",
        "sql": """
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
"""
    },
    
    # --- SECTION 6: DISCOUNT & PROFITABILITY ANALYSIS ---
    {
        "id": "q20_discount_bands_profitability",
        "section": "Section 6: Discount & Profitability",
        "title": "Profitability Analysis across Discount Bands",
        "question": "How do sales volume, net profit, and profit margins behave across standardized discount bands?",
        "sql": """
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
"""
    },
    
    # --- SECTION 7: ADVANCED SQL ANALYTICS ---
    {
        "id": "q21_running_totals_over_time",
        "section": "Section 7: Advanced SQL Analytics",
        "title": "Cumulative Running Total of Sales and Profit",
        "question": "What is the cumulative running total of revenue and profit across consecutive months using window SUM()?",
        "sql": """
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
"""
    },
    {
        "id": "q22_subcategory_share_of_category",
        "section": "Section 7: Advanced SQL Analytics",
        "title": "Sub-Category Revenue Contribution to Parent Category",
        "question": "What percentage does each sub-category contribute to its parent category's total sales using PARTITION BY?",
        "sql": """
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
"""
    },
    {
        "id": "q23_customer_repeat_buyer_cohorts",
        "section": "Section 7: Advanced SQL Analytics",
        "title": "Customer Purchase Frequency Cohorts",
        "question": "How many customer accounts fall into single-order buyers versus repeat purchase tiers?",
        "sql": """
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
"""
    },
    {
        "id": "q24_rolling_3m_average",
        "section": "Section 7: Advanced SQL Analytics",
        "title": "3-Month Moving Average Revenue Trend",
        "question": "What is the 3-month moving average of monthly sales across the entire timeline?",
        "sql": """
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
"""
    },
    {
        "id": "q25_top_loss_making_states_breakdown",
        "section": "Section 7: Advanced SQL Analytics",
        "title": "Detailed Loss-Making States Breakdown (All Deficit States)",
        "question": "Which US states operate at a cumulative net loss, including order count, sales, loss amount, and average discount rate?",
        "sql": """
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
"""
    }
]

print(f"Executing and validating all {len(queries)} SQL queries against superstore.db...")

# Prepare consolidated SQL script
full_sql_content = """-- ==============================================================================
-- PROJECT: E-Commerce Sales Analytics Portfolio Project
-- SCRIPT: 06_business_analysis.sql
-- DATABASE: superstore.db (SQLite 3.30+)
-- TABLE: superstore_sales (9,994 validated records)
-- DESCRIPTION: Comprehensive suite of 25 enterprise SQL business queries
-- ==============================================================================
"""

executed_count = 0
query_outputs = []

for q in queries:
    full_sql_content += f"\n\n-- ==============================================================================\n"
    full_sql_content += f"-- {q['section'].upper()} | {q['title']}\n"
    full_sql_content += f"-- ==============================================================================\n"
    full_sql_content += q['sql'].strip() + "\n"
    
    # Execute query against SQLite
    try:
        clean_sql = q['sql'].strip()
        df_res = pd.read_sql_query(clean_sql, conn)
        executed_count += 1
        
        # Save result CSV
        csv_filename = f"{q['id']}.csv"
        csv_path = os.path.join(results_dir, csv_filename)
        df_res.to_csv(csv_path, index=False)
        
        query_outputs.append({
            "id": q['id'],
            "section": q['section'],
            "title": q['title'],
            "question": q['question'],
            "sql": clean_sql,
            "df": df_res,
            "csv_file": csv_filename
        })
        print(f"[PASSED] Query {executed_count:02d}: {q['title']} -> ({len(df_res)} rows returned)")
    except Exception as e:
        print(f"[FAILED] Query {q['id']}: {e}")

# Write sql/06_business_analysis.sql
with open('sql/06_business_analysis.sql', 'w', encoding='utf-8') as f:
    f.write(full_sql_content)

print(f"\nAll {executed_count}/{len(queries)} queries executed successfully.")
print(f"Saved master SQL script to sql/06_business_analysis.sql")
print(f"Saved {len(query_outputs)} query result CSVs to sql/query_results/")

conn.close()
