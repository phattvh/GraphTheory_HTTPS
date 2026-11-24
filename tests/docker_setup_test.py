import json
import ssl
import urllib.request

BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def get(path: str):
    with urllib.request.urlopen(BASE_URL + path, context=SSL_CTX) as resp:
        return resp.status, resp.read().decode("utf-8")


def test_health_endpoint():
    status, body = get("/api/v1/health")
    assert status == 200
    data = json.loads(body)
    assert data["status"] == "ok"
    assert data["service"] == "fastapi"
    assert data["database"] == "connected"


def test_swagger_docs():
    status, body = get("/docs")
    assert status == 200
    assert "Swagger UI" in body


def test_static_web():
    status, _ = get("/")
    assert status == 200


def test_security_headers():
    with urllib.request.urlopen(BASE_URL + "/", context=SSL_CTX) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        assert "max-age=" in headers.get("strict-transport-security", "")
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "server" not in headers, f"Server header should be stripped, got: {headers.get('server')}"


if __name__ == "__main__":
    test_health_endpoint()
    test_swagger_docs()
    test_static_web()
    test_security_headers()
    print("ALL TESTS PASSED!")
