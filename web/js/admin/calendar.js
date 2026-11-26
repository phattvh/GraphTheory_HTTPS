/**
 * Khởi tạo & Điều khiển Lịch thi Toàn trường trên FullCalendar (UC10 UI — TV4 Ngày 4)
 * File: web/js/admin/calendar.js
 * Hỗ trợ:
 * - Chuyển đổi chế độ xem: Tuần (timeGridWeek), Chia Ca (shiftGridWeek), Tháng (dayGridMonth)
 * - Tùy chọn chia khung giờ trục dọc: Chia theo Ca (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00,
 *   Ca 3: 13h30-15h00, Ca 4: 15h30-17h00) hoặc Chia theo Giờ chuẩn (07:00, 08:00...)
 * - Lọc theo Môn học, Phòng thi, Ca thi.
 */

const SHIFT_TIME_SLOTS = {
  "07:30": "Ca 1: 7h30 - 9h00",
  "09:00": "Nghỉ chuyển ca (9h00 - 9h30)",
  "09:30": "Ca 2: 9h30 - 11h00",
  "11:00": "Nghỉ trưa (11h00 - 13h30)",
  "13:30": "Ca 3: 13h30 - 15h00",
  "15:00": "Nghỉ chuyển ca (15h00 - 15h30)",
  "15:30": "Ca 4: 15h30 - 17h00",
  "17:00": "Kết thúc ngày thi (17h00)",
};

const SHIFT_COLOR_PALETTE = {
  1: {
    label: "Ca 1: 7h30 - 9h00",
    subLabel: "Buổi sáng (Màu 1)",
    backgroundColor: "#eff6ff",
    borderColor: "#93c5fd",
    textColor: "#1e3a8a",
    cellBgClass: "bg-blue-50/50 space-y-1.5",
    titleClass: "font-bold text-blue-900",
    badgeClass: "px-3 py-1 rounded-full font-semibold bg-blue-100 text-blue-900",
    badgeText: "Ca 1: 7h30 - 9h00 • Màu #1",
  },
  2: {
    label: "Ca 2: 9h30 - 11h00",
    subLabel: "Buổi sáng (Màu 2)",
    backgroundColor: "#ecfdf5",
    borderColor: "#6ee7b7",
    textColor: "#064e3b",
    cellBgClass: "bg-emerald-50/50 space-y-1.5",
    titleClass: "font-bold text-emerald-900",
    badgeClass: "px-3 py-1 rounded-full font-semibold bg-emerald-100 text-emerald-900",
    badgeText: "Ca 2: 9h30 - 11h00 • Màu #2",
  },
  3: {
    label: "Ca 3: 13h30 - 15h00",
    subLabel: "Buổi chiều (Màu 3)",
    backgroundColor: "#fffbeb",
    borderColor: "#fcd34d",
    textColor: "#78350f",
    cellBgClass: "bg-amber-50/50 space-y-1.5",
    titleClass: "font-bold text-amber-900",
    badgeClass: "px-3 py-1 rounded-full font-semibold bg-amber-100 text-amber-900",
    badgeText: "Ca 3: 13h30 - 15h00 • Màu #3",
  },
  4: {
    label: "Ca 4: 15h30 - 17h00",
    subLabel: "Buổi chiều (Màu 4)",
    backgroundColor: "#f5f3ff",
    borderColor: "#c4b5fd",
    textColor: "#4c1d95",
    cellBgClass: "bg-violet-50/50 space-y-1.5",
    titleClass: "font-bold text-violet-900",
    badgeClass: "px-3 py-1 rounded-full font-semibold bg-violet-100 text-violet-900",
    badgeText: "Ca 4: 15h30 - 17h00 • Màu #4",
  },
};

const SAMPLE_EXAM_EVENTS = [
  {
    id: "evt-it002",
    ma_mon: "IT002",
    ten_mon: "Cấu trúc Dữ liệu & Giải thuật",
    stt_ca: 1,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T07:30:00",
    end: "2026-12-15T09:00:00",
    rooms: ["A101", "A102"],
    so_luong_sv: 180,
    deg: 11,
  },
  {
    id: "evt-it005",
    ma_mon: "IT005",
    ten_mon: "An toàn & Bảo mật Thông tin",
    stt_ca: 1,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T07:30:00",
    end: "2026-12-15T09:00:00",
    rooms: ["B201"],
    so_luong_sv: 95,
    deg: 5,
  },
  {
    id: "evt-it001",
    ma_mon: "IT001",
    ten_mon: "Lý thuyết Đồ thị (Graph Theory)",
    stt_ca: 2,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T09:30:00",
    end: "2026-12-15T11:00:00",
    rooms: ["A101", "A102"],
    so_luong_sv: 145,
    deg: 8,
  },
  {
    id: "evt-it006",
    ma_mon: "IT006",
    ten_mon: "Trí tuệ Nhân tạo (AI Foundations)",
    stt_ca: 2,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T09:30:00",
    end: "2026-12-15T11:00:00",
    rooms: ["B201", "B202"],
    so_luong_sv: 160,
    deg: 9,
  },
  {
    id: "evt-it008",
    ma_mon: "IT008",
    ten_mon: "Toán Rời rạc & Tổ hợp",
    stt_ca: 3,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T13:30:00",
    end: "2026-12-15T15:00:00",
    rooms: ["A101", "A102"],
    so_luong_sv: 175,
    deg: 10,
  },
  {
    id: "evt-it004",
    ma_mon: "IT004",
    ten_mon: "Lập trình Web (FastAPI & Python)",
    stt_ca: 3,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T13:30:00",
    end: "2026-12-15T15:00:00",
    rooms: ["B201"],
    so_luong_sv: 110,
    deg: 6,
  },
  {
    id: "evt-it003",
    ma_mon: "IT003",
    ten_mon: "Hệ Quản trị CSDL PostgreSQL",
    stt_ca: 4,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T15:30:00",
    end: "2026-12-15T17:00:00",
    rooms: ["B201", "B202"],
    so_luong_sv: 132,
    deg: 7,
  },
  {
    id: "evt-it007",
    ma_mon: "IT007",
    ten_mon: "Mạng Máy tính & Truyền thông",
    stt_ca: 4,
    ngay_thi: "2026-12-15",
    start: "2026-12-15T15:30:00",
    end: "2026-12-15T17:00:00",
    rooms: ["A101", "C301"],
    so_luong_sv: 125,
    deg: 6,
  },
  {
    id: "evt-it009",
    ma_mon: "IT009",
    ten_mon: "Giải tích 1",
    stt_ca: 1,
    ngay_thi: "2026-12-16",
    start: "2026-12-16T07:30:00",
    end: "2026-12-16T09:00:00",
    rooms: ["A101", "A103"],
    so_luong_sv: 190,
    deg: 7,
  },
  {
    id: "evt-it010",
    ma_mon: "IT010",
    ten_mon: "Đại số Tuyến tính",
    stt_ca: 2,
    ngay_thi: "2026-12-16",
    start: "2026-12-16T09:30:00",
    end: "2026-12-16T11:00:00",
    rooms: ["A101"],
    so_luong_sv: 120,
    deg: 5,
  },
  {
    id: "evt-it011",
    ma_mon: "IT011",
    ten_mon: "Kiến trúc Máy tính",
    stt_ca: 3,
    ngay_thi: "2026-12-16",
    start: "2026-12-16T13:30:00",
    end: "2026-12-16T15:00:00",
    rooms: ["A103"],
    so_luong_sv: 90,
    deg: 4,
  },
  {
    id: "evt-it012",
    ma_mon: "IT012",
    ten_mon: "Lập trình Hướng đối tượng (OOP)",
    stt_ca: 1,
    ngay_thi: "2026-12-17",
    start: "2026-12-17T07:30:00",
    end: "2026-12-17T09:00:00",
    rooms: ["B202", "B203"],
    so_luong_sv: 150,
    deg: 6,
  },
  {
    id: "evt-it013",
    ma_mon: "IT013",
    ten_mon: "Công nghệ Phần mềm",
    stt_ca: 2,
    ngay_thi: "2026-12-17",
    start: "2026-12-17T09:30:00",
    end: "2026-12-17T11:00:00",
    rooms: ["B201"],
    so_luong_sv: 135,
    deg: 5,
  },
  {
    id: "evt-it014",
    ma_mon: "IT014",
    ten_mon: "Hệ điều hành",
    stt_ca: 1,
    ngay_thi: "2026-12-18",
    start: "2026-12-18T07:30:00",
    end: "2026-12-18T09:00:00",
    rooms: ["A101"],
    so_luong_sv: 110,
    deg: 4,
  },
  {
    id: "evt-it015",
    ma_mon: "IT015",
    ten_mon: "Xác suất Thống kê",
    stt_ca: 3,
    ngay_thi: "2026-12-18",
    start: "2026-12-18T13:30:00",
    end: "2026-12-18T15:00:00",
    rooms: ["B202", "B203"],
    so_luong_sv: 140,
    deg: 5,
  },
];

const EXAM_WEEK_DAYS = ["2026-12-15", "2026-12-16", "2026-12-17", "2026-12-18", "2026-12-19"];

let adminCalendarInstance = null;
let currentCalendarView = "timeGridWeek";
let currentSlotMode = "shift"; // "shift" (Ca 1: 7h30-9h, Ca 2: 9h30-11h...) | "hour" (07:00, 08:00...)

/**
 * Định dạng nhãn trục giờ của FullCalendar theo Ca thi hoặc theo Giờ tiêu chuẩn.
 * @param {Date} dateObj
 * @param {string} mode
 */
function formatSlotLabelByMode(dateObj, mode = currentSlotMode) {
  if (!(dateObj instanceof Date) || Number.isNaN(dateObj.getTime())) return "";
  const hh = String(dateObj.getHours()).padStart(2, "0");
  const mm = String(dateObj.getMinutes()).padStart(2, "0");
  const key = `${hh}:${mm}`;

  if (mode === "shift") {
    if (SHIFT_TIME_SLOTS[key]) {
      return SHIFT_TIME_SLOTS[key];
    }
    return `${hh}h${mm}`;
  }
  return mm === "00" ? `${hh}:00` : "";
}

/**
 * Chuyển đổi danh sách ca thi thành định dạng Event Object chuẩn của FullCalendar.
 * @param {Array<Record<string, any>>} rawEvents
 */
function buildFullCalendarEvents(rawEvents = SAMPLE_EXAM_EVENTS) {
  return rawEvents.map((item) => {
    const palette = SHIFT_COLOR_PALETTE[item.stt_ca] || SHIFT_COLOR_PALETTE[1];
    const roomText = Array.isArray(item.rooms) ? item.rooms.join(", ") : String(item.rooms || "");
    return {
      id: item.id,
      title: `[Ca ${item.stt_ca}] ${item.ma_mon} - ${item.ten_mon} (${roomText})`,
      start: item.start,
      end: item.end,
      backgroundColor: palette.backgroundColor,
      borderColor: palette.borderColor,
      textColor: palette.textColor,
      extendedProps: {
        ma_mon: item.ma_mon,
        ten_mon: item.ten_mon,
        stt_ca: item.stt_ca,
        ngay_thi: item.ngay_thi,
        rooms: item.rooms,
        so_luong_sv: item.so_luong_sv,
        deg: item.deg,
      },
    };
  });
}

/**
 * Trả về cấu hình khởi tạo FullCalendar với chế độ xem Tuần (timeGridWeek) & Tháng (dayGridMonth)
 * cùng tùy chọn chia ca theo giờ (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00).
 * @param {string} initialView
 * @param {string} slotMode
 */
function getCalendarViewConfig(initialView = "timeGridWeek", slotMode = currentSlotMode) {
  const safeView = initialView === "dayGridMonth" ? "dayGridMonth" : "timeGridWeek";
  const isShiftAxis = slotMode !== "hour";

  return {
    initialView: safeView,
    initialDate: "2026-12-15",
    locale: "vi",
    firstDay: 1,
    allDaySlot: false,
    slotMinTime: isShiftAxis ? "07:30:00" : "07:00:00",
    slotMaxTime: isShiftAxis ? "17:30:00" : "18:00:00",
    slotDuration: "00:30:00",
    slotLabelInterval: isShiftAxis ? "00:30:00" : "01:00:00",
    slotLabelContent: (arg) => formatSlotLabelByMode(arg.date, slotMode),
    expandRows: true,
    height: "auto",
    nowIndicator: true,
    dayMaxEvents: true,
    headerToolbar: false,
    views: {
      timeGridWeek: {
        type: "timeGrid",
        duration: { weeks: 1 },
        buttonText: "Tuần (Week)",
      },
      dayGridMonth: {
        type: "dayGrid",
        duration: { months: 1 },
        buttonText: "Tháng (Month)",
      },
    },
    events: buildFullCalendarEvents(SAMPLE_EXAM_EVENTS),
    eventClick: (info) => {
      if (info && info.event) {
        updateCalendarInspector(info.event.extendedProps, info.event.start);
      }
    },
  };
}

/**
 * Cập nhật khung thông tin chi tiết khi người dùng chọn một môn thi trên lịch.
 * @param {Record<string, any>} props
 * @param {Date | string | null} startDate
 */
function updateCalendarInspector(props, startDate) {
  if (!props) return;
  const titleEl = document.getElementById("calendar-inspector-title");
  const metaEl = document.getElementById("calendar-inspector-meta");
  const badgeEl = document.getElementById("calendar-inspector-badge");
  const palette = SHIFT_COLOR_PALETTE[props.stt_ca] || SHIFT_COLOR_PALETTE[1];
  const rooms = Array.isArray(props.rooms) ? props.rooms.join(", ") : String(props.rooms || "");
  const dateLabel =
    startDate instanceof Date
      ? startDate.toLocaleDateString("vi-VN", {
          weekday: "long",
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        })
      : props.ngay_thi || "Đợt thi HK1 (12/2026)";

  if (titleEl) {
    titleEl.textContent = `${props.ma_mon} - ${props.ten_mon} • Bậc xung đột deg(v) = ${props.deg}`;
  }
  if (metaEl) {
    metaEl.textContent = `${palette.label} (${dateLabel}) • Phòng thi FFD: ${rooms} • Sĩ số: ${props.so_luong_sv} SV`;
  }
  if (badgeEl) {
    badgeEl.className = palette.badgeClass;
    badgeEl.textContent = palette.badgeText;
  }
}

/**
 * Kết xuất động bảng Lịch Thi Chia Theo 4 Ca Chuẩn (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00)
 * bằng DOM API an toàn (createElement & textContent).
 * @param {Array<Record<string, any>>} eventsList
 */
function renderShiftMatrixTable(eventsList = SAMPLE_EXAM_EVENTS) {
  const tbody = document.getElementById("calendar-shift-matrix-body");
  if (!tbody || typeof document.createElement !== "function") return;

  const rows = [];
  for (let shiftNum = 1; shiftNum <= 4; shiftNum += 1) {
    const palette = SHIFT_COLOR_PALETTE[shiftNum];
    const tr = document.createElement("tr");

    const labelTd = document.createElement("td");
    labelTd.className = "font-bold text-slate-800 bg-slate-50/70";
    const shiftMainText = document.createElement("div");
    shiftMainText.textContent = palette.label;
    const shiftSubText = document.createElement("span");
    shiftSubText.className = "font-normal text-slate-500";
    shiftSubText.textContent = palette.subLabel;
    labelTd.appendChild(shiftMainText);
    labelTd.appendChild(shiftSubText);
    tr.appendChild(labelTd);

    EXAM_WEEK_DAYS.forEach((dayIso) => {
      const td = document.createElement("td");
      const matches = eventsList.filter(
        (ev) => Number(ev.stt_ca) === shiftNum && ev.ngay_thi === dayIso
      );

      if (matches.length === 0) {
        td.className = "text-slate-500";
        td.textContent = "Trống";
      } else {
        td.className = palette.cellBgClass;
        matches.forEach((ev, idx) => {
          const itemBox = document.createElement("div");
          itemBox.className = idx > 0 ? "pt-1.5 border-t border-slate-200/60 cursor-pointer" : "cursor-pointer";
          itemBox.addEventListener("click", () => updateCalendarInspector(ev, new Date(ev.start)));

          const titleDiv = document.createElement("div");
          titleDiv.className = palette.titleClass;
          titleDiv.textContent = `${ev.ma_mon} - ${ev.ten_mon}`;

          const roomDiv = document.createElement("div");
          roomDiv.className = "text-slate-600";
          const roomStr = Array.isArray(ev.rooms) ? ev.rooms.join(", ") : String(ev.rooms || "");
          roomDiv.textContent = `Phòng: ${roomStr} (${ev.so_luong_sv} SV)`;

          itemBox.appendChild(titleDiv);
          itemBox.appendChild(roomDiv);
          td.appendChild(itemBox);
        });
      }
      tr.appendChild(td);
    });

    rows.push(tr);
  }

  if (typeof tbody.replaceChildren === "function") {
    tbody.replaceChildren(...rows);
  }
}

/**
 * Đồng bộ trạng thái nút bấm Tuần (timeGridWeek) / Chia Ca (shiftGridWeek) / Tháng (dayGridMonth).
 * @param {string} viewName
 */
function updateCalendarViewButtons(viewName) {
  const weekBtn = document.getElementById("btn-view-week");
  const shiftBtn = document.getElementById("btn-view-shift");
  const monthBtn = document.getElementById("btn-view-month");
  const viewBadge = document.getElementById("calendar-view-badge");
  const rangeHeading = document.getElementById("calendar-current-range");
  const fcContainer = document.getElementById("admin-fullcalendar");

  const isMonth = viewName === "dayGridMonth";
  const isShiftOnly = viewName === "shiftGridWeek";
  const isWeek = !isMonth && !isShiftOnly;

  const activeClass =
    "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white transition cursor-pointer";
  const inactiveClass =
    "px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:text-slate-900 transition cursor-pointer";

  if (weekBtn) {
    weekBtn.className = isWeek ? activeClass : inactiveClass;
    weekBtn.setAttribute("aria-pressed", isWeek ? "true" : "false");
  }
  if (shiftBtn) {
    shiftBtn.className = isShiftOnly ? activeClass : inactiveClass;
    shiftBtn.setAttribute("aria-pressed", isShiftOnly ? "true" : "false");
  }
  if (monthBtn) {
    monthBtn.className = isMonth ? activeClass : inactiveClass;
    monthBtn.setAttribute("aria-pressed", isMonth ? "true" : "false");
  }

  if (fcContainer && fcContainer.classList) {
    fcContainer.classList.toggle("hidden", isShiftOnly);
    fcContainer.classList.toggle("is-shift-axis", currentSlotMode === "shift");
  }

  if (viewBadge) {
    if (isShiftOnly) {
      viewBadge.textContent = "Chế độ xem: Chia theo 4 Ca chuẩn (Ca 1: 7h30-9h, Ca 2: 9h30-11h...)";
    } else if (isMonth) {
      viewBadge.textContent = "Chế độ xem: Tháng (dayGridMonth)";
    } else {
      const slotDesc =
        currentSlotMode === "shift"
          ? "Chia theo Ca: Ca 1 7h30-9h, Ca 2 9h30-11h..."
          : "Chia theo Giờ chuẩn 07:00 - 18:00";
      viewBadge.textContent = `Chế độ xem: Tuần (${slotDesc})`;
    }
  }

  if (rangeHeading) {
    if (!isShiftOnly && adminCalendarInstance && adminCalendarInstance.view && adminCalendarInstance.view.title) {
      rangeHeading.textContent = adminCalendarInstance.view.title;
    } else {
      rangeHeading.textContent = isMonth
        ? "Tháng 12 / 2026 (Toàn bộ đợt thi Học kỳ 1)"
        : "Tuần thi: Thứ Hai 15/12/2026 - Thứ Bảy 20/12/2026";
    }
  }
}

/**
 * Chuyển đổi tùy chọn chia khung giờ trục dọc:
 * - "shift": Chia theo Ca (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00)
 * - "hour": Chia theo Giờ chuẩn (07:00, 08:00, 09:00...)
 * @param {string} mode
 */
function switchCalendarSlotMode(mode) {
  currentSlotMode = mode === "hour" ? "hour" : "shift";
  const slotSelect = document.getElementById("calendar-slot-mode");
  if (slotSelect && slotSelect.value !== currentSlotMode) {
    slotSelect.value = currentSlotMode;
  }

  if (adminCalendarInstance && typeof adminCalendarInstance.setOption === "function") {
    const isShiftAxis = currentSlotMode === "shift";
    adminCalendarInstance.setOption("slotMinTime", isShiftAxis ? "07:30:00" : "07:00:00");
    adminCalendarInstance.setOption("slotMaxTime", isShiftAxis ? "17:30:00" : "18:00:00");
    adminCalendarInstance.setOption("slotLabelInterval", isShiftAxis ? "00:30:00" : "01:00:00");
    adminCalendarInstance.setOption("slotLabelContent", (arg) =>
      formatSlotLabelByMode(arg.date, currentSlotMode)
    );
  }

  updateCalendarViewButtons(currentCalendarView);
  return currentSlotMode;
}

/**
 * Chuyển đổi chế độ hiển thị của FullCalendar giữa Tuần (timeGridWeek), Chia Ca (shiftGridWeek) và Tháng (dayGridMonth).
 * @param {string} viewName
 */
function switchCalendarView(viewName) {
  let targetView = "timeGridWeek";
  if (viewName === "dayGridMonth") {
    targetView = "dayGridMonth";
  } else if (viewName === "shiftGridWeek") {
    targetView = "shiftGridWeek";
  }
  currentCalendarView = targetView;

  if (
    targetView !== "shiftGridWeek" &&
    adminCalendarInstance &&
    typeof adminCalendarInstance.changeView === "function"
  ) {
    adminCalendarInstance.changeView(targetView);
  }
  updateCalendarViewButtons(targetView);
  return targetView;
}

/**
 * Điều hướng thời gian trên FullCalendar ('prev' | 'next' | 'today').
 * @param {string} action
 */
function navigateCalendar(action) {
  if (!adminCalendarInstance) return;
  if (action === "prev" && typeof adminCalendarInstance.prev === "function") {
    adminCalendarInstance.prev();
  } else if (action === "next" && typeof adminCalendarInstance.next === "function") {
    adminCalendarInstance.next();
  } else if (action === "today" && typeof adminCalendarInstance.gotoDate === "function") {
    adminCalendarInstance.gotoDate("2026-12-15");
  }
  updateCalendarViewButtons(currentCalendarView);
}

/**
 * Lọc danh sách sự kiện trên FullCalendar & bảng Ma trận Chia Ca theo Môn học, Phòng thi và Ca thi.
 */
function filterCalendarEvents() {
  const courseSelect = document.getElementById("calendar-filter-course");
  const roomSelect = document.getElementById("calendar-filter-room");
  const shiftSelect = document.getElementById("calendar-filter-shift");
  const summaryEl = document.getElementById("calendar-active-filter-summary");

  const courseVal = courseSelect ? courseSelect.value : "ALL";
  const roomVal = roomSelect ? roomSelect.value : "ALL";
  const shiftVal = shiftSelect ? shiftSelect.value : "ALL";

  const filtered = SAMPLE_EXAM_EVENTS.filter((item) => {
    const matchCourse = courseVal === "ALL" || item.ma_mon === courseVal;
    const matchRoom =
      roomVal === "ALL" || (Array.isArray(item.rooms) && item.rooms.includes(roomVal));
    const matchShift = shiftVal === "ALL" || String(item.stt_ca) === String(shiftVal);
    return matchCourse && matchRoom && matchShift;
  });

  if (adminCalendarInstance && typeof adminCalendarInstance.removeAllEvents === "function") {
    adminCalendarInstance.removeAllEvents();
    const fcEvents = buildFullCalendarEvents(filtered);
    fcEvents.forEach((ev) => adminCalendarInstance.addEvent(ev));
  }

  renderShiftMatrixTable(filtered);

  if (summaryEl) {
    summaryEl.textContent = `Đang hiển thị: ${filtered.length}/${SAMPLE_EXAM_EVENTS.length} môn thi phù hợp bộ lọc`;
  }
  return filtered;
}

/**
 * Đặt lại toàn bộ bộ lọc Môn học / Phòng thi / Ca thi về trạng thái mặc định.
 */
function resetCalendarFilters() {
  const courseSelect = document.getElementById("calendar-filter-course");
  const roomSelect = document.getElementById("calendar-filter-room");
  const shiftSelect = document.getElementById("calendar-filter-shift");
  if (courseSelect) courseSelect.value = "ALL";
  if (roomSelect) roomSelect.value = "ALL";
  if (shiftSelect) shiftSelect.value = "ALL";
  return filterCalendarEvents();
}

/**
 * Khởi tạo FullCalendar trên phần tử #admin-fullcalendar.
 */
function initExamFullCalendar() {
  const calendarEl = document.getElementById("admin-fullcalendar");
  if (!calendarEl) return null;

  updateCalendarViewButtons(currentCalendarView);
  renderShiftMatrixTable(SAMPLE_EXAM_EVENTS);

  if (!window.FullCalendar || typeof window.FullCalendar.Calendar !== "function") {
    return null;
  }

  const config = getCalendarViewConfig(
    currentCalendarView === "shiftGridWeek" ? "timeGridWeek" : currentCalendarView,
    currentSlotMode
  );
  adminCalendarInstance = new window.FullCalendar.Calendar(calendarEl, config);
  adminCalendarInstance.render();
  updateCalendarViewButtons(currentCalendarView);
  return adminCalendarInstance;
}

document.addEventListener("DOMContentLoaded", () => {
  initExamFullCalendar();
});
