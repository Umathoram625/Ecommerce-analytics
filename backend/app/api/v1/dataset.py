import io
import os
import pandas as pd
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.sales import SaleTransaction, UploadAuditLog
from backend.app.schemas.analytics import UploadResponse, FilterParams
from backend.app.api.v1.analytics import get_filter_params
from backend.app.services.data_cleaner import DataCleaningService
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_csv_dataset(
    file: UploadFile = File(...),
    replace_existing: bool = Query(True, description="Whether to replace or append data"),
    db: Session = Depends(get_db)
):
    """Upload, automatically validate, clean, and ingest a new CSV dataset."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")
    
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")
    
    try:
        result = DataCleaningService.ingest_csv_to_db(
            csv_content=contents,
            filename=file.filename,
            db=db,
            replace_existing=replace_existing
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data ingestion failed: {str(e)}")

@router.post("/reset")
def reset_to_sample_data(db: Session = Depends(get_db)):
    """Reset database to the original bundled Sample Superstore dataset."""
    sample_paths = [
        settings.DEFAULT_DATA_PATH,
        settings.CLEANED_DATA_PATH,
        os.path.join(os.getcwd(), "data", "raw", "Sample_Superstore.csv"),
        os.path.join(os.getcwd(), "data", "cleaned", "superstore_cleaned.csv")
    ]
    
    found_path = None
    for p in sample_paths:
        if os.path.exists(p):
            found_path = p
            break
            
    if not found_path:
        raise HTTPException(status_code=404, detail="Default sample dataset file not found on server.")
        
    with open(found_path, "rb") as f:
        content = f.read()
        
    result = DataCleaningService.ingest_csv_to_db(
        csv_content=content,
        filename=os.path.basename(found_path),
        db=db,
        replace_existing=True
    )
    return {"message": "Database reset to sample dataset successfully.", "stats": result}

@router.get("/export")
def export_filtered_data(
    filters: FilterParams = Depends(get_filter_params),
    db: Session = Depends(get_db)
):
    """Export the currently filtered transactions as a downloadable CSV."""
    query = db.query(SaleTransaction)
    query = AnalyticsService.apply_filters(query, filters)
    rows = query.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No transactions match the selected filters.")

    data = []
    for r in rows:
        data.append({
            "Order ID": r.order_id,
            "Order Date": str(r.order_date),
            "Ship Date": str(r.ship_date) if r.ship_date else "",
            "Ship Mode": r.ship_mode,
            "Customer ID": r.customer_id,
            "Customer Name": r.customer_name,
            "Segment": r.segment,
            "Country": r.country,
            "City": r.city,
            "State": r.state,
            "Postal Code": r.postal_code,
            "Region": r.region,
            "Product ID": r.product_id,
            "Category": r.category,
            "Sub-Category": r.sub_category,
            "Product Name": r.product_name,
            "Sales": r.sales,
            "Quantity": r.quantity,
            "Discount": r.discount,
            "Profit": r.profit,
            "Shipping Days": r.shipping_days,
            "Profit Margin": r.profit_margin
        })

    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=filtered_ecommerce_sales.csv"
    return response

@router.get("/audit-logs")
def get_upload_audit_logs(db: Session = Depends(get_db)):
    """Retrieve history of dataset uploads and validation audit summaries."""
    logs = db.query(UploadAuditLog).order_by(UploadAuditLog.uploaded_at.desc()).limit(10).all()
    return logs
