from pathlib import Path
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def test_login_files_exist():
    """Kiểm tra đầy đủ file UI màn hình Đăng nhập (TV5 Ngày 1 — UC01 UI)."""
    for file_path in [
        WEB_DIR / "login.html",
        WEB_DIR / "css" / "login.css",
        WEB_DIR / "js" / "core" / "login.js",
        WEB_DIR / "js" / "core" / "auth.js",
    ]:
        assert file_path.exists(), f"Thiếu file đăng nhập bắt buộc: {file_path}"


def test_login_page_structure_and_security():
    """Kiểm tra cấu trúc form Đăng nhập, accessibility và không còn chuỗi thừa từ template."""
    html = (WEB_DIR / "login.html").read_text(encoding="utf-8")
    css = (WEB_DIR / "css" / "login.css").read_text(encoding="utf-8")
    js = (WEB_DIR / "js" / "core" / "login.js").read_text(encoding="utf-8")
    auth_js = (WEB_DIR / "js" / "core" / "auth.js").read_text(encoding="utf-8")

    for marker in [
        'id="login-card"',
        'id="login-form"',
        'id="login-username"',
        'name="ten_dang_nhap"',
        'id="login-password"',
        'name="mat_khau"',
        'data-pw-toggle',
        'data-caps',
        'href="/css/login.css"',
        'src="/js/core/auth.js"',
        'src="/js/core/login.js"',
        'src="/assets/logo.svg"',
        'class="https-login__pupil"',
    ]:
        assert marker in html, f"web/login.html thiếu thành phần: {marker}"

    for forbidden in ["Colorlib", "Sprout", "plant pal", "GraphSchedule"]:
        assert forbidden not in html, f"web/login.html còn sót chuỗi template cũ: {forbidden}"

    assert ".https-login-card" in css and ".is-shy" in css
    assert "/api/v1/auth/login" in js and "CapsLock" in js
    assert "innerHTML" not in js, "web/js/core/login.js không được dùng innerHTML để tránh XSS"
    assert "innerHTML" not in auth_js, "web/js/core/auth.js không được dùng innerHTML để tránh XSS"


def test_login_form_submit_json_payload():
    """Kiểm tra mã JS bắt sự kiện submit form gửi payload JSON (TV4 Ngày 2 — UC01 UI)."""
    js = (WEB_DIR / "js" / "core" / "login.js").read_text(encoding="utf-8")

    for required_token in [
        "function buildLoginPayload",
        "function sendLoginJsonPayload",
        "handleLoginFormSubmit",
        "ten_dang_nhap:",
        "mat_khau:",
        'method: "POST"',
        '"Content-Type": "application/json"',
        "JSON.stringify(payload)",
        'form.addEventListener("submit", handleLoginFormSubmit)',
    ]:
        assert required_token in js, f"web/js/core/login.js thiếu logic submit JSON: {required_token}"


def test_jwt_storage_and_role_redirection():
    """Kiểm tra nối API login, lưu JWT vào localStorage và điều hướng theo vai_tro (TV4 Ngày 3 — UC01 UI)."""
    auth_js = (WEB_DIR / "js" / "core" / "auth.js").read_text(encoding="utf-8")
    login_js = (WEB_DIR / "js" / "core" / "login.js").read_text(encoding="utf-8")

    for auth_marker in [
        "function normalizeRole",
        "function parseJwtPayload",
        "function isTokenExpired",
        "function saveAuthSession",
        "function getAccessToken",
        "function getCurrentUser",
        "function getAuthHeaders",
        "function clearAuthSession",
        "function navigateByRole",
        "function handleLogout",
        "localStorage.setItem",
        "localStorage.getItem",
        "localStorage.removeItem",
        "Bearer ",
        '"/student.html"',
        '"/index.html"',
    ]:
        assert auth_marker in auth_js, f"web/js/core/auth.js thiếu thành phần JWT/Role: {auth_marker}"
    assert 'method: "HEAD"' not in auth_js, "handleLogout không được gửi request HEAD thừa"

    for login_marker in [
        "function handleLoginSuccessResponse",
        "saveAuthSession(data)",
        "navigateByRole(",
        "handleLoginSuccessResponse(data)",
        "resp.status === 401",
    ]:
        assert login_marker in login_js, f"web/js/core/login.js thiếu logic nối JWT & điều hướng: {login_marker}"


def test_auth_js_runtime_edge_cases():
    """Chạy thực tế web/js/core/auth.js & login.js bằng Node.js (nếu có) để kiểm chứng mọi edge case."""
    if not shutil.which("node"):
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const store = new Map();
const sandbox = {
  localStorage: {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  },
  window: { location: { pathname: "/login.html", search: "", href: "/login.html" } },
  document: { addEventListener: () => {}, querySelector: () => null },
  URLSearchParams,
  atob: (b64) => Buffer.from(b64, "base64").toString("binary"),
  TextDecoder,
  Uint8Array,
  fetch: () => { throw new Error("fetch should not be called on handleLogout"); },
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/core/auth.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("web/js/core/login.js", "utf8"), sandbox);

const makeJwt = (payload) => {
  const b64u = (obj) => Buffer.from(JSON.stringify(obj), "utf8").toString("base64url");
  return `${b64u({ alg: "HS256", typ: "JWT" })}.${b64u(payload)}.sig`;
};

const now = Math.floor(Date.now() / 1000);

// 1. Valid admin JWT with Vietnamese UTF-8 ho_ten
const adminJwt = makeJwt({ sub: "admin", vai_tro: "admin", ho_ten: "Trần Vũ Hòa Phát", exp: now + 3600 });
const adminRes = sandbox.handleLoginSuccessResponse({ access_token: adminJwt });
assert.strictEqual(adminRes.vai_tro, "admin");
assert.strictEqual(sandbox.getAccessToken(), adminJwt);
assert.strictEqual(sandbox.getCurrentUser().ho_ten, "Trần Vũ Hòa Phát");
assert.strictEqual(sandbox.window.location.href, "/index.html");

// 2. Expired JWT must invalidate cached current_user in getCurrentUser()
const expiredJwt = makeJwt({ sub: "admin", vai_tro: "admin", exp: now - 10 });
store.set("access_token", expiredJwt);
store.set("current_user", JSON.stringify({ ten_dang_nhap: "admin", vai_tro: "admin" }));
assert.strictEqual(sandbox.getCurrentUser(), null);
assert.strictEqual(store.has("access_token"), false);
assert.strictEqual(store.has("current_user"), false);

// 3. Malformed non-JWT string in localStorage must be cleared
store.set("access_token", "corrupted-token");
assert.strictEqual(sandbox.getAccessToken(), null);
assert.strictEqual(store.has("access_token"), false);

// 4. Missing access_token in login response must NOT save session or redirect
sandbox.window.location = { pathname: "/login.html", search: "", href: "/login.html" };
assert.strictEqual(sandbox.handleLoginSuccessResponse({ vai_tro: "admin" }), null);
assert.strictEqual(store.has("current_user"), false);
assert.strictEqual(sandbox.window.location.href, "/login.html");

// 5. Unknown role must fail closed (never default to admin)
const unknownRoleJwt = makeJwt({ sub: "hacker", vai_tro: "superadmin", exp: now + 3600 });
assert.strictEqual(sandbox.handleLoginSuccessResponse({ access_token: unknownRoleJwt }), null);
assert.strictEqual(sandbox.window.location.href, "/login.html");
sandbox.navigateByRole("superadmin");
assert.strictEqual(sandbox.window.location.href, "/login.html");

// 6. Valid student JWT redirects to /student.html
const svJwt = makeJwt({ sub: "22110399", vai_tro: "sinh_vien", mssv: "22110399", exp: now + 3600 });
const svRes = sandbox.handleLoginSuccessResponse({ access_token: svJwt });
assert.strictEqual(svRes.vai_tro, "sinh_vien");
assert.strictEqual(sandbox.window.location.href, "/student.html");

// 7. handleLogout clears session and redirects directly without fetch
sandbox.handleLogout();
assert.strictEqual(store.size, 0);
assert.strictEqual(sandbox.window.location.href, "/login.html");
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime auth test failed:\n{res.stderr or res.stdout}"


def test_cytoscape_cdn_configuration():
    """Kiểm tra cấu hình nhúng CDN thư viện cytoscape.js trên web/graph.html (TV5 Ngày 1)."""
    graph_html = (WEB_DIR / "graph.html").read_text(encoding="utf-8")
    layout_css = (WEB_DIR / "css" / "layout.css").read_text(encoding="utf-8")
    graph_js = (WEB_DIR / "js" / "admin" / "graph.js").read_text(encoding="utf-8")

    assert "cytoscape" in graph_html and "cytoscape.min.js" in graph_html
    assert 'id="cy"' in graph_html
    assert 'src="/js/admin/graph.js"' in graph_html
    assert "#cy" in layout_css
    assert "initConflictGraph" in graph_js and "window.cytoscape" in graph_js


def test_caddy_serves_login_and_graph_assets():
    """Nếu Caddy đang chạy, kiểm tra HTTP 200 OK cho /login.html, CSS/JS và /js/admin/graph.js."""
    try:
        for path, marker in [
            ("/login.html", 'id="login-form"'),
            ("/css/login.css", ".https-login-card"),
            ("/js/core/login.js", "handleLoginSuccessResponse"),
            ("/js/core/auth.js", "saveAuthSession"),
            ("/graph.html", "cytoscape.min.js"),
            ("/js/admin/graph.js", "initConflictGraph"),
        ]:
            with urllib.request.urlopen(BASE_URL + path, context=SSL_CTX, timeout=3) as resp:
                body = resp.read().decode("utf-8")
                assert resp.status == 200, f"GET {path} trả về {resp.status}"
                assert marker in body, f"GET {path} thiếu marker {marker}"
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError:
        pass


if __name__ == "__main__":
    test_login_files_exist()
    test_login_page_structure_and_security()
    test_login_form_submit_json_payload()
    test_jwt_storage_and_role_redirection()
    test_auth_js_runtime_edge_cases()
    test_cytoscape_cdn_configuration()
    test_caddy_serves_login_and_graph_assets()
    print("ALL LOGIN & CYTOSCAPE TESTS PASSED!")
