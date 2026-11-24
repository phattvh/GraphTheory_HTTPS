from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.database import get_db
from backend.core.config import settings
from backend.models import NguoiDung, KyThi

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)


@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    """Kiểm tra trạng thái dịch vụ FastAPI và kết nối tới container PostgreSQL."""
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "fastapi",
        "database": "connected",
    }
