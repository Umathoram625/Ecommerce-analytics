import io
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.sales import SaleTransaction, UploadAuditLog

class DataCleaningService:
    """Production-grade universal data validation, normalization, and bulk ingestion service.
    
    Dynamically accepts ANY commercial, e-commerce, retail, or trade dataset.
    Intelligently infers schema, auto-maps columns, and applies mathematical fallbacks.
    """

    COLUMN_SYNONYMS = {
        "order_id": [
            "order_id", "order id", "orderid", "trade_id", "trade id", "tradeid",
            "transaction_id", "transaction id", "deal_id", "deal id", "invoice_id", 
            "invoice id", "tx_id", "txid", "ticket_id", "id", "order_no", "bill_no", 
            "reference", "ref_no", "order"
        ],
        "order_date": [
            "order_date", "order date", "orderdate", "trade_date", "trade date", "tradedate",
            "date", "timestamp", "datetime", "purchase_date", "transaction_date", "time", 
            "created_at", "execution_date", "executed_at", "entry_date", "invoice_date"
        ],
        "ship_date": [
            "ship_date", "ship date", "shipdate", "shipping_date", "dispatch_date", 
            "settlement_date", "settled_at", "delivery_date", "completion_date", "exit_date"
        ],
        "ship_mode": [
            "ship_mode", "ship mode", "shipmode", "shipping_mode", "delivery_method", 
            "execution_venue", "exchange", "venue", "order_type", "type", "method", "class"
        ],
        "customer_id": [
            "customer_id", "customer id", "customerid", "client_id", "user_id", 
            "account_id", "trader_id", "counterparty_id", "portfolio_id", "cust_id"
        ],
        "customer_name": [
            "customer_name", "customer name", "customername", "client_name", "user_name", 
            "account_name", "client", "trader_name", "trader", "customer", "buyer", 
            "party", "party_name", "account"
        ],
        "segment": [
            "segment", "customer_segment", "customer segment", "consumer_segment", 
            "market_segment", "tier", "account_type", "client_tier", "classification", 
            "group_type", "division"
        ],
        "country": [
            "country", "nation", "country_region", "country/region", "market_country", 
            "jurisdiction", "domicile"
        ],
        "city": [
            "city", "town", "municipality", "location", "hub", "metro", "center"
        ],
        "state": [
            "state", "province", "region_state", "territory_state", "zone_state", "prefecture"
        ],
        "postal_code": [
            "postal_code", "postal code", "postalcode", "zip", "zip_code", "zipcode", 
            "pin", "pincode", "postcode"
        ],
        "region": [
            "region", "zone", "territory", "geographic_region", "market", "exchange_region", 
            "area", "continent", "district"
        ],
        "product_id": [
            "product_id", "product id", "productid", "item_id", "sku", "symbol", 
            "ticker", "instrument_id", "asset_id", "code", "isin", "security_id"
        ],
        "category": [
            "category", "product_category", "dept", "department", "sector", "industry", 
            "asset_class", "instrument", "asset_type", "item_type", "class"
        ],
        "sub_category": [
            "sub_category", "sub-category", "sub category", "subcategory", "item_group", 
            "sub_sector", "subindustry", "family", "subgroup", "niche"
        ],
        "product_name": [
            "product_name", "product name", "productname", "item_name", "title", 
            "symbol", "ticker", "asset", "security", "instrument_name", "product", 
            "item", "description", "item_description", "name"
        ],
        "sales": [
            "sales", "revenue", "sale_amount", "amount", "total_sales", "turnover", 
            "trade_value", "notional", "value", "total", "grand_total", "gross_amount", 
            "gross_sales", "subtotal", "cost_basis", "transaction_amount", "volume_usd", 
            "price_total", "total_price"
        ],
        "quantity": [
            "quantity", "qty", "units", "items_count", "order_quantity", "volume", 
            "shares", "lots", "contracts", "trade_qty", "size", "count", "num_items"
        ],
        "discount": [
            "discount", "disc", "discount_rate", "discount_percent", "rebate", 
            "fee", "fees", "commission", "spread", "slippage", "cost_basis_fee"
        ],
        "profit": [
            "profit", "net_profit", "margin_amount", "earnings", "income", "pnl", 
            "net_pnl", "realized_pnl", "return", "gain_loss", "net_income", 
            "net_return", "net_gain", "gain", "net"
        ]
    }

    @classmethod
    def detect_column_mappings(cls, df: pd.DataFrame) -> Tuple[Dict[str, str], List[str]]:
        """Map heterogeneous CSV column variations into standard canonical fields with intelligent fallbacks."""
        df_cols_lower = {str(c).strip().lower(): c for c in df.columns}
        rename_map = {}
        detected_canonical = {}
        warnings = []

        # 1. Exact or synonym matching
        for canonical, synonyms in cls.COLUMN_SYNONYMS.items():
            for syn in synonyms:
                clean_syn = syn.strip().lower()
                if clean_syn in df_cols_lower:
                    orig_col = df_cols_lower[clean_syn]
                    rename_map[orig_col] = canonical
                    detected_canonical[canonical] = orig_col
                    break

        # 2. Heuristic detection for Sales / Monetary column if not yet matched
        if "sales" not in detected_canonical:
            candidate_cols = [c for c in df.columns if any(kw in str(c).lower() for kw in ["amount", "price", "val", "total", "usd", "eur", "sum"])]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            matched_col = None
            for c in candidate_cols:
                if c in numeric_cols:
                    matched_col = c
                    break
            if not matched_col and numeric_cols:
                matched_col = numeric_cols[0]

            if matched_col:
                rename_map[matched_col] = "sales"
                detected_canonical["sales"] = matched_col
                warnings.append(f"Inferred Sales / Revenue from column: '{matched_col}'")
            else:
                warnings.append("No numeric sales column detected; auto-generating standard transaction value ($100.00).")

        # 3. Heuristic detection for Date column if not yet matched
        if "order_date" not in detected_canonical:
            date_candidates = [c for c in df.columns if any(kw in str(c).lower() for kw in ["date", "time", "day", "dt", "year", "timestamp"])]
            matched_date_col = None
            for c in date_candidates:
                sample = df[c].dropna().head(5)
                try:
                    pd.to_datetime(sample, errors="raise")
                    matched_date_col = c
                    break
                except Exception:
                    continue
            if matched_date_col:
                rename_map[matched_date_col] = "order_date"
                detected_canonical["order_date"] = matched_date_col
                warnings.append(f"Inferred Order Date from column: '{matched_date_col}'")
            else:
                warnings.append("No date column detected; auto-generating sequential dates spanning the past 12 months.")

        # 4. Check for Profit column
        if "profit" not in detected_canonical:
            profit_candidates = [c for c in df.columns if any(kw in str(c).lower() for kw in ["profit", "pnl", "gain", "margin", "earn", "income", "net"])]
            matched_profit_col = None
            for c in profit_candidates:
                if c in df.select_dtypes(include=[np.number]).columns:
                    matched_profit_col = c
                    break
            if matched_profit_col:
                rename_map[matched_profit_col] = "profit"
                detected_canonical["profit"] = matched_profit_col
                warnings.append(f"Inferred Profit / PnL from column: '{matched_profit_col}'")
            else:
                warnings.append("No profit column detected; estimated dynamically at 15% standard margin.")

        return rename_map, warnings

    @classmethod
    def clean_and_transform_dataframe(cls, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate, coerce data types, clean anomalies, and compute derived dimensions for ANY dataset."""
        initial_rows = len(df_raw)
        stats = {
            "initial_rows": initial_rows,
            "missing_imputed": 0,
            "duplicates_removed": 0,
            "invalid_dates": 0,
            "invalid_numbers": 0,
            "final_valid_rows": 0,
            "column_mappings": {},
            "warnings": []
        }

        rename_map, warnings = cls.detect_column_mappings(df_raw)
        stats["column_mappings"] = {str(k): str(v) for k, v in rename_map.items()}
        stats["warnings"] = warnings

        df = df_raw.rename(columns=rename_map).copy()

        # Deduplicate
        if "order_id" in df.columns and "order_date" in df.columns and "sales" in df.columns:
            dup_cols = [c for c in ["order_id", "product_id", "order_date", "sales"] if c in df.columns]
            if dup_cols:
                dup_count = df.duplicated(subset=dup_cols).sum()
                if dup_count > 0:
                    df = df.drop_duplicates(subset=dup_cols).reset_index(drop=True)
                    stats["duplicates_removed"] = int(dup_count)

        # 1. Order Date Parsing / Generation
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
            invalid_dates = df["order_date"].isna().sum()
            if invalid_dates > 0:
                stats["invalid_dates"] = int(invalid_dates)
                df["order_date"] = df["order_date"].ffill()
                if df["order_date"].isna().any():
                    df["order_date"] = df["order_date"].fillna(datetime.now())
        else:
            base_date = datetime.now() - timedelta(days=365)
            step = 365.0 / max(1, len(df))
            df["order_date"] = [base_date + timedelta(days=int(i * step)) for i in range(len(df))]

        # 2. Ship Date
        if "ship_date" in df.columns:
            df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce", format="mixed")
            bad_ship = df["ship_date"].isna() | (df["ship_date"] < df["order_date"])
            df.loc[bad_ship, "ship_date"] = df.loc[bad_ship, "order_date"] + pd.Timedelta(days=3)
        else:
            df["ship_date"] = df["order_date"] + pd.Timedelta(days=3)

        # 3. Numeric Coercion & Dynamic Derivation
        if "sales" in df.columns:
            df["sales"] = pd.to_numeric(df["sales"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
        else:
            price_col = next((c for c in df.columns if "price" in str(c).lower()), None)
            qty_col = next((c for c in df.columns if "qty" in str(c).lower() or "quantity" in str(c).lower()), None)
            if price_col and qty_col:
                p = pd.to_numeric(df[price_col].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(10.0)
                q = pd.to_numeric(df[qty_col].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(1.0)
                df["sales"] = p * q
            else:
                df["sales"] = 100.0

        zero_sales = (df["sales"] <= 0).sum()
        if zero_sales > 0:
            df = df[df["sales"] > 0].reset_index(drop=True)
            stats["invalid_numbers"] += int(zero_sales)

        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(1).astype(int)
            df["quantity"] = df["quantity"].clip(lower=1)
        else:
            df["quantity"] = 1

        if "discount" in df.columns:
            df["discount"] = pd.to_numeric(df["discount"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
            df.loc[df["discount"] > 1.0, "discount"] = df.loc[df["discount"] > 1.0, "discount"] / 100.0
            df["discount"] = df["discount"].clip(lower=0.0, upper=0.9)
        else:
            df["discount"] = 0.0

        if "profit" in df.columns:
            df["profit"] = pd.to_numeric(df["profit"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(0.0)
        else:
            cost_col = next((c for c in df.columns if "cost" in str(c).lower()), None)
            if cost_col:
                c_val = pd.to_numeric(df[cost_col].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce").fillna(df["sales"] * 0.85)
                df["profit"] = (df["sales"] - c_val).round(2)
            else:
                df["profit"] = (df["sales"] * 0.15).round(2)

        # 4. Text & Categorical Attributes
        defaults = {
            "order_id": [f"TRD-{i+1:05d}" for i in range(len(df))],
            "customer_id": [f"ACC-{(i % 50) + 1:03d}" for i in range(len(df))],
            "customer_name": [f"Account-{(i % 50) + 1}" for i in range(len(df))],
            "segment": "Standard Client",
            "country": "Global",
            "city": "Metro Center",
            "state": "Primary Market",
            "postal_code": "10001",
            "region": "National",
            "product_id": [f"ASSET-{(i % 30) + 1:03d}" for i in range(len(df))],
            "category": "Core Operations",
            "sub_category": "Standard Transactions",
            "product_name": "Standard Item",
            "ship_mode": "Electronic / Standard"
        }

        for col, default_val in defaults.items():
            if col not in df.columns:
                df[col] = default_val
            else:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(["nan", "None", "", "NaN", "null"], "Standard" if isinstance(default_val, str) else "N/A")

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
            from backend.app.core.database import Base
            Base.metadata.create_all(bind=db.get_bind())
            if replace_existing:
                db.query(SaleTransaction).delete()
                db.commit()

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

            msg = f"Successfully ingested {stats['final_valid_rows']:,} records."
            if stats["warnings"]:
                msg += f" ({len(stats['warnings'])} adaptive mappings applied)."

            return {
                "filename": filename,
                "total_rows": stats["initial_rows"],
                "valid_rows": stats["final_valid_rows"],
                "invalid_rows": stats["initial_rows"] - stats["final_valid_rows"],
                "status": "SUCCESS",
                "message": msg,
                "duration_seconds": duration,
                "columns_detected": list(df_raw.columns),
                "column_mappings": stats["column_mappings"],
                "warnings": stats["warnings"]
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
