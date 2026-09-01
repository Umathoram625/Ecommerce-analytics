from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.analytics import FilterParams, ForecastResponse
from backend.app.api.v1.analytics import get_filter_params
from backend.app.services.forecasting_service import ForecastingService

router = APIRouter()

@router.get("", response_model=ForecastResponse)
def get_sales_forecast(
    metric: str = Query("sales", pattern="^(sales|profit)$", description="Target metric: sales or profit"),
    horizon: int = Query(6, ge=1, le=24, description="Forecast horizon in months"),
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Compute statistical time-series forecasts with 95% confidence intervals."""
    return ForecastingService.generate_forecast(db, metric=metric, horizon=horizon, filters=filters)
