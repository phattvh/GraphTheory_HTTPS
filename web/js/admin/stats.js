/**
 * Khởi tạo & Điều khiển Giao diện Thống kê KPI & Biểu đồ Chart.js (UC13, UC14 UI)
 * File: web/js/admin/stats.js
 * Hỗ trợ:
 * - 4 thẻ KPI tổng quan đồng nhất (Tổng môn |V| & cạnh |E|, SV & lượt đăng ký, Số ca tối ưu χ(G), Tỷ lệ lấp đầy phòng TB)
 * - Biểu đồ 1 (Chart.js): Tỷ lệ lấp đầy phòng thi (%) theo từng Ca thi (bỏ biểu đồ so sánh ms không cần thiết)
 * - Biểu đồ 2 (Chart.js): Phân bố số môn thi trong 1 ngày của sinh viên (Doughnut Chart — UC14)
 * - Bảng chi tiết phân bổ từng Ca thi, 100% DOM API an toàn (textContent)
 */

const STATS_EXAM_DATASETS = {
  KTHK1_2026: {
    ma_ky_thi: "KTHK1_2026",
    nam_hoc: "2026 - 2027",
    short_label: "KTHK1_2026 - Thi cuối kỳ HK1",
    ten_ky_thi: "Học kỳ 1 (2026 - 2027)",
    total_courses: 15,
    total_edges: 46,
    total_students: 100,
    total_registrations: 300,
    total_rooms: 10,
    dsatur_shifts: 4,
    welsh_powell_shifts: 5,
    avg_room_utilization_percent: 75.0,
    shifts_breakdown: [
      {
        stt_ca: 1,
        label: "Ca 1",
        khung_gio: "07:30 - 09:00",
        course_count: 4,
        students: 88,
        rooms_used: 3,
        capacity_used: 105,
        utilization_percent: 83.8,
        status: "Tải cao",
      },
      {
        stt_ca: 2,
        label: "Ca 2",
        khung_gio: "09:30 - 11:00",
        course_count: 4,
        students: 82,
        rooms_used: 3,
        capacity_used: 105,
        utilization_percent: 78.1,
        status: "Ổn định",
      },
      {
        stt_ca: 3,
        label: "Ca 3",
        khung_gio: "13:30 - 15:00",
        course_count: 4,
        students: 74,
        rooms_used: 3,
        capacity_used: 100,
        utilization_percent: 74.0,
        status: "Ổn định",
      },
      {
        stt_ca: 4,
        label: "Ca 4",
        khung_gio: "15:30 - 17:00",
        course_count: 3,
        students: 56,
        rooms_used: 2,
        capacity_used: 90,
        utilization_percent: 62.2,
        status: "Thông thoáng",
      },
    ],
    daily_exam_distribution: [
      { label: "1 môn / ngày", students: 62 },
      { label: "2 môn / ngày", students: 31 },
      { label: "3+ môn / ngày", students: 7 },
    ],
  },
  KTHK2_2025: {
    ma_ky_thi: "KTHK2_2025",
    nam_hoc: "2025 - 2026",
    short_label: "KTHK2_2025 - Thi cuối kỳ HK2",
    ten_ky_thi: "Học kỳ 2 (2025 - 2026)",
    total_courses: 12,
    total_edges: 34,
    total_students: 85,
    total_registrations: 240,
    total_rooms: 8,
    dsatur_shifts: 4,
    welsh_powell_shifts: 4,
    avg_room_utilization_percent: 71.4,
    shifts_breakdown: [
      {
        stt_ca: 1,
        label: "Ca 1",
        khung_gio: "07:30 - 09:00",
        course_count: 3,
        students: 72,
        rooms_used: 3,
        capacity_used: 95,
        utilization_percent: 75.8,
        status: "Ổn định",
      },
      {
        stt_ca: 2,
        label: "Ca 2",
        khung_gio: "09:30 - 11:00",
        course_count: 3,
        students: 66,
        rooms_used: 2,
        capacity_used: 80,
        utilization_percent: 82.5,
        status: "Tải cao",
      },
      {
        stt_ca: 3,
        label: "Ca 3",
        khung_gio: "13:30 - 15:00",
        course_count: 3,
        students: 58,
        rooms_used: 2,
        capacity_used: 85,
        utilization_percent: 68.2,
        status: "Ổn định",
      },
      {
        stt_ca: 4,
        label: "Ca 4",
        khung_gio: "15:30 - 17:00",
        course_count: 3,
        students: 44,
        rooms_used: 2,
        capacity_used: 75,
        utilization_percent: 58.7,
        status: "Thông thoáng",
      },
    ],
    daily_exam_distribution: [
      { label: "1 môn / ngày", students: 56 },
      { label: "2 môn / ngày", students: 24 },
      { label: "3+ môn / ngày", students: 5 },
    ],
  },
};

const SHIFT_BADGE_CLASSES = {
  1: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800",
  2: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800",
  3: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800",
  4: "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-100 text-violet-800",
};

let shiftUtilizationChartInstance = null;
let dailyExamChartInstance = null;
let activeStatsExamCode = "KTHK1_2026";

function formatNumberVi(value) {
  const num = Number(value || 0);
  return num.toLocaleString("en-US");
}

function getStatsDataset(examCode = activeStatsExamCode) {
  return STATS_EXAM_DATASETS[examCode] || STATS_EXAM_DATASETS.KTHK1_2026;
}

function getUtilizationBarColor(percent) {
  const val = Number(percent || 0);
  if (val >= 95) return { bg: "rgba(220, 38, 38, 0.85)", border: "#b91c1c" };
  if (val >= 80) return { bg: "rgba(217, 119, 6, 0.85)", border: "#b45309" };
  return { bg: "rgba(37, 99, 235, 0.85)", border: "#1d4ed8" };
}

function getShiftStatusBadgeClass(status) {
  if (status === "Quá tải" || status === "Tách phòng") {
    return "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700";
  }
  if (status === "Tải cao") {
    return "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800";
  }
  return "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700";
}

/**
 * Cập nhật 4 thẻ KPI và các nhãn tiêu đề theo kỳ thi đang chọn.
 * @param {Record<string, any>} dataset
 */
function renderStatsKpiCards(dataset) {
  const data = dataset || getStatsDataset();

  const headingEl = document.getElementById("stats-exam-heading");
  if (headingEl) {
    headingEl.textContent = "Thống kê & phân tích kỳ thi";
  }

  const coursesEl = document.getElementById("kpi-total-courses");
  if (coursesEl) {
    coursesEl.textContent = `${data.total_courses} môn`;
  }

  const studentsEl = document.getElementById("kpi-total-students");
  if (studentsEl) {
    studentsEl.textContent = `${formatNumberVi(data.total_students)} SV`;
  }

  const shiftsEl = document.getElementById("kpi-min-shifts");
  if (shiftsEl) {
    shiftsEl.textContent = `${data.dsatur_shifts} ca`;
  }

  const utilEl = document.getElementById("kpi-room-utilization");
  if (utilEl) {
    utilEl.textContent = `${Number(data.avg_room_utilization_percent).toFixed(1)}%`;
  }
}

/**
 * Render bảng chi tiết phân bổ từng Ca thi bằng DOM API an toàn.
 * @param {Record<string, any>} dataset
 */
function renderStatsShiftSummaryTable(dataset) {
  const data = dataset || getStatsDataset();
  const tbody = document.getElementById("stats-shift-summary-tbody");
  if (!tbody) return;

  const shifts = Array.isArray(data.shifts_breakdown) ? data.shifts_breakdown : [];

  tbody.replaceChildren();
  shifts.forEach((shift) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 divide-x divide-slate-200";

    const tdShift = document.createElement("td");
    tdShift.className = "py-2.5 px-3 text-center";
    const shiftBadge = document.createElement("span");
    shiftBadge.className = SHIFT_BADGE_CLASSES[shift.stt_ca] || SHIFT_BADGE_CLASSES[1];
    shiftBadge.textContent = shift.label;
    tdShift.appendChild(shiftBadge);

    const tdTime = document.createElement("td");
    tdTime.className = "py-2.5 px-3 text-center font-mono text-slate-700 tabular-nums";
    tdTime.textContent = shift.khung_gio;

    const tdCourses = document.createElement("td");
    tdCourses.className = "py-2.5 px-3 text-center font-semibold text-slate-900 tabular-nums";
    tdCourses.textContent = `${shift.course_count} môn`;

    const tdStudents = document.createElement("td");
    tdStudents.className = "py-2.5 px-3 text-center text-slate-800 tabular-nums";
    tdStudents.textContent = `${shift.students} / ${shift.capacity_used} chỗ`;

    const tdRooms = document.createElement("td");
    tdRooms.className = "py-2.5 px-3 text-center text-slate-700 tabular-nums";
    tdRooms.textContent = `${shift.rooms_used} / ${data.total_rooms} phòng`;

    const tdUtil = document.createElement("td");
    tdUtil.className = "py-2.5 px-3 text-center font-mono font-bold text-slate-900 tabular-nums";
    tdUtil.textContent = `${Number(shift.utilization_percent).toFixed(1)}%`;

    const tdStatus = document.createElement("td");
    tdStatus.className = "py-2.5 px-3 text-center";
    const statusBadge = document.createElement("span");
    statusBadge.className = getShiftStatusBadgeClass(shift.status);
    statusBadge.textContent = shift.status;
    tdStatus.appendChild(statusBadge);

    tr.append(tdShift, tdTime, tdCourses, tdStudents, tdRooms, tdUtil, tdStatus);
    tbody.appendChild(tr);
  });
}

/**
 * Xây dựng cấu hình Chart.js cho Biểu đồ 1: Tỷ lệ lấp đầy phòng theo từng Ca thi.
 * @param {Record<string, any>} dataset
 */
function buildShiftUtilizationChartConfig(dataset) {
  const data = dataset || getStatsDataset();
  const shifts = Array.isArray(data.shifts_breakdown) ? data.shifts_breakdown : [];
  const colors = shifts.map((s) => getUtilizationBarColor(s.utilization_percent));

  return {
    type: "bar",
    data: {
      labels: shifts.map((s) => s.label),
      datasets: [
        {
          label: "Tỷ lệ lấp đầy phòng (%)",
          data: shifts.map((s) => s.utilization_percent),
          backgroundColor: colors.map((c) => c.bg),
          borderColor: colors.map((c) => c.border),
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 56,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const s = shifts[ctx.dataIndex];
              if (!s) return `${ctx.parsed.y}%`;
              return `${s.utilization_percent}% (${s.students}/${s.capacity_used} chỗ · ${s.course_count} môn · ${s.rooms_used} phòng)`;
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            callback: (val) => `${val}%`,
          },
          title: {
            display: true,
            text: "Tỷ lệ lấp đầy (%)",
            font: { size: 11, weight: "600" },
          },
        },
      },
    },
  };
}

/**
 * Xây dựng cấu hình Chart.js cho Biểu đồ 2: Phân bố số môn thi trong 1 ngày của Sinh viên (Doughnut Chart).
 * @param {Record<string, any>} dataset
 */
function buildDailyExamDistributionChartConfig(dataset) {
  const data = dataset || getStatsDataset();
  const buckets = Array.isArray(data.daily_exam_distribution) ? data.daily_exam_distribution : [];
  const totalStudents =
    buckets.reduce((sum, item) => sum + Number(item.students || 0), 0) ||
    Number(data.total_students || 0) ||
    1;

  return {
    type: "doughnut",
    data: {
      labels: buckets.map((item) => {
        const pct = ((Number(item.students || 0) / totalStudents) * 100).toFixed(1);
        return `${item.label} (${item.students} SV · ${pct}%)`;
      }),
      datasets: [
        {
          label: "Số sinh viên",
          data: buckets.map((item) => item.students),
          backgroundColor: [
            "rgba(37, 99, 235, 0.88)",
            "rgba(245, 158, 11, 0.88)",
            "rgba(220, 38, 38, 0.85)",
          ],
          borderColor: "#ffffff",
          borderWidth: 2,
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyle: "circle",
            font: { size: 11, weight: "600" },
          },
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items && items[0] ? items[0].dataIndex : -1;
              const bucket = buckets[idx];
              return bucket ? bucket.label : "";
            },
            label: (ctx) => {
              const bucket = buckets[ctx.dataIndex];
              if (!bucket) return `${ctx.parsed} SV`;
              const pct = ((Number(bucket.students || 0) / totalStudents) * 100).toFixed(1);
              return `${bucket.students} sinh viên (${pct}%)`;
            },
          },
        },
      },
    },
  };
}

/**
 * Lấy danh sách năm học duy nhất sắp xếp mới nhất trước.
 * @returns {string[]}
 */
function getAvailableAcademicYears() {
  const years = new Set();
  Object.values(STATS_EXAM_DATASETS).forEach((item) => {
    if (item && item.nam_hoc) years.add(item.nam_hoc);
  });
  return Array.from(years).sort((a, b) => b.localeCompare(a));
}

/**
 * Lọc danh sách kỳ thi thuộc một năm học cụ thể.
 * @param {string} academicYear
 * @returns {Array<Record<string, any>>}
 */
function getExamsByAcademicYear(academicYear) {
  return Object.values(STATS_EXAM_DATASETS).filter((item) => item && item.nam_hoc === academicYear);
}

/**
 * Đồng bộ 2 ô lọc Năm học -> Kỳ thi bằng DOM API an toàn (textContent).
 * @param {string} academicYear
 * @param {string} preferredExamCode
 * @returns {string} Mã kỳ thi đang được chọn sau khi đồng bộ
 */
function syncStatsSelectors(academicYear, preferredExamCode) {
  const years = getAvailableAcademicYears();
  const activeYear = years.includes(academicYear) ? academicYear : years[0] || "";
  const examsInYear = getExamsByAcademicYear(activeYear);
  const matchedExam =
    examsInYear.find((item) => item.ma_ky_thi === preferredExamCode) ||
    examsInYear[0] ||
    getStatsDataset("KTHK1_2026");

  const yearSelect = document.getElementById("stats-year-select");
  if (yearSelect && typeof yearSelect.replaceChildren === "function") {
    yearSelect.replaceChildren();
    years.forEach((yr) => {
      const opt = document.createElement("option");
      opt.value = yr;
      opt.textContent = yr;
      if (yr === activeYear) opt.selected = true;
      yearSelect.appendChild(opt);
    });
    yearSelect.value = activeYear;
  }

  const examSelect = document.getElementById("stats-exam-select");
  if (examSelect && typeof examSelect.replaceChildren === "function") {
    examSelect.replaceChildren();
    examsInYear.forEach((ex) => {
      const opt = document.createElement("option");
      opt.value = ex.ma_ky_thi;
      opt.textContent = ex.short_label || `${ex.ma_ky_thi} - ${ex.ten_ky_thi}`;
      if (ex.ma_ky_thi === matchedExam.ma_ky_thi) opt.selected = true;
      examSelect.appendChild(opt);
    });
    examSelect.value = matchedExam.ma_ky_thi;
  }

  return matchedExam.ma_ky_thi;
}

/**
 * Khởi tạo hoặc vẽ lại cả 2 khung canvas biểu đồ Chart.js trên trang Thống kê.
 * @param {string} examCode
 */
function initStatsCharts(examCode = activeStatsExamCode) {
  activeStatsExamCode = STATS_EXAM_DATASETS[examCode] ? examCode : "KTHK1_2026";
  const dataset = getStatsDataset(activeStatsExamCode);
  syncStatsSelectors(dataset.nam_hoc, dataset.ma_ky_thi);

  renderStatsKpiCards(dataset);
  renderStatsShiftSummaryTable(dataset);

  const shiftCanvas = document.getElementById("chart-shift-utilization");
  const dailyExamCanvas = document.getElementById("chart-daily-exam-distribution");

  if (typeof window === "undefined" || typeof window.Chart !== "function") {
    return null;
  }

  if (shiftUtilizationChartInstance && typeof shiftUtilizationChartInstance.destroy === "function") {
    shiftUtilizationChartInstance.destroy();
  }
  if (dailyExamChartInstance && typeof dailyExamChartInstance.destroy === "function") {
    dailyExamChartInstance.destroy();
  }

  if (shiftCanvas) {
    shiftUtilizationChartInstance = new window.Chart(
      shiftCanvas,
      buildShiftUtilizationChartConfig(dataset)
    );
  }

  if (dailyExamCanvas) {
    dailyExamChartInstance = new window.Chart(
      dailyExamCanvas,
      buildDailyExamDistributionChartConfig(dataset)
    );
  }

  return {
    shiftChart: shiftUtilizationChartInstance,
    dailyExamChart: dailyExamChartInstance,
  };
}

/**
 * Xử lý khi Admin đổi Năm học trên dropdown #stats-year-select:
 * tự động lọc danh sách Kỳ thi thuộc năm đó và vẽ lại thống kê.
 */
function handleStatsYearChange() {
  const yearSelect = document.getElementById("stats-year-select");
  const selectedYear = yearSelect && yearSelect.value ? yearSelect.value : getAvailableAcademicYears()[0];
  const resolvedExamCode = syncStatsSelectors(selectedYear, "");
  return initStatsCharts(resolvedExamCode);
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
