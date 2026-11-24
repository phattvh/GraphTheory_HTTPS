"""Kiểm thử tự động schema PostgreSQL Ngày 1 (TV2: db/init/init.sql).

Chạy bên trong container fastapi:
    docker compose exec fastapi python tests/db_schema_test.py
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from backend.core.database import SessionLocal, engine

EXPECTED_TABLES = {
    "ky_thi",
    "mon_hoc",
    "sinh_vien",
    "phong_thi",
    "nguoi_dung",
    "dang_ky_thi",
    "ca_thi",
    "lich_thi",
}

EXPECTED_INDEXES = {
    "idx_dang_ky_thi_ky_thi_mon",
    "idx_dang_ky_thi_ky_thi_sv",
    "idx_ca_thi_ky_thi",
    "idx_lich_thi_ca_thi",
    "idx_lich_thi_mon_hoc",
}


def test_all_8_tables_exist():
    """Kiểm tra đủ 8 bảng trong PostgreSQL theo docs/04. Database design.md."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names(schema="public"))
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Thiếu bảng trong PostgreSQL: {missing}"


def test_all_5_custom_indexes_exist():
    """Kiểm tra đủ 5 index tối ưu truy vấn từ db/init/init.sql."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        ).fetchall()
    existing_indexes = {row[0] for row in rows}
    missing = EXPECTED_INDEXES - existing_indexes
    assert not missing, f"Thiếu index trong PostgreSQL: {missing}"


def test_seed_admin_exists():
    """Kiểm tra tài khoản admin mặc định đã được seed với bcrypt hash."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT ten_dang_nhap, vai_tro, mat_khau_hash FROM nguoi_dung WHERE ten_dang_nhap = 'admin'")
        ).fetchone()
    assert row is not None, "Thiếu tài khoản seed 'admin'"
    assert row[1] == "admin"
    assert row[2].startswith("$2b$12$"), "Mật khẩu admin phải là bcrypt cost 12"


def test_check_constraints_enforced():
    """Kiểm tra các ràng buộc CHECK quan trọng (sức chứa > 0, vai_tro hợp lệ, ngày thi hợp lệ)."""
    db = SessionLocal()
    try:
        # 1. Phòng thi có sức chứa <= 0 phải bị từ chối
        try:
            db.execute(
                text(
                    "INSERT INTO phong_thi (ma_phong, ten_phong, suc_chua) "
                    "VALUES ('TEST_ERR_P', 'Phòng lỗi', 0)"
                )
            )
            db.commit()
            raise AssertionError("CHECK ck_phong_thi_suc_chua không chặn suc_chua = 0")
        except IntegrityError:
            db.rollback()

        # 2. Kỳ thi có ngay_ket_thuc < ngay_bat_dau phải bị từ chối
        try:
            db.execute(
                text(
                    "INSERT INTO ky_thi (ma_ky_thi, ten_ky_thi, ngay_bat_dau, ngay_ket_thuc) "
                    "VALUES ('TEST_ERR_KT', 'Kỳ thi lỗi', '2026-12-20', '2026-12-10')"
                )
            )
            db.commit()
            raise AssertionError("CHECK ck_ky_thi_ngay không chặn ngày kết thúc < ngày bắt đầu")
        except IntegrityError:
            db.rollback()

        # 3. Người dùng vai_tro = 'sinh_vien' thiếu mssv phải bị từ chối
        try:
            db.execute(
                text(
                    "INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau_hash, vai_tro, ho_ten) "
                    "VALUES ('test_sv_no_mssv', 'hash', 'sinh_vien', 'SV Lỗi')"
                )
            )
            db.commit()
            raise AssertionError("CHECK ck_sv_co_mssv không chặn sinh viên thiếu MSSV")
        except IntegrityError:
            db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_all_8_tables_exist()
    test_all_5_custom_indexes_exist()
    test_seed_admin_exists()
    test_check_constraints_enforced()
    print("ALL DB SCHEMA TESTS PASSED!")
