"""Pydantic v2 schemas for master data management (UC02 - UC06).

Phụ trách: TV2 (Backend: CSDL & Dữ liệu đầu vào)
Tham chiếu: docs/04. Database design.md & docs/09. Project structure.md
"""

from datetime import date, datetime
from typing import Annotated, Iterable, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

ExamStatus = Literal["khoi_tao", "da_xep_lich", "cong_bo"]
MAX_PG_BIGINT = 9_223_372_036_854_775_807


def _required_str(max_length: int):
    """Chuỗi bắt buộc: tự động cắt khoảng trắng hai đầu, không chấp nhận chuỗi rỗng."""
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length),
    ]


def _optional_str(max_length: int):
    """Chuỗi tùy chọn: tự động cắt khoảng trắng hai đầu và giới hạn độ dài."""
    return Annotated[
        Optional[str],
        StringConstraints(strip_whitespace=True, max_length=max_length),
    ]


def _normalize_optional_blank(value: Optional[str]) -> Optional[str]:
    """Chuẩn hóa chuỗi rỗng sau khi trim thành None để giữ sạch cột nullable trong CSDL."""
    if value is None:
        return None
    return value or None


def _reject_explicit_none(model: BaseModel, non_nullable_fields: Iterable[str]) -> None:
    """Chặn gán explicit null cho các cột NOT NULL khi cập nhật từng phần."""
    for field_name in non_nullable_fields:
        if field_name in model.model_fields_set and getattr(model, field_name) is None:
            raise ValueError(f"Trường '{field_name}' không được phép để trống (null).")


# ---------------------------------------------------------------------------
# 1. KỲ THI (UC02)
# ---------------------------------------------------------------------------
class KyThiBase(BaseModel):
    ma_ky_thi: _required_str(50) = Field(..., examples=["KTHK1_2026"])
    ten_ky_thi: _required_str(255) = Field(
        ..., examples=["Kỳ thi kết thúc học phần HK1 2026"]
    )
    ngay_bat_dau: date
    ngay_ket_thuc: date
    so_ca_moi_ngay: int = Field(default=4, gt=0, le=20)
    trang_thai: ExamStatus = "khoi_tao"

    @model_validator(mode="after")
    def validate_date_range(self) -> "KyThiBase":
        if self.ngay_ket_thuc < self.ngay_bat_dau:
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.")
        return self


class KyThiCreate(KyThiBase):
    pass


class KyThiUpdate(BaseModel):
    ten_ky_thi: Optional[_required_str(255)] = None
    ngay_bat_dau: Optional[date] = None
    ngay_ket_thuc: Optional[date] = None
    so_ca_moi_ngay: Optional[int] = Field(default=None, gt=0, le=20)
    trang_thai: Optional[ExamStatus] = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "KyThiUpdate":
        _reject_explicit_none(
            self,
            ("ten_ky_thi", "ngay_bat_dau", "ngay_ket_thuc", "so_ca_moi_ngay", "trang_thai"),
        )
        if (
            self.ngay_bat_dau is not None
            and self.ngay_ket_thuc is not None
            and self.ngay_ket_thuc < self.ngay_bat_dau
        ):
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.")
        return self


class KyThiOut(KyThiBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 2. MÔN HỌC / HỌC PHẦN (UC04)
# ---------------------------------------------------------------------------
class MonHocBase(BaseModel):
    ma_mon: _required_str(20) = Field(..., examples=["IT3010"])
    ten_mon: _required_str(255) = Field(..., examples=["Lý thuyết đồ thị"])
    thoi_luong_phut: int = Field(default=90, gt=0, le=600)
    so_tin_chi: Optional[int] = Field(default=3, gt=0, le=20)


class MonHocCreate(MonHocBase):
    pass


class MonHocUpdate(BaseModel):
    ten_mon: Optional[_required_str(255)] = None
    thoi_luong_phut: Optional[int] = Field(default=None, gt=0, le=600)
    so_tin_chi: Optional[int] = Field(default=None, gt=0, le=20)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "MonHocUpdate":
        _reject_explicit_none(self, ("ten_mon", "thoi_luong_phut"))
        return self


class MonHocOut(MonHocBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 3. SINH VIÊN (UC03)
# ---------------------------------------------------------------------------
class SinhVienBase(BaseModel):
    mssv: _required_str(20) = Field(..., examples=["22110001"])
    ho_ten: _required_str(100) = Field(..., examples=["Nguyễn Văn An"])
    email: _optional_str(100) = Field(default=None, examples=["an.nv@univ.edu.vn"])
    lop_sinh_hoat: _optional_str(50) = Field(default=None, examples=["22CNTT1"])

    @field_validator("email", "lop_sinh_hoat", mode="after")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_blank(value)


class SinhVienCreate(SinhVienBase):
    pass


class SinhVienUpdate(BaseModel):
    ho_ten: Optional[_required_str(100)] = None
    email: _optional_str(100) = None
    lop_sinh_hoat: _optional_str(50) = None

    @field_validator("email", "lop_sinh_hoat", mode="after")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_blank(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "SinhVienUpdate":
        _reject_explicit_none(self, ("ho_ten",))
        return self


class SinhVienOut(SinhVienBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 4. PHÒNG THI (UC06)
# ---------------------------------------------------------------------------
class PhongThiBase(BaseModel):
    ma_phong: _required_str(50) = Field(..., examples=["TC-301"])
    ten_phong: _required_str(100) = Field(..., examples=["Phòng thi Nhà TC - 301"])
    suc_chua: int = Field(..., gt=0, le=10000, examples=[60])
    toa_nha: _optional_str(50) = Field(default=None, examples=["Nhà TC"])
    dang_su_dung: bool = True

    @field_validator("toa_nha", mode="after")
    @classmethod
    def normalize_toa_nha(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_blank(value)


class PhongThiCreate(PhongThiBase):
    pass


class PhongThiUpdate(BaseModel):
    ten_phong: Optional[_required_str(100)] = None
    suc_chua: Optional[int] = Field(default=None, gt=0, le=10000)
    toa_nha: _optional_str(50) = None
    dang_su_dung: Optional[bool] = None

    @field_validator("toa_nha", mode="after")
    @classmethod
    def normalize_toa_nha(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_blank(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "PhongThiUpdate":
        _reject_explicit_none(self, ("ten_phong", "suc_chua", "dang_su_dung"))
        return self


class PhongThiOut(PhongThiBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 5. ĐĂNG KÝ THI (UC05)
# ---------------------------------------------------------------------------
class DangKyThiBase(BaseModel):
    ky_thi_id: int = Field(..., gt=0, le=MAX_PG_BIGINT)
    sinh_vien_id: int = Field(..., gt=0, le=MAX_PG_BIGINT)
    mon_hoc_id: int = Field(..., gt=0, le=MAX_PG_BIGINT)


class DangKyThiCreate(DangKyThiBase):
    pass


class DangKyThiOut(DangKyThiBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
