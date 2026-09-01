from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

class FilterParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    segment: Optional[str] = None
    ship_mode: Optional[str] = None
    min_sales: Optional[float] = None
    max_sales: Optional[float] = None

class KPISummary(BaseModel):
    total_sales: float
    total_profit: float
    total_orders: int
    total_customers: int
    avg_order_value: float
    profit_margin: float
    total_quantity: int
    avg_shipping_days: float
    avg_discount: float
    sales_growth_yoy: Optional[float] = None
    profit_growth_yoy: Optional[float] = None

class MonthlyTrendItem(BaseModel):
    year_month: str
    year: int
    month: int
    month_name: str
    sales: float
    profit: float
    orders: int
    profit_margin: float
    sales_mom_growth: Optional[float] = None
    sales_yoy_growth: Optional[float] = None

class CategoryPerformanceItem(BaseModel):
    category: str
    sales: float
    profit: float
    quantity: int
    orders: int
    profit_margin: float
    sub_categories: List[Dict[str, Any]] = []

class ProductPerformanceItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    sub_category: str
    sales: float
    profit: float
    quantity: int
    profit_margin: float

class RegionalPerformanceItem(BaseModel):
    region: str
    sales: float
    profit: float
    orders: int
    customers: int
    profit_margin: float
    top_states: List[Dict[str, Any]] = []

class StatePerformanceItem(BaseModel):
    state: str
    region: str
    sales: float
    profit: float
    orders: int
    profit_margin: float

class CustomerSegmentItem(BaseModel):
    segment: str
    sales: float
    profit: float
    customers: int
    orders: int
    avg_spend: float
    profit_margin: float

class RFMSegmentItem(BaseModel):
    segment: str
    customer_count: int
    avg_recency: float
    avg_frequency: float
    avg_monetary: float
    total_revenue: float
    total_profit: float

class TopCustomerItem(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    total_spend: float
    total_profit: float
    order_count: int
    avg_order_value: float

class ForecastPoint(BaseModel):
    period: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

class ForecastResponse(BaseModel):
    metric: str
    horizon_months: int
    model_name: str
    historical_count: int
    mae: float
    rmse: float
    data: List[ForecastPoint]

class FilterOptionsResponse(BaseModel):
    date_range: Dict[str, str]
    regions: List[str]
    states: List[str]
    categories: List[str]
    sub_categories: List[str]
    segments: List[str]
    ship_modes: List[str]

class UploadResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    status: str
    message: str
    duration_seconds: float
    columns_detected: List[str]
