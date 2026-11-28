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

ADMIN_PAGES = {
    "index.html": ("crud", 'id="tab-crud"'),
    "graph.html": ("graph", 'id="tab-graph"'),
    "calendar.html": ("calendar", 'id="tab-calendar"'),
    "stats.html": ("stats", 'id="tab-stats"'),
}


def test_layout_files_exist():
    """Kiểm tra đầy đủ 4 trang Admin, trang Sinh viên, CSS và JS theo 09. Project structure.md."""
    required_files = [
        WEB_DIR / "index.html",
        WEB_DIR / "graph.html",
        WEB_DIR / "calendar.html",
        WEB_DIR / "stats.html",
        WEB_DIR / "student.html",
        WEB_DIR / "assets" / "logo.svg",
        WEB_DIR / "css" / "layout.css",
        WEB_DIR / "js" / "core" / "auth.js",
        WEB_DIR / "js" / "admin" / "layout.js",
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Thiếu file giao diện bắt buộc: {file_path}"


def test_admin_pages_and_student_structure():
    """Kiểm tra cấu trúc HTML tách riêng của 4 trang Admin và trang Sinh viên."""
    layout_js = (WEB_DIR / "js" / "admin" / "layout.js").read_text(encoding="utf-8")
    auth_js = (WEB_DIR / "js" / "core" / "auth.js").read_text(encoding="utf-8")

    # Kiểm tra các hàm dùng chung trong layout.js và auth.js
    for marker in ["initAdminShell", "toggleRightDrawer", "closeRightDrawer", 'id="admin-header"', 'id="admin-sidebar"', "/assets/logo.svg", ">HTTPS<"]:
        assert marker in layout_js, f"Thiếu thành phần shell dùng chung trong layout.js: {marker}"
    assert "Cổng Sinh viên" not in layout_js, "Không còn hiển thị Cổng Sinh viên trên thanh Admin"
    assert "Đang xem:" not in layout_js, "Không còn hiển thị nhãn 'Đang xem:'"
    assert "DSatur &amp; Welsh–Powell Engine" not in layout_js, "Không còn hiển thị dòng Engine dưới logo"
    assert "0% Xung đột SV • χ(G) = 4 Ca thi" not in layout_js, "Không còn hiển thị badge xung đột trên header"
    assert "📥 Import Excel" not in layout_js, "Không còn nút Import Excel trên header"
    assert "⚡ Xếp lịch DSatur" not in layout_js, "Không còn nút Xếp lịch DSatur trên header"
    assert "CRUD_ENTITIES" in layout_js and '"Kỳ thi"' in layout_js and '"Quản lý Sinh viên"' in layout_js
    assert 'activePage === "crud"' in layout_js and 'id="crud-entity-menubar"' in layout_js
    assert 'id="crud-entity-menubar" class="w-full px-6 bg-white' in layout_js, "Thanh danh mục CRUD phải cùng màu nền trắng với header phía trên"
    assert "bg-slate-50/90" not in layout_js, "Không dùng nền xám tách biệt cho thanh danh mục CRUD"
    assert "font-bold text-blue-700 border-b-2 border-blue-700" in layout_js, "Mục CRUD đang chọn phải chữ xanh đậm và có gạch dưới"
    assert ">Menu<" not in layout_js, "Nút mở sidebar chỉ dùng biểu tượng, bỏ chữ Menu"
    assert 'aria-label="Mở menu điều hướng"' in layout_js and "w-10 h-10" in layout_js
    assert 'id="global-search-input"' not in layout_js, "Đã bỏ thanh tìm kiếm nhanh trên header Admin"
    assert "Trạng thái Engine" not in layout_js, "Đã bỏ khung Trạng thái Engine khỏi sidebar Admin"
    assert "(UC" not in layout_js, "Không còn nhãn (UC...) trên giao diện"
    assert "max-w-[1440px]" not in layout_js, "Header Admin phải dùng full-width"
    assert layout_js.index('id="btn-open-right-drawer"') < layout_js.index(">HTTPS<"), "Nút Menu phải nằm cùng chỗ bên trái với logo HTTPS"

    for marker in ["navigateByRole", "handleLogout"]:
        assert marker in auth_js, f"Thiếu hàm điều khiển trong auth.js: {marker}"

    # Kiểm tra từng trang Admin tách riêng
    for filename, (page_key, section_id) in ADMIN_PAGES.items():
        html = (WEB_DIR / filename).read_text(encoding="utf-8")
        assert "https://cdn.tailwindcss.com" in html, f"{filename} thiếu Tailwind CSS CDN"
        assert f'data-admin-page="{page_key}"' in html, f"{filename} thiếu data-admin-page={page_key}"
        assert 'id="admin-layout-shell"' in html, f"{filename} thiếu admin-layout-shell"
        assert 'id="admin-shell-mount"' in html, f"{filename} thiếu admin-shell-mount"
        assert 'id="admin-main-content"' in html, f"{filename} thiếu admin-main-content"
        assert "max-w-[1440px]" not in html, f"{filename} phải dùng full-width flex"
        assert "GraphSchedule" not in html, f"{filename} phải đổi tên thành HTTPS"
        assert section_id in html, f"{filename} thiếu section chính {section_id}"
        assert 'src="/js/core/auth.js"' in html
        assert 'src="/js/admin/layout.js"' in html
        assert 'href="/login.html"' not in html

    # Kiểm tra đủ 5 CRUD panels (UC02-UC06) trên index.html & crud.js
    index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    crud_js = (WEB_DIR / "js" / "admin" / "crud.js").read_text(encoding="utf-8")
    for panel_id in [
        'id="crud-panel-ky_thi"',
        'id="crud-panel-mon_hoc"',
        'id="crud-panel-sinh_vien"',
        'id="crud-panel-phong_thi"',
        'id="crud-panel-dang_ky_thi"',
        'id="course-crud-modal"',
        'id="student-crud-modal"',
        'id="exam-crud-modal"',
        'id="import-data-modal"',
        'id="delete-confirm-modal"',
        'role="alertdialog"',
        'id="btn-confirm-delete"',
        'id="btn-open-course-modal"',
        'id="btn-open-student-modal"',
        'id="btn-open-exam-modal"',
        'id="btn-open-import-modal"',
        'id="btn-export-excel"',
        'id="exam-crud-form"',
        'id="exam-table-body"',
        'id="course-crud-form"',
        'id="course-table-body"',
    ]:
        assert panel_id in index_html, f"index.html thiếu thành phần {panel_id}"
    assert 'id="crud-active-heading"' not in index_html, "Đã bỏ banner tiêu đề thừa phía trên bảng CRUD"
    assert "Cấu hình Kỳ thi hiện tại" not in index_html, "Đã bỏ khung mockup tĩnh Cấu hình Kỳ thi hiện tại"
    assert 'src="/js/admin/crud.js"' in index_html
    for fn in [
        "switchCrudEntity",
        "createTableActionCell",
        "openCourseModal",
        "openStudentModal",
        "openExamModal",
        "openImportModal",
        "openDeleteAlert",
        "closeDeleteAlert",
        "confirmPendingDelete",
        "exportSelectedEntityData",
        "sanitizeCsvCell",
        "closeAllCrudModals",
        "saveStudentForm",
        "renderExamTable",
        "saveExamForm",
        "renderCourseTable",
        "saveCourseForm",
    ]:
        assert fn in crud_js, f"web/js/admin/crud.js thiếu hàm {fn}"
    assert "font-bold text-blue-700 border-b-2 border-blue-700" in crud_js, "switchCrudEntity phải giữ style xanh đậm + gạch dưới cho mục đang chọn"
    assert '" • "' not in crud_js, "Nút Sửa và Xóa phải tách thành 2 button riêng, không nối bằng dấu chấm"
    assert "border-blue-200 bg-blue-50" in crud_js and "border-red-200 bg-red-50" in crud_js
    assert "innerHTML" not in crud_js, "web/js/admin/crud.js không được dùng innerHTML để tránh XSS"

    # Kiểm tra khung giao diện Sinh viên nằm tách biệt tại student.html và không kéo thừa JS/link của Admin
    student_html = (WEB_DIR / "student.html").read_text(encoding="utf-8")
    assert "https://cdn.tailwindcss.com" in student_html
    assert 'href="/css/layout.css"' in student_html
    assert 'src="/js/admin/layout.js"' not in student_html
    assert "index.html#tab-crud" not in student_html, "student.html không được chứa link điều hướng sang trang Admin"
    assert "GraphSchedule" not in student_html, "student.html phải đổi tên thành HTTPS"
    for marker in [
        'id="student-header"',
        'id="student-main-content"',
        'id="student-fullcalendar-shell"',
        "Student Portal",
        'src="/js/core/auth.js"',
        'onclick="handleLogout()"',
    ]:
        assert marker in student_html, f"Thiếu thành phần khung Sinh viên trong student.html: {marker}"
    assert 'href="/login.html"' not in student_html


def test_caddy_serves_all_pages_if_running():
    """Nếu container caddy:2-alpine đang chạy, kiểm tra truy cập 200 OK cho cả 4 trang Admin + Student + CSS/JS."""
    try:
        for filename, (_key, section_id) in ADMIN_PAGES.items():
            path = "/" if filename == "index.html" else f"/{filename}"
            with urllib.request.urlopen(BASE_URL + path, context=SSL_CTX, timeout=3) as resp:
                body = resp.read().decode("utf-8")
                assert resp.status == 200
                assert section_id in body

        with urllib.request.urlopen(BASE_URL + "/student.html", context=SSL_CTX, timeout=3) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert 'id="student-header"' in body

        with urllib.request.urlopen(BASE_URL + "/css/layout.css", context=SSL_CTX, timeout=3) as resp:
            css_body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "@media print" in css_body

        with urllib.request.urlopen(BASE_URL + "/js/core/auth.js", context=SSL_CTX, timeout=3) as resp:
            auth_js = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "navigateByRole" in auth_js
            assert "handleLogout" in auth_js

        with urllib.request.urlopen(BASE_URL + "/js/admin/layout.js", context=SSL_CTX, timeout=3) as resp:
            layout_js = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "initAdminShell" in layout_js
            assert "toggleRightDrawer" in layout_js

        with urllib.request.urlopen(BASE_URL + "/js/admin/crud.js", context=SSL_CTX, timeout=3) as resp:
            crud_js = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "switchCrudEntity" in crud_js

        with urllib.request.urlopen(BASE_URL + "/assets/logo.svg", context=SSL_CTX, timeout=3) as resp:
            logo_svg = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "<svg" in logo_svg
    except urllib.error.HTTPError:
        # Không được nuốt lỗi 404/502 khi Caddy đang chạy
        raise
    except urllib.error.URLError:
        # Chỉ bỏ qua khi không kết nối được (container chưa bật)
        pass


def test_crud_modals_and_delete_alert_runtime():
    """Chạy thực tế web/js/admin/crud.js bằng Node.js để kiểm chứng alert xác nhận xóa và chống Formula Injection."""
    if not shutil.which("node"):
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const makeClassList = (initial = []) => {
  const set = new Set(initial);
  return {
    add: (...cls) => cls.forEach((c) => set.add(c)),
    remove: (...cls) => cls.forEach((c) => set.delete(c)),
    toggle: (c, force) => (force === undefined ? (set.has(c) ? set.delete(c) : set.add(c)) : (force ? set.add(c) : set.delete(c))),
    contains: (c) => set.has(c),
  };
};

const makeEl = (initialClasses = []) => ({
  classList: makeClassList(initialClasses),
  textContent: "",
  value: "",
  readOnly: false,
  focus: () => {},
  reset: () => {},
  replaceChildren: () => {},
  appendChild: () => {},
});

const elements = {
  "delete-confirm-modal": makeEl(["hidden"]),
  "delete-alert-title": makeEl(),
  "delete-alert-message": makeEl(),
  "btn-cancel-delete": makeEl(),
  "course-crud-modal": makeEl(["hidden"]),
  "student-crud-modal": makeEl(["hidden"]),
  "exam-crud-modal": makeEl(["hidden"]),
  "import-data-modal": makeEl(["hidden"]),
};

const sandbox = {
  document: {
    body: { classList: makeClassList() },
    getElementById: (id) => elements[id] || null,
    querySelectorAll: () => [],
    addEventListener: () => {},
  },
  window: { location: { search: "" } },
  URLSearchParams,
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/crud.js", "utf8"), sandbox);

// 1. Click Delete must open alert dialog and NOT delete immediately
const beforeCount = vm.runInContext("courseRecords.length", sandbox);
sandbox.deleteCourse("IT001");
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), false);
assert.ok(elements["delete-alert-message"].textContent.includes("IT001"));
assert.strictEqual(vm.runInContext("courseRecords.length", sandbox), beforeCount);

// 2. Cancelling alert must keep record untouched
sandbox.closeDeleteAlert();
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("courseRecords.length", sandbox), beforeCount);

// 3. Confirming alert must delete the record and close dialog
sandbox.deleteCourse("IT001");
sandbox.confirmPendingDelete();
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("courseRecords.length", sandbox), beforeCount - 1);

// 4. CSV export cell sanitizer blocks Formula Injection (=, +, -, @)
assert.strictEqual(sandbox.sanitizeCsvCell("=SUM(A1:A2)"), `"'=SUM(A1:A2)"`);
assert.strictEqual(sandbox.sanitizeCsvCell("+1+2"), `"'+1+2"`);
assert.strictEqual(sandbox.sanitizeCsvCell("@cmd"), `"'@cmd"`);
assert.strictEqual(sandbox.sanitizeCsvCell("IT002"), `"IT002"`);
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime CRUD test failed:\n{res.stderr or res.stdout}"


def test_no_raw_unicode_emojis_in_web_ui():
    """Đảm bảo giao diện web dùng Lucide SVG icons, không còn emoji Unicode thô trong web/."""
    import re

    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    offenders = []
    for path in sorted(WEB_DIR.rglob("*")):
        if path.is_file() and path.suffix in {".html", ".js"}:
            text = path.read_text(encoding="utf-8")
            found = emoji_re.findall(text)
            if found:
                offenders.append(f"{path.relative_to(ROOT_DIR)}: {''.join(sorted(set(found)))}")
    assert not offenders, f"Còn emoji Unicode thô trong web/ (cần thay bằng Lucide SVG): {offenders}"


if __name__ == "__main__":
    test_layout_files_exist()
    test_admin_pages_and_student_structure()
    test_crud_modals_and_delete_alert_runtime()
    test_no_raw_unicode_emojis_in_web_ui()
    test_caddy_serves_all_pages_if_running()
    print("ALL LAYOUT TESTS PASSED!")
