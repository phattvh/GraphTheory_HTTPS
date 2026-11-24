"""Test suite cho Ngày 2: Xác thực kết nối SQLAlchemy & Models NguoiDung, KyThi (UC02).

Phụ trách: TV2 (Hồ Thanh Hải)
Chạy trong container: docker compose exec fastapi python -m tests.day2_backend_db_test
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH để có thể import backend khi chạy trực tiếp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date
from sqlalchemy import text
from backend.core.database import SessionLocal
from backend.models import NguoiDung, KyThi


def test_db_connection():
    """Kiểm tra kết nối thô tới PostgreSQL."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1, "Kết nối CSDL thất bại"
        print("✓ Test 1: Kết nối SQLAlchemy -> PostgreSQL container thành công (SELECT 1).")
    finally:
        db.close()


def test_query_nguoi_dung():
    """Kiểm tra ánh xạ ORM bảng nguoi_dung và tài khoản admin khởi tạo."""
    db = SessionLocal()
    try:
        admin = db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == "admin").first()
        assert admin is not None, "Không tìm thấy tài khoản admin trong CSDL"
        assert admin.vai_tro == "admin", f"Vai trò không khớp: {admin.vai_tro}"
        print(f"✓ Test 2: Model NguoiDung hoạt động tốt, tìm thấy admin (role={admin.vai_tro}).")
    finally:
        db.close()


def test_crud_ky_thi():
    """Kiểm tra ánh xạ ORM bảng ky_thi (thêm mới, truy vấn, xóa)."""
    db = SessionLocal()
    try:
        test_exam = KyThi(
            ma_ky_thi="KT_TEST_DAY2_VERIFY",
            ten_ky_thi="Kỳ thi kiểm tra Ngày 2 TV2",
            ngay_bat_dau=date(2026, 7, 1),
            ngay_ket_thuc=date(2026, 7, 15),
            so_ca_moi_ngay=4,
            trang_thai="khoi_tao",
        )
        db.add(test_exam)
        db.commit()
        db.refresh(test_exam)

        assert test_exam.id is not None, "Không tạo được ID cho kỳ thi"

        queried = db.query(KyThi).filter(KyThi.ma_ky_thi == "KT_TEST_DAY2_VERIFY").first()
        assert queried is not None, "Không truy vấn được kỳ thi vừa tạo"
        assert queried.ten_ky_thi == "Kỳ thi kiểm tra Ngày 2 TV2"

        # Dọn dẹp dữ liệu test
        db.delete(queried)
        db.commit()

        deleted = db.query(KyThi).filter(KyThi.ma_ky_thi == "KT_TEST_DAY2_VERIFY").first()
        assert deleted is None, "Chưa xóa được bản ghi test"

        print("✓ Test 3: Model KyThi hoạt động hoàn hảo (Tạo -> Truy vấn -> Dọn dẹp).")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== BẮT ĐẦU KIỂM THỬ NGÀY 2 (TV2: SQLAlchemy & Models) ===")
    try:
        test_db_connection()
        test_query_nguoi_dung()
        test_crud_ky_thi()
        print("=== TẤT CẢ CÁC BƯỚC KIỂM THỬ ĐÃ ĐẠT 100% ===")
    except AssertionError as err:
        print(f"✗ LỖI KIỂM THỬ: {err}")
        sys.exit(1)
    except Exception as exc:
        print(f"✗ LỖI KHÔNG MONG MUỐN: {exc}")
        sys.exit(1)
