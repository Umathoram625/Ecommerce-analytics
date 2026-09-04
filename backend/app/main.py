import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.api.v1 import api_router
from backend.app.models.sales import SaleTransaction
from backend.app.services.data_cleaner import DataCleaningService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context: initialize tables and seed default dataset if empty."""
    print(f"Starting {settings.PROJECT_NAME} (Env: {settings.ENVIRONMENT})...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed database if empty
    db = SessionLocal()
    try:
        count = db.query(SaleTransaction).count()
        if count == 0:
            print("Database is empty. Checking for default sample dataset...")
            env_source = os.getenv("DATA_FILE") or os.getenv("DATA_SOURCE")
            sample_paths = [
                env_source,
                os.path.join("data", "raw", "Global_Superstore.csv"),
                os.path.join("data", "raw", "Global_Superstore.xlsx"),
                settings.DEFAULT_DATA_PATH,
                settings.CLEANED_DATA_PATH,
                os.path.join("data", "raw", "Sample_Superstore.csv"),
            ]
            sample_paths = [p for p in sample_paths if p]
            found = False
            for p in sample_paths:
                if os.path.exists(p):
                    print(f"Auto-seeding initial dataset from {p}...")
                    with open(p, "rb") as f:
                        DataCleaningService.ingest_csv_to_db(
                            csv_content=f.read(),
                            filename=os.path.basename(p),
                            db=db,
                            replace_existing=True
                        )
                    print(f"Successfully seeded database with {p}!")
                    found = True
                    break
            if not found:
                print("Notice: No default sample dataset found at startup. Upload CSV via UI.")
        else:
            print(f"Database ready with {count:,} existing transactions.")
    except Exception as e:
        print(f"Database startup warning: {e}")
    finally:
        db.close()

    yield
    print("Shutting down Application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Static Frontend Serving
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
        
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        target_file = os.path.join(frontend_dir, full_path)
        if os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
