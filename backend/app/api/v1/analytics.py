from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from backend.app.core.database import get_db
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.analytics import (
    FilterParams, KPISummary, SalesTrendItem, ProfitTrendItem,
    CategoryPerformanceItem, SubCategoryPerformanceItem, ProductPerformanceItem,
    CustomerPerformanceResponse, TopCustomerItem, CustomerSegmentItem,
    RFMSegmentItem, GeographyItem, ShippingItem, DiscountImpactItem,
    PaginatedOrdersResponse, ReturnsResponse, DynamicInsightsResponse
)

router = APIRouter()

def get_filter_params(
    year: Optional[int] = Query(None, description="Filter by transaction year"),
    quarter: Optional[str] = Query(None, description="Filter by quarter (e.g. Q1, Q2)"),
    month: Optional[int] = Query(None, description="Filter by month number (1-12)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    market: Optional[str] = Query(None, description="Filter by global market"),
    region: Optional[str] = Query(None, description="Filter by region"),
    state: Optional[str] = Query(None, description="Filter by state or province"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    sub_category: Optional[str] = Query(None, description="Filter by subcategory"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    ship_mode: Optional[str] = Query(None, description="Filter by shipping mode"),
    order_status: Optional[str] = Query(None, description="Filter by order status (Completed, Returned)"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
) -> FilterParams:
    return FilterParams(
        year=year,
        quarter=quarter,
        month=month,
        country=country,
        market=market,
        region=region,
        state=state,
        category=category,
        sub_category=sub_category,
        product_id=product_id,
        segment=segment,
        ship_mode=ship_mode,
        order_status=order_status,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/summary", response_model=KPISummary)
@router.get("/kpis", response_model=KPISummary)
def get_summary_kpis(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Dynamically calculate top-level commercial KPI cards."""
    return AnalyticsService.get_kpis(db, filters)

@router.get("/sales-trend", response_model=List[SalesTrendItem])
@router.get("/trends", response_model=List[SalesTrendItem])
def get_sales_trend(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve dynamic monthly sales trends, order volumes, and growth metrics."""
    return AnalyticsService.get_sales_trend(db, filters)

@router.get("/profit-trend", response_model=List[ProfitTrendItem])
def get_profit_trend(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve monthly profit trajectories and profitable vs loss-making order distributions."""
    return AnalyticsService.get_profit_trend(db, filters)

@router.get("/category-performance", response_model=List[CategoryPerformanceItem])
@router.get("/categories", response_model=List[CategoryPerformanceItem])
def get_category_performance(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve category revenue, profit, margin, and contribution breakdown."""
    return AnalyticsService.get_category_performance(db, filters)

@router.get("/subcategory-performance", response_model=List[SubCategoryPerformanceItem])
def get_subcategory_performance(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve subcategory margin performance and share of parent category."""
    return AnalyticsService.get_subcategory_performance(db, filters)

@router.get("/top-products", response_model=List[ProductPerformanceItem])
@router.get("/products", response_model=List[ProductPerformanceItem])
def get_top_products(
    sort_by: str = Query("revenue", pattern="^(revenue|profit|quantity|sales)$"),
    limit: int = Query(10, ge=1, le=100),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Rank top-performing products by revenue, profit, or units sold."""
    sort_field = "revenue" if sort_by in ["revenue", "sales"] else sort_by
    return AnalyticsService.get_top_products(db, filters, sort_by=sort_field, limit=limit)

@router.get("/loss-making-products", response_model=List[ProductPerformanceItem])
def get_loss_making_products(
    limit: int = Query(10, ge=1, le=100),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Identify products causing the largest commercial margin drainage."""
    return AnalyticsService.get_loss_making_products(db, filters, limit=limit)

@router.get("/customer-performance", response_model=CustomerPerformanceResponse)
@router.get("/customers", response_model=CustomerPerformanceResponse)
def get_customer_performance(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Compute customer cohort metrics, repeat purchase rates, and Pareto contribution."""
    return AnalyticsService.get_customer_performance(db, filters)

@router.get("/top-customers", response_model=List[TopCustomerItem])
def get_top_customers(
    limit: int = Query(10, ge=1, le=100),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Fetch customer lifetime value leaderboard ranked by total spend."""
    perf = AnalyticsService.get_customer_performance(db, filters)
    return perf.top_customers[:limit]

@router.get("/customer-segments", response_model=List[CustomerSegmentItem])
def get_customer_segments(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Analyze customer segment distribution, revenue shares, and profitability."""
    return AnalyticsService.get_customer_segments(db, filters)

@router.get("/rfm", response_model=List[RFMSegmentItem])
def get_rfm_analysis(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Execute dynamic RFM scoring and behavioral clustering for the active filter context."""
    return AnalyticsService.get_rfm_analysis(db, filters)

@router.get("/geography", response_model=List[GeographyItem])
@router.get("/regional", response_model=List[GeographyItem])
def get_geographical_analysis(
    limit: int = Query(20, ge=1, le=150),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Analyze country and regional sales volumes and profit margins."""
    return AnalyticsService.get_geography_analysis(db, filters, limit=limit)

@router.get("/shipping", response_model=List[ShippingItem])
def get_shipping_analysis(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Evaluate shipping modes, logistics expenses, and delivery speed."""
    return AnalyticsService.get_shipping_analysis(db, filters)

@router.get("/discount-impact", response_model=List[DiscountImpactItem])
def get_discount_impact(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Evaluate discount band elasticity and identify margin degradation tiers."""
    return AnalyticsService.get_discount_impact(db, filters)

@router.get("/orders", response_model=PaginatedOrdersResponse)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("order_date"),
    sort_desc: bool = Query(True),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Server-side paginated, searchable, and sortable order transactions ledger."""
    return AnalyticsService.get_orders_paginated(
        db=db,
        filters=filters,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc
    )

@router.get("/returns", response_model=ReturnsResponse)
def get_returns_analysis(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Analyze return rates, returned revenue, and high-return items."""
    return AnalyticsService.get_returns_analysis(db, filters)

@router.get("/insights", response_model=DynamicInsightsResponse)
def get_dynamic_insights(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve dynamic natural-language business insights based on real data rankings."""
    return AnalyticsService.get_dynamic_insights(db, filters)
