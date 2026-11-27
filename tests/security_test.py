"""Kiểm thử tự động bảo mật Bcrypt & Native JWT Ngày 2 (TV3: backend/core/security.py).

Chạy bên trong container fastapi:
    docker compose exec fastapi python tests/security_test.py
"""

from datetime import timedelta
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import jwt

from backend.core import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

# Hash bcrypt cost 12 của mật khẩu mặc định 'admin123' trong db/init/init.sql
SEED_ADMIN_HASH = "$2b$12$vP7lBCkdmRqOg4.tVNt26.VgNq85ByD2HxuX4m9grMVsm9s1Se.kW"


def test_password_hash_and_verify():
    """Kiểm tra băm mật khẩu bcrypt (salt ngẫu nhiên, cost 12) và đối chiếu."""
    plain = "MatKhauBaoMat@2026"
    hash_1 = get_password_hash(plain)
    hash_2 = get_password_hash(plain)

    assert hash_1 != plain
    assert hash_1.startswith("$2b$12$"), f"Hash phải dùng bcrypt cost 12, nhận được: {hash_1[:7]}"
    assert hash_1 != hash_2, "Hai lần băm cùng mật khẩu phải sinh salt khác nhau"

    assert verify_password(plain, hash_1) is True
    assert verify_password(plain, hash_2) is True
    assert verify_password("SaiMatKhau", hash_1) is False
    assert verify_password("", hash_1) is False
    assert verify_password(plain, "") is False
    assert verify_password(plain, "not-a-valid-bcrypt-hash") is False

    try:
        get_password_hash("")
        raise AssertionError("get_password_hash('') phải ném ValueError")
    except ValueError:
        pass


def test_verify_seed_admin_hash():
    """Kiểm tra verify_password khớp chính xác với tài khoản admin seed trong db/init/init.sql."""
    assert verify_password("admin123", SEED_ADMIN_HASH) is True
    assert verify_password("admin124", SEED_ADMIN_HASH) is False


def test_create_and_decode_access_token():
    """Kiểm tra tạo & giải mã JWT HS256 cho cả vai trò admin và sinh_vien."""
    admin_token = create_access_token({"sub": "admin", "vai_tro": "admin", "mssv": None})
    admin_payload = decode_access_token(admin_token)
    assert admin_payload["sub"] == "admin"
    assert admin_payload["vai_tro"] == "admin"
    assert admin_payload["mssv"] is None
    assert "iat" in admin_payload and "exp" in admin_payload

    student_token = create_access_token(
        {"sub": "22110399", "vai_tro": "sinh_vien", "mssv": "22110399"},
        expires_delta=timedelta(minutes=30),
    )
    student_payload = decode_access_token(student_token)
    assert student_payload["sub"] == "22110399"
    assert student_payload["vai_tro"] == "sinh_vien"
    assert student_payload["mssv"] == "22110399"


def test_invalid_and_expired_tokens():
    """Kiểm tra từ chối token bị sửa chữ ký, sai secret hoặc đã hết hạn."""
    valid_token = create_access_token({"sub": "admin", "vai_tro": "admin"})
    tampered_token = valid_token[:-2] + ("AA" if not valid_token.endswith("AA") else "BB")

    try:
        decode_access_token(tampered_token)
        raise AssertionError("Token bị giả mạo chữ ký phải bị từ chối")
    except jwt.InvalidTokenError:
        pass

    wrong_secret_token = jwt.encode(
        {"sub": "admin", "vai_tro": "admin"},
        "wrong-secret-key-at-least-32-bytes-long",
        algorithm="HS256",
    )
    try:
        decode_access_token(wrong_secret_token)
        raise AssertionError("Token ký bằng secret sai phải bị từ chối")
    except jwt.InvalidSignatureError:
        pass

    expired_token = create_access_token(
        {"sub": "admin", "vai_tro": "admin"},
        expires_delta=timedelta(seconds=-5),
    )
    try:
        decode_access_token(expired_token)
        raise AssertionError("Token đã hết hạn phải ném ExpiredSignatureError")
    except jwt.ExpiredSignatureError:
        pass


def test_jwt_secret_and_app_env_validation():
    """Kiểm tra Settings chặn JWT_SECRET < 32 bytes và chặn secret mặc định khi APP_ENV=production."""
    from pydantic import ValidationError
    from backend.core.config import Settings

    # 1. Secret ngắn hơn 32 bytes bị từ chối ở mọi môi trường
    for env in ("development", "production"):
        try:
            Settings(APP_ENV=env, JWT_SECRET="too-short-secret")
            raise AssertionError(f"JWT_SECRET < 32 bytes phải bị chặn ở APP_ENV={env}")
        except ValidationError:
            pass

    # 2. Secret mặc định được phép ở development nhưng bị chặn ở production (fail-fast)
    dev_cfg = Settings(
        APP_ENV="development",
        JWT_SECRET="dev-secret-change-me-at-least-32-bytes",
    )
    assert dev_cfg.APP_ENV == "development"

    for default_secret in (
        "dev-secret-change-me-at-least-32-bytes",
        "change-this-secret-in-production-at-least-32-bytes",
    ):
        try:
            Settings(APP_ENV="production", JWT_SECRET=default_secret)
            raise AssertionError("APP_ENV=production phải từ chối JWT_SECRET mặc định")
        except ValidationError:
            pass

    # 3. Secret mạnh >= 32 bytes hoạt động bình thường ở production
    prod_cfg = Settings(
        APP_ENV="  PRODUCTION  ",
        JWT_SECRET="9f8e7d6c5b4a3928172635445566778899aabbccddeeff00",
    )
    assert prod_cfg.APP_ENV == "production"

    # 4. APP_ENV lạ phải bị chặn
    try:
        Settings(APP_ENV="staging_unknown", JWT_SECRET="9f8e7d6c5b4a3928172635445566778899aabbccddeeff00")
        raise AssertionError("APP_ENV không hợp lệ phải bị từ chối")
    except ValidationError:
        pass


if __name__ == "__main__":
    test_password_hash_and_verify()
    test_verify_seed_admin_hash()
    test_create_and_decode_access_token()
    test_invalid_and_expired_tokens()
    test_jwt_secret_and_app_env_validation()
    print("ALL SECURITY TESTS PASSED!")
