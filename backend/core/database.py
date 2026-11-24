"""Database configuration and session management.

Phụ trách: TV2 (Backend: CSDL & Dữ liệu đầu vào)
Tham chiếu: docs/04. Database design.md & docs/09. Project structure.md
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.core.config import settings

# Đảm bảo connection string tương thích với driver psycopg2-binary
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Khởi tạo engine kết nối PostgreSQL
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Tự động kiểm tra trạng thái kết nối trước khi thực thi
    pool_size=10,
    max_overflow=20,
)

# Khởi tạo SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho toàn bộ SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency cung cấp session CSDL cho từng request trong FastAPI.

    Tự động đóng session sau khi xử lý xong request để giải phóng connection pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
