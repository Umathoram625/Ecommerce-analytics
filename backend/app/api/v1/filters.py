from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.analytics import FilterOptionsResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("", response_model=FilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)):
    """Fetch distinct available values for all frontend filter dropdowns and date limits."""
    return AnalyticsService.get_filter_options(db)
