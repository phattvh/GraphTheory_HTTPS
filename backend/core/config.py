import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Hệ thống xếp lịch thi tập trung bằng thuật toán tô màu đồ thị"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://exam_user:exam_pass@postgres:5432/graphtheory_db",
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4  # 4 giờ


settings = Settings()
