from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models import NguoiDung
import bcrypt
import jwt

from backend.core.config import settings

BCRYPT_ROUNDS = 12

bearer_scheme = HTTPBearer(auto_error=False)
UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}

def get_password_hash(password: str) -> str:
    """Băm mật khẩu bằng bcrypt (cost factor 12)."""
    if not password:
        raise ValueError("Mật khẩu không được để trống")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Đối chiếu mật khẩu thời gian hằng số (chống timing attack)."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo JWT HS256 có thời hạn exp (mặc định từ settings)."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Giải mã và kiểm chứng chữ ký + hạn dùng của JWT."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> NguoiDung:
    """Xác thực Bearer JWT và trả về ORM NguoiDung hiện tại (lỗi -> 401)."""
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
        if isinstance(username, str) and username
        else None
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại.",
            headers=UNAUTHORIZED_HEADERS,
        )
    return user


def require_admin(
    current_user: NguoiDung = Depends(get_current_user),
) -> NguoiDung:
    """Chặn tài khoản không phải admin (sinh_vien -> 403 Forbidden)."""
    if current_user.vai_tro != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện chức năng này (yêu cầu quyền admin).",
        )
    return current_user