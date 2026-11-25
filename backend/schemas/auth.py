"""Pydantic v2 schemas cho xác thực Native JWT (UC01)."""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

RoleType = Literal["admin", "sinh_vien"]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ten_dang_nhap: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
    ] = Field(..., examples=["admin"])
    mat_khau: str = Field(..., min_length=1, max_length=128, examples=["admin123"])


class UserOut(BaseModel):
    id: int
    ten_dang_nhap: str
    vai_tro: RoleType
    mssv: Optional[str] = None
    ho_ten: str
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut