"""Kiểm thử tự động API CRUD Kỳ thi (UC02) & Môn học (UC04) — Ngày 4 (TV2).

Hỗ trợ chạy cả hai môi trường:
- Từ máy host qua Caddy HTTPS: python tests/master_data_api_test.py
- Bên trong container fastapi: docker compose exec fastapi python tests/master_data_api_test.py
"""

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional, Tuple

SSL_CTX = ssl._create_unverified_context()


def _detect_base_url() -> str:
    """Ưu tiên biến môi trường API_BASE_URL; tự thử Caddy HTTPS rồi fallback FastAPI nội bộ."""
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    for candidate in ("https://localhost", "http://127.0.0.1:8000"):
        req = urllib.request.Request(f"{candidate}/api/v1/health", method="GET")
        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=3) as resp:
                if resp.status == 200:
                    return candidate
        except (urllib.error.URLError, OSError):
            continue
    return "https://localhost"


BASE_URL = _detect_base_url()
ADMIN_USERNAME = os.getenv("TEST_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASS", "admin123")
_ADMIN_TOKEN: Optional[str] = None


def _get_admin_token() -> str:
    global _ADMIN_TOKEN
    if _ADMIN_TOKEN:
        return _ADMIN_TOKEN
    status_code, body = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": ADMIN_USERNAME, "mat_khau": ADMIN_PASSWORD},
        auth=False,
    )
    assert status_code == 200 and body and body.get("access_token"), (
        f"Đăng nhập admin thất bại ({status_code}): {body}"
    )
    _ADMIN_TOKEN = body["access_token"]
    return _ADMIN_TOKEN


def request_json(
    method: str,
    path: str,
    body: Optional[dict[str, Any]] = None,
    auth: bool = True,
) -> Tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {_get_admin_token()}"
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
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        return err.code, (json.loads(raw) if raw else None)


def test_openapi_exposes_ky_thi_and_mon_hoc_endpoints():
    """Swagger/OpenAPI phải hiển thị đầy đủ 10 route CRUD cho Kỳ thi và Môn học."""
    status_code, spec = request_json("GET", "/openapi.json")
    assert status_code == 200, f"GET /openapi.json failed: {status_code}"
    paths = spec.get("paths", {})

    expected = {
        "/api/v1/ky-thi": {"get", "post"},
        "/api/v1/ky-thi/{ky_thi_id}": {"get", "put", "delete"},
        "/api/v1/mon-hoc": {"get", "post"},
        "/api/v1/mon-hoc/{mon_hoc_id}": {"get", "put", "delete"},
    }
    for path, methods in expected.items():
        assert path in paths, f"Thiếu route {path} trong OpenAPI"
        missing_methods = methods - set(paths[path].keys())
        assert not missing_methods, f"Route {path} thiếu method: {missing_methods}"
    print(f"✓ Test 1: OpenAPI ({BASE_URL}) hiển thị đủ 10 endpoint CRUD Kỳ thi & Môn học.")


def test_ky_thi_crud_lifecycle_and_edge_cases():
    """Kiểm thử toàn bộ vòng đời CRUD /api/v1/ky-thi và các trường hợp biên."""
    created_ids: list[int] = []
    unique_code = "KT_TEST_D4_100%"
    try:
        # 1. Tạo mới (POST) kèm khoảng trắng thừa để kiểm tra auto-trim
        s_create, created = request_json(
            "POST",
            "/api/v1/ky-thi",
            {
                "ma_ky_thi": f"  {unique_code}  ",
                "ten_ky_thi": "  Kỳ thi Test Ngày 4 (100%)  ",
                "ngay_bat_dau": "2026-08-01",
                "ngay_ket_thuc": "2026-08-10",
            },
        )
        assert s_create == 201, f"Expected 201, got {s_create}: {created}"
        exam_id = created["id"]
        created_ids.append(exam_id)
        assert created["ma_ky_thi"] == unique_code
        assert created["ten_ky_thi"] == "Kỳ thi Test Ngày 4 (100%)"
        assert created["so_ca_moi_ngay"] == 4
        assert created["trang_thai"] == "khoi_tao"

        # 2. Chặn trùng mã kỳ thi (409 Conflict)
        s_dup, _ = request_json(
            "POST",
            "/api/v1/ky-thi",
            {
                "ma_ky_thi": unique_code,
                "ten_ky_thi": "Kỳ thi trùng mã",
                "ngay_bat_dau": "2026-08-01",
                "ngay_ket_thuc": "2026-08-05",
            },
        )
        assert s_dup == 409, f"Expected 409 on duplicate ma_ky_thi, got {s_dup}"

        # 3. Tìm kiếm có ký tự wildcard '%' (đảm bảo escape LIKE đúng)
        q_encoded = urllib.parse.quote("100%")
        s_list, items = request_json(
            "GET", f"/api/v1/ky-thi?q={q_encoded}&trang_thai=khoi_tao"
        )
        assert s_list == 200
        assert any(item["id"] == exam_id for item in items)

        # Kiểm tra ký tự '%' không match bừa các bản ghi không chứa '%'
        s_nomatch, items_nomatch = request_json("GET", f"/api/v1/ky-thi?q={urllib.parse.quote('___NONEXIST___%')}")
        assert s_nomatch == 200 and items_nomatch == []

        # 4. Lấy chi tiết (GET /{id}) & biên ID không hợp lệ
        s_get, detail = request_json("GET", f"/api/v1/ky-thi/{exam_id}")
        assert s_get == 200 and detail["ma_ky_thi"] == unique_code

        s_notfound, _ = request_json("GET", "/api/v1/ky-thi/999999999")
        assert s_notfound == 404

        for bad_id in ("0", "-1", "99999999999999999999999"):
            s_bad, _ = request_json("GET", f"/api/v1/ky-thi/{bad_id}")
            assert s_bad == 422, f"Expected 422 for id={bad_id}, got {s_bad}"

        # 5. Chặn PUT chỉ truyền 1 đầu ngày làm ngay_ket_thuc < ngay_bat_dau trong DB
        s_bad_date, _ = request_json(
            "PUT",
            f"/api/v1/ky-thi/{exam_id}",
            {"ngay_ket_thuc": "2026-07-15"},
        )
        assert s_bad_date == 422, f"Expected 422 for end < db start, got {s_bad_date}"

        s_bad_start, _ = request_json(
            "PUT",
            f"/api/v1/ky-thi/{exam_id}",
            {"ngay_bat_dau": "2026-09-01"},
        )
        assert s_bad_start == 422, f"Expected 422 for start > db end, got {s_bad_start}"

        # PUT body rỗng (no-op hợp lệ -> 200) và PUT/DELETE vào ID không tồn tại (-> 404)
        s_noop, noop_body = request_json("PUT", f"/api/v1/ky-thi/{exam_id}", {})
        assert s_noop == 200 and noop_body["id"] == exam_id
        s_put_404, _ = request_json("PUT", "/api/v1/ky-thi/999999999", {"ten_ky_thi": "Không tồn tại"})
        assert s_put_404 == 404
        s_del_404, _ = request_json("DELETE", "/api/v1/ky-thi/999999999")
        assert s_del_404 == 404

        # Biên phân trang skip & limit
        for bad_query in ("limit=0", "limit=501", "skip=-1", "skip=100001"):
            s_pg, _ = request_json("GET", f"/api/v1/ky-thi?{bad_query}")
            assert s_pg == 422, f"Expected 422 for {bad_query}, got {s_pg}"
        s_pg_ok, pg_items = request_json("GET", "/api/v1/ky-thi?skip=0&limit=1")
        assert s_pg_ok == 200 and len(pg_items) <= 1

        # 6. Cập nhật hợp lệ (PUT)
        s_upd, updated = request_json(
            "PUT",
            f"/api/v1/ky-thi/{exam_id}",
            {
                "ten_ky_thi": "Kỳ thi Test Ngày 4 - Đã sửa",
                "ngay_ket_thuc": "2026-08-20",
                "so_ca_moi_ngay": 3,
                "trang_thai": "da_xep_lich",
            },
        )
        assert s_upd == 200, f"Expected 200 on PUT, got {s_upd}: {updated}"
        assert updated["ten_ky_thi"] == "Kỳ thi Test Ngày 4 - Đã sửa"
        assert updated["ngay_ket_thuc"] == "2026-08-20"
        assert updated["so_ca_moi_ngay"] == 3
        assert updated["trang_thai"] == "da_xep_lich"

        # 7. Xóa kỳ thi (DELETE -> 204) và xác nhận đã xóa (GET -> 404)
        s_del, _ = request_json("DELETE", f"/api/v1/ky-thi/{exam_id}")
        assert s_del == 204, f"Expected 204 on DELETE, got {s_del}"
        created_ids.remove(exam_id)

        s_after_del, _ = request_json("GET", f"/api/v1/ky-thi/{exam_id}")
        assert s_after_del == 404
        print("✓ Test 2: CRUD Kỳ thi (/api/v1/ky-thi) và kiểm tra biên đạt 100%.")
    finally:
        for leftover_id in created_ids:
            request_json("DELETE", f"/api/v1/ky-thi/{leftover_id}")


def test_mon_hoc_crud_lifecycle_and_edge_cases():
    """Kiểm thử toàn bộ vòng đời CRUD /api/v1/mon-hoc và các trường hợp biên."""
    created_ids: list[int] = []
    unique_code = "TEST_D4_IT99"
    try:
        # 1. Tạo mới (POST)
        s_create, created = request_json(
            "POST",
            "/api/v1/mon-hoc",
            {
                "ma_mon": f"  {unique_code}  ",
                "ten_mon": "  Toán rời rạc Test D4  ",
                "thoi_luong_phut": 90,
                "so_tin_chi": 3,
            },
        )
        assert s_create == 201, f"Expected 201, got {s_create}: {created}"
        course_id = created["id"]
        created_ids.append(course_id)
        assert created["ma_mon"] == unique_code
        assert created["ten_mon"] == "Toán rời rạc Test D4"

        # 2. Chặn trùng mã môn (409) & chặn dữ liệu sai (422)
        s_dup, _ = request_json(
            "POST",
            "/api/v1/mon-hoc",
            {"ma_mon": unique_code, "ten_mon": "Trùng mã"},
        )
        assert s_dup == 409, f"Expected 409 on duplicate ma_mon, got {s_dup}"

        invalid_payloads = [
            {"ma_mon": "   ", "ten_mon": "Rỗng"},
            {"ma_mon": "IT_ERR1", "ten_mon": "Âm phút", "thoi_luong_phut": 0},
            {"ma_mon": "IT_ERR2", "ten_mon": "Bool phút", "thoi_luong_phut": True},
            {"ma_mon": "IT_ERR3", "ten_mon": "Dư trường", "unknown": 123},
        ]
        for payload in invalid_payloads:
            s_inv, _ = request_json("POST", "/api/v1/mon-hoc", payload)
            assert s_inv == 422, f"Expected 422 for {payload}, got {s_inv}"

        # 3. Danh sách & tìm kiếm (GET) & chi tiết (GET /{id})
        s_list, items = request_json("GET", f"/api/v1/mon-hoc?q={unique_code}")
        assert s_list == 200 and any(item["id"] == course_id for item in items)

        s_get, detail = request_json("GET", f"/api/v1/mon-hoc/{course_id}")
        assert s_get == 200 and detail["ma_mon"] == unique_code

        s_notfound, _ = request_json("GET", "/api/v1/mon-hoc/999999999")
        assert s_notfound == 404
        s_put_404, _ = request_json("PUT", "/api/v1/mon-hoc/999999999", {"ten_mon": "Không tồn tại"})
        assert s_put_404 == 404
        s_del_404, _ = request_json("DELETE", "/api/v1/mon-hoc/999999999")
        assert s_del_404 == 404

        # 4. Cập nhật từng phần (PUT), bao gồm cho phép so_tin_chi=None, body rỗng {} và chặn ten_mon=None
        s_noop, noop_course = request_json("PUT", f"/api/v1/mon-hoc/{course_id}", {})
        assert s_noop == 200 and noop_course["id"] == course_id
        s_null_ten, _ = request_json("PUT", f"/api/v1/mon-hoc/{course_id}", {"ten_mon": None})
        assert s_null_ten == 422

        s_upd, updated = request_json(
            "PUT",
            f"/api/v1/mon-hoc/{course_id}",
            {"ten_mon": "Toán rời rạc - Updated", "thoi_luong_phut": 120, "so_tin_chi": None},
        )
        assert s_upd == 200, f"Expected 200 on PUT, got {s_upd}: {updated}"
        assert updated["ten_mon"] == "Toán rời rạc - Updated"
        assert updated["thoi_luong_phut"] == 120
        assert updated["so_tin_chi"] is None

        # 5. Xóa môn học (DELETE -> 204) & kiểm tra GET -> 404
        s_del, _ = request_json("DELETE", f"/api/v1/mon-hoc/{course_id}")
        assert s_del == 204, f"Expected 204 on DELETE, got {s_del}"
        created_ids.remove(course_id)

        s_after_del, _ = request_json("GET", f"/api/v1/mon-hoc/{course_id}")
        assert s_after_del == 404
        print("✓ Test 3: CRUD Môn học (/api/v1/mon-hoc) và kiểm tra biên đạt 100%.")
    finally:
        for leftover_id in created_ids:
            request_json("DELETE", f"/api/v1/mon-hoc/{leftover_id}")


if __name__ == "__main__":
    print(f"=== BẮT ĐẦU KIỂM THỬ NGÀY 4 (TV2 CRUD KyThi & MonHoc qua {BASE_URL}) ===")
    test_openapi_exposes_ky_thi_and_mon_hoc_endpoints()
    test_ky_thi_crud_lifecycle_and_edge_cases()
    test_mon_hoc_crud_lifecycle_and_edge_cases()
    print("=== TẤT CẢ CÁC BƯỚC KIỂM THỬ NGÀY 4 ĐÃ ĐẠT 100% ===")
