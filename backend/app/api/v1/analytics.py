from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.analytics import (
    FilterParams, KPISummary, MonthlyTrendItem, 
    CategoryPerformanceItem, ProductPerformanceItem, 
    RegionalPerformanceItem, StatePerformanceItem, 
    RFMSegmentItem
)
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()

def get_filter_params(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    region: Optional[str] = Query(None, description="Region filter"),
    state: Optional[str] = Query(None, description="State filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    sub_category: Optional[str] = Query(None, description="Sub-category filter"),
    segment: Optional[str] = Query(None, description="Customer segment filter"),
    ship_mode: Optional[str] = Query(None, description="Ship mode filter"),
    min_sales: Optional[float] = Query(None, description="Min sales filter"),
    max_sales: Optional[float] = Query(None, description="Max sales filter"),
) -> FilterParams:
    return FilterParams(
        start_date=start_date,
        end_date=end_date,
        region=region,
        state=state,
        category=category,
        sub_category=sub_category,
        segment=segment,
        ship_mode=ship_mode,
        min_sales=min_sales,
        max_sales=max_sales
    )

@router.get("/kpis", response_model=KPISummary)
def get_kpi_summary(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve dynamic aggregated KPIs based on active filters."""
    return AnalyticsService.get_kpis(db, filters)

@router.get("/trends", response_model=List[MonthlyTrendItem])
def get_monthly_trends(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve monthly sales and profit trends over time."""
    return AnalyticsService.get_monthly_trends(db, filters)

@router.get("/categories", response_model=List[CategoryPerformanceItem])
def get_categories(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve category and sub-category performance breakdowns."""
    return AnalyticsService.get_category_performance(db, filters)

@router.get("/products", response_model=List[ProductPerformanceItem])
def get_products(
    sort_by: str = Query("sales", description="Sort by: sales, profit, quantity"),
    ascending: bool = Query(False, description="Ascending order (useful for loss makers)"),
    limit: int = Query(10, ge=1, le=100, description="Top N items"),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve ranked product performance (top sellers or bottom loss-makers)."""
    return AnalyticsService.get_product_performance(db, filters, sort_by=sort_by, ascending=ascending, limit=limit)

@router.get("/regional", response_model=List[RegionalPerformanceItem])
def get_regional(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve regional sales, profit, orders, and nested state breakdown."""
    return AnalyticsService.get_regional_analysis(db, filters)

@router.get("/states", response_model=List[StatePerformanceItem])
def get_states(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve all state-level performance rankings."""
    return AnalyticsService.get_state_performance(db, filters)

@router.get("/customers")
def get_customers(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve customer segments and top 10 customer leaderboard."""
    return AnalyticsService.get_customer_analysis(db, filters)

@router.get("/rfm", response_model=List[RFMSegmentItem])
def get_rfm_segments(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Retrieve RFM (Recency, Frequency, Monetary) behavioral cohort distribution."""
    return AnalyticsService.get_rfm_segmentation(db, filters)
