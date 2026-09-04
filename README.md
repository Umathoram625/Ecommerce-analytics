# 📊 E-Commerce Sales Analytics Platform (Fully Dynamic Enterprise Edition)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4+-FF6384.svg?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Render](https://img.shields.io/badge/Render-Cloud%20Deploy-46E3B7.svg?logo=render&logoColor=black)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, fully dynamic **E-Commerce Commercial & Sales Analytics** web application powered by **51,290 real-world transactional records** spanning 4 full calendar years (2011–2014) across 147 countries.

Every KPI, trend chart, ranking table, pagination ledger, and business insight is **100% dynamically calculated on-the-fly** from the underlying database in response to user filter selections. **Zero hardcoded metrics or manufactured dates.**

---

## 📌 Executive Summary & Dynamic Dataset Metrics

All metrics across the full 4-year transactional dataset are empirically computed:

```text
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│     TOTAL REVENUE      │  │       NET PROFIT       │  │     PROFIT MARGIN      │
│     $12,642,501.91     │  │     $1,467,457.29      │  │         11.61%         │
└────────────────────────┘  └────────────────────────┘  └────────────────────────┘
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│      TOTAL ORDERS      │  │      TOTAL UNITS       │  │   AVG ORDER VALUE      │
│         25,035         │  │        178,312         │  │        $504.99         │
└────────────────────────┘  └────────────────────────┘  └────────────────────────┘
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│    UNIQUE CUSTOMERS    │  │   AVG DISCOUNT RATE    │  │     RETURNED ORDERS    │
│     1,590 accounts     │  │         14.29%         │  │   1,172 (4.68% rate)   │
└────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

---

## 📂 Dataset Specification

The platform utilizes the complete **Global Superstore** transactional dataset merged with the verified **Returns** ledger:

* **Source Provider**: Tableau Community / Kaggle Open Analytics
* **Total Transactions**: 51,290 line items
* **Unique Orders**: 25,035 commercial orders
* **Date Range**: January 1, 2011 – December 31, 2014 (48 continuous months)
* **Geographic Coverage**: 147 Countries, 7 Global Markets (`APAC`, `EU`, `US`, `LATAM`, `EMEA`, `Africa`, `Canada`), 13 Sub-Regions
* **Product Hierarchy**: 3 Categories (`Technology`, `Furniture`, `Office Supplies`), 17 Subcategories, 10,292 distinct SKU references
* **Customer Base**: 1,590 registered corporate, consumer, and home office accounts
* **Returns Volume**: 1,172 real-world recorded returns ($632,544.75 returned merchandise)

### Data Dictionary

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `row_id` | Integer | Unique surrogate identifier for each transaction line item |
| `order_id` | String | Commercial order identifier (e.g., `CA-2014-100006`, `IN-2013-77878`) |
| `order_date` | Date | Date when the order was placed (`YYYY-MM-DD`) |
| `ship_date` | Date | Date when the order was dispatched |
| `ship_mode` | String | Logistics fulfillment tier: `Same Day`, `First Class`, `Second Class`, `Standard Class` |
| `customer_id` | String | Unique customer identifier |
| `customer_name` | String | Full name of the commercial buyer |
| `segment` | String | Customer market classification: `Consumer`, `Corporate`, `Home Office` |
| `city` / `state` | String | Local delivery destination |
| `country` | String | Sovereign nation (147 unique nations) |
| `postal_code` | String | Postal/ZIP delivery code |
| `market` | String | Macro trade territory (`APAC`, `EU`, `US`, `LATAM`, `EMEA`, `Africa`, `Canada`) |
| `region` | String | Sub-continental geographic sales division |
| `product_id` | String | Catalog product identifier |
| `category` | String | High-level category: `Technology`, `Furniture`, `Office Supplies` |
| `sub_category` | String | Specific merchandise classification (17 subcategories) |
| `product_name` | String | Full title of the purchased product |
| `sales` | Float | Net sales revenue generated ($ USD) |
| `quantity` | Integer | Total units purchased in the line item |
| `discount` | Float | Fractional discount applied (0.00 to 0.85) |
| `profit` | Float | Net operating profit or loss generated ($ USD) |
| `shipping_cost` | Float | Freight logistics expense incurred ($ USD) |
| `order_priority` | String | Urgency tier: `Critical`, `High`, `Medium`, `Low` |
| `order_status` | String | Fulfillment outcome: `Completed` or `Returned` |
| `is_returned` | Boolean | True if order appears in the Returns ledger |
| `is_profitable` | Boolean | True if profit > 0 |
| `is_discounted` | Boolean | True if discount > 0 |
| `shipping_days` | Integer | Lead time days elapsed between order date and ship date |
| `profit_margin` | Float | Ratio of net profit to gross sales revenue (`profit / sales`) |
| `year` / `quarter` / `month` | Derived | Calendar partition attributes for rapid filtering and aggregation |

---

## 🏗️ Architecture & Technology Stack

The application employs a decoupled modern web architecture designed for low latency, sub-second query execution, and high analytical throughput:

```text
[ Browser Client ]  <--->  [ REST API Layer ]  <--->  [ Analytics Engine ]  <--->  [ Database Layer ]
 Vanilla JS (ES6+)          FastAPI (Python 3.11)      SQLAlchemy 2.0 ORM          SQLite 3 (Local)
 Chart.js 4.4               Pydantic v2 Schemas        Pandas Data Pipeline        PostgreSQL (Cloud)
 Responsive CSS3            Gunicorn / Uvicorn         In-Memory Caching           Composite B-Tree Indexes
```

### Core Technologies
* **Backend**: FastAPI 0.109+, Python 3.10 / 3.11, Uvicorn ASGI server.
* **ORM & Database**: SQLAlchemy 2.0+ with optimized multi-column composite indexes (`order_date`, `year`, `category`, `market`, `customer_id`).
* **Frontend**: Vanilla JavaScript (ES6+ modular controllers), HTML5 semantic markup, CSS3 custom design tokens (supporting Dark Mode and Light Mode).
* **Visualization**: Chart.js 4.4+ with dual-axis sales/profit combination charts, doughnut distributions, horizontal category bars, polar area RFM diagrams, and 95% confidence interval forecast bands.
* **Cloud Infrastructure**: Render Web Service configuration via `render.yaml` with persistent volume mount and PostgreSQL database support.

---

## 🌐 Complete REST API Reference (18 Endpoints)

All endpoints accept standard multi-dimensional filter query parameters:
* `year` (e.g. `2014`)
* `quarter` (e.g. `Q3`)
* `month` (e.g. `8`)
* `country` (e.g. `United States`, `Germany`)
* `region` (e.g. `Western Europe`, `Central`)
* `category` (e.g. `Technology`)
* `sub_category` (e.g. `Phones`, `Chairs`)
* `segment` (e.g. `Consumer`, `Corporate`)
* `ship_mode` (e.g. `Second Class`)
* `order_status` (e.g. `Completed`, `Returned`)

### Endpoint Catalog

| HTTP Method | Endpoint Path | Description & Response Model |
| :--- | :--- | :--- |
| `GET` | `/api/v1/analytics/summary` | Core executive KPIs (Revenue, Profit, Margin %, Orders, Units, Customers, AOV, Returns, Shipping). |
| `GET` | `/api/v1/analytics/sales-trend` | Monthly sales progression, YoY growth percentage, 3-month rolling average, cumulative running totals. |
| `GET` | `/api/v1/analytics/profit-trend` | Monthly net profit trajectory, profit margin percentages, and count of loss-making transactions. |
| `GET` | `/api/v1/analytics/categories` | High-level category performance breakdown (Sales, Profit, Margin %, Units, Orders). |
| `GET` | `/api/v1/analytics/subcategories` | 17 Subcategory profitability rankings, sorted by net profit contribution. |
| `GET` | `/api/v1/analytics/top-products` | Top N products sorted by sales revenue or net profit (supports `limit=10`). |
| `GET` | `/api/v1/analytics/loss-making-products` | Deepest loss-generating products (negative margin audit with average discount analysis). |
| `GET` | `/api/v1/analytics/customers/rfm` | Behavioral RFM segmentation breakdown (Champions, Loyalists, At Risk, Hibernating, etc.). |
| `GET` | `/api/v1/analytics/customers/top` | Top individual customer accounts by total revenue spend and lifetime net profit contribution. |
| `GET` | `/api/v1/analytics/geography` | Regional and national commercial performance across 147 countries and 7 global markets. |
| `GET` | `/api/v1/analytics/shipping` | Supply chain logistics breakdown by shipping tier (average duration days, freight costs, margin). |
| `GET` | `/api/v1/analytics/discounts` | Discount elasticity tiers (`0%`, `1-10%`, `11-20%`, `21-30%`, `31-50%`, `>50%`) and margin destruction impact. |
| `GET` | `/api/v1/analytics/orders` | Paginated, searchable transaction ledger (`page`, `page_size`, `search` query). |
| `GET` | `/api/v1/analytics/returns` | Order return audit, return rate analysis, top returned products, and repeat return customer accounts. |
| `GET` | `/api/v1/analytics/insights` | Dynamic, rule-based natural language insights generated directly from filtered dataset metrics. |
| `GET` | `/api/v1/analytics/forecast` | Linear trend trajectory with Holt-Winters seasonal decomposition and 95% confidence intervals. |
| `GET` | `/api/v1/analytics/export/csv` | Streams a dynamic RFC-4180 compliant CSV export containing all records matching active filters. |
| `GET` | `/api/v1/filters/options` | Returns dynamically populated distinct filter options (available years, markets, categories, segments). |

---

## 🔬 Analytical Methodologies & Formulas

### 1. Profitability & Margin
$$\text{Gross Profit} = \sum \text{profit}$$
$$\text{Profit Margin (\%)} = \left( \frac{\sum \text{profit}}{\sum \text{sales}} \right) \times 100$$
$$\text{Average Order Value (AOV)} = \frac{\sum \text{sales}}{\text{COUNT}(\text{DISTINCT } \text{order\_id})}$$

### 2. Customer RFM Behavioral Segmentation
Customers are scored along three behavioral dimensions calculated relative to the latest transaction date:
* **Recency (R)**: Days elapsed since the customer's most recent completed order.
* **Frequency (F)**: Total number of distinct orders completed by the customer.
* **Monetary (M)**: Cumulative net sales revenue generated by the customer.

Using quintile distributions ($1$ to $5$ score), customers are segmented into 9 actionable behavioral cohorts:
* **Champions** ($R \ge 4, F \ge 4, M \ge 4$): High frequency, recent buyers, large commercial basket sizes.
* **Loyal Customers** ($F \ge 3, M \ge 3$): Consistent recurring purchasing cadence.
* **Potential Loyalists** ($R \ge 4, F \ge 2$): Recent buyers with high potential for repeat purchase expansion.
* **At Risk VIPs** ($R \le 2, F \ge 3, M \ge 3$): High-value historical buyers who haven't ordered in 6+ months.
* **Can't Lose Them** ($R = 1, F \ge 4, M \ge 4$): Former key accounts facing critical lapse risk.
* **Hibernating / Lost** ($R \le 2, F \le 2$): Infrequent, low-spend accounts with prolonged inactivity.

### 3. Product Returns Analysis
$$\text{Return Rate (\%)} = \left( \frac{\text{COUNT}(\text{DISTINCT Returned Orders})}{\text{COUNT}(\text{DISTINCT Total Orders})} \right) \times 100$$
All returns are linked to the master order record via exact `order_id` join, tracking both refunded revenue volume and reverse logistics freight impacts.

---

## 🚀 Quick Start & Local Execution

### 1. Prerequisites
* Python 3.10 or 3.11 installed.
* Git installed.

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/johnyarrabolu/Ecommerce-sales-analytics.git
cd Ecommerce-sales-analytics

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Ingest Dataset & Build Database
The ingestion script cleans the raw transactional data, parses ISO dates, coerces numeric fields, maps Returns, computes derived metrics, and bulk-inserts all 51,290 records into the SQLite database with full index coverage:

```bash
# Ingest data into local database
python scripts/ingest_data.py --source data/raw/Global_Superstore.csv --rebuild-db
```

### 4. Execute Standalone SQL Business Queries
Validate all 25 production SQL queries against the local database:
```bash
python scripts/execute_sql_analysis.py
```
This executes all 25 queries, validates non-empty result sets, outputs query runtimes, saves results to `sql/query_results/`, and creates `sql/06_business_analysis.sql`.

### 5. Launch Application Server
Start the local FastAPI development server:
```bash
python run_server.py
```
* **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
* **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc API Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## ☁️ Cloud Deployment (Render)

This repository includes turnkey deployment configuration for **[Render](https://render.com/)**:

1. Fork or push this repository to your GitHub account.
2. Sign in to your Render dashboard and click **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically detect the `render.yaml` specification:
   * **Service Type**: Web Service (Python 3.11)
   * **Build Command**: `pip install -r requirements.txt && python scripts/ingest_data.py`
   * **Start Command**: `gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   * **Disk Storage**: Optional 1GB persistent disk mounted to `/var/data` for SQLite, or connection string to a managed PostgreSQL database via `DATABASE_URL`.
4. Click **Apply**. Render will build the environment, seed the dataset, and launch the application on a live HTTPS URL.

---

## 🔒 Automated Verification & Tests

To run the automated endpoint validation test suite:
```bash
python scratch/test_endpoints.py
```
This suite sends requests to all 18 endpoints, verifying HTTP 200 responses, schema contract validation, and dynamic filtering recalculation.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
