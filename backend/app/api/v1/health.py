import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.sales import SaleTransaction
from backend.app.core.config import settings

router = APIRouter()
start_time = time.time()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Render uptime & health check endpoint."""
    try:
        count = db.query(func.count(SaleTransaction.id)).scalar() or 0
        db_status = "connected"
    except Exception as e:
        count = 0
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - start_time, 2),
        "database": db_status,
        "total_records": count,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }
