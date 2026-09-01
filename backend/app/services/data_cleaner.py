import io
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.sales import SaleTransaction, UploadAuditLog

class DataCleaningService:
    """Production-grade data validation, normalization, and bulk ingestion service."""

    REQUIRED_LOGICAL_COLUMNS = [
        "order_id", "order_date", "customer_id", "customer_name",
        "segment", "city", "state", "region", "product_id",
        "category", "sub_category", "product_name", "sales", "quantity", "profit"
    ]

    COLUMN_SYNONYMS = {
        "order_id": ["order_id", "order id", "orderid", "transaction_id", "order_no"],
        "order_date": ["order_date", "order date", "orderdate", "date", "purchase_date"],
        "ship_date": ["ship_date", "ship date", "shipdate", "shipping_date", "dispatch_date"],
        "ship_mode": ["ship_mode", "ship mode", "shipmode", "shipping_mode", "delivery_method"],
        "customer_id": ["customer_id", "customer id", "customerid", "client_id", "user_id"],
        "customer_name": ["customer_name", "customer name", "customername", "client_name", "user_name"],
        "segment": ["segment", "customer_segment", "customer segment", "consumer_segment", "market_segment"],
        "country": ["country", "nation", "country_region", "country/region"],
        "city": ["city", "town", "municipality"],
        "state": ["state", "province", "region_state"],
        "postal_code": ["postal_code", "postal code", "postalcode", "zip", "zip_code", "zipcode"],
        "region": ["region", "zone", "territory", "geographic_region"],
        "product_id": ["product_id", "product id", "productid", "item_id", "sku"],
        "category": ["category", "product_category", "dept", "department"],
        "sub_category": ["sub_category", "sub-category", "sub category", "subcategory", "item_group"],
        "product_name": ["product_name", "product name", "productname", "item_name", "title"],
        "sales": ["sales", "revenue", "sale_amount", "amount", "total_sales", "price"],
        "quantity": ["quantity", "qty", "units", "items_count", "order_quantity"],
        "discount": ["discount", "disc", "discount_rate", "discount_percent", "rebate"],
        "profit": ["profit", "net_profit", "margin_amount", "earnings", "income"]
    }

    @classmethod
    def normalize_column_names(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Map heterogeneous CSV column variations into standard canonical names."""
        df_cols = {str(c).strip().lower(): c for c in df.columns}
        rename_map = {}
        for canonical, synonyms in cls.COLUMN_SYNONYMS.items():
            for syn in synonyms:
                clean_syn = syn.strip().lower()
                if clean_syn in df_cols:
                    rename_map[df_cols[clean_syn]] = canonical
                    break
        df = df.rename(columns=rename_map)
        return df

    @classmethod
    def clean_and_transform_dataframe(cls, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate, coerce data types, clean anomalies, and compute derived dimensions."""
        initial_rows = len(df_raw)
        stats = {
            "initial_rows": initial_rows,
            "missing_imputed": 0,
            "duplicates_removed": 0,
            "invalid_dates": 0,
            "invalid_numbers": 0,
            "final_valid_rows": 0,
        }

        df = cls.normalize_column_names(df_raw.copy())

        # Ensure mandatory columns exist
        missing_cols = [c for c in cls.REQUIRED_LOGICAL_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing essential dataset columns: {', '.join(missing_cols)}")

        # 1. Deduplication
        dedup_cols = [c for c in ["order_id", "product_id", "order_date", "sales"] if c in df.columns]
        if dedup_cols:
            dup_count = df.duplicated(subset=dedup_cols).sum()
            if dup_count > 0:
                df = df.drop_duplicates(subset=dedup_cols).reset_index(drop=True)
                stats["duplicates_removed"] = int(dup_count)

        # 2. Date parsing
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
        invalid_order_dates = df["order_date"].isna().sum()
        stats["invalid_dates"] += int(invalid_order_dates)
        df = df.dropna(subset=["order_date"]).reset_index(drop=True)

        if "ship_date" in df.columns:
            df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce", format="mixed")
            # If ship_date missing or before order_date, fallback to order_date + 3 days
            bad_ship = df["ship_date"].isna() | (df["ship_date"] < df["order_date"])
            df.loc[bad_ship, "ship_date"] = df.loc[bad_ship, "order_date"] + pd.Timedelta(days=3)
        else:
            df["ship_date"] = df["order_date"] + pd.Timedelta(days=3)

        # 3. Numeric Coercion & Boundary Validation
        for num_col in ["sales", "profit", "discount", "quantity"]:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce")
            else:
                if num_col == "discount":
                    df[num_col] = 0.0
                elif num_col == "quantity":
                    df[num_col] = 1

        # Fill numeric NAs
        df["sales"] = df["sales"].fillna(0.0)
        df["profit"] = df["profit"].fillna(0.0)
        df["quantity"] = df["quantity"].fillna(1).astype(int)
        df["discount"] = df["discount"].fillna(0.0)

        # Remove negative or zero sales if erroneous
        invalid_sales = (df["sales"] <= 0).sum()
        if invalid_sales > 0:
            df = df[df["sales"] > 0].reset_index(drop=True)
            stats["invalid_numbers"] += int(invalid_sales)

        # Clamp discount between 0.0 and 1.0 (if percentage >= 1.0 like 20 for 20%, scale down)
        df.loc[df["discount"] > 1.0, "discount"] = df.loc[df["discount"] > 1.0, "discount"] / 100.0
        df["discount"] = df["discount"].clip(lower=0.0, upper=0.9)
        df["quantity"] = df["quantity"].clip(lower=1)

        # 4. Text and Categorical Normalization
        text_columns = {
            "customer_id": "CUST-UNKNOWN",
            "customer_name": "Valued Customer",
            "segment": "Consumer",
            "country": "United States",
            "city": "Unknown City",
            "state": "Unknown State",
            "postal_code": "00000",
            "region": "National",
            "product_id": "PROD-UNKNOWN",
            "category": "General",
            "sub_category": "Miscellaneous",
            "product_name": "Standard Product",
            "ship_mode": "Standard Class"
        }
        for col, default_val in text_columns.items():
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(["nan", "None", "", "NaN", "null"], default_val)
            else:
                df[col] = default_val

        # Normalize Postal Code (5-digit padding)
        df["postal_code"] = df["postal_code"].str.replace(r"\.0$", "", regex=True).str.zfill(5)

        # 5. Derived Dimensions
        df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days.clip(lower=0)
        df["profit_margin"] = (df["profit"] / df["sales"]).round(4)
        df["year"] = df["order_date"].dt.year
        df["month"] = df["order_date"].dt.month
        df["month_name"] = df["order_date"].dt.strftime("%B")
        df["quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
        df["year_month"] = df["order_date"].dt.strftime("%Y-%m")

        if "row_id" not in df.columns:
            df["row_id"] = np.arange(1, len(df) + 1)
        else:
            df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce").fillna(np.arange(1, len(df) + 1)).astype(int)

        stats["final_valid_rows"] = len(df)
        return df, stats

    @classmethod
    def ingest_csv_to_db(cls, csv_content: bytes, filename: str, db: Session, replace_existing: bool = True) -> Dict[str, Any]:
        """Ingest raw CSV bytes into PostgreSQL/SQLite via batch bulk insert."""
        start_time = time.time()
        
        # Try common encodings
        df_raw = None
        for enc in ["utf-8", "windows-1252", "latin-1", "iso-8859-1"]:
            try:
                df_raw = pd.read_csv(io.BytesIO(csv_content), encoding=enc)
                break
            except Exception:
                continue
        
        if df_raw is None:
            raise ValueError("Unable to parse CSV file with supported encodings (UTF-8, Windows-1252, Latin-1).")

        df_clean, stats = cls.clean_and_transform_dataframe(df_raw)
        
        try:
            if replace_existing:
                db.query(SaleTransaction).delete()
                db.commit()

            # Bulk insert records in optimized batches
            records = []
            for _, row in df_clean.iterrows():
                tx = SaleTransaction(
                    row_id=int(row["row_id"]),
                    order_id=str(row["order_id"]),
                    order_date=row["order_date"].date() if hasattr(row["order_date"], "date") else row["order_date"],
                    ship_date=row["ship_date"].date() if hasattr(row["ship_date"], "date") else row["ship_date"],
                    ship_mode=str(row["ship_mode"]),
                    customer_id=str(row["customer_id"]),
                    customer_name=str(row["customer_name"]),
                    segment=str(row["segment"]),
                    country=str(row["country"]),
                    city=str(row["city"]),
                    state=str(row["state"]),
                    postal_code=str(row["postal_code"]),
                    region=str(row["region"]),
                    product_id=str(row["product_id"]),
                    category=str(row["category"]),
                    sub_category=str(row["sub_category"]),
                    product_name=str(row["product_name"]),
                    sales=float(row["sales"]),
                    quantity=int(row["quantity"]),
                    discount=float(row["discount"]),
                    profit=float(row["profit"]),
                    shipping_days=int(row["shipping_days"]),
                    profit_margin=float(row["profit_margin"]),
                    year=int(row["year"]),
                    month=int(row["month"]),
                    month_name=str(row["month_name"]),
                    quarter=str(row["quarter"]),
                    year_month=str(row["year_month"])
                )
                records.append(tx)
                if len(records) >= 2000:
                    db.bulk_save_objects(records)
                    db.commit()
                    records = []
            
            if records:
                db.bulk_save_objects(records)
                db.commit()

            duration = round(time.time() - start_time, 2)
            
            audit = UploadAuditLog(
                filename=filename,
                file_size_bytes=len(csv_content),
                total_rows=stats["initial_rows"],
                valid_rows=stats["final_valid_rows"],
                invalid_rows=stats["initial_rows"] - stats["final_valid_rows"],
                status="SUCCESS",
                error_summary=None
            )
            db.add(audit)
            db.commit()

            return {
                "filename": filename,
                "total_rows": stats["initial_rows"],
                "valid_rows": stats["final_valid_rows"],
                "invalid_rows": stats["initial_rows"] - stats["final_valid_rows"],
                "status": "SUCCESS",
                "message": f"Successfully ingested {stats['final_valid_rows']:,} valid transactions.",
                "duration_seconds": duration,
                "columns_detected": list(df_clean.columns)
            }
        except Exception as e:
            db.rollback()
            audit = UploadAuditLog(
                filename=filename,
                file_size_bytes=len(csv_content),
                total_rows=stats.get("initial_rows", 0),
                valid_rows=0,
                invalid_rows=stats.get("initial_rows", 0),
                status="FAILED",
                error_summary=str(e)
            )
            db.add(audit)
            db.commit()
            raise e
