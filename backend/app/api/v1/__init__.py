from fastapi import APIRouter
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.forecast import router as forecast_router
from backend.app.api.v1.filters import router as filters_router
from backend.app.api.v1.dataset import router as dataset_router
from backend.app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(forecast_router, prefix="/forecast", tags=["Forecasting"])
api_router.include_router(filters_router, prefix="/filters", tags=["Filters"])
api_router.include_router(dataset_router, prefix="/dataset", tags=["Dataset Management"])
api_router.include_router(health_router, prefix="", tags=["System Health"])
