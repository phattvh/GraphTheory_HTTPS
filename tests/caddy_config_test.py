"""Automated tests for Caddyfile configuration (TV3 — Day 5).

Verifies:
1. Caddyfile syntax validation inside the running caddy container.
2. Gzip compression (Accept-Encoding: gzip -> Content-Encoding: gzip) on static & API endpoints.
3. Explicit routing for /, /api/v1/*, /docs, /redoc, /openapi.json and Cache-Control policies.
4. OWASP security headers (including Permissions-Policy) and stripped Server header.
"""

import gzip
import json
import ssl
import subprocess
import sys
import urllib.request

BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def _request(path: str, headers: dict[str, str] | None = None):
    req = urllib.request.Request(BASE_URL + path, headers=headers or {})
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=5) as resp:
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, resp_headers, resp.read()


def test_caddyfile_validate() -> None:
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "caddy", "caddy", "validate", "--config", "/etc/caddy/Caddyfile"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"caddy validate failed (exit {result.returncode}):\n{result.stderr or result.stdout}"
    )
    print("[PASS] caddy validate --config /etc/caddy/Caddyfile succeeded.")


def test_gzip_compression_on_static_and_api() -> None:
    for path, expected_marker in [("/", "<!DOCTYPE html>"), ("/openapi.json", '"openapi"')]:
        status, headers, raw_body = _request(path, headers={"Accept-Encoding": "gzip"})
        assert status == 200, f"GET {path} returned {status}"
        assert headers.get("content-encoding") == "gzip", (
            f"Expected Content-Encoding: gzip for {path}, got: {headers.get('content-encoding')}"
        )
        decompressed = gzip.decompress(raw_body).decode("utf-8")
        assert expected_marker.lower() in decompressed.lower(), (
            f"Decompressed response for {path} missing marker {expected_marker!r}"
        )
    print("[PASS] Gzip compression verified on / and /openapi.json.")


def test_routing_and_cache_control() -> None:
    # Static root route /
    status, headers, _ = _request("/")
    assert status == 200
    assert headers.get("cache-control") == "no-cache", (
        f"Expected Cache-Control: no-cache on /, got: {headers.get('cache-control')}"
    )

    # API v1 route /api/v1/health
    status, headers, raw_body = _request("/api/v1/health")
    assert status == 200
    assert headers.get("cache-control") == "no-store", (
        f"Expected Cache-Control: no-store on /api/v1/health, got: {headers.get('cache-control')}"
    )
    payload = json.loads(raw_body.decode("utf-8"))
    assert payload.get("status") == "ok"
    assert payload.get("service") == "fastapi"

    # Docs routes (/docs, /redoc, /openapi.json)
    for path in ["/docs", "/redoc", "/openapi.json"]:
        st, _, _ = _request(path)
        assert st == 200, f"Expected 200 on {path}, got {st}"

    print("[PASS] Routing (/, /api/v1/*, /docs, /redoc, /openapi.json) & Cache-Control verified.")


def test_owasp_security_headers() -> None:
    for path in ["/", "/api/v1/health"]:
        _, headers, _ = _request(path)
        assert "max-age=" in headers.get("strict-transport-security", "")
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "geolocation=()" in headers.get("permissions-policy", "")
        assert "server" not in headers, f"Server header leaked on {path}: {headers.get('server')}"
    print("[PASS] OWASP security headers & Permissions-Policy verified on / and /api/v1/health.")


def main() -> int:
    test_caddyfile_validate()
    test_gzip_compression_on_static_and_api()
    test_routing_and_cache_control()
    test_owasp_security_headers()
    print("ALL CADDY CONFIG TESTS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
