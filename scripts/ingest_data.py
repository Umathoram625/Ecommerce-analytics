#!/usr/bin/env python3
"""
Repeatable Data Ingestion and Validation Pipeline for E-Commerce Sales Analytics.
Rebuilds the analytical star-schema database from raw CSV or Excel datasets.

Usage:
    python scripts/ingest_data.py [--source path/to/dataset.csv] [--rebuild-db]
"""

import os
import sys
import argparse
import time
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.sales import SaleTransaction, UploadAuditLog
from backend.app.core.config import settings

def find_raw_dataset(specified_path: str = None) -> str:
    """Find the best available dataset in order of precedence."""
    if specified_path and os.path.exists(specified_path):
        return specified_path

    env_path = os.getenv("DATA_FILE") or os.getenv("DATA_SOURCE")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = [
        os.path.join(BASE_DIR, "data", "raw", "Global_Superstore.csv"),
        os.path.join(BASE_DIR, "data", "raw", "Global_Superstore.xlsx"),
        os.path.join(BASE_DIR, "data", "raw", "Online_Retail.xlsx"),
        os.path.join(BASE_DIR, "data", "raw", "Sample_Superstore.csv"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    # Fallback to any CSV in data/raw
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.lower().endswith((".csv", ".xlsx")):
                return os.path.join(raw_dir, f)

    raise FileNotFoundError("No raw dataset found in data/raw/ or specified path.")

def load_and_clean_data(file_path: str):
    """Load raw dataset, cross-reference returns, validate types, and compute dimensions."""
    print(f"Loading raw dataset from: {file_path}")
    start_t = time.time()

    is_excel = file_path.lower().endswith((".xlsx", ".xls"))
    returns_set = set()

    if is_excel:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        orders_sheet = "Orders" if "Orders" in sheet_names else sheet_names[0]
        df = pd.read_excel(xl, sheet_name=orders_sheet)
        if "Returns" in sheet_names:
            df_ret = pd.read_excel(xl, sheet_name="Returns")
            if "Order ID" in df_ret.columns:
                returns_set = set(df_ret["Order ID"].dropna().unique())
    else:
        for enc in ["utf-8", "latin1", "windows-1252", "iso-8859-1"]:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except Exception:
                continue

    # Check for companion Returns.csv in the same directory
    ret_companion = os.path.join(os.path.dirname(file_path), "Returns.csv")
    if not returns_set and os.path.exists(ret_companion):
        try:
            df_ret = pd.read_csv(ret_companion)
            if "Order ID" in df_ret.columns:
                returns_set = set(df_ret["Order ID"].dropna().unique())
        except Exception:
            pass

    initial_rows = len(df)
    print(f"Raw rows loaded: {initial_rows:,}")

    # Column Synonym Resolution
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        col_map[col] = c_clean

    df = df.rename(columns=col_map)

    # Standardize expected columns
    synonyms = {
        "order_id": ["order_id", "orderid", "invoice_no", "invoiceno"],
        "order_date": ["order_date", "orderdate", "invoice_date", "invoicedate", "date"],
        "ship_date": ["ship_date", "shipdate"],
        "ship_mode": ["ship_mode", "shipmode", "delivery_method"],
        "customer_id": ["customer_id", "customerid", "customer"],
        "customer_name": ["customer_name", "customername", "client_name"],
        "segment": ["segment", "customer_segment"],
        "city": ["city", "town"],
        "state": ["state", "province"],
        "country": ["country", "nation"],
        "postal_code": ["postal_code", "postalcode", "zip", "zip_code"],
        "market": ["market", "trade_market"],
        "region": ["region", "zone"],
        "product_id": ["product_id", "productid", "item_id", "stock_code", "stockcode"],
        "category": ["category", "product_category", "dept"],
        "sub_category": ["sub_category", "subcategory", "item_group"],
        "product_name": ["product_name", "productname", "item_name", "description"],
        "sales": ["sales", "revenue", "amount", "total_revenue"],
        "quantity": ["quantity", "qty", "units"],
        "discount": ["discount", "disc"],
        "profit": ["profit", "net_profit", "earnings"],
        "shipping_cost": ["shipping_cost", "shippingcost", "freight"],
        "order_priority": ["order_priority", "orderpriority", "priority"]
    }

    rename_final = {}
    for canonical, syn_list in synonyms.items():
        for col in df.columns:
            if col in syn_list and canonical not in rename_final.values():
                rename_final[col] = canonical
                break

    df = df.rename(columns=rename_final)

    # Date parsing
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
        df = df.dropna(subset=["order_date"]).reset_index(drop=True)
    else:
        raise ValueError("Missing essential order_date column.")

    if "ship_date" in df.columns:
        df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce", format="mixed")
        bad_ship = df["ship_date"].isna() | (df["ship_date"] < df["order_date"])
        df.loc[bad_ship, "ship_date"] = df.loc[bad_ship, "order_date"] + pd.Timedelta(days=3)
    else:
        df["ship_date"] = df["order_date"] + pd.Timedelta(days=3)

    # Numeric coercion & cleaning
    if "sales" in df.columns:
        df["sales"] = pd.to_numeric(df["sales"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
    else:
        if "quantity" in df.columns and "unit_price" in df.columns:
            df["sales"] = df["quantity"] * df["unit_price"]
        else:
            df["sales"] = 100.0

    # Filter out non-positive sales
    df = df[df["sales"] > 0].reset_index(drop=True)

    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(1).astype(int)
        df["quantity"] = df["quantity"].clip(lower=1)
    else:
        df["quantity"] = 1

    if "unit_price" not in df.columns or df["unit_price"].isna().all():
        df["unit_price"] = (df["sales"] / df["quantity"]).round(2)
    else:
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna((df["sales"] / df["quantity"]).round(2))

    if "discount" in df.columns:
        df["discount"] = pd.to_numeric(df["discount"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
        df.loc[df["discount"] > 1.0, "discount"] = df.loc[df["discount"] > 1.0, "discount"] / 100.0
        df["discount"] = df["discount"].clip(lower=0.0, upper=0.95)
    else:
        df["discount"] = 0.0

    if "profit" in df.columns:
        df["profit"] = pd.to_numeric(df["profit"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
    else:
        # If cost column exists
        if "cost" in df.columns:
            df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(df["sales"] * 0.85)
            df["profit"] = (df["sales"] - df["cost"]).round(2)
        else:
            # Baseline estimated profit
            df["profit"] = (df["sales"] * 0.15).round(2)

    if "shipping_cost" in df.columns:
        df["shipping_cost"] = pd.to_numeric(df["shipping_cost"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0).clip(lower=0.0)
    else:
        df["shipping_cost"] = 0.0

    # Categorical & Dimension Defaults
    text_defaults = {
        "order_id": [f"ORD-{i+1:06d}" for i in range(len(df))],
        "customer_id": [f"CUST-{(i % 2000) + 1:04d}" for i in range(len(df))],
        "customer_name": [f"Customer-{(i % 2000) + 1}" for i in range(len(df))],
        "segment": "Consumer",
        "city": "Unknown",
        "state": "Unknown",
        "country": "United States",
        "postal_code": "00000",
        "market": "Global",
        "region": "Domestic",
        "product_id": [f"PROD-{(i % 1000) + 1:04d}" for i in range(len(df))],
        "category": "General Merchandise",
        "sub_category": "Standard Items",
        "product_name": "Standard Product",
        "ship_mode": "Standard Class",
        "order_priority": "Medium"
    }

    for col, default_val in text_defaults.items():
        if col not in df.columns:
            df[col] = default_val
        else:
            df[col] = df[col].astype(str).str.strip().replace(["nan", "None", "", "NaN", "null"], "Standard" if isinstance(default_val, str) else "N/A")

    # Status and flags
    if returns_set:
        df["is_returned"] = df["order_id"].isin(returns_set)
    elif "is_returned" in df.columns:
        df["is_returned"] = df["is_returned"].astype(bool)
    else:
        df["is_returned"] = False

    df["order_status"] = np.where(df["is_returned"], "Returned", "Completed")
    df["is_profitable"] = df["profit"] > 0
    df["is_discounted"] = df["discount"] > 0

    # Derived dates & metrics
    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days.clip(lower=0)
    df["profit_margin"] = (df["profit"] / df["sales"]).round(4)
    df["year"] = df["order_date"].dt.year.astype(int)
    df["quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["month"] = df["order_date"].dt.month.astype(int)
    df["month_name"] = df["order_date"].dt.strftime("%B")
    df["week"] = df["order_date"].dt.isocalendar().week.astype(int)
    df["day"] = df["order_date"].dt.day.astype(int)
    df["day_of_week"] = df["order_date"].dt.strftime("%A")
    df["year_month"] = df["order_date"].dt.strftime("%Y-%m")

    df["row_id"] = np.arange(1, len(df) + 1, dtype=int)

    duration = round(time.time() - start_t, 2)
    print(f"Data cleaned and transformed in {duration}s. Final valid rows: {len(df):,}")
    return df

def ingest_to_database(df: pd.DataFrame, file_path: str, rebuild_db: bool = True):
    """Rebuild analytical database and bulk load records."""
    print("Connecting to database and preparing tables...")
    start_t = time.time()

    if rebuild_db:
        # Recreate tables to ensure schema matches model
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("Database tables recreated successfully.")
    else:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if not rebuild_db:
            db.query(SaleTransaction).delete()
            db.commit()

        total_rows = len(df)
        batch_size = 3000
        records = []
        inserted = 0

        print(f"Ingesting {total_rows:,} records in batches of {batch_size}...")

        for idx, row in df.iterrows():
            tx = SaleTransaction(
                row_id=int(row["row_id"]),
                order_id=str(row["order_id"]),
                order_date=row["order_date"].date() if hasattr(row["order_date"], "date") else row["order_date"],
                ship_date=row["ship_date"].date() if hasattr(row["ship_date"], "date") else row["ship_date"],
                ship_mode=str(row["ship_mode"]),
                customer_id=str(row["customer_id"]),
                customer_name=str(row["customer_name"]),
                segment=str(row["segment"]),
                city=str(row["city"]),
                state=str(row["state"]),
                country=str(row["country"]),
                postal_code=str(row["postal_code"]),
                market=str(row["market"]),
                region=str(row["region"]),
                product_id=str(row["product_id"]),
                category=str(row["category"]),
                sub_category=str(row["sub_category"]),
                product_name=str(row["product_name"]),
                sales=float(row["sales"]),
                quantity=int(row["quantity"]),
                discount=float(row["discount"]),
                profit=float(row["profit"]),
                unit_price=float(row["unit_price"]),
                shipping_cost=float(row["shipping_cost"]),
                order_priority=str(row["order_priority"]),
                order_status=str(row["order_status"]),
                is_returned=bool(row["is_returned"]),
                is_profitable=bool(row["is_profitable"]),
                is_discounted=bool(row["is_discounted"]),
                shipping_days=int(row["shipping_days"]),
                profit_margin=float(row["profit_margin"]),
                year=int(row["year"]),
                quarter=str(row["quarter"]),
                month=int(row["month"]),
                month_name=str(row["month_name"]),
                week=int(row["week"]),
                day=int(row["day"]),
                day_of_week=str(row["day_of_week"]),
                year_month=str(row["year_month"])
            )
            records.append(tx)

            if len(records) >= batch_size:
                db.bulk_save_objects(records)
                db.commit()
                inserted += len(records)
                print(f"  Progress: {inserted:,} / {total_rows:,} ({inserted/total_rows*100:.1f}%)")
                records = []

        if records:
            db.bulk_save_objects(records)
            db.commit()
            inserted += len(records)

        # Audit log entry
        audit = UploadAuditLog(
            filename=os.path.basename(file_path),
            file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            total_rows=total_rows,
            valid_rows=inserted,
            invalid_rows=0,
            status="SUCCESS",
            error_summary=None
        )
        db.add(audit)
        db.commit()

        # Create compatibility view for standalone SQL queries
        try:
            from sqlalchemy import text
            db.execute(text("CREATE VIEW IF NOT EXISTS superstore_sales AS SELECT * FROM sales_transactions;"))
            db.commit()
        except Exception as e:
            print(f"Notice on view creation: {e}")

        duration = round(time.time() - start_t, 2)
        print(f"\nAll {inserted:,} transactions successfully committed in {duration}s.")
        return inserted
    except Exception as e:
        db.rollback()
        print(f"Error during ingestion: {e}")
        raise e
    finally:
        db.close()

def print_data_quality_report(df: pd.DataFrame, source_file: str):
    """Display comprehensive data quality and validation statistics."""
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    returned_orders = df[df["is_returned"]]["order_id"].nunique()
    total_orders = df["order_id"].nunique()
    return_rate = (returned_orders / total_orders * 100) if total_orders > 0 else 0

    print("\n" + "="*70)
    print("         DATA QUALITY & INGESTION REPORT")
    print("="*70)
    print(f"Source Dataset:         {source_file}")
    print(f"Total Transactions:     {len(df):,}")
    print(f"Unique Orders:          {total_orders:,}")
    print(f"Unique Customers:       {df['customer_id'].nunique():,}")
    print(f"Unique Products:        {df['product_id'].nunique():,}")
    print(f"Date Range:             {df['order_date'].min().date()} to {df['order_date'].max().date()}")
    print(f"Years Detected:         {sorted(df['year'].unique().tolist())}")
    print(f"Countries:              {df['country'].nunique():,}")
    print(f"Markets / Regions:      {df['market'].nunique()} markets, {df['region'].nunique()} regions")
    print(f"Categories:             {df['category'].nunique()} categories, {df['sub_category'].nunique()} subcategories")
    print("-" * 70)
    print(f"Total Gross Revenue:    ${total_sales:,.2f}")
    print(f"Total Net Profit:       ${total_profit:,.2f}")
    print(f"Overall Profit Margin:  {profit_margin:.2f}%")
    print(f"Total Units Sold:       {df['quantity'].sum():,}")
    print(f"Returned Orders:        {returned_orders:,} ({return_rate:.2f}% return rate)")
    print(f"Returned Revenue:       ${df[df['is_returned']]['sales'].sum():,.2f}")
    print(f"Profitable Line Items:  {df['is_profitable'].sum():,} ({df['is_profitable'].mean()*100:.1f}%)")
    print(f"Loss-Making Line Items: {(~df['is_profitable']).sum():,} ({(~df['is_profitable']).mean()*100:.1f}%)")
    print(f"Discounted Line Items:  {df['is_discounted'].sum():,} ({df['is_discounted'].mean()*100:.1f}%)")
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Ingest e-commerce dataset into database.")
    parser.add_argument("--source", type=str, default=None, help="Path to raw CSV or Excel dataset")
    parser.add_argument("--rebuild-db", action="store_true", default=True, help="Recreate database tables")
    args = parser.parse_args()

    file_path = find_raw_dataset(args.source)
    df = load_and_clean_data(file_path)
    ingest_to_database(df, file_path, rebuild_db=args.rebuild_db)
    print_data_quality_report(df, file_path)

if __name__ == "__main__":
    main()
