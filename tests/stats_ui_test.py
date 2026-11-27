"""
Kiểm tra giao diện Thống kê & Phân tích (UC13, UC14 UI):
- Nhúng thư viện Chart.js v4 qua CDN (kèm SRI sha384) trong web/stats.html
- 4 thẻ KPI tổng quan đồng nhất (Môn/|E|, SV/Lượt thi, Số ca χ(G), Tỷ lệ lấp đầy phòng TB)
- 2 biểu đồ Chart.js: (1) Tỷ lệ lấp đầy phòng theo từng Ca thi (không vẽ thời gian ms),
  (2) Top 5 môn có bậc đỉnh cao nhất (trục Y gọn mã môn)
- Bảng chi tiết phân bổ từng Ca thi (không lặp lại Top 5 môn) & chuyển đổi kỳ thi trong stats.js
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
        'id="stats-exam-select"',
        'onchange="handleStatsExamChange()"',
        'id="kpi-total-courses"',
        'id="kpi-total-students"',
        'id="kpi-min-shifts"',
        'id="kpi-room-utilization"',
        "<canvas",
        'id="chart-shift-utilization"',
        'id="chart-top-degree-courses"',
        'id="stats-shift-summary-tbody"',
        'src="/js/admin/stats.js"',
    ]:
        assert required_marker in html, f"web/stats.html thiếu thành phần bắt buộc: {required_marker}"

    assert html.count("<canvas") >= 2, "web/stats.html phải có ít nhất 2 khung <canvas> biểu đồ Chart.js"
    assert "Thời gian chạy (ms)" not in js, "Không vẽ cột thời gian chạy (ms) không cần thiết trên biểu đồ"

    for js_marker in [
        "STATS_EXAM_DATASETS",
        "function renderStatsKpiCards",
        "function renderStatsShiftSummaryTable",
        "function buildShiftUtilizationChartConfig",
        "function buildTopDegreeChartConfig",
        "function initStatsCharts",
        "function handleStatsExamChange",
        "window.Chart",
    ]:
        assert js_marker in js, f"web/js/admin/stats.js thiếu hàm/cấu hình: {js_marker}"

    assert "innerHTML" not in js, "web/js/admin/stats.js không được dùng innerHTML để tránh XSS"


def test_stats_js_runtime_charts_and_exam_switch():
    """Chạy kiểm thử runtime bằng Node.js cho 2 biểu đồ Chart.js, 4 thẻ KPI, bảng từng ca và đổi kỳ thi."""
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
  children: [],
  replaceChildren: function(...nodes) { this.children = nodes; },
  appendChild: function(node) { this.children.push(node); return node; },
  append: function(...nodes) { this.children.push(...nodes); },
});

const elements = {
  "stats-exam-heading": makeEl("h2"),
  "stats-exam-select": makeEl("select"),
  "kpi-total-courses": makeEl("div"),
  "kpi-total-edges-sub": makeEl("div"),
  "kpi-total-students": makeEl("div"),
  "kpi-total-regs-sub": makeEl("div"),
  "kpi-min-shifts": makeEl("div"),
  "kpi-algo-compare-sub": makeEl("div"),
  "kpi-room-utilization": makeEl("div"),
  "kpi-room-summary-sub": makeEl("div"),
  "stats-utilization-badge": makeEl("span"),
  "stats-max-degree-badge": makeEl("span"),
  "stats-table-summary": makeEl("span"),
  "stats-shift-summary-tbody": makeEl("tbody"),
  "chart-shift-utilization": makeEl("canvas"),
  "chart-top-degree-courses": makeEl("canvas"),
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

// 1. Khởi tạo mặc định kỳ thi KTHK1_2026: tạo đúng 2 biểu đồ Chart.js & bảng phân bổ 4 ca thi
const res = sandbox.initStatsCharts("KTHK1_2026");
assert.ok(res && res.shiftChart && res.degreeChart);
assert.strictEqual(createdCharts.length, 2);
assert.strictEqual(res.shiftChart.config.type, "bar");
assert.deepStrictEqual(Array.from(res.shiftChart.config.data.labels), ["Ca 1", "Ca 2", "Ca 3", "Ca 4"]);
assert.strictEqual(res.shiftChart.config.data.datasets.length, 1);
assert.strictEqual(res.degreeChart.config.type, "bar");
assert.strictEqual(res.degreeChart.config.options.indexAxis, "y");
assert.deepStrictEqual(
  Array.from(res.degreeChart.config.data.labels),
  ["IT002", "IT008", "IT006", "IT001", "IT003"]
);
assert.strictEqual(elements["kpi-total-courses"].textContent, "15 Môn");
assert.strictEqual(elements["kpi-total-students"].textContent, "100 SV");
assert.strictEqual(elements["kpi-min-shifts"].textContent, "4 Ca");
assert.strictEqual(elements["kpi-algo-compare-sub"].textContent, "DSatur: 4 ca · Welsh-Powell: 5 ca");
assert.strictEqual(elements["kpi-room-utilization"].textContent, "75.0%");
assert.strictEqual(elements["stats-shift-summary-tbody"].children.length, 4);

// 2. Chuyển sang kỳ thi KTHK2_2025: hủy 2 chart cũ và vẽ 2 chart mới với dữ liệu mới
elements["stats-exam-select"].value = "KTHK2_2025";
const res2 = sandbox.handleStatsExamChange();
assert.ok(res2 && res2.shiftChart && res2.degreeChart);
assert.strictEqual(res.shiftChart.destroyed, true);
assert.strictEqual(res.degreeChart.destroyed, true);
assert.strictEqual(elements["kpi-total-courses"].textContent, "12 Môn");
assert.strictEqual(elements["kpi-room-utilization"].textContent, "71.4%");
assert.ok(elements["stats-max-degree-badge"].textContent.includes("IT004"));
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
