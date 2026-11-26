"""
Kiểm tra giao diện quản lý Sinh viên (UC03) và Phòng thi (UC06) trong web/index.html
và logic CRUD trong web/js/admin/crud.js.
"""

from pathlib import Path
import re
import shutil
import subprocess

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
    """Kiểm tra đầy đủ phần tử HTML cho màn hình Quản lý Sinh viên (UC03)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    for marker in [
        'id="crud-panel-sinh_vien"',
        'id="student-count-label"',
        'id="student-search-input"',
        'oninput="renderStudentTable()"',
        'id="btn-open-student-modal"',
        'onclick="openStudentModal()"',
        'id="student-table-body"',
        'id="student-crud-modal"',
        'id="student-crud-form"',
        'id="sv-form-mssv"',
        'id="sv-form-hoten"',
        'id="sv-form-email"',
        'id="sv-form-lop"',
        'id="student-form-error"',
        "handleCrudModalBackdropClick(event, 'student-crud-modal')",
        'src="/js/admin/crud.js"',
    ]:
        assert marker in html, f"Thiếu phần tử UI Sinh viên: {marker}"


def test_room_management_ui_elements():
    """Kiểm tra đầy đủ phần tử HTML cho màn hình Quản lý Phòng thi (UC06)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    for marker in [
        'id="crud-panel-phong_thi"',
        'id="room-count-label"',
        'id="room-search-input"',
        'oninput="renderRoomTable()"',
        "openImportModal('phong_thi')",
        'id="btn-open-room-modal"',
        'onclick="openRoomModal()"',
        'id="room-table-body"',
        'id="room-crud-modal"',
        'id="room-crud-form"',
        'id="room-form-ma"',
        'id="room-form-ten"',
        'id="room-form-capacity"',
        'id="room-form-building"',
        'id="room-form-active"',
        'id="room-form-error"',
        "handleCrudModalBackdropClick(event, 'room-crud-modal')",
    ]:
        assert marker in html, f"Thiếu phần tử UI Phòng thi: {marker}"


def test_registration_management_ui_elements():
    """Kiểm tra đầy đủ phần tử HTML cho màn hình Quản lý Đăng ký thi (UC05)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    for marker in [
        'id="crud-panel-dang_ky_thi"',
        'id="registration-count-label"',
        'id="registration-course-filter"',
        'onchange="renderRegistrationTable()"',
        'id="registration-search-input"',
        'oninput="renderRegistrationTable()"',
        "openImportModal('dang_ky_thi')",
        'id="btn-open-registration-modal"',
        'onclick="openRegistrationModal()"',
        'id="registration-table-body"',
        'id="registration-crud-modal"',
        'id="registration-crud-form"',
        'id="reg-form-ky-thi"',
        'id="reg-form-ma-mon"',
        'id="reg-form-mssv"',
        'id="registration-form-error"',
        "handleCrudModalBackdropClick(event, 'registration-crud-modal')",
    ]:
        assert marker in html, f"Thiếu phần tử UI Đăng ký thi (UC05): {marker}"
    assert 'id="registration-course-summary"' not in html, "Đã xóa thanh pill tóm tắt môn học thừa"


def test_crud_js_logic_structure():
    """Kiểm tra cấu trúc logic CRUD Sinh viên & Phòng thi và an toàn XSS trong crud.js."""
    js = CRUD_JS.read_text(encoding="utf-8")

    assert "innerHTML" not in js, "web/js/admin/crud.js không được dùng innerHTML để tránh XSS"

    for token in [
        "function switchCrudEntity",
        "studentRecords",
        "roomRecords",
        "ma_phong",
        "ten_phong",
        "suc_chua",
        "toa_nha",
        "dang_su_dung",
        "function renderStudentTable",
        "function openStudentModal",
        "function closeStudentModal",
        "function saveStudentForm",
        "function startEditStudent",
        "function deleteStudent",
        "function renderRoomTable",
        "function openRoomModal",
        "function closeRoomModal",
        "function saveRoomForm",
        "function startEditRoom",
        "function deleteRoom",
        "registrationRecords",
        "function renderRegistrationTable",
        "function openRegistrationModal",
        "function closeRegistrationModal",
        "function saveRegistrationForm",
        "function startEditRegistration",
        "function deleteRegistration",
        "function openCrudModal",
        "function closeCrudModal",
        "function openDeleteAlert",
        "function confirmPendingDelete",
    ]:
        assert token in js, f"Thiếu thành phần bắt buộc trong crud.js: {token}"


def test_no_removed_ui_artifacts():
    """Kiểm tra các nhãn nội bộ / phần tử đã xóa không còn hiển thị trong UI."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    no_comments = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    for banned in ["UC03", "UC05", "UC06", "UC08", "UC09"]:
        assert banned not in no_comments, (
            f"Nhãn {banned} vẫn còn hiện trong UI (ngoài comment)"
        )

    assert "χ(G) = 4" not in html and "χ(G)=4" not in html
    assert "Trạng thái Engine" not in html


def test_crud_js_node_student_and_room_runtime():
    """
    Chạy Node.js kiểm chứng luồng runtime CRUD cho cả Sinh viên (UC03) & Phòng thi (UC06):
    - Render & tìm kiếm
    - Thêm mới / Chỉnh sửa qua modal nổi & validate sức chứa phòng thi
    - Xóa phải bật alert xác nhận, huỷ không xóa, xác nhận mới xóa
    """
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
    toggle: (c, force) =>
      force === undefined
        ? set.has(c) ? set.delete(c) : set.add(c)
        : force ? set.add(c) : set.delete(c),
    contains: (c) => set.has(c),
  };
};

const makeEl = (tag = "div", initialClasses = []) => {
  const el = {
    tagName: tag.toUpperCase(),
    className: "",
    classList: makeClassList(initialClasses),
    textContent: "",
    value: "",
    type: "",
    readOnly: false,
    children: [],
    focus: () => {},
    reset: () => {},
    replaceChildren: (...nodes) => { el.children = nodes; },
    appendChild: (node) => { el.children.push(node); return node; },
    append: (...nodes) => { el.children.push(...nodes); },
  };
  return el;
};

const elements = {
  "delete-confirm-modal":  makeEl("div", ["hidden"]),
  "delete-alert-title":    makeEl("h3"),
  "delete-alert-message":  makeEl("p"),
  "btn-cancel-delete":     makeEl("button"),
  "student-crud-modal":    makeEl("div", ["hidden"]),
  "student-crud-form":     makeEl("form"),
  "student-modal-title":   makeEl("h3"),
  "student-modal-submit":  makeEl("button"),
  "student-table-body":    makeEl("tbody"),
  "student-count-label":   makeEl("h3"),
  "student-search-input":  makeEl("input"),
  "sv-form-mssv":          makeEl("input"),
  "sv-form-hoten":         makeEl("input"),
  "sv-form-email":         makeEl("input"),
  "sv-form-lop":           makeEl("input"),
  "student-form-error":    makeEl("p"),
  "room-crud-modal":       makeEl("div", ["hidden"]),
  "room-crud-form":        makeEl("form"),
  "room-modal-title":      makeEl("h3"),
  "room-modal-submit":     makeEl("button"),
  "room-table-body":       makeEl("tbody"),
  "room-count-label":      makeEl("h3"),
  "room-search-input":     makeEl("input"),
  "room-form-ma":          makeEl("input"),
  "room-form-ten":         makeEl("input"),
  "room-form-capacity":    makeEl("input"),
  "room-form-building":    makeEl("input"),
  "room-form-active":      makeEl("select"),
  "room-form-error":       makeEl("p"),
  "course-crud-modal":     makeEl("div", ["hidden"]),
  "exam-crud-modal":       makeEl("div", ["hidden"]),
  "import-data-modal":     makeEl("div", ["hidden"]),
  "registration-crud-modal": makeEl("div", ["hidden"]),
  "registration-crud-form":  makeEl("form"),
  "registration-modal-title": makeEl("h3"),
  "registration-modal-submit": makeEl("button"),
  "registration-table-body": makeEl("tbody"),
  "registration-count-label": makeEl("h3"),
  "registration-course-filter": makeEl("select"),
  "registration-search-input": makeEl("input"),
  "reg-form-ky-thi":       makeEl("select"),
  "reg-form-ma-mon":       makeEl("select"),
  "reg-form-mssv":         makeEl("select"),
  "registration-form-error": makeEl("p"),
};

const sandbox = {
  document: {
    body: { classList: makeClassList() },
    getElementById: (id) => elements[id] || null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    createElement: (tag) => makeEl(tag),
    createTextNode: (text) => ({ nodeType: 3, textContent: String(text) }),
  },
  window: { location: { search: "" } },
  URLSearchParams,
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/crud.js", "utf8"), sandbox);

// --- 1. SINH VIÊN (UC03): Thêm, Sửa, Tìm kiếm, Xóa có Alert ---
const svBefore = vm.runInContext("studentRecords.length", sandbox);
assert.ok(svBefore > 0, "Phải có dữ liệu sinh viên mock");

sandbox.openStudentModal();
assert.strictEqual(elements["student-crud-modal"].classList.contains("hidden"), false);
elements["sv-form-mssv"].value = "22119999";
elements["sv-form-hoten"].value = "Nguyễn Kiểm Thử";
elements["sv-form-email"].value = "test@univ.edu.vn";
elements["sv-form-lop"].value = "22CNTT9";
sandbox.saveStudentForm({ preventDefault: () => {} });
assert.strictEqual(elements["student-crud-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), svBefore + 1);
assert.strictEqual(elements["student-table-body"].children.length, svBefore + 1);

// Xóa sinh viên -> phải bật alert, huỷ giữ nguyên, xác nhận mới xóa
sandbox.deleteStudent("22119999");
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), false);
assert.ok(elements["delete-alert-message"].textContent.includes("22119999"));
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), svBefore + 1);
sandbox.closeDeleteAlert();
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), svBefore + 1);
sandbox.deleteStudent("22119999");
sandbox.confirmPendingDelete();
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), svBefore);

// --- 2. PHÒNG THI (UC06): Render, Validate, Thêm, Sửa, Tìm kiếm, Xóa có Alert ---
const roomBefore = vm.runInContext("roomRecords.length", sandbox);
assert.ok(roomBefore >= 3, "Phải có dữ liệu phòng thi mock");
sandbox.renderRoomTable();
assert.strictEqual(elements["room-table-body"].children.length, roomBefore);

// Validate sức chứa <= 0 phải bị chặn và giữ modal mở
sandbox.openRoomModal();
assert.strictEqual(elements["room-crud-modal"].classList.contains("hidden"), false);
elements["room-form-ma"].value = "D401";
elements["room-form-ten"].value = "Phòng thi D401";
elements["room-form-capacity"].value = "0";
elements["room-form-building"].value = "Nhà D";
elements["room-form-active"].value = "true";
sandbox.saveRoomForm({ preventDefault: () => {} });
assert.strictEqual(elements["room-crud-modal"].classList.contains("hidden"), false);
assert.ok(elements["room-form-error"].textContent.length > 0);
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), roomBefore);

// Thêm phòng hợp lệ -> lưu & đóng modal
elements["room-form-capacity"].value = "80";
sandbox.saveRoomForm({ preventDefault: () => {} });
assert.strictEqual(elements["room-crud-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), roomBefore + 1);

// Sửa phòng -> khóa mã phòng, cập nhật sức chứa & trạng thái
sandbox.startEditRoom("D401");
assert.strictEqual(elements["room-crud-modal"].classList.contains("hidden"), false);
assert.strictEqual(elements["room-form-ma"].readOnly, true);
elements["room-form-capacity"].value = "90";
elements["room-form-active"].value = "false";
sandbox.saveRoomForm({ preventDefault: () => {} });
const updatedRoom = vm.runInContext('roomRecords.find((r) => r.ma_phong === "D401")', sandbox);
assert.strictEqual(updatedRoom.suc_chua, 90);
assert.strictEqual(updatedRoom.dang_su_dung, false);

// Tìm kiếm phòng thi theo tòa nhà
elements["room-search-input"].value = "Nhà D";
sandbox.renderRoomTable();
assert.strictEqual(elements["room-table-body"].children.length, 1);
elements["room-search-input"].value = "";

// Xóa phòng thi -> alert xác nhận
sandbox.deleteRoom("D401");
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), false);
assert.ok(elements["delete-alert-message"].textContent.includes("D401"));
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), roomBefore + 1);
sandbox.closeDeleteAlert();
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), roomBefore + 1);
sandbox.deleteRoom("D401");
sandbox.confirmPendingDelete();
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), roomBefore);

// --- 3. ĐĂNG KÝ THI (UC05): Lọc theo môn học, Thêm, Chống trùng lặp, Sửa, Xóa ---
const regBefore = vm.runInContext("registrationRecords.length", sandbox);
assert.ok(regBefore >= 5, "Phải có dữ liệu đăng ký thi mẫu");
sandbox.renderRegistrationTable();
assert.strictEqual(elements["registration-table-body"].children.length, regBefore);

// Lọc danh sách sinh viên đăng ký theo từng môn học (VD: IT001)
elements["registration-course-filter"].value = "IT001";
sandbox.renderRegistrationTable();
const it001Count = vm.runInContext('registrationRecords.filter((r) => r.ma_mon === "IT001").length', sandbox);
assert.strictEqual(elements["registration-table-body"].children.length, it001Count);
assert.ok(!elements["registration-count-label"].textContent.includes("IT001"));
const it001Option = elements["registration-course-filter"].children.find((o) => o.value === "IT001");
assert.strictEqual(it001Option.textContent, "IT001 - Lý thuyết Đồ thị");

// Chuyển lại tất cả môn học
elements["registration-course-filter"].value = "ALL";
sandbox.renderRegistrationTable();
assert.strictEqual(elements["registration-table-body"].children.length, regBefore);

// Kiểm tra chặn đăng ký trùng (ma_ky_thi, ma_mon, mssv)
sandbox.openRegistrationModal();
assert.strictEqual(elements["registration-crud-modal"].classList.contains("hidden"), false);
elements["reg-form-ky-thi"].value = "KTHK1_2026";
elements["reg-form-ma-mon"].value = "IT001";
elements["reg-form-mssv"].value = "22110399";
sandbox.saveRegistrationForm({ preventDefault: () => {} });
assert.strictEqual(elements["registration-crud-modal"].classList.contains("hidden"), false);
assert.ok(elements["registration-form-error"].textContent.includes("đã đăng ký"));
assert.strictEqual(vm.runInContext("registrationRecords.length", sandbox), regBefore);

// Thêm đăng ký mới hợp lệ
elements["reg-form-ma-mon"].value = "IT006";
elements["reg-form-mssv"].value = "22110399";
sandbox.saveRegistrationForm({ preventDefault: () => {} });
assert.strictEqual(elements["registration-crud-modal"].classList.contains("hidden"), true);
assert.strictEqual(vm.runInContext("registrationRecords.length", sandbox), regBefore + 1);

// Sửa bản ghi đăng ký mới thêm
const newRegId = vm.runInContext('registrationRecords.find((r) => r.ma_mon === "IT006" && r.mssv === "22110399").id', sandbox);
sandbox.startEditRegistration(newRegId);
assert.strictEqual(elements["registration-crud-modal"].classList.contains("hidden"), false);
elements["reg-form-ma-mon"].value = "IT007";
sandbox.saveRegistrationForm({ preventDefault: () => {} });
assert.strictEqual(elements["registration-crud-modal"].classList.contains("hidden"), true);
const editedReg = vm.runInContext(`registrationRecords.find((r) => r.id === ${newRegId})`, sandbox);
assert.strictEqual(editedReg.ma_mon, "IT007");

// Xóa đăng ký -> bật alert xác nhận
sandbox.deleteRegistration(newRegId);
assert.strictEqual(elements["delete-confirm-modal"].classList.contains("hidden"), false);
sandbox.closeDeleteAlert();
assert.strictEqual(vm.runInContext("registrationRecords.length", sandbox), regBefore + 1);
sandbox.deleteRegistration(newRegId);
sandbox.confirmPendingDelete();
assert.strictEqual(vm.runInContext("registrationRecords.length", sandbox), regBefore);

// Kiểm tra trạng thái rỗng khi tìm kiếm ra 0 kết quả
elements["registration-search-input"].value = "KHONG_TON_TAI_99999";
sandbox.renderRegistrationTable();
assert.strictEqual(elements["registration-table-body"].children.length, 1);
const emptyTd = elements["registration-table-body"].children[0].children[0];
assert.strictEqual(emptyTd.colSpan, 7);
assert.ok(emptyTd.textContent.includes("Không có lượt đăng ký"));
elements["registration-search-input"].value = "";
sandbox.renderRegistrationTable();

// Kiểm tra closeAllCrudModals (phím Escape) reset editingRegistrationId
sandbox.startEditRegistration(1);
assert.strictEqual(vm.runInContext("editingRegistrationId", sandbox), 1);
sandbox.closeAllCrudModals();
assert.strictEqual(vm.runInContext("editingRegistrationId", sandbox), null);

// Kiểm tra startEditRegistration giữ option dự phòng nếu môn học đã bị xóa khỏi danh mục
vm.runInContext('courseRecords = courseRecords.filter((c) => c.ma_mon !== "IT005")', sandbox);
const orphanRegId = vm.runInContext('registrationRecords.find((r) => r.ma_mon === "IT005").id', sandbox);
sandbox.startEditRegistration(orphanRegId);
assert.strictEqual(elements["reg-form-ma-mon"].value, "IT005");
assert.ok(elements["reg-form-ma-mon"].children.some((o) => o.value === "IT005" && o.textContent.includes("đã xóa")));
sandbox.closeRegistrationModal();
"""

    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"Node.js student & room CRUD test thất bại:\n{res.stderr or res.stdout}"
    )


if __name__ == "__main__":
    test_tv5_files_exist()
    test_student_management_ui_elements()
    test_room_management_ui_elements()
    test_registration_management_ui_elements()
    test_crud_js_logic_structure()
    test_no_removed_ui_artifacts()
    test_crud_js_node_student_and_room_runtime()
    print("ALL STUDENT, ROOM & REGISTRATION UI TESTS PASSED!")
