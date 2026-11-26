"""
Kiểm tra giao diện modal nạp file CSV/Excel (UC07) trong web/index.html
và logic parse/validate/rollback/chống Formula Injection trong web/js/admin/crud.js.
"""

from pathlib import Path
import re
import shutil
import subprocess

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
INDEX_HTML = WEB_DIR / "index.html"
CRUD_JS = WEB_DIR / "js" / "admin" / "crud.js"


def test_import_modal_html_elements():
    """Kiểm tra đầy đủ phần tử HTML cho modal Import CSV/Excel (UC07)."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    for marker in [
        'id="import-data-modal"',
        'id="import-data-form"',
        'id="import-entity-select"',
        'id="import-entity-display"',
        'type="hidden"',
        'id="btn-download-import-template"',
        'onclick="downloadImportTemplate()"',
        'id="import-template-guide"',
        'id="import-required-cols"',
        'id="import-dropzone"',
        'id="import-file-input"',
        'accept=".xlsx,.csv"',
        'id="import-selected-file"',
        'id="import-preview-box"',
        'id="import-preview-summary"',
        'id="import-preview-list"',
        'id="import-form-error"',
        'id="import-form-status"',
        'id="btn-export-excel"',
        'id="import-modal-submit"',
        "openImportModal('sinh_vien')",
        "openImportModal('mon_hoc')",
        "openImportModal('phong_thi')",
    ]:
        assert marker in html, f"Thiếu phần tử modal Import (UC07): {marker}"

    no_comments = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    assert "UC07" not in no_comments, "Không để mã UC07 hiển thị trực tiếp ngoài comment HTML"


def test_import_js_xss_and_symbols():
    """Kiểm tra crud.js không dùng innerHTML và có đủ hàm xử lý UC07."""
    js = CRUD_JS.read_text(encoding="utf-8")
    assert "innerHTML" not in js, "web/js/admin/crud.js không được dùng innerHTML"

    for symbol in [
        "IMPORT_SCHEMAS",
        "function neutralizeFormulaCell",
        "function parseCsvText",
        "function validateImportCsvText",
        "function renderImportPreview",
        "function updateImportEntityGuide",
        "function handleImportEntityChange",
        "function downloadImportTemplate",
        "function applyImportedRecords",
        "function openImportModal",
        "function selectImportFile",
        "function submitImportForm",
    ]:
        assert symbol in js, f"Thiếu hàm/hằng số UC07 trong crud.js: {symbol}"


def test_import_modal_runtime_behavior():
    """Kiểm thử runtime Node.js cho luồng chọn file, validate CSV, rollback lỗi, Formula Injection và nạp bảng."""
    if shutil.which("node") is None:
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

const makeEl = (tag = "div", classes = []) => {
  const el = {
    tagName: tag.toUpperCase(),
    className: "",
    classList: makeClassList(classes),
    textContent: "",
    value: "",
    href: "",
    download: "",
    children: [],
    selectedOptions: [],
    readOnly: false,
    focus: () => {},
    reset: () => {},
    click: () => {},
    remove: () => {},
    append: (...nodes) => el.children.push(...nodes),
    appendChild: (node) => el.children.push(node),
    replaceChildren: (...nodes) => { el.children = [...nodes]; },
    setAttribute: () => {},
    addEventListener: () => {},
  };
  return el;
};

const elements = {
  "import-data-modal": makeEl("div", ["hidden"]),
  "import-data-form": makeEl("form"),
  "import-entity-select": makeEl("select"),
  "import-required-cols": makeEl("p"),
  "import-file-input": makeEl("input"),
  "import-selected-file": makeEl("p", ["hidden"]),
  "import-preview-box": makeEl("div", ["hidden"]),
  "import-preview-summary": makeEl("p"),
  "import-preview-list": makeEl("ul"),
  "import-form-error": makeEl("p"),
  "import-form-status": makeEl("p", ["hidden"]),
  "student-table-body": makeEl("tbody"),
  "student-count-label": makeEl("h3"),
  "course-table-body": makeEl("tbody"),
  "course-count-label": makeEl("h3"),
  "room-table-body": makeEl("tbody"),
  "room-count-label": makeEl("h3"),
};

let lastDownloaded = null;
const sandbox = {
  document: {
    body: {
      classList: makeClassList(),
      appendChild: (node) => { lastDownloaded = node; },
    },
    getElementById: (id) => elements[id] || null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    createElement: (tag) => makeEl(tag),
  },
  window: { location: { search: "" } },
  URLSearchParams,
  Blob: class MockBlob {
    constructor(parts, opts) {
      this.parts = parts;
      this.opts = opts;
    }
  },
  URL: {
    createObjectURL: () => "blob:mock-url",
    revokeObjectURL: () => {},
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/crud.js", "utf8"), sandbox);

// 1. Open modal for sinh_vien updates schema guide
sandbox.openImportModal("sinh_vien");
assert.strictEqual(elements["import-data-modal"].classList.contains("hidden"), false);
assert.strictEqual(elements["import-entity-select"].value, "sinh_vien");
assert.ok(elements["import-required-cols"].textContent.includes("mssv*"));
assert.ok(elements["import-required-cols"].textContent.includes("ho_ten*"));

// 2. Reject invalid file extension & >5MB file
sandbox.selectImportFile({ name: "students.pdf", size: 1024 });
assert.ok(elements["import-form-error"].textContent.includes(".xlsx hoặc .csv"));

sandbox.selectImportFile({ name: "big.csv", size: 6 * 1024 * 1024 });
assert.ok(elements["import-form-error"].textContent.includes("5MB"));

// 3. Submit without file shows error
sandbox.submitImportForm({ preventDefault: () => {} });
assert.ok(elements["import-form-error"].textContent.includes("Vui lòng chọn tệp"));

// 4. Download CSV template
sandbox.downloadImportTemplate();
assert.ok(lastDownloaded && lastDownloaded.download === "sinh_vien_template.csv");
assert.ok(elements["import-form-status"].textContent.includes("sinh_vien_template.csv"));

// 5. All-or-nothing rollback when CSV has an invalid row (bad email)
const initialStudents = vm.runInContext("studentRecords.length", sandbox);
const badStudentCsv = "mssv,ho_ten,email,lop_sinh_hoat\n22119001,Sinh Viên Tốt,tot@univ.edu.vn,22CNTT1\n22119002,Sinh Viên Lỗi,not-an-email,22CNTT1";
sandbox.selectImportFile({ name: "sv_bad.csv", size: 512, text: () => badStudentCsv });
sandbox.submitImportForm({ preventDefault: () => {} });
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), initialStudents);
assert.ok(elements["import-form-error"].textContent.includes("rollback"));
assert.ok(elements["import-preview-list"].children.some((li) => li.textContent.includes("Dòng 3")));

// 6. Valid student CSV import (including Formula Injection neutralization) updates studentRecords
const goodStudentCsv = "\uFEFFmssv,ho_ten,email,lop_sinh_hoat\n22119001,=CMD(),khoi@univ.edu.vn,22CNTT1\n22110001,Nguyễn Văn An Cập Nhật,an.nv@univ.edu.vn,22CNTT1";
sandbox.selectImportFile({ name: "sv_good.csv", size: 512, text: () => goodStudentCsv });
sandbox.submitImportForm({ preventDefault: () => {} });
assert.strictEqual(vm.runInContext("studentRecords.length", sandbox), initialStudents + 1);
const importedSv = vm.runInContext("studentRecords.find(s => s.mssv === '22119001')", sandbox);
assert.strictEqual(importedSv.ho_ten, "'=CMD()");
assert.ok(elements["import-form-status"].textContent.includes("thêm mới: 1, cập nhật: 1"));

// 7. Import mon_hoc & phong_thi CSVs
sandbox.openImportModal("mon_hoc");
assert.ok(elements["import-required-cols"].textContent.includes("ma_mon*"));
const initialCourses = vm.runInContext("courseRecords.length", sandbox);
const courseCsv = "ma_mon,ten_mon,thoi_luong_phut,so_tin_chi\nIT9999,\"Toán ứng dụng, Phần 1\",120,4";
sandbox.selectImportFile({ name: "mon_hoc.csv", size: 256, text: () => courseCsv });
sandbox.submitImportForm({ preventDefault: () => {} });
assert.strictEqual(vm.runInContext("courseRecords.length", sandbox), initialCourses + 1);
const importedCourse = vm.runInContext("courseRecords.find(c => c.ma_mon === 'IT9999')", sandbox);
assert.strictEqual(importedCourse.ten_mon, "Toán ứng dụng, Phần 1");
assert.strictEqual(importedCourse.thoi_luong_phut, 120);

sandbox.openImportModal("phong_thi");
assert.ok(elements["import-required-cols"].textContent.includes("suc_chua*"));
const initialRooms = vm.runInContext("roomRecords.length", sandbox);
const roomCsv = "ma_phong,ten_phong,suc_chua,toa_nha,dang_su_dung\nD401,Phòng D401,80,Nhà D,true";
sandbox.selectImportFile({ name: "phong_thi.csv", size: 256, text: () => roomCsv });
sandbox.submitImportForm({ preventDefault: () => {} });
assert.strictEqual(vm.runInContext("roomRecords.length", sandbox), initialRooms + 1);

// 8. .xlsx file readiness message
sandbox.selectImportFile({ name: "phong_thi.xlsx", size: 2048 });
sandbox.submitImportForm({ preventDefault: () => {} });
assert.ok(elements["import-form-status"].textContent.includes("API Import Transaction ACID"));

// 9. Hardening: reject impossible calendar date (2026-02-31), ignore __proto__ header, uppercase codes, reset on Escape
const badDateExam = sandbox.validateImportCsvText(
  "ky_thi",
  "ma_ky_thi,ten_ky_thi,ngay_bat_dau,ngay_ket_thuc\nKT_BAD,Test,2026-02-31,2026-03-05"
);
assert.strictEqual(badDateExam.ok, false);

const protoCsv = sandbox.validateImportCsvText(
  "mon_hoc",
  "__proto__,ma_mon,ten_mon\npolluted,it001,Lý thuyết Đồ thị Updated"
);
assert.strictEqual(protoCsv.ok, true);
assert.strictEqual(protoCsv.records[0].ma_mon, "IT001");
assert.strictEqual(({}).polluted, undefined);

sandbox.closeAllCrudModals();
assert.strictEqual(vm.runInContext("selectedImportFile", sandbox), null);
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime import UI test failed:\n{res.stderr or res.stdout}"


if __name__ == "__main__":
    test_import_modal_html_elements()
    test_import_js_xss_and_symbols()
    test_import_modal_runtime_behavior()
    print("ALL IMPORT UI TESTS PASSED!")
