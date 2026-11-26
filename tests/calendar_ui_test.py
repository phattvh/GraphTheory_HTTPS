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
    """Kiểm tra nhúng thư viện FullCalendar qua CDN, ô dropdown gộp Tuần (Chia Ca / Theo Giờ) và nút Tháng."""
    html = (WEB_DIR / "calendar.html").read_text(encoding="utf-8")
    js = (WEB_DIR / "js" / "admin" / "calendar.js").read_text(encoding="utf-8")

    for required_marker in [
        "https://cdn.tailwindcss.com",
        "fullcalendar@6.1.15/index.global.min.js",
        'data-admin-page="calendar"',
        'id="tab-calendar"',
        'id="admin-fullcalendar-shell"',
        'id="admin-fullcalendar"',
        'id="calendar-search-input"',
        'id="calendar-search-suggestions"',
        'data-search-keyword="IT001"',
        'data-search-keyword="A101"',
        'data-search-keyword="Ca 1"',
        'id="calendar-select-year"',
        'id="calendar-select-semester"',
        'id="calendar-select-week"',
        "Năm học",
        "Học kỳ",
        "Tuần",
        "14/12/2026-20/12/2026",
        "18/01/2027-24/01/2027",
        'id="btn-view-week"',
        'data-calendar-view="timeGridWeek"',
        'value="shift"',
        'value="hour"',
        "Tuần: Chia theo ca",
        "Tuần: Chia theo giờ",
        'id="btn-view-month"',
        'data-calendar-view="dayGridMonth"',
        "Ca 1: 7h30 - 9h00",
        "Ca 2: 9h30 - 11h00",
        "Ca 3: 13h30 - 15h00",
        "Ca 4: 15h30 - 17h00",
        'src="/js/admin/calendar.js"',
    ]:
        assert required_marker in html, f"web/calendar.html thiếu thành phần bắt buộc: {required_marker}"

    assert 'id="btn-view-shift"' not in html, "Đã gộp Tuần và Chia Ca thành 1 ô select dropdown duy nhất"

    for js_marker in [
        "function initExamFullCalendar",
        "function getCalendarViewConfig",
        "function formatSlotLabelByMode",
        "function renderCustomEventContent",
        "function switchCalendarSlotMode",
        "function switchCalendarView",
        "function handleAcademicPeriodChange",
        "function applyCalendarSearchKeyword",
        "function filterCalendarEvents",
        "function resetCalendarFilters",
        "function renderShiftMatrixTable",
        "SHIFT_AXIS_ROWS",
        "SHIFT_COMPACT_TIME_RANGES",
        "timeGridWeek",
        "dayGridMonth",
        "window.FullCalendar",
    ]:
        assert js_marker in js, f"web/js/admin/calendar.js thiếu hàm/cấu hình: {js_marker}"

    assert "Nghỉ chuyển ca" not in js and "Nghỉ trưa" not in js, "Không được còn các hàng nghỉ giữa ca"
    assert "innerHTML" not in js, "web/js/admin/calendar.js không được dùng innerHTML để tránh XSS"


def test_calendar_js_runtime_view_switch_and_filters():
    """Chạy kiểm thử runtime bằng Node.js cho ô dropdown gộp Tuần (Chia Ca / Theo Giờ), nút Tháng và bộ lọc."""
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

const elements = {
  "btn-view-week": { value: "shift", className: "", setAttribute: function(k, v) { this[k] = v; } },
  "btn-view-month": { className: "", setAttribute: function(k, v) { this[k] = v; } },
  "calendar-view-badge": { textContent: "" },
  "calendar-current-range": { textContent: "" },
  "calendar-search-input": { value: "" },
  "calendar-active-filter-summary": { textContent: "" },
  "calendar-inspector-title": { textContent: "" },
  "calendar-inspector-meta": { textContent: "" },
  "calendar-inspector-badge": { className: "", textContent: "" },
  "admin-fullcalendar": { classList: makeClassList(["is-shift-axis"]) },
  "calendar-shift-matrix-body": { replaceChildren: function(...rows) { this.rows = rows; } },
};

let renderedView = null;
let currentEvents = [];
let optionsLog = {};

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
  setOption(key, val) {
    optionsLog[key] = val;
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
    createElement: (tag) => ({
      tagName: tag,
      className: "",
      textContent: "",
      children: [],
      appendChild: function(c) { this.children.push(c); },
      addEventListener: () => {},
    }),
    addEventListener: () => {},
  },
  window: {
    FullCalendar: { Calendar: FakeFullCalendar },
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/calendar.js", "utf8"), sandbox);

// 1. Khởi tạo mặc định ở chế độ xem Tuần (timeGridWeek) với 4 hàng Ca gộp liền nhau
const cal = sandbox.initExamFullCalendar();
assert.ok(cal);
assert.strictEqual(renderedView, "timeGridWeek");
assert.strictEqual(cal.config.slotMinTime, "01:00:00");
assert.strictEqual(cal.config.slotMaxTime, "05:00:00");
assert.strictEqual(cal.config.slotDuration, "01:00:00");
assert.strictEqual(elements["btn-view-week"]["aria-pressed"], "true");
assert.strictEqual(elements["btn-view-week"].value, "shift");
assert.strictEqual(currentEvents.length, 15);

// 2. Kiểm tra 4 hàng trục dọc tương ứng đúng 4 Ca thi
assert.strictEqual(
  sandbox.formatSlotLabelByMode(new Date("2026-12-15T01:00:00"), "shift"),
  "Ca 1: 7h30 - 9h00"
);
assert.strictEqual(
  sandbox.formatSlotLabelByMode(new Date("2026-12-15T02:00:00"), "shift"),
  "Ca 2: 9h30 - 11h00"
);
assert.strictEqual(
  sandbox.formatSlotLabelByMode(new Date("2026-12-15T03:00:00"), "shift"),
  "Ca 3: 13h30 - 15h00"
);
assert.strictEqual(
  sandbox.formatSlotLabelByMode(new Date("2026-12-15T04:00:00"), "shift"),
  "Ca 4: 15h30 - 17h00"
);

// 3. Chuyển sang chế độ xem Tháng (dayGridMonth), sau đó chọn tùy chọn trong ô dropdown Tuần sẽ tự quay về Tuần
assert.strictEqual(sandbox.switchCalendarView("dayGridMonth"), "dayGridMonth");
assert.strictEqual(renderedView, "dayGridMonth");
assert.strictEqual(elements["btn-view-month"]["aria-pressed"], "true");
assert.strictEqual(elements["btn-view-week"]["aria-pressed"], "false");

assert.strictEqual(sandbox.switchCalendarSlotMode("hour"), "hour");
assert.strictEqual(renderedView, "timeGridWeek");
assert.strictEqual(elements["btn-view-week"]["aria-pressed"], "true");
assert.strictEqual(elements["btn-view-week"].value, "hour");
assert.strictEqual(optionsLog.slotMinTime, "07:00:00");
assert.strictEqual(optionsLog.slotMaxTime, "18:00:00");
assert.strictEqual(currentEvents[0].start, "2026-12-15T07:30:00");
assert.strictEqual(currentEvents[0].end, "2026-12-15T08:15:00");
assert.strictEqual(currentEvents[1].start, "2026-12-15T08:15:00");
assert.strictEqual(currentEvents[1].end, "2026-12-15T09:00:00");

assert.strictEqual(sandbox.switchCalendarSlotMode("shift"), "shift");
assert.strictEqual(elements["btn-view-week"].value, "shift");
assert.strictEqual(optionsLog.slotMinTime, "01:00:00");
assert.strictEqual(optionsLog.slotMaxTime, "05:00:00");
assert.strictEqual(currentEvents[0].start, "2026-12-15T01:00:00");
assert.strictEqual(currentEvents[0].end, "2026-12-15T01:30:00");
assert.strictEqual(currentEvents[1].start, "2026-12-15T01:30:00");
assert.strictEqual(currentEvents[1].end, "2026-12-15T02:00:00");

// 4. Kiểm tra ô tìm kiếm từ khóa gợi ý & Đặt lại
const shift1Events = sandbox.applyCalendarSearchKeyword("Ca 1");
assert.strictEqual(elements["calendar-search-input"].value, "Ca 1");
assert.ok(shift1Events.length > 0 && shift1Events.length < 15);
assert.strictEqual(currentEvents.length, shift1Events.length);

const roomA101Events = sandbox.applyCalendarSearchKeyword("A101");
assert.ok(roomA101Events.length > 0 && roomA101Events.length < 15);

const allEvents = sandbox.resetCalendarFilters();
assert.strictEqual(elements["calendar-search-input"].value, "");
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
            ("/calendar.html", "Tuần: Chia theo ca"),
            ("/js/admin/calendar.js", "SHIFT_COMPACT_TIME_RANGES"),
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
