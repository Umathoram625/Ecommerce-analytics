from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Text, Index, Boolean
from backend.app.core.database import Base

class SaleTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    row_id = Column(Integer, index=True, nullable=True)
    order_id = Column(String(50), index=True, nullable=False)
    order_date = Column(Date, index=True, nullable=False)
    ship_date = Column(Date, nullable=True)
    ship_mode = Column(String(50), index=True, nullable=True)
    
    # Customer Information
    customer_id = Column(String(50), index=True, nullable=False)
    customer_name = Column(String(150), index=True, nullable=False)
    segment = Column(String(50), index=True, nullable=False)
    
    # Geography
    country = Column(String(100), index=True, default="United States")
    city = Column(String(100), index=True, nullable=False)
    state = Column(String(100), index=True, nullable=False)
    postal_code = Column(String(20), index=True, nullable=True)
    market = Column(String(50), index=True, default="Global")
    region = Column(String(50), index=True, nullable=False)
    
    # Product
    product_id = Column(String(50), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    sub_category = Column(String(100), index=True, nullable=False)
    product_name = Column(String(300), nullable=False)
    
    # Financials & Metrics
    sales = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    discount = Column(Float, default=0.0)
    profit = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    order_priority = Column(String(30), default="Medium")
    
    # Status & Flags
    order_status = Column(String(30), index=True, default="Completed")
    is_returned = Column(Boolean, default=False, index=True)
    is_profitable = Column(Boolean, default=True, index=True)
    is_discounted = Column(Boolean, default=False, index=True)
    
    # Derived Date Dimensions
    shipping_days = Column(Integer, default=0)
    profit_margin = Column(Float, default=0.0)
    year = Column(Integer, index=True, nullable=False)
    quarter = Column(String(10), index=True, nullable=True)
    month = Column(Integer, index=True, nullable=False)
    month_name = Column(String(20), nullable=True)
    week = Column(Integer, nullable=True)
    day = Column(Integer, nullable=True)
    day_of_week = Column(String(15), nullable=True)
    year_month = Column(String(10), index=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Multi-column indexes for ultra-fast multi-parameter analytical filtering
    __table_args__ = (
        Index("idx_sales_filter_comp", "year", "region", "category", "segment"),
        Index("idx_sales_ym_cat", "year_month", "category"),
        Index("idx_sales_country_market", "country", "market"),
        Index("idx_sales_status_date", "order_status", "order_date"),
    )


class UploadAuditLog(Base):
    __tablename__ = "upload_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_rows = Column(Integer, nullable=False)
    invalid_rows = Column(Integer, default=0)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, PARTIAL, FAILED
    error_summary = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
