from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

class FilterParams(BaseModel):
    year: Optional[int] = None
    quarter: Optional[str] = None
    month: Optional[int] = None
    country: Optional[str] = None
    market: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    product_id: Optional[str] = None
    segment: Optional[str] = None
    ship_mode: Optional[str] = None
    order_status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class KPISummary(BaseModel):
    total_revenue: float
    total_profit: float
    profit_margin: float
    total_orders: int
    units_sold: int
    total_customers: int
    avg_order_value: float
    total_returned_orders: int
    return_rate: float
    returned_revenue: float
    profitable_orders: int
    loss_orders: int
    avg_discount: float
    avg_shipping_cost: float
    # Backward compatibility aliases
    total_sales: Optional[float] = None
    total_quantity: Optional[int] = None

class SalesTrendItem(BaseModel):
    period: str
    year: int
    month: int
    month_name: str
    quarter: str
    revenue: float
    orders: int
    units: int
    yoy_growth: Optional[float] = None
    rolling_3m_revenue: Optional[float] = None
    running_total_revenue: Optional[float] = None
    # Backward compatibility
    sales: Optional[float] = None
    sales_mom_growth: Optional[float] = None
    sales_yoy_growth: Optional[float] = None

class ProfitTrendItem(BaseModel):
    period: str
    year: int
    month: int
    month_name: str
    profit: float
    profit_margin: float
    profitable_orders: int
    loss_making_orders: int

class CategoryPerformanceItem(BaseModel):
    category: str
    revenue: float
    profit: float
    profit_margin: float
    orders: int
    quantity: int
    share_of_total: float
    # Backward compatibility
    sales: Optional[float] = None

class SubCategoryPerformanceItem(BaseModel):
    sub_category: str
    category: str
    revenue: float
    profit: float
    profit_margin: float
    orders: int
    quantity: int
    share_of_category: float
    # Backward compatibility
    sales: Optional[float] = None

class ProductPerformanceItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    sub_category: str
    revenue: float
    profit: float
    quantity: int
    profit_margin: float
    avg_discount: float
    # Backward compatibility
    sales: Optional[float] = None

class TopCustomerItem(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    country: str
    total_spend: float
    total_profit: float
    order_count: int
    avg_order_value: float

class CustomerPerformanceResponse(BaseModel):
    total_customers: int
    repeat_customers: int
    single_purchase_customers: int
    repeat_customer_rate: float
    avg_revenue_per_customer: float
    customer_contribution_top20: float
    top_customers: List[TopCustomerItem]
    # Backward compatibility
    segments: Optional[List[Any]] = None

class CustomerSegmentItem(BaseModel):
    segment: str
    customer_count: int
    revenue: float
    profit: float
    profit_margin: float
    orders_count: int
    avg_spend: float
    share_of_revenue: float
    # Backward compatibility
    sales: Optional[float] = None

class RFMSegmentItem(BaseModel):
    segment: str
    customer_count: int
    total_revenue: float
    total_profit: float
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: float
    share_of_customers: float

class GeographyItem(BaseModel):
    country: str
    market: str
    region: str
    revenue: float
    profit: float
    profit_margin: float
    orders: int
    # Backward compatibility
    sales: Optional[float] = None

class ShippingItem(BaseModel):
    ship_mode: str
    order_count: int
    total_revenue: float
    total_profit: float
    avg_shipping_cost: float
    avg_shipping_days: float
    # Backward compatibility
    sales: Optional[float] = None

class DiscountImpactItem(BaseModel):
    discount_band: str
    min_discount: float
    max_discount: float
    order_count: int
    revenue: float
    profit: float
    profit_margin: float
    loss_orders_count: int
    # Backward compatibility
    sales: Optional[float] = None

class OrderItem(BaseModel):
    row_id: int
    order_id: str
    order_date: str
    ship_date: Optional[str] = None
    customer_name: str
    country: str
    region: str
    product_name: str
    category: str
    sub_category: str
    quantity: int
    unit_price: float
    sales: float
    discount: float
    profit: float
    order_status: str
    ship_mode: str

class PaginatedOrdersResponse(BaseModel):
    total_records: int
    page: int
    page_size: int
    total_pages: int
    data: List[OrderItem]

class ReturnsResponse(BaseModel):
    total_returns: int
    return_rate: float
    returned_revenue: float
    top_returned_products: List[Dict[str, Any]]
    top_returned_customers: List[Dict[str, Any]]

class DynamicInsightItem(BaseModel):
    title: str
    description: str
    category: str
    status: str

class DynamicInsightsResponse(BaseModel):
    insights: List[DynamicInsightItem]

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
    years: List[int]
    quarters: List[str]
    months: List[Dict[str, Any]]
    countries: List[str]
    markets: List[str]
    regions: List[str]
    categories: List[str]
    sub_categories: List[str]
    segments: List[str]
    ship_modes: List[str]
    order_statuses: List[str]
    date_range: Dict[str, str]

class UploadResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    status: str
    message: str
    duration_seconds: float
    columns_detected: List[str]
    column_mappings: Dict[str, str] = {}
    warnings: List[str] = []
