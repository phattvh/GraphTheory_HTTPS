"""Auth router: POST /api/v1/auth/login và GET /api/v1/auth/me (UC01)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from backend.models import NguoiDung
from backend.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Auth (UC01)"])
bearer_scheme = HTTPBearer(auto_error=False)

INVALID_CREDENTIALS_MSG = "Tên đăng nhập hoặc mật khẩu không chính xác."
UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Xác thực tài khoản (bcrypt) và phát hành JWT HS256."""
    user = (
        db.query(NguoiDung)
        .filter(NguoiDung.ten_dang_nhap == payload.ten_dang_nhap)
        .first()
    )
    if user is None or not verify_password(payload.mat_khau, user.mat_khau_hash):
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
def get_me(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Trả về thông tin tài khoản hiện tại dựa trên Bearer JWT hợp lệ."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token xác thực.",
            headers=UNAUTHORIZED_HEADERS,
        )
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn.",
            headers=UNAUTHORIZED_HEADERS,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không hợp lệ.",
            headers=UNAUTHORIZED_HEADERS,
        )

    username = claims.get("sub")
    user = (
        db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == username).first()
        if username
        else None
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại.",
            headers=UNAUTHORIZED_HEADERS,
        )
    return UserOut.model_validate(user)