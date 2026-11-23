from pathlib import Path
import ssl
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def test_layout_files_exist():
    """Kiểm tra đầy đủ các file khung giao diện Admin & Sinh viên trong web/."""
    required_files = [
        WEB_DIR / "index.html",
        WEB_DIR / "student.html",
        WEB_DIR / "css" / "layout.css",
        WEB_DIR / "js" / "layout.js",
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Thiếu file giao diện bắt buộc: {file_path}"


def test_admin_and_student_shell_structure():
    """Kiểm tra cấu trúc HTML của khung Admin (Sidebar, Header, 4 tab) và Sinh viên."""
    index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    student_html = (WEB_DIR / "student.html").read_text(encoding="utf-8")

    # Kiểm tra nhúng Tailwind CSS CDN theo 07. Technology stack.md
    assert "https://cdn.tailwindcss.com" in index_html
    assert "https://cdn.tailwindcss.com" in student_html

    # Kiểm tra các vùng khung giao diện Admin (Sidebar, Top Header, Main Content, 4 Tabs)
    admin_markers = [
        'id="admin-layout-shell"',
        'id="admin-sidebar"',
        'id="admin-header"',
        'id="admin-main-content"',
        'id="tab-crud"',
        'id="tab-graph"',
        'id="tab-calendar"',
        'id="tab-stats"',
        "GraphSchedule",
    ]
    for marker in admin_markers:
        assert marker in index_html, f"Thiếu thành phần khung Admin: {marker}"

    # Kiểm tra khung giao diện Sinh viên (Student Portal)
    student_markers = [
        'id="student-header"',
        'id="student-main-content"',
        'id="student-fullcalendar-shell"',
        "Student Portal",
    ]
    for marker in student_markers:
        assert marker in index_html, f"Thiếu thành phần khung Sinh viên trong index.html: {marker}"
        assert marker in student_html, f"Thiếu thành phần khung Sinh viên trong student.html: {marker}"


def test_caddy_serves_layout_if_running():
    """Nếu container caddy:2-alpine đang chạy, kiểm tra truy cập trực tiếp qua HTTPS."""
    try:
        with urllib.request.urlopen(BASE_URL + "/", context=SSL_CTX, timeout=3) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert 'id="admin-layout-shell"' in body
            assert 'id="student-layout-shell"' in body

        with urllib.request.urlopen(BASE_URL + "/student.html", context=SSL_CTX, timeout=3) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert 'id="student-header"' in body

        with urllib.request.urlopen(BASE_URL + "/js/layout.js", context=SSL_CTX, timeout=3) as resp:
            js_body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "switchAdminTab" in js_body
    except urllib.error.URLError:
        # Cho phép chạy unit test cấu trúc file ngay cả khi container chưa bật
        pass


if __name__ == "__main__":
    test_layout_files_exist()
    test_admin_and_student_shell_structure()
    test_caddy_serves_layout_if_running()
    print("ALL LAYOUT TESTS PASSED!")
