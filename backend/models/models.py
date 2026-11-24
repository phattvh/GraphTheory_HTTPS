"""SQLAlchemy ORM Models for 8 database tables.

Phụ trách: TV2 (Backend: CSDL & Dữ liệu đầu vào)
Tham chiếu: docs/04. Database design.md
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from backend.core.database import Base


class NguoiDung(Base):
    """Bảng nguoi_dung: Tài khoản & Phân quyền (FastAPI Native JWT)."""

    __tablename__ = "nguoi_dung"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau_hash = Column(String(255), nullable=False)
    vai_tro = Column(String(20), nullable=False)  # 'admin' hoặc 'sinh_vien'
    mssv = Column(
        String(20),
        ForeignKey("sinh_vien.mssv", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    ho_ten = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ 0..1 - 0..1 với SinhVien
    sinh_vien = relationship("SinhVien", back_populates="nguoi_dung", uselist=False)


class KyThi(Base):
    """Bảng ky_thi: Thông tin các đợt thi (UC02)."""

    __tablename__ = "ky_thi"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ma_ky_thi = Column(String(50), nullable=False, unique=True)
    ten_ky_thi = Column(String(255), nullable=False)
    ngay_bat_dau = Column(Date, nullable=False)
    ngay_ket_thuc = Column(Date, nullable=False)
    so_ca_moi_ngay = Column(Integer, nullable=False, default=4)
    trang_thai = Column(String(20), nullable=False, default="khoi_tao")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ
    dang_ky_this = relationship(
        "DangKyThi", back_populates="ky_thi", cascade="all, delete-orphan"
    )
    ca_this = relationship(
        "CaThi", back_populates="ky_thi", cascade="all, delete-orphan"
    )


class MonHoc(Base):
    """Bảng mon_hoc: Danh mục môn thi / học phần (UC04)."""

    __tablename__ = "mon_hoc"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ma_mon = Column(String(20), nullable=False, unique=True)
    ten_mon = Column(String(255), nullable=False)
    thoi_luong_phut = Column(Integer, nullable=False, default=90)
    so_tin_chi = Column(Integer, nullable=True, default=3)

    # Quan hệ
    dang_ky_this = relationship(
        "DangKyThi", back_populates="mon_hoc", cascade="all, delete-orphan"
    )
    lich_this = relationship(
        "LichThi", back_populates="mon_hoc", cascade="all, delete-orphan"
    )


class SinhVien(Base):
    """Bảng sinh_vien: Danh sách sinh viên (UC03)."""

    __tablename__ = "sinh_vien"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    mssv = Column(String(20), nullable=False, unique=True)
    ho_ten = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    lop_sinh_hoat = Column(String(50), nullable=True)

    # Quan hệ
    nguoi_dung = relationship("NguoiDung", back_populates="sinh_vien", uselist=False)
    dang_ky_this = relationship(
        "DangKyThi", back_populates="sinh_vien", cascade="all, delete-orphan"
    )


class PhongThi(Base):
    """Bảng phong_thi: Danh mục phòng thi (UC06)."""

    __tablename__ = "phong_thi"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ma_phong = Column(String(50), nullable=False, unique=True)
    ten_phong = Column(String(100), nullable=False)
    suc_chua = Column(Integer, nullable=False)
    toa_nha = Column(String(50), nullable=True)
    dang_su_dung = Column(Boolean, nullable=False, default=True)

    # Quan hệ
    lich_this = relationship("LichThi", back_populates="phong_thi")


class DangKyThi(Base):
    """Bảng dang_ky_thi: Danh sách đăng ký thi (UC05, UC07).

    Dữ liệu đầu vào để trích xuất tập đỉnh V và tập cạnh E (Self-Join).
    """

    __tablename__ = "dang_ky_thi"
    __table_args__ = (
        UniqueConstraint("ky_thi_id", "sinh_vien_id", "mon_hoc_id", name="uq_dang_ky"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ky_thi_id = Column(
        BigInteger, ForeignKey("ky_thi.id", ondelete="CASCADE"), nullable=False
    )
    sinh_vien_id = Column(
        BigInteger, ForeignKey("sinh_vien.id", ondelete="CASCADE"), nullable=False
    )
    mon_hoc_id = Column(
        BigInteger, ForeignKey("mon_hoc.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ
    ky_thi = relationship("KyThi", back_populates="dang_ky_this")
    sinh_vien = relationship("SinhVien", back_populates="dang_ky_this")
    mon_hoc = relationship("MonHoc", back_populates="dang_ky_this")


class CaThi(Base):
    """Bảng ca_thi: Ca thi tương ứng từng màu 1..k từ thuật toán tô màu (UC08)."""

    __tablename__ = "ca_thi"
    __table_args__ = (
        UniqueConstraint("ky_thi_id", "stt_ca", name="uq_ca_thi"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ky_thi_id = Column(
        BigInteger, ForeignKey("ky_thi.id", ondelete="CASCADE"), nullable=False
    )
    stt_ca = Column(Integer, nullable=False)
    ngay_thi = Column(Date, nullable=False)
    gio_bat_dau = Column(Time, nullable=False)
    gio_ket_thuc = Column(Time, nullable=False)
    thuat_toan = Column(String(30), nullable=False, default="DSATUR")

    # Quan hệ
    ky_thi = relationship("KyThi", back_populates="ca_this")
    lich_this = relationship(
        "LichThi", back_populates="ca_thi", cascade="all, delete-orphan"
    )


class LichThi(Base):
    """Bảng lich_thi: Phân bổ chi tiết môn thi - ca thi - phòng thi (UC08 FFD)."""

    __tablename__ = "lich_thi"
    __table_args__ = (
        UniqueConstraint("ca_thi_id", "phong_thi_id", name="uq_lich_phong"),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ca_thi_id = Column(
        BigInteger, ForeignKey("ca_thi.id", ondelete="CASCADE"), nullable=False
    )
    mon_hoc_id = Column(
        BigInteger, ForeignKey("mon_hoc.id", ondelete="CASCADE"), nullable=False
    )
    phong_thi_id = Column(
        BigInteger, ForeignKey("phong_thi.id", ondelete="RESTRICT"), nullable=False
    )
    so_luong_sv = Column(Integer, nullable=False)
    ghi_chu = Column(String(255), nullable=True)

    # Quan hệ
    ca_thi = relationship("CaThi", back_populates="lich_this")
    mon_hoc = relationship("MonHoc", back_populates="lich_this")
    phong_thi = relationship("PhongThi", back_populates="lich_this")
