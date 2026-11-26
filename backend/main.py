from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.database import get_db
from backend.core.config import settings
from backend.models import NguoiDung, KyThi
from backend.routers import auth as auth_router
from backend.routers import master_data as master_data_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)

app.include_router(auth_router.router)
app.include_router(master_data_router.router)

@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    """Kiểm tra trạng thái dịch vụ FastAPI và kết nối tới container PostgreSQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {
        "status": "ok",
        "service": "fastapi",
        "database": "connected",
    }
