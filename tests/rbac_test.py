"""Kiểm thử tự động phân quyền RBAC (get_current_user & require_admin) — Ngày 4 (TV3).

Chạy trong container fastapi:
    docker compose exec -T fastapi python tests/rbac_test.py
"""

from datetime import timedelta
import json
import os
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.core.database import SessionLocal
from backend.core.security import create_access_token, get_password_hash
from backend.models.models import KyThi, MonHoc, NguoiDung, SinhVien

SSL_CTX = ssl._create_unverified_context()
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.getenv("TEST_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("TEST_ADMIN_PASS", "admin123")


def request_json(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    scheme: str = "Bearer",
) -> Tuple[int, Dict[str, str], Any]:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"{scheme} {token}" if scheme else token
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, resp_headers, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        resp_headers = {k.lower(): v for k, v in err.headers.items()}
        return err.code, resp_headers, (json.loads(raw) if raw else None)


def login_and_get_token(username: str, password: str) -> str:
    status_code, _, body = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": username, "mat_khau": password},
    )
    assert status_code == 200 and body and body.get("access_token"), (
        f"Login failed for {username}: {status_code} {body}"
    )
    return body["access_token"]


def test_unauthenticated_and_invalid_tokens_return_401():
    """Thiếu token, sai scheme, token giả hoặc hết hạn phải trả 401 + WWW-Authenticate: Bearer."""
    protected_routes = [
        ("GET", "/api/v1/auth/me", None),
        ("GET", "/api/v1/ky-thi", None),
        ("POST", "/api/v1/ky-thi", {"ma_ky_thi": "NOAUTH", "ten_ky_thi": "X", "ngay_bat_dau": "2026-09-01", "ngay_ket_thuc": "2026-09-05"}),
        ("GET", "/api/v1/mon-hoc", None),
        ("POST", "/api/v1/mon-hoc", {"ma_mon": "NOAUTH", "ten_mon": "X"}),
        ("GET", "/api/v1/sinh-vien", None),
        ("POST", "/api/v1/sinh-vien", {"mssv": "NOAUTH", "ho_ten": "X"}),
        ("GET", "/api/v1/phong-thi", None),
        ("POST", "/api/v1/phong-thi", {"ma_phong": "NOAUTH", "ten_phong": "X", "suc_chua": 30}),
        ("GET", "/api/v1/dang-ky-thi", None),
        ("GET", "/api/v1/ky-thi/1/dang-ky-thi", None),
        ("POST", "/api/v1/dang-ky-thi", {"ky_thi_id": 1, "sinh_vien_id": 1, "mon_hoc_id": 1}),
    ]
    for method, path, payload in protected_routes:
        code, headers, _ = request_json(method, path, payload)
        assert code == 401, f"{method} {path} without token expected 401, got {code}"
        assert "bearer" in headers.get("www-authenticate", "").lower()

    # Token sai chữ ký / rác
    code, headers, _ = request_json("GET", "/api/v1/mon-hoc", token="invalid.jwt.token")
    assert code == 401 and "bearer" in headers.get("www-authenticate", "").lower()

    # Sai scheme (Basic thay vì Bearer)
    code, headers, _ = request_json("GET", "/api/v1/mon-hoc", token="abc", scheme="Basic")
    assert code == 401 and "bearer" in headers.get("www-authenticate", "").lower()

    # Token hết hạn
    expired_token = create_access_token(
        {"sub": ADMIN_USER, "vai_tro": "admin"},
        expires_delta=timedelta(seconds=-10),
    )
    code, headers, _ = request_json("GET", "/api/v1/mon-hoc", token=expired_token)
    assert code == 401 and "bearer" in headers.get("www-authenticate", "").lower()

    # Token mang sub không tồn tại trong DB
    ghost_token = create_access_token({"sub": "ghost_user_rbac_test", "vai_tro": "admin"})
    code, _, _ = request_json("GET", "/api/v1/mon-hoc", token=ghost_token)
    assert code == 401

    print("✓ Test 1: Thiếu token / token sai / hết hạn / user không tồn tại đều trả 401.")


def test_role_guard_student_vs_admin():
    """Kiểm chứng sinh_vien bị chặn 403 ở API admin & chỉ thấy kỳ thi cong_bo; admin có toàn quyền."""
    sv_username = "sv_rbac_test_d4"
    sv_mssv = "22119988"
    sv_password = "StudentPass123!"
    draft_code = "KT_RBAC_DRAFT_D4"
    pub_code = "KT_RBAC_PUB_D4"
    course_code = "MH_RBAC_D4"

    db = SessionLocal()
    draft_exam_id = None
    pub_exam_id = None
    course_id = None
    try:
        # Tạo sinh viên và tài khoản sinh_vien tạm để kiểm thử RBAC
        db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == sv_username).delete()
        db.query(SinhVien).filter(SinhVien.mssv == sv_mssv).delete()
        db.commit()

        sv_profile = SinhVien(
            mssv=sv_mssv,
            ho_ten="Sinh Viên Test RBAC",
            email="sv.rbac@univ.edu.vn",
            lop_sinh_hoat="22CNTT1",
        )
        db.add(sv_profile)
        db.flush()

        sv_user = NguoiDung(
            ten_dang_nhap=sv_username,
            mat_khau_hash=get_password_hash(sv_password),
            vai_tro="sinh_vien",
            mssv=sv_mssv,
            ho_ten="Sinh Viên Test RBAC",
            email="sv.rbac@univ.edu.vn",
        )
        db.add(sv_user)
        db.commit()

        admin_token = login_and_get_token(ADMIN_USER, ADMIN_PASS)
        sv_token = login_and_get_token(sv_username, sv_password)

        # Admin tạo 1 kỳ thi nháp (khoi_tao), 1 kỳ thi đã công bố (cong_bo) và 1 môn học
        c1, _, draft_exam = request_json(
            "POST",
            "/api/v1/ky-thi",
            {
                "ma_ky_thi": draft_code,
                "ten_ky_thi": "Kỳ thi nháp RBAC",
                "ngay_bat_dau": "2026-10-01",
                "ngay_ket_thuc": "2026-10-05",
                "trang_thai": "khoi_tao",
            },
            token=admin_token,
        )
        assert c1 == 201, f"Admin create draft exam failed: {c1} {draft_exam}"
        draft_exam_id = draft_exam["id"]

        c2, _, pub_exam = request_json(
            "POST",
            "/api/v1/ky-thi",
            {
                "ma_ky_thi": pub_code,
                "ten_ky_thi": "Kỳ thi công bố RBAC",
                "ngay_bat_dau": "2026-11-01",
                "ngay_ket_thuc": "2026-11-05",
                "trang_thai": "cong_bo",
            },
            token=admin_token,
        )
        assert c2 == 201, f"Admin create published exam failed: {c2} {pub_exam}"
        pub_exam_id = pub_exam["id"]

        c3, _, course = request_json(
            "POST",
            "/api/v1/mon-hoc",
            {"ma_mon": course_code, "ten_mon": "Môn học RBAC", "thoi_luong_phut": 90, "so_tin_chi": 3},
            token=admin_token,
        )
        assert c3 == 201, f"Admin create course failed: {c3} {course}"
        course_id = course["id"]

        # 1. Sinh viên gọi /auth/me thành công (200)
        c_me, _, me_body = request_json("GET", "/api/v1/auth/me", token=sv_token)
        assert c_me == 200 and me_body["vai_tro"] == "sinh_vien"

        # 2. Sinh viên gọi GET /ky-thi chỉ thấy cong_bo, KHÔNG thấy khoi_tao (kể cả khi truyền ?trang_thai=khoi_tao)
        c_list, _, sv_exams = request_json("GET", "/api/v1/ky-thi", token=sv_token)
        assert c_list == 200
        assert all(item["trang_thai"] == "cong_bo" for item in sv_exams)
        assert any(item["id"] == pub_exam_id for item in sv_exams)
        assert all(item["id"] != draft_exam_id for item in sv_exams)

        c_draft_filter, _, draft_filtered = request_json(
            "GET", "/api/v1/ky-thi?trang_thai=khoi_tao", token=sv_token
        )
        assert c_draft_filter == 200 and draft_filtered == []

        # Sinh viên xem chi tiết kỳ thi cong_bo -> 200; xem kỳ thi nháp -> 403
        c_pub_get, _, _ = request_json("GET", f"/api/v1/ky-thi/{pub_exam_id}", token=sv_token)
        assert c_pub_get == 200
        c_draft_get, _, _ = request_json("GET", f"/api/v1/ky-thi/{draft_exam_id}", token=sv_token)
        assert c_draft_get == 403, f"Student reading draft exam expected 403, got {c_draft_get}"

        # 3. Sinh viên bị chặn 403 trên mọi API quản trị (POST/PUT/DELETE ky-thi & toàn bộ mon-hoc)
        forbidden_calls = [
            ("POST", "/api/v1/ky-thi", {"ma_ky_thi": "SV_TRY", "ten_ky_thi": "X", "ngay_bat_dau": "2026-10-01", "ngay_ket_thuc": "2026-10-02"}),
            ("PUT", f"/api/v1/ky-thi/{draft_exam_id}", {"ten_ky_thi": "Hacked"}),
            ("DELETE", f"/api/v1/ky-thi/{draft_exam_id}", None),
            ("GET", "/api/v1/mon-hoc", None),
            ("GET", f"/api/v1/mon-hoc/{course_id}", None),
            ("POST", "/api/v1/mon-hoc", {"ma_mon": "SV_MH", "ten_mon": "X"}),
            ("PUT", f"/api/v1/mon-hoc/{course_id}", {"ten_mon": "Hacked"}),
            ("DELETE", f"/api/v1/mon-hoc/{course_id}", None),
            ("GET", "/api/v1/sinh-vien", None),
            ("POST", "/api/v1/sinh-vien", {"mssv": "SV_TRY", "ho_ten": "X"}),
            ("GET", "/api/v1/phong-thi", None),
            ("POST", "/api/v1/phong-thi", {"ma_phong": "P_TRY", "ten_phong": "X", "suc_chua": 30}),
            ("GET", "/api/v1/dang-ky-thi", None),
            ("GET", f"/api/v1/ky-thi/{pub_exam_id}/dang-ky-thi", None),
            ("POST", "/api/v1/dang-ky-thi", {"ky_thi_id": pub_exam_id, "sinh_vien_id": 1, "mon_hoc_id": course_id}),
        ]
        for method, path, payload in forbidden_calls:
            code, _, _ = request_json(method, path, payload, token=sv_token)
            assert code == 403, f"Student {method} {path} expected 403, got {code}"

        # 4. Giả mạo claim vai_tro="admin" trong JWT cho user sinh_vien vẫn bị chặn 403 (vì đọc vai_tro từ DB)
        forged_role_token = create_access_token({"sub": sv_username, "vai_tro": "admin"})
        c_forged, _, _ = request_json("GET", "/api/v1/mon-hoc", token=forged_role_token)
        assert c_forged == 403, f"Forged admin claim for student user must be 403, got {c_forged}"

        # 5. Xóa SinhVien đang có tài khoản sinh_vien gắn MSSV phải trả 409 Conflict thay vì lỗi 500
        c_del_sv_linked, _, _ = request_json(
            "DELETE", f"/api/v1/sinh-vien/{sv_profile.id}", token=admin_token
        )
        assert c_del_sv_linked == 409, (
            f"Deleting student linked to user expected 409, got {c_del_sv_linked}"
        )

        print("✓ Test 2: RBAC chặn 403 đúng với sinh_vien (kể cả giả claim vai_tro), lọc cong_bo & chặn xóa SV đang liên kết (409).")
    finally:
        # Dọn sạch dữ liệu test trong DB
        db.rollback()
        if course_id is not None:
            db.query(MonHoc).filter(MonHoc.id == course_id).delete()
        if draft_exam_id is not None:
            db.query(KyThi).filter(KyThi.id == draft_exam_id).delete()
        if pub_exam_id is not None:
            db.query(KyThi).filter(KyThi.id == pub_exam_id).delete()
        db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == sv_username).delete()
        db.query(SinhVien).filter(SinhVien.mssv == sv_mssv).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    print(f"=== BẮT ĐẦU KIỂM THỬ RBAC NGÀY 4 (TV3 qua {BASE_URL}) ===")
    test_unauthenticated_and_invalid_tokens_return_401()
    test_role_guard_student_vs_admin()
    print("=== TẤT CẢ CÁC BƯỚC KIỂM THỬ RBAC ĐÃ ĐẠT 100% ===")
