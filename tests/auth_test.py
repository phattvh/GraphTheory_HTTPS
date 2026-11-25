"""Kiểm thử tự động API xác thực Native JWT Ngày 3 (TV3: UC01).

Kiểm thử end-to-end qua Caddy HTTPS -> FastAPI -> PostgreSQL:
    python3 tests/auth_test.py
"""

import json
import ssl
import urllib.error
import urllib.request

BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def request_json(method: str, path: str, body=None, headers=None):
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers=req_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            headers_lower = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, json.loads(raw) if raw else {}, headers_lower
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        parsed = json.loads(raw) if raw else {}
        headers_lower = {k.lower(): v for k, v in err.headers.items()}
        return err.code, parsed, headers_lower


def test_openapi_exposes_auth_endpoints():
    """Swagger/OpenAPI phải hiển thị đủ POST /api/v1/auth/login và GET /api/v1/auth/me."""
    status, data, _ = request_json("GET", "/openapi.json")
    assert status == 200
    paths = data.get("paths", {})
    assert "/api/v1/auth/login" in paths and "post" in paths["/api/v1/auth/login"]
    assert "/api/v1/auth/me" in paths and "get" in paths["/api/v1/auth/me"]


def test_login_admin_success_and_get_me():
    """Đăng nhập admin thành công -> trả JWT hợp lệ, không lộ mat_khau_hash, gọi /me trả 200."""
    status, data, _ = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "admin", "mat_khau": "admin123"},
    )
    assert status == 200, f"Expected 200, got {status}: {data}"
    assert data.get("token_type") == "bearer"
    token = data.get("access_token", "")
    assert isinstance(token, str) and len(token.split(".")) == 3

    user = data.get("user", {})
    assert user.get("ten_dang_nhap") == "admin"
    assert user.get("vai_tro") == "admin"
    assert "mat_khau_hash" not in user, "Tuyệt đối không được trả mat_khau_hash ra response"

    # Kiểm thử GET /api/v1/auth/me với Bearer JWT
    me_status, me_data, _ = request_json(
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_status == 200, f"Expected 200 on /me, got {me_status}: {me_data}"
    assert me_data.get("ten_dang_nhap") == "admin"
    assert me_data.get("vai_tro") == "admin"
    assert "mat_khau_hash" not in me_data


def test_login_invalid_credentials_and_anti_enumeration():
    """Sai mật khẩu và tài khoản không tồn tại phải trả 401 cùng thông báo lỗi chung."""
    s1, d1, h1 = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "admin", "mat_khau": "wrong-password"},
    )
    s2, d2, h2 = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "user_khong_ton_tai_999", "mat_khau": "admin123"},
    )
    assert s1 == 401 and s2 == 401
    assert d1.get("detail") == d2.get("detail"), "Thông báo lỗi phải đồng nhất để chống dò tài khoản"
    assert "bearer" in h1.get("WWW-Authenticate", h1.get("www-authenticate", "")).lower()
    assert "bearer" in h2.get("WWW-Authenticate", h2.get("www-authenticate", "")).lower()


def test_login_validation_errors():
    """Chặn payload rỗng, mật khẩu quá dài (>128) và trường thừa (extra='forbid')."""
    s_empty, _, _ = request_json("POST", "/api/v1/auth/login", {"ten_dang_nhap": "   ", "mat_khau": "123"})
    assert s_empty == 422

    s_extra, _, _ = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "admin", "mat_khau": "admin123", "vai_tro": "admin"},
    )
    assert s_extra == 422

    # Mật khẩu > 72 bytes (giới hạn bcrypt) không được gây lỗi 500
    s_long, _, _ = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "admin", "mat_khau": "a" * 100},
    )
    assert s_long == 401


def test_me_unauthorized_cases():
    """GET /api/v1/auth/me phải trả 401 khi thiếu token, sai scheme hoặc token bị sửa chữ ký."""
    s_missing, _, _ = request_json("GET", "/api/v1/auth/me")
    assert s_missing == 401

    s_bad_scheme, _, _ = request_json(
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert s_bad_scheme == 401

    s_garbage, _, _ = request_json(
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert s_garbage == 401

    # Lấy token thật rồi sửa chữ ký
    _, login_data, _ = request_json(
        "POST",
        "/api/v1/auth/login",
        {"ten_dang_nhap": "admin", "mat_khau": "admin123"},
    )
    tok = login_data["access_token"]
    tampered = tok[:-2] + ("AA" if not tok.endswith("AA") else "BB")
    s_tampered, _, _ = request_json(
        "GET",
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert s_tampered == 401


if __name__ == "__main__":
    test_openapi_exposes_auth_endpoints()
    test_login_admin_success_and_get_me()
    test_login_invalid_credentials_and_anti_enumeration()
    test_login_validation_errors()
    test_me_unauthorized_cases()
    print("ALL AUTH API TESTS PASSED!")
