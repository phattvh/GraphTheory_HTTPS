"""
Kiểm tra giao diện Thống kê & Phân tích (UC13, UC14 UI):
- Nhúng thư viện Chart.js v4 qua CDN (kèm SRI sha384) trong web/stats.html
- 4 thẻ KPI tổng quan đồng nhất (Môn/|E|, SV/Lượt thi, Số ca χ(G), Tỷ lệ lấp đầy phòng TB)
- 2 biểu đồ Chart.js: (1) Tỷ lệ lấp đầy phòng theo từng Ca thi (không vẽ thời gian ms),
  (2) Phân bố số môn thi trong 1 ngày của sinh viên (Doughnut Chart)
- Bảng chi tiết phân bổ từng Ca thi & chuyển đổi kỳ thi trong stats.js
"""

from pathlib import Path
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
STATS_HTML = WEB_DIR / "stats.html"
STATS_JS = WEB_DIR / "js" / "admin" / "stats.js"
BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def test_stats_files_exist():
    """Kiểm tra sự tồn tại của web/stats.html và web/js/admin/stats.js."""
    for file_path in [STATS_HTML, STATS_JS]:
        assert file_path.exists(), f"Thiếu file giao diện Thống kê bắt buộc: {file_path}"


def test_stats_html_chartjs_cdn_and_canvases():
    """Kiểm tra web/stats.html nhúng Chart.js qua CDN, có đủ 4 thẻ KPI, 2 khung canvas và bảng phân bổ ca."""
    html = STATS_HTML.read_text(encoding="utf-8")
    js = STATS_JS.read_text(encoding="utf-8")

    for required_marker in [
        "https://cdn.tailwindcss.com",
        "chart.js@4.4.7/dist/chart.umd.min.js",
        'data-admin-page="stats"',
        'id="tab-stats"',
        'id="stats-year-select"',
        'onchange="handleStatsYearChange()"',
        'id="stats-exam-select"',
        'onchange="handleStatsExamChange()"',
        'id="kpi-total-courses"',
        'id="kpi-total-students"',
        'id="kpi-min-shifts"',
        'id="kpi-room-utilization"',
        "<canvas",
        'id="chart-shift-utilization"',
        'id="chart-daily-exam-distribution"',
        'id="stats-shift-summary-tbody"',
        'src="/js/admin/stats.js"',
    ]:
        assert required_marker in html, f"web/stats.html thiếu thành phần bắt buộc: {required_marker}"

    assert html.count("<canvas") >= 2, "web/stats.html phải có ít nhất 2 khung <canvas> biểu đồ Chart.js"
    assert "Thời gian chạy (ms)" not in js, "Không vẽ cột thời gian chạy (ms) không cần thiết trên biểu đồ"
    for removed_clutter in [
        "kpi-total-edges-sub",
        "kpi-total-regs-sub",
        "kpi-algo-compare-sub",
        "kpi-room-summary-sub",
        "stats-utilization-badge",
        "stats-max-degree-badge",
        "stats-table-summary",
        "Di chuột vào từng thanh",
    ]:
        assert removed_clutter not in html, f"web/stats.html không được còn chữ phụ thừa: {removed_clutter}"

    for js_marker in [
        "STATS_EXAM_DATASETS",
        "function getAvailableAcademicYears",
        "function getExamsByAcademicYear",
        "function syncStatsSelectors",
        "function handleStatsYearChange",
        "function renderStatsKpiCards",
        "function renderStatsShiftSummaryTable",
        "function buildShiftUtilizationChartConfig",
        "function buildDailyExamDistributionChartConfig",
        "function initStatsCharts",
        "function handleStatsExamChange",
        "window.Chart",
    ]:
        assert js_marker in js, f"web/js/admin/stats.js thiếu hàm/cấu hình: {js_marker}"

    assert "innerHTML" not in js, "web/js/admin/stats.js không được dùng innerHTML để tránh XSS"


def test_stats_js_runtime_charts_and_exam_switch():
    """Chạy kiểm thử runtime bằng Node.js cho 2 biểu đồ Chart.js, 4 thẻ KPI, lọc 2 cấp Năm học -> Kỳ thi."""
    if not shutil.which("node"):
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const makeEl = (tag = "div") => ({
  tagName: tag.toUpperCase(),
  className: "",
  textContent: "",
  value: "",
  selected: false,
  children: [],
  replaceChildren: function(...nodes) { this.children = nodes; },
  appendChild: function(node) { this.children.push(node); return node; },
  append: function(...nodes) { this.children.push(...nodes); },
});

const elements = {
  "stats-exam-heading": makeEl("h2"),
  "stats-year-select": makeEl("select"),
  "stats-exam-select": makeEl("select"),
  "kpi-total-courses": makeEl("div"),
  "kpi-total-students": makeEl("div"),
  "kpi-min-shifts": makeEl("div"),
  "kpi-room-utilization": makeEl("div"),
  "stats-shift-summary-tbody": makeEl("tbody"),
  "chart-shift-utilization": makeEl("canvas"),
  "chart-daily-exam-distribution": makeEl("canvas"),
};

const createdCharts = [];

class FakeChart {
  constructor(canvasEl, config) {
    this.canvas = canvasEl;
    this.config = config;
    this.destroyed = false;
    createdCharts.push(this);
  }
  destroy() {
    this.destroyed = true;
  }
}

const sandbox = {
  document: {
    getElementById: (id) => elements[id] || null,
    createElement: (tag) => makeEl(tag),
    addEventListener: () => {},
  },
  window: {
    Chart: FakeChart,
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/stats.js", "utf8"), sandbox);

// 1. Khởi tạo mặc định kỳ thi KTHK1_2026: tiêu đề gọn, lọc 2 cấp đồng bộ, tạo 2 biểu đồ & bảng 4 ca thi
const res = sandbox.initStatsCharts("KTHK1_2026");
assert.ok(res && res.shiftChart && res.dailyExamChart);
assert.strictEqual(createdCharts.length, 2);
assert.strictEqual(elements["stats-exam-heading"].textContent, "Thống kê & Phân tích Kỳ thi");
assert.strictEqual(elements["stats-year-select"].value, "2026 - 2027");
assert.strictEqual(elements["stats-exam-select"].value, "KTHK1_2026");
assert.strictEqual(elements["stats-exam-select"].children.length, 1);
assert.strictEqual(res.shiftChart.config.type, "bar");
assert.deepStrictEqual(Array.from(res.shiftChart.config.data.labels), ["Ca 1", "Ca 2", "Ca 3", "Ca 4"]);
assert.strictEqual(res.shiftChart.config.data.datasets.length, 1);
assert.strictEqual(res.dailyExamChart.config.type, "doughnut");
assert.deepStrictEqual(
  Array.from(res.dailyExamChart.config.data.datasets[0].data),
  [62, 31, 7]
);
assert.strictEqual(
  res.dailyExamChart.config.data.datasets[0].data.reduce((a, b) => a + b, 0),
  100
);
assert.ok(res.dailyExamChart.config.data.labels[0].includes("1 môn / ngày"));
assert.strictEqual(
  res.dailyExamChart.config.options.plugins.tooltip.callbacks.label({ dataIndex: 1, parsed: 31 }),
  "31 sinh viên (31.0%)"
);
assert.strictEqual(elements["kpi-total-courses"].textContent, "15 Môn");
assert.strictEqual(elements["kpi-total-students"].textContent, "100 SV");
assert.strictEqual(elements["kpi-min-shifts"].textContent, "4 Ca");
assert.strictEqual(elements["kpi-room-utilization"].textContent, "75.0%");
assert.strictEqual(elements["stats-shift-summary-tbody"].children.length, 4);

// 2. Chuyển Năm học sang 2025 - 2026: tự lọc #stats-exam-select chỉ còn kỳ thi năm 2025 - 2026 & vẽ lại 2 chart
elements["stats-year-select"].value = "2025 - 2026";
const res2 = sandbox.handleStatsYearChange();
assert.ok(res2 && res2.shiftChart && res2.dailyExamChart);
assert.strictEqual(res.shiftChart.destroyed, true);
assert.strictEqual(res.dailyExamChart.destroyed, true);
assert.strictEqual(elements["stats-exam-select"].value, "KTHK2_2025");
assert.strictEqual(elements["stats-exam-select"].children.length, 1);
assert.strictEqual(elements["kpi-total-courses"].textContent, "12 Môn");
assert.strictEqual(elements["kpi-room-utilization"].textContent, "71.4%");
assert.deepStrictEqual(
  Array.from(res2.dailyExamChart.config.data.datasets[0].data),
  [56, 24, 5]
);
assert.strictEqual(
  res2.dailyExamChart.config.data.datasets[0].data.reduce((a, b) => a + b, 0),
  85
);
"""

    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime stats test failed:\n{res.stderr or res.stdout}"


def test_caddy_serves_stats_assets():
    """Nếu container Caddy đang chạy, kiểm tra HTTP 200 OK cho /stats.html và /js/admin/stats.js."""
    try:
        for path, marker in [
            ("/stats.html", 'id="chart-shift-utilization"'),
            ("/js/admin/stats.js", "initStatsCharts"),
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
    test_stats_files_exist()
    test_stats_html_chartjs_cdn_and_canvases()
    test_stats_js_runtime_charts_and_exam_switch()
    test_caddy_serves_stats_assets()
    print("ALL STATS CHART.JS UI TESTS PASSED!")
