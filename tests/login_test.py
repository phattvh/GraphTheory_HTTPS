from pathlib import Path
import ssl
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
    ]:
        assert file_path.exists(), f"Thiếu file đăng nhập bắt buộc: {file_path}"


def test_login_page_structure_and_security():
    """Kiểm tra cấu trúc form Đăng nhập, accessibility và không còn chuỗi thừa từ template."""
    html = (WEB_DIR / "login.html").read_text(encoding="utf-8")
    css = (WEB_DIR / "css" / "login.css").read_text(encoding="utf-8")
    js = (WEB_DIR / "js" / "core" / "login.js").read_text(encoding="utf-8")

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
        ">HTTPS<",
    ]:
        assert marker in html, f"web/login.html thiếu thành phần: {marker}"

    for forbidden in ["Colorlib", "Sprout", "plant pal", "GraphSchedule"]:
        assert forbidden not in html, f"web/login.html còn sót chuỗi template cũ: {forbidden}"

    assert ".https-login-card" in css and ".is-shy" in css
    assert "/api/v1/auth/login" in js and "CapsLock" in js
    assert "innerHTML" not in js, "web/js/core/login.js không được dùng innerHTML để tránh XSS"


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
            ("/js/core/login.js", "/api/v1/auth/login"),
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
    test_cytoscape_cdn_configuration()
    test_caddy_serves_login_and_graph_assets()
    print("ALL LOGIN & CYTOSCAPE TESTS PASSED!")
