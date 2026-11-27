import os
from pydantic import BaseModel, model_validator

MIN_JWT_SECRET_BYTES = 32
INSECURE_DEFAULT_SECRETS = frozenset(
    {
        "dev-secret-change-me-at-least-32-bytes",
        "change-this-secret-in-production-at-least-32-bytes",
    }
)
ALLOWED_APP_ENVS = frozenset({"development", "production", "testing"})


class Settings(BaseModel):
    PROJECT_NAME: str = "Hệ thống xếp lịch thi tập trung bằng thuật toán tô màu đồ thị"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://exam_user:exam_pass@postgres:5432/graphtheory_db",
    )
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "dev-secret-change-me-at-least-32-bytes"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4  # 4 giờ

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        env = (self.APP_ENV or "").strip().lower() or "development"
        if env not in ALLOWED_APP_ENVS:
            raise ValueError(
                f"APP_ENV không hợp lệ: '{self.APP_ENV}' (chấp nhận: development, production, testing)."
            )
        self.APP_ENV = env

        secret = self.JWT_SECRET or ""
        if len(secret.encode("utf-8")) < MIN_JWT_SECRET_BYTES:
            raise ValueError(
                f"JWT_SECRET phải có độ dài tối thiểu {MIN_JWT_SECRET_BYTES} bytes (256-bit) cho thuật toán HS256."
            )

        if self.APP_ENV == "production" and secret in INSECURE_DEFAULT_SECRETS:
            raise ValueError(
                "Không được sử dụng JWT_SECRET mặc định của môi trường dev khi APP_ENV=production."
            )
        return self


settings = Settings()
