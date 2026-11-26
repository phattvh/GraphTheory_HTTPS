"""Auth router: POST /api/v1/auth/login và GET /api/v1/auth/me (UC01)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import (
    UNAUTHORIZED_HEADERS,
    create_access_token,
    get_current_user,
    verify_password,
)
from backend.models import NguoiDung
from backend.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Auth (UC01)"])

INVALID_CREDENTIALS_MSG = "Tên đăng nhập hoặc mật khẩu không chính xác."
# Hash bcrypt cost 12 giả lập dùng khi user không tồn tại để cân bằng thời gian phản hồi (chống timing attack)
_DUMMY_BCRYPT_HASH = "$2b$12$000000000000000000000u6M0f2Q8nP5kS3xZ1vJ4wL7rT9yB2eG."


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Xác thực tài khoản (bcrypt) và phát hành JWT HS256."""
    user = (
        db.query(NguoiDung)
        .filter(NguoiDung.ten_dang_nhap == payload.ten_dang_nhap)
        .first()
    )
    if user is None:
        verify_password(payload.mat_khau, _DUMMY_BCRYPT_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MSG,
            headers=UNAUTHORIZED_HEADERS,
        )
    if not verify_password(payload.mat_khau, user.mat_khau_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MSG,
            headers=UNAUTHORIZED_HEADERS,
        )

    token = create_access_token(
        {
            "sub": user.ten_dang_nhap,
            "vai_tro": user.vai_tro,
            "mssv": user.mssv,
            "ho_ten": user.ho_ten,
        }
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: NguoiDung = Depends(get_current_user)):
    """Trả về thông tin tài khoản hiện tại dựa trên Bearer JWT hợp lệ."""
    return UserOut.model_validate(current_user)