/**
 * Khởi tạo & Điều khiển Giao diện Thống kê KPI & Biểu đồ Chart.js (UC13, UC14 UI - TV4 Ngày 6)
 * File: web/js/admin/stats.js
 * Hỗ trợ:
 * - Cập nhật 4 thẻ KPI tổng quan kỳ thi (Tổng số môn |V|, Tổng số SV, Số ca thi tối thiểu, Tỷ lệ xung đột 0.0%)
 * - Biểu đồ 1 (Chart.js): Đối chứng thuật toán DSatur vs Welsh-Powell (Số ca thi & Thời gian xử lý ms)
 * - Biểu đồ 2 (Chart.js): Top môn học có bậc đỉnh deg(v) cao nhất trong đồ thị xung đột
 * - Bảng dữ liệu chi tiết đi kèm phục vụ tra cứu và hỗ trợ tiếp cận (Accessibility Fallback)
 */

const STATS_EXAM_DATASETS = {
  KTHK1_2026: {
    ma_ky_thi: "KTHK1_2026",
    ten_ky_thi: "Học kỳ 1 (2026 - 2027)",
    total_courses: 15,
    total_edges: 46,
    total_students: 1250,
    total_registrations: 3420,
    dsatur_shifts: 4,
    welsh_powell_shifts: 5,
    dsatur_time_ms: 12.4,
    welsh_powell_time_ms: 9.8,
    conflict_rate_percent: 0.0,
    top_degree_courses: [
      { ma_mon: "IT002", ten_mon: "Cấu trúc Dữ liệu & Giải thuật", deg: 11, so_sv: 180, stt_ca: 1, khung_gio: "Ca 1: 7h30 - 9h00" },
      { ma_mon: "IT008", ten_mon: "Toán Rời rạc & Tổ hợp", deg: 10, so_sv: 175, stt_ca: 3, khung_gio: "Ca 3: 13h30 - 15h00" },
      { ma_mon: "IT006", ten_mon: "Trí tuệ Nhân tạo", deg: 9, so_sv: 160, stt_ca: 2, khung_gio: "Ca 2: 9h30 - 11h00" },
      { ma_mon: "IT001", ten_mon: "Lý thuyết Đồ thị", deg: 8, so_sv: 145, stt_ca: 2, khung_gio: "Ca 2: 9h30 - 11h00" },
      { ma_mon: "IT003", ten_mon: "Hệ Quản trị Cơ sở Dữ liệu PostgreSQL", deg: 7, so_sv: 132, stt_ca: 4, khung_gio: "Ca 4: 15h30 - 17h00" },
    ],
  },
  KTHK2_2025: {
    ma_ky_thi: "KTHK2_2025",
    ten_ky_thi: "Học kỳ 2 (2025 - 2026)",
    total_courses: 12,
    total_edges: 34,
    total_students: 980,
    total_registrations: 2640,
    dsatur_shifts: 4,
    welsh_powell_shifts: 4,
    dsatur_time_ms: 9.2,
    welsh_powell_time_ms: 7.5,
    conflict_rate_percent: 0.0,
    top_degree_courses: [
      { ma_mon: "IT004", ten_mon: "Lập trình Web", deg: 9, so_sv: 155, stt_ca: 1, khung_gio: "Ca 1: 7h30 - 9h00" },
      { ma_mon: "IT005", ten_mon: "An toàn & Bảo mật Thông tin", deg: 8, so_sv: 142, stt_ca: 2, khung_gio: "Ca 2: 9h30 - 11h00" },
      { ma_mon: "IT007", ten_mon: "Mạng Máy tính & Truyền thông", deg: 7, so_sv: 128, stt_ca: 3, khung_gio: "Ca 3: 13h30 - 15h00" },
      { ma_mon: "IT012", ten_mon: "Lập trình Hướng đối tượng (OOP)", deg: 6, so_sv: 120, stt_ca: 1, khung_gio: "Ca 1: 7h30 - 9h00" },
      { ma_mon: "IT014", ten_mon: "Hệ điều hành", deg: 5, so_sv: 110, stt_ca: 4, khung_gio: "Ca 4: 15h30 - 17h00" },
    ],
  },
};

const SHIFT_BADGE_CLASSES = {
  1: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800",
  2: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800",
  3: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800",
  4: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-100 text-violet-800",
};

let algoComparisonChartInstance = null;
let topDegreeChartInstance = null;
let activeStatsExamCode = "KTHK1_2026";

function formatNumberVi(value) {
  const num = Number(value || 0);
  return num.toLocaleString("en-US");
}

function getStatsDataset(examCode = activeStatsExamCode) {
  return STATS_EXAM_DATASETS[examCode] || STATS_EXAM_DATASETS.KTHK1_2026;
}

/**
 * Cập nhật 4 thẻ KPI và các nhãn tiêu đề theo kỳ thi đang chọn.
 * @param {Record<string, any>} dataset
 */
function renderStatsKpiCards(dataset) {
  const data = dataset || getStatsDataset();

  const headingEl = document.getElementById("stats-exam-heading");
  if (headingEl) {
    headingEl.textContent = `Thống kê & Giám sát Đồ thị Xung đột: ${data.ten_ky_thi}`;
  }

  const coursesEl = document.getElementById("kpi-total-courses");
  if (coursesEl) {
    coursesEl.textContent = `${data.total_courses} Môn`;
  }

  const edgesEl = document.getElementById("kpi-total-edges");
  if (edgesEl) {
    edgesEl.textContent = `${data.total_edges} cạnh xung đột |E| trong đồ thị`;
  }

  const studentsEl = document.getElementById("kpi-total-students");
  if (studentsEl) {
    studentsEl.textContent = `${formatNumberVi(data.total_students)} SV`;
  }

  const regEl = document.getElementById("kpi-total-registrations");
  if (regEl) {
    regEl.textContent = `${formatNumberVi(data.total_registrations)} lượt đăng ký dự thi (dang_ky_thi)`;
  }

  const shiftsEl = document.getElementById("kpi-min-shifts");
  if (shiftsEl) {
    shiftsEl.textContent = `${data.dsatur_shifts} Ca thi`;
  }

  const shiftCompEl = document.getElementById("kpi-shift-comparison");
  if (shiftCompEl) {
    const diff = data.welsh_powell_shifts - data.dsatur_shifts;
    shiftCompEl.textContent =
      diff > 0
        ? `DSatur tiết kiệm ${diff} ca so với Welsh-Powell (${data.welsh_powell_shifts} ca)`
        : `DSatur và Welsh-Powell cùng hội tụ ở ${data.dsatur_shifts} ca thi`;
  }

  const conflictEl = document.getElementById("kpi-conflict-rate");
  if (conflictEl) {
    conflictEl.textContent = `${Number(data.conflict_rate_percent).toFixed(1)}%`;
  }

  const algoBadgeEl = document.getElementById("stats-algo-badge");
  if (algoBadgeEl) {
    algoBadgeEl.textContent = `DSatur: ${data.dsatur_shifts} Ca (${data.dsatur_time_ms} ms)`;
  }

  const maxDegreeBadgeEl = document.getElementById("stats-max-degree-badge");
  if (maxDegreeBadgeEl && Array.isArray(data.top_degree_courses) && data.top_degree_courses.length > 0) {
    const topCourse = data.top_degree_courses[0];
    maxDegreeBadgeEl.textContent = `Max deg(v) = ${topCourse.deg} (${topCourse.ma_mon})`;
  }
}

/**
 * Render bảng dữ liệu chi tiết Top môn học có bậc đỉnh cao nhất bằng DOM API an toàn.
 * @param {Record<string, any>} dataset
 */
function renderStatsTopDegreeTable(dataset) {
  const data = dataset || getStatsDataset();
  const tbody = document.getElementById("stats-top-degree-tbody");
  const summaryEl = document.getElementById("stats-table-summary");
  if (!tbody) return;

  const list = Array.isArray(data.top_degree_courses) ? data.top_degree_courses : [];
  if (summaryEl) {
    summaryEl.textContent = `Hiển thị Top ${list.length} học phần có bậc xung đột cao nhất`;
  }

  tbody.replaceChildren();
  list.forEach((item, idx) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdRank = document.createElement("td");
    tdRank.className = "py-2.5 px-3 text-center font-bold text-slate-700 tabular-nums";
    tdRank.textContent = `#${idx + 1}`;

    const tdCode = document.createElement("td");
    tdCode.className = "py-2.5 px-3 text-center font-mono font-semibold text-blue-700";
    tdCode.textContent = item.ma_mon;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3 font-medium text-slate-900";
    tdName.textContent = item.ten_mon;

    const tdDeg = document.createElement("td");
    tdDeg.className = "py-2.5 px-3 text-center font-mono font-bold text-slate-900 tabular-nums";
    tdDeg.textContent = `deg(v) = ${item.deg}`;

    const tdStudents = document.createElement("td");
    tdStudents.className = "py-2.5 px-3 text-center text-slate-700 tabular-nums";
    tdStudents.textContent = `${item.so_sv} SV`;

    const tdShift = document.createElement("td");
    tdShift.className = "py-2.5 px-3 text-center";
    const badge = document.createElement("span");
    badge.className = SHIFT_BADGE_CLASSES[item.stt_ca] || SHIFT_BADGE_CLASSES[1];
    badge.textContent = item.khung_gio;
    tdShift.appendChild(badge);

    tr.append(tdRank, tdCode, tdName, tdDeg, tdStudents, tdShift);
    tbody.appendChild(tr);
  });
}

/**
 * Xây dựng cấu hình Chart.js cho Biểu đồ 1: Đối chứng DSatur vs Welsh-Powell.
 * @param {Record<string, any>} dataset
 */
function buildAlgoComparisonChartConfig(dataset) {
  const data = dataset || getStatsDataset();
  return {
    type: "bar",
    data: {
      labels: ["DSatur (Bậc bão hòa)", "Welsh-Powell (Bậc giảm dần)"],
      datasets: [
        {
          label: "Số ca thi χ(G)",
          data: [data.dsatur_shifts, data.welsh_powell_shifts],
          backgroundColor: ["rgba(37, 99, 235, 0.85)", "rgba(245, 158, 11, 0.85)"],
          borderColor: ["#1d4ed8", "#d97706"],
          borderWidth: 1.5,
          borderRadius: 6,
          yAxisID: "yShifts",
        },
        {
          label: "Thời gian chạy (ms)",
          data: [data.dsatur_time_ms, data.welsh_powell_time_ms],
          backgroundColor: ["rgba(148, 163, 184, 0.45)", "rgba(148, 163, 184, 0.45)"],
          borderColor: ["#64748b", "#64748b"],
          borderWidth: 1.5,
          borderRadius: 6,
          yAxisID: "yTime",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: {
            boxWidth: 14,
            font: { size: 12, weight: "600" },
          },
        },
      },
      scales: {
        yShifts: {
          type: "linear",
          position: "left",
          beginAtZero: true,
          suggestedMax: 6,
          ticks: { stepSize: 1 },
          title: {
            display: true,
            text: "Số ca thi χ(G)",
            font: { size: 11, weight: "600" },
          },
        },
        yTime: {
          type: "linear",
          position: "right",
          beginAtZero: true,
          suggestedMax: 16,
          grid: { drawOnChartArea: false },
          title: {
            display: true,
            text: "Thời gian xử lý (ms)",
            font: { size: 11, weight: "600" },
          },
        },
      },
    },
  };
}

/**
 * Xây dựng cấu hình Chart.js cho Biểu đồ 2: Top Môn học có Bậc đỉnh deg(v) cao nhất.
 * @param {Record<string, any>} dataset
 */
function buildTopDegreeChartConfig(dataset) {
  const data = dataset || getStatsDataset();
  const list = Array.isArray(data.top_degree_courses) ? data.top_degree_courses : [];

  return {
    type: "bar",
    data: {
      labels: list.map((item) => `${item.ma_mon} - ${item.ten_mon}`),
      datasets: [
        {
          label: "Bậc đỉnh deg(v) (số môn xung đột)",
          data: list.map((item) => item.deg),
          backgroundColor: [
            "rgba(37, 99, 235, 0.88)",
            "rgba(59, 130, 246, 0.82)",
            "rgba(16, 185, 129, 0.82)",
            "rgba(245, 158, 11, 0.82)",
            "rgba(139, 92, 246, 0.82)",
          ],
          borderColor: ["#1d4ed8", "#2563eb", "#059669", "#d97706", "#7c3aed"],
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: {
            boxWidth: 14,
            font: { size: 12, weight: "600" },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          suggestedMax: 12,
          ticks: { stepSize: 2 },
          title: {
            display: true,
            text: "Số môn xung đột trực tiếp deg(v)",
            font: { size: 11, weight: "600" },
          },
        },
      },
    },
  };
}

/**
 * Khởi tạo hoặc vẽ lại cả 2 khung canvas biểu đồ Chart.js trên trang Thống kê.
 * @param {string} examCode
 */
function initStatsCharts(examCode = activeStatsExamCode) {
  activeStatsExamCode = STATS_EXAM_DATASETS[examCode] ? examCode : "KTHK1_2026";
  const dataset = getStatsDataset(activeStatsExamCode);

  renderStatsKpiCards(dataset);
  renderStatsTopDegreeTable(dataset);

  const algoCanvas = document.getElementById("chart-algo-comparison");
  const degreeCanvas = document.getElementById("chart-top-degree-courses");

  if (typeof window === "undefined" || typeof window.Chart !== "function") {
    return null;
  }

  if (algoComparisonChartInstance && typeof algoComparisonChartInstance.destroy === "function") {
    algoComparisonChartInstance.destroy();
  }
  if (topDegreeChartInstance && typeof topDegreeChartInstance.destroy === "function") {
    topDegreeChartInstance.destroy();
  }

  if (algoCanvas) {
    algoComparisonChartInstance = new window.Chart(
      algoCanvas,
      buildAlgoComparisonChartConfig(dataset)
    );
  }

  if (degreeCanvas) {
    topDegreeChartInstance = new window.Chart(
      degreeCanvas,
      buildTopDegreeChartConfig(dataset)
    );
  }

  return {
    algoChart: algoComparisonChartInstance,
    degreeChart: topDegreeChartInstance,
  };
}

/**
 * Xử lý khi Admin đổi kỳ thi trên dropdown #stats-exam-select.
 */
function handleStatsExamChange() {
  const selectEl = document.getElementById("stats-exam-select");
  const selectedCode = selectEl && selectEl.value ? selectEl.value : "KTHK1_2026";
  return initStatsCharts(selectedCode);
}

document.addEventListener("DOMContentLoaded", () => {
  initStatsCharts("KTHK1_2026");
});
