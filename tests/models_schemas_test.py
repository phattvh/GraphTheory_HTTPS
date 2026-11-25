"""Kiểm thử tự động Ngày 3 (TV2): Models MonHoc, SinhVien, PhongThi & Pydantic v2 Schemas.

Chạy trong container fastapi:
    docker compose exec fastapi python tests/models_schemas_test.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from sqlalchemy import inspect

from backend.core.database import SessionLocal, engine
from backend.models import MonHoc, PhongThi, SinhVien
from backend.schemas import (
    DangKyThiCreate,
    KyThiCreate,
    KyThiUpdate,
    MonHocCreate,
    MonHocOut,
    MonHocUpdate,
    PhongThiCreate,
    PhongThiOut,
    PhongThiUpdate,
    SinhVienCreate,
    SinhVienOut,
    SinhVienUpdate,
)


def _assert_raises_validation_error(fn, label: str) -> None:
    try:
        fn()
    except ValidationError:
        return
    raise AssertionError(f"Expected ValidationError for: {label}")


def test_orm_columns_match_postgres_tables():
    """Đảm bảo các cột của MonHoc, SinhVien, PhongThi khớp 100% với bảng trong PostgreSQL."""
    inspector = inspect(engine)
    expected = {
        MonHoc: {"id", "ma_mon", "ten_mon", "thoi_luong_phut", "so_tin_chi"},
        SinhVien: {"id", "mssv", "ho_ten", "email", "lop_sinh_hoat"},
        PhongThi: {"id", "ma_phong", "ten_phong", "suc_chua", "toa_nha", "dang_su_dung"},
    }
    for model_cls, required_cols in expected.items():
        table_name = model_cls.__tablename__
        db_cols = {c["name"] for c in inspector.get_columns(table_name)}
        orm_cols = {c.name for c in model_cls.__table__.columns}
        assert required_cols.issubset(db_cols), f"Thiếu cột trong DB bảng {table_name}: {required_cols - db_cols}"
        assert orm_cols == required_cols, f"Model {model_cls.__name__} lệch cột: {orm_cols ^ required_cols}"
    print("✓ Test 1: Cột ORM của MonHoc, SinhVien, PhongThi khớp 100% với PostgreSQL.")


def test_schemas_validation_and_sanitization():
    """Kiểm tra validate, trim khoảng trắng và chặn giá trị biên không hợp lệ."""
    # MonHoc valid + trim
    mh_in = MonHocCreate(ma_mon="  IT3010  ", ten_mon="  Lý thuyết đồ thị  ")
    assert mh_in.ma_mon == "IT3010"
    assert mh_in.ten_mon == "Lý thuyết đồ thị"
    assert mh_in.thoi_luong_phut == 90
    assert mh_in.so_tin_chi == 3

    # MonHoc invalid cases
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="   ", ten_mon="Môn"), "blank ma_mon")
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="IT01", ten_mon="Môn", thoi_luong_phut=0), "thoi_luong_phut=0")
    _assert_raises_validation_error(lambda: MonHocCreate(ma_mon="IT01", ten_mon="Môn", so_tin_chi=-1), "so_tin_chi=-1")
    _assert_raises_validation_error(lambda: MonHocUpdate(ten_mon=None), "explicit null ten_mon in update")

    # SinhVien valid + blank optional normalization
    sv_in = SinhVienCreate(mssv=" 22110001 ", ho_ten=" Nguyễn Văn An ", email="   ", lop_sinh_hoat=" 22CNTT1 ")
    assert sv_in.mssv == "22110001"
    assert sv_in.ho_ten == "Nguyễn Văn An"
    assert sv_in.email is None
    assert sv_in.lop_sinh_hoat == "22CNTT1"

    _assert_raises_validation_error(lambda: SinhVienCreate(mssv="", ho_ten="An"), "empty mssv")
    _assert_raises_validation_error(lambda: SinhVienUpdate(ho_ten=None), "explicit null ho_ten in update")

    # PhongThi valid & invalid
    pt_in = PhongThiCreate(ma_phong=" TC-301 ", ten_phong=" Phòng TC 301 ", suc_chua=60, toa_nha="  ")
    assert pt_in.ma_phong == "TC-301"
    assert pt_in.toa_nha is None
    assert pt_in.dang_su_dung is True

    _assert_raises_validation_error(lambda: PhongThiCreate(ma_phong="P1", ten_phong="P1", suc_chua=0), "suc_chua=0")
    _assert_raises_validation_error(lambda: PhongThiUpdate(suc_chua=None), "explicit null suc_chua in update")
    _assert_raises_validation_error(lambda: PhongThiUpdate(dang_su_dung=None), "explicit null dang_su_dung in update")

    # KyThi date check & DangKyThi positive ids
    _assert_raises_validation_error(
        lambda: KyThiCreate(
            ma_ky_thi="KT1",
            ten_ky_thi="KT",
            ngay_bat_dau=date(2026, 6, 15),
            ngay_ket_thuc=date(2026, 6, 10),
        ),
        "ngay_ket_thuc < ngay_bat_dau",
    )
    _assert_raises_validation_error(
        lambda: KyThiUpdate(ngay_bat_dau=date(2026, 6, 15), ngay_ket_thuc=date(2026, 6, 10)),
        "KyThiUpdate date order",
    )
    _assert_raises_validation_error(
        lambda: DangKyThiCreate(ky_thi_id=0, sinh_vien_id=1, mon_hoc_id=1),
        "DangKyThi ky_thi_id=0",
    )

    # Edge cases: tràn số nguyên INT/BIGINT, ép kiểu bool->int, sai định dạng email, truyền thừa trường lạ
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P_HUGE", ten_phong="Huge", suc_chua=10**12),
        "suc_chua overflow INT",
    )
    _assert_raises_validation_error(
        lambda: DangKyThiCreate(ky_thi_id=10**25, sinh_vien_id=1, mon_hoc_id=1),
        "ky_thi_id overflow BIGINT",
    )
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P_BOOL", ten_phong="Bool", suc_chua=True),
        "bool as suc_chua",
    )
    _assert_raises_validation_error(
        lambda: MonHocCreate(ma_mon="IT02", ten_mon="Môn", thoi_luong_phut=True),
        "bool as thoi_luong_phut",
    )
    _assert_raises_validation_error(
        lambda: SinhVienCreate(mssv="22110002", ho_ten="An", email="not-an-email"),
        "invalid email format",
    )
    _assert_raises_validation_error(
        lambda: SinhVienUpdate(email="bad@@domain"),
        "invalid email in SinhVienUpdate",
    )
    _assert_raises_validation_error(
        lambda: MonHocUpdate(ma_mon="IMMUTABLE"),
        "extra forbidden field in MonHocUpdate",
    )
    _assert_raises_validation_error(
        lambda: PhongThiCreate(ma_phong="P2", ten_phong="P2", suc_chua=50, unknown_field=1),
        "extra forbidden field in PhongThiCreate",
    )
    print("✓ Test 2: Toàn bộ Pydantic v2 schemas validate chuẩn xác (hợp lệ & chặn lỗi).")


def test_orm_crud_and_pydantic_from_attributes():
    """Kiểm tra vòng đời ORM (Create -> Query -> Update -> Out serialization -> Cleanup) trên PostgreSQL."""
    db = SessionLocal()
    try:
        # 1. MonHoc
        mh_payload = MonHocCreate(
            ma_mon="TEST_D3_IT99",
            ten_mon="Môn kiểm thử Ngày 3",
            thoi_luong_phut=90,
            so_tin_chi=3,
        )
        mh_orm = MonHoc(**mh_payload.model_dump())
        db.add(mh_orm)
        db.flush()

        mh_upd = MonHocUpdate(thoi_luong_phut=120)
        for k, v in mh_upd.model_dump(exclude_unset=True).items():
            setattr(mh_orm, k, v)
        db.flush()
        mh_out = MonHocOut.model_validate(mh_orm)
        assert mh_out.id == mh_orm.id and mh_out.thoi_luong_phut == 120

        # 2. SinhVien
        sv_payload = SinhVienCreate(
            mssv="TESTD3_22119999",
            ho_ten="Sinh Viên Test Ngày 3",
            email="svtest@univ.edu.vn",
            lop_sinh_hoat="22CNTT-TEST",
        )
        sv_orm = SinhVien(**sv_payload.model_dump())
        db.add(sv_orm)
        db.flush()

        sv_upd = SinhVienUpdate(lop_sinh_hoat="22CNTT-UPDATED")
        for k, v in sv_upd.model_dump(exclude_unset=True).items():
            setattr(sv_orm, k, v)
        db.flush()
        sv_out = SinhVienOut.model_validate(sv_orm)
        assert sv_out.id == sv_orm.id and sv_out.lop_sinh_hoat == "22CNTT-UPDATED"

        # 3. PhongThi
        pt_payload = PhongThiCreate(
            ma_phong="TEST_D3_P999",
            ten_phong="Phòng thi Test Ngày 3",
            suc_chua=75,
            toa_nha="Nhà Test",
            dang_su_dung=True,
        )
        pt_orm = PhongThi(**pt_payload.model_dump())
        db.add(pt_orm)
        db.flush()

        pt_upd = PhongThiUpdate(suc_chua=80, dang_su_dung=False)
        for k, v in pt_upd.model_dump(exclude_unset=True).items():
            setattr(pt_orm, k, v)
        db.flush()
        pt_out = PhongThiOut.model_validate(pt_orm)
        assert pt_out.id == pt_orm.id and pt_out.suc_chua == 80 and pt_out.dang_su_dung is False

        # Rollback để không làm bẩn CSDL thật
        db.rollback()
        print("✓ Test 3: ORM <-> Pydantic Out (from_attributes=True) và giao dịch Postgres pass 100%.")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== BẮT ĐẦU KIỂM THỬ NGÀY 3 (TV2: MonHoc, SinhVien, PhongThi Models & Schemas) ===")
    try:
        test_orm_columns_match_postgres_tables()
        test_schemas_validation_and_sanitization()
        test_orm_crud_and_pydantic_from_attributes()
        print("=== TẤT CẢ CÁC BƯỚC KIỂM THỬ NGÀY 3 ĐÃ ĐẠT 100% ===")
    except AssertionError as err:
        print(f"✗ LỖI KIỂM THỬ: {err}")
        sys.exit(1)
    except Exception as exc:
        print(f"✗ LỖI KHÔNG MONG MUỐN: {exc}")
        sys.exit(1)
