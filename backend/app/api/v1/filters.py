from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.analytics import FilterOptionsResponse

router = APIRouter()

@router.get("", response_model=FilterOptionsResponse)
@router.get("/", response_model=FilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)):
    """Fetch distinct dynamic filter options currently available in the database."""
    return AnalyticsService.get_filter_options(db)
