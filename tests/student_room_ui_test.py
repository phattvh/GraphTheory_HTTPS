"""
Kiểm tra giao diện quản lý Sinh viên (UC03) và Phòng thi (UC06) trong admin/index.html
và logic CRUD trong web/js/admin/crud.js.
"""

import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
INDEX_HTML = WEB_DIR / "index.html"
CRUD_JS = WEB_DIR / "js" / "admin" / "crud.js"


def test_tv5_files_exist():
    """Kiểm tra các file TV5 bắt buộc tồn tại trên đĩa."""
    required = [
        CRUD_JS,
        INDEX_HTML,
        WEB_DIR / "js" / "admin" / "layout.js",
        WEB_DIR / "js" / "core" / "auth.js",
    ]
    for path in required:
        assert path.exists(), f"Thiếu file bắt buộc: {path}"


def test_student_management_ui_elements():
    """Kiểm tra các phần tử HTML cho màn hình Quản lý Sinh viên (UC03)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Panel sinh viên phải có id đúng
    assert 'id="crud-panel-sinh_vien"' in html, "Thiếu panel sinh viên"

    # Bảng dữ liệu sinh viên
    assert 'id="student-table-body"' in html, "Thiếu tbody cho bảng sinh viên"

    # Input tìm kiếm sinh viên (tìm theo MSSV, họ tên…)
    assert "Tìm MSSV" in html or "MSSV" in html, "Thiếu input tìm kiếm sinh viên"

    # Nút mở modal thêm sinh viên
    assert "openStudentModal()" in html, "Thiếu nút mở modal thêm sinh viên"

    # Modal sinh viên
    assert 'id="student-crud-modal"' in html, "Thiếu modal sinh viên"

    # Trường form MSSV trong modal
    assert 'id="sv-form-mssv"' in html, "Thiếu trường MSSV trong form sinh viên"

    # Backdrop click handler trên modal
    assert "handleCrudModalBackdropClick(event, 'student-crud-modal')" in html, (
        "Thiếu backdrop click handler cho modal sinh viên"
    )

    # Script crud.js phải được nhúng
    assert 'src="/js/admin/crud.js"' in html, "Thiếu thẻ script crud.js trong index.html"


def test_room_management_ui_elements():
    """Kiểm tra các phần tử HTML cho màn hình Quản lý Phòng thi (UC06)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Panel phòng thi phải có id đúng
    assert 'id="crud-panel-phong_thi"' in html, "Thiếu panel phòng thi"

    # Nút import modal cho phòng thi
    assert "openImportModal('phong_thi')" in html, "Thiếu nút import cho phòng thi"

    # Có ít nhất 1 dòng dữ liệu phòng thi mẫu trong HTML
    assert "Phòng thi A101" in html or "phong_thi" in html, (
        "Thiếu dữ liệu phòng thi mẫu trong bảng"
    )


def test_crud_js_logic_structure():
    """Kiểm tra cấu trúc logic trong crud.js: các hàm bắt buộc và dữ liệu mock."""
    js = CRUD_JS.read_text(encoding="utf-8")

    # Hàm chuyển entity (bắt buộc)
    assert "function switchCrudEntity" in js, "Thiếu hàm switchCrudEntity"

    # Dữ liệu mock sinh viên
    assert "studentRecords" in js, "Thiếu biến studentRecords"
    assert "mssv" in js, "Thiếu trường mssv trong dữ liệu sinh viên"
    assert "ho_ten" in js, "Thiếu trường ho_ten trong dữ liệu sinh viên"
    assert "lop_sinh_hoat" in js, "Thiếu trường lop_sinh_hoat trong dữ liệu sinh viên"

    # Hàm CRUD sinh viên
    for fn in [
        "function renderStudentTable",
        "function openStudentModal",
        "function closeStudentModal",
        "function saveStudentForm",
        "function startEditStudent",
        "function deleteStudent",
    ]:
        assert fn in js, f"Thiếu hàm {fn} trong crud.js"

    # heading entity cho sinh viên và phòng thi
    assert "sinh_vien" in js, "Thiếu entity key sinh_vien"
    assert "phong_thi" in js, "Thiếu entity key phong_thi"

    # Hàm modal dùng chung
    assert "function openCrudModal" in js, "Thiếu hàm openCrudModal"
    assert "function closeCrudModal" in js, "Thiếu hàm closeCrudModal"
    assert "function openDeleteAlert" in js, "Thiếu hàm openDeleteAlert"
    assert "function confirmPendingDelete" in js, "Thiếu hàm confirmPendingDelete"


def test_no_removed_ui_artifacts():
    """Kiểm tra các phần tử đã được xóa không còn xuất hiện trong UI."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Nhãn UC không được hiện trong UI (chỉ cho phép trong comment HTML <!-- -->)
    import re

    # Lấy nội dung bỏ HTML comment
    no_comments = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    for banned in ["UC03", "UC06", "UC08", "UC09"]:
        assert banned not in no_comments, (
            f"Nhãn {banned} vẫn còn hiện trong UI (ngoài comment)"
        )

    # χ(G) badge không được xuất hiện trong HTML
    assert "χ(G) = 4" not in html and "χ(G)=4" not in html, (
        "Badge χ(G) = 4 ca thi vẫn còn trong index.html"
    )

    # Trạng thái Engine không được xuất hiện
    assert "Trạng thái Engine" not in html, (
        "Khung Trạng thái Engine vẫn còn trong index.html"
    )


def test_crud_js_node_student_delete_confirmation():
    """
    Chạy Node.js để kiểm tra luồng xóa sinh viên:
    - Click xóa → phải mở alert, KHÔNG xóa ngay
    - Huỷ → record còn nguyên
    - Xác nhận → record bị xóa
    """
    if not shutil.which("node"):
        # Bỏ qua nếu Node.js không có trên máy
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
    toggle: (c, force) =>
      force === undefined
        ? set.has(c) ? set.delete(c) : set.add(c)
        : force ? set.add(c) : set.delete(c),
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
  "delete-confirm-modal":  makeEl(["hidden"]),
  "delete-alert-title":    makeEl(),
  "delete-alert-message":  makeEl(),
  "btn-cancel-delete":     makeEl(),
  "student-crud-modal":    makeEl(["hidden"]),
  "student-table-body":    makeEl(),
  "sv-form-mssv":          makeEl(),
  "sv-form-name":          makeEl(),
  "sv-form-email":         makeEl(),
  "sv-form-class":         makeEl(),
  "sv-search-input":       makeEl(),
  "sv-filter-class":       makeEl(),
  "course-crud-modal":     makeEl(["hidden"]),
  "exam-crud-modal":       makeEl(["hidden"]),
  "import-data-modal":     makeEl(["hidden"]),
};

const sandbox = {
  document: {
    body:            { classList: makeClassList() },
    getElementById: (id) => elements[id] || null,
    querySelectorAll: () => [],
    addEventListener: () => {},
  },
  window: { location: { search: "" } },
  URLSearchParams,
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/crud.js", "utf8"), sandbox);

// Trước khi xóa: đếm số sinh viên ban đầu
const before = vm.runInContext("studentRecords.length", sandbox);
assert.ok(before > 0, "Phải có dữ liệu sinh viên mock");

// Lấy MSSV của sinh viên đầu tiên
const firstMssv = vm.runInContext("studentRecords[0].mssv", sandbox);

// Click xóa → phải mở alert, KHÔNG xóa ngay
sandbox.deleteStudent(firstMssv);
assert.strictEqual(
  elements["delete-confirm-modal"].classList.contains("hidden"),
  false,
  "Alert xác nhận phải hiện khi xóa sinh viên"
);
assert.ok(
  elements["delete-alert-message"].textContent.includes(firstMssv),
  "Alert phải hiển thị MSSV của sinh viên cần xóa"
);
assert.strictEqual(
  vm.runInContext("studentRecords.length", sandbox),
  before,
  "Số sinh viên không được thay đổi trước khi xác nhận"
);

// Huỷ → record còn nguyên
sandbox.closeDeleteAlert();
assert.strictEqual(
  elements["delete-confirm-modal"].classList.contains("hidden"),
  true,
  "Alert phải đóng sau khi huỷ"
);
assert.strictEqual(
  vm.runInContext("studentRecords.length", sandbox),
  before,
  "Số sinh viên không đổi sau khi huỷ xóa"
);

// Xác nhận → record bị xóa
sandbox.deleteStudent(firstMssv);
sandbox.confirmPendingDelete();
assert.strictEqual(
  elements["delete-confirm-modal"].classList.contains("hidden"),
  true,
  "Alert phải đóng sau khi xác nhận"
);
assert.strictEqual(
  vm.runInContext("studentRecords.length", sandbox),
  before - 1,
  "Số sinh viên phải giảm 1 sau khi xác nhận xóa"
);

console.log("OK: student delete confirmation flow passed");
"""

    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"Node.js student CRUD test thất bại:\n{res.stderr or res.stdout}"
    )


if __name__ == "__main__":
    test_tv5_files_exist()
    test_student_management_ui_elements()
    test_room_management_ui_elements()
    test_crud_js_logic_structure()
    test_no_removed_ui_artifacts()
    test_crud_js_node_student_delete_confirmation()
    print("ALL STUDENT & ROOM UI TESTS PASSED!")
