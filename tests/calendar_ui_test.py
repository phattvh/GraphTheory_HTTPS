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


def test_calendar_files_exist():
    """Kiểm tra sự tồn tại của web/calendar.html và web/js/admin/calendar.js (TV4 Ngày 4 — UC10 UI)."""
    for file_path in [
        WEB_DIR / "calendar.html",
        WEB_DIR / "js" / "admin" / "calendar.js",
    ]:
        assert file_path.exists(), f"Thiếu file giao diện Lịch thi bắt buộc: {file_path}"


def test_calendar_html_fullcalendar_cdn_and_views():
    """Kiểm tra nhúng thư viện FullCalendar qua CDN và các nút cấu hình xem Tháng/Tuần."""
    html = (WEB_DIR / "calendar.html").read_text(encoding="utf-8")
    js = (WEB_DIR / "js" / "admin" / "calendar.js").read_text(encoding="utf-8")

    for required_marker in [
        "https://cdn.tailwindcss.com",
        "fullcalendar@6.1.15/index.global.min.js",
        'data-admin-page="calendar"',
        'id="tab-calendar"',
        'id="admin-fullcalendar-shell"',
        'id="admin-fullcalendar"',
        'id="calendar-filter-course"',
        'id="calendar-filter-room"',
        'id="calendar-filter-shift"',
        'id="btn-view-week"',
        'data-calendar-view="timeGridWeek"',
        'id="btn-view-month"',
        'data-calendar-view="dayGridMonth"',
        'src="/js/admin/calendar.js"',
    ]:
        assert required_marker in html, f"web/calendar.html thiếu thành phần bắt buộc: {required_marker}"

    for js_marker in [
        "function initExamFullCalendar",
        "function getCalendarViewConfig",
        "function switchCalendarView",
        "function filterCalendarEvents",
        "function resetCalendarFilters",
        "timeGridWeek",
        "dayGridMonth",
        "window.FullCalendar",
    ]:
        assert js_marker in js, f"web/js/admin/calendar.js thiếu hàm/cấu hình: {js_marker}"

    assert "innerHTML" not in js, "web/js/admin/calendar.js không được dùng innerHTML để tránh XSS"


def test_calendar_js_runtime_view_switch_and_filters():
    """Chạy kiểm thử runtime bằng Node.js cho logic cấu hình Tháng/Tuần và lọc sự kiện của calendar.js."""
    if not shutil.which("node"):
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const elements = {
  "btn-view-week": { className: "", setAttribute: function(k, v) { this[k] = v; } },
  "btn-view-month": { className: "", setAttribute: function(k, v) { this[k] = v; } },
  "calendar-view-badge": { textContent: "" },
  "calendar-current-range": { textContent: "" },
  "calendar-filter-course": { value: "ALL" },
  "calendar-filter-room": { value: "ALL" },
  "calendar-filter-shift": { value: "ALL" },
  "calendar-active-filter-summary": { textContent: "" },
  "calendar-inspector-title": { textContent: "" },
  "calendar-inspector-meta": { textContent: "" },
  "calendar-inspector-badge": { className: "", textContent: "" },
  "admin-fullcalendar": {},
};

let renderedView = null;
let currentEvents = [];

class FakeFullCalendar {
  constructor(el, config) {
    this.el = el;
    this.config = config;
    renderedView = config.initialView;
    currentEvents = [...(config.events || [])];
    this.view = { title: "15 – 20 Thg 12, 2026" };
  }
  render() {}
  changeView(viewName) {
    renderedView = viewName;
    this.view.title = viewName === "dayGridMonth" ? "Tháng 12 Năm 2026" : "15 – 20 Thg 12, 2026";
  }
  removeAllEvents() {
    currentEvents = [];
  }
  addEvent(ev) {
    currentEvents.push(ev);
  }
}

const sandbox = {
  document: {
    getElementById: (id) => elements[id] || null,
    addEventListener: () => {},
  },
  window: {
    FullCalendar: { Calendar: FakeFullCalendar },
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/calendar.js", "utf8"), sandbox);

// 1. Khởi tạo mặc định ở chế độ xem Tuần (timeGridWeek)
const cal = sandbox.initExamFullCalendar();
assert.ok(cal);
assert.strictEqual(renderedView, "timeGridWeek");
assert.strictEqual(elements["btn-view-week"]["aria-pressed"], "true");
assert.strictEqual(elements["btn-view-month"]["aria-pressed"], "false");
assert.strictEqual(currentEvents.length, 15);

// 2. Chuyển sang chế độ xem Tháng (dayGridMonth) và ngược lại
assert.strictEqual(sandbox.switchCalendarView("dayGridMonth"), "dayGridMonth");
assert.strictEqual(renderedView, "dayGridMonth");
assert.strictEqual(elements["btn-view-month"]["aria-pressed"], "true");
assert.strictEqual(elements["btn-view-week"]["aria-pressed"], "false");

assert.strictEqual(sandbox.switchCalendarView("timeGridWeek"), "timeGridWeek");
assert.strictEqual(renderedView, "timeGridWeek");

// 3. Kiểm tra bộ lọc Ca thi & Phòng thi
elements["calendar-filter-shift"].value = "1";
const shift1Events = sandbox.filterCalendarEvents();
assert.ok(shift1Events.length > 0 && shift1Events.length < 15);
assert.strictEqual(currentEvents.length, shift1Events.length);

// 4. Đặt lại bộ lọc trả về đủ 15 môn
const allEvents = sandbox.resetCalendarFilters();
assert.strictEqual(allEvents.length, 15);
assert.strictEqual(currentEvents.length, 15);
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime calendar test failed:\n{res.stderr or res.stdout}"


def test_caddy_serves_calendar_assets():
    """Nếu container Caddy đang chạy, kiểm tra HTTP 200 OK cho /calendar.html và /js/admin/calendar.js."""
    try:
        for path, marker in [
            ("/calendar.html", "fullcalendar@6.1.15"),
            ("/js/admin/calendar.js", "initExamFullCalendar"),
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
    test_calendar_files_exist()
    test_calendar_html_fullcalendar_cdn_and_views()
    test_calendar_js_runtime_view_switch_and_filters()
    test_caddy_serves_calendar_assets()
    print("ALL CALENDAR FULLCALENDAR UI TESTS PASSED!")
