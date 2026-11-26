/**
 * Khởi tạo & Điều khiển Lịch thi Toàn trường trên FullCalendar (UC10 UI — TV4 Ngày 4)
 * File: web/js/admin/calendar.js
 * Hỗ trợ:
 * - Chuyển đổi chế độ xem: Tuần (timeGridWeek), Chia Ca (shiftGridWeek), Tháng (dayGridMonth)
 * - Tùy chọn chia khung giờ trục dọc:
 *   + "shift": Gộp mỗi ca thành đúng 1 hàng duy nhất (Ca 1: 7h30 - 9h00, Ca 2: 9h30 - 11h00,
 *     Ca 3: 13h30 - 15h00, Ca 4: 15h30 - 17h00), loại bỏ hoàn toàn các hàng lẻ 30p và hàng nghỉ giữa ca.
 *   + "hour": Chia theo từng giờ chuẩn (07:00, 08:00, 09:00...)
 * - Lọc theo Môn học, Phòng thi, Ca thi.
 */

const SHIFT_AXIS_ROWS = {
  "01:00": "Ca 1: 7h30 - 9h00",
  "02:00": "Ca 2: 9h30 - 11h00",
  "03:00": "Ca 3: 13h30 - 15h00",
  "04:00": "Ca 4: 15h30 - 17h00",
};

const SHIFT_COMPACT_TIME_RANGES = {
  1: { startSlot: "01:00:00", endSlot: "02:00:00", realTime: "7h30 - 9h00" },
  2: { startSlot: "02:00:00", endSlot: "03:00:00", realTime: "9h30 - 11h00" },
  3: { startSlot: "03:00:00", endSlot: "04:00:00", realTime: "13h30 - 15h00" },
  4: { startSlot: "04:00:00", endSlot: "05:00:00", realTime: "15h30 - 17h00" },
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
let currentSlotMode = "shift"; // "shift" (Gộp 4 hàng Ca 1..Ca 4, không có hàng nghỉ) | "hour" (07:00, 08:00...)

/**
 * Định dạng nhãn trục giờ của FullCalendar:
 * - Khi mode === "shift": Gộp đúng 4 hàng Ca 1..Ca 4 (không có hàng 08h00, 08h30 hay hàng nghỉ giữa ca).
 * - Khi mode === "hour": Hiển thị theo từng giờ chuẩn (07:00, 08:00...).
 * @param {Date} dateObj
 * @param {string} mode
 */
function formatSlotLabelByMode(dateObj, mode = currentSlotMode) {
  if (!(dateObj instanceof Date) || Number.isNaN(dateObj.getTime())) return "";
  const hh = String(dateObj.getHours()).padStart(2, "0");
  const mm = String(dateObj.getMinutes()).padStart(2, "0");
  const key = `${hh}:${mm}`;

  if (mode === "shift") {
    if (SHIFT_AXIS_ROWS[key]) {
      return SHIFT_AXIS_ROWS[key];
    }
    const realHourToShiftMap = {
      "07:30": "Ca 1: 7h30 - 9h00",
      "09:30": "Ca 2: 9h30 - 11h00",
      "13:30": "Ca 3: 13h30 - 15h00",
      "15:30": "Ca 4: 15h30 - 17h00",
    };
    return realHourToShiftMap[key] || "";
  }
  return mm === "00" ? `${hh}:00` : "";
}

/**
 * Cộng thêm số phút vào chuỗi thời gian "HH:MM:SS".
 * @param {string} timeStr
 * @param {number} minutesToAdd
 */
function addMinutesToTimeString(timeStr, minutesToAdd) {
  const parts = String(timeStr || "00:00:00").split(":").map(Number);
  const totalMinutes = (parts[0] || 0) * 60 + (parts[1] || 0) + Math.round(minutesToAdd);
  const hh = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const mm = String(totalMinutes % 60).padStart(2, "0");
  return `${hh}:${mm}:00`;
}

/**
 * Chuyển đổi danh sách ca thi thành định dạng Event Object chuẩn của FullCalendar.
 * Các môn thi cùng ngày + cùng ca được chia thành các dải hàng ngang 100% chiều rộng
 * nằm gọn bên trong ô ca đó (không bị ép cột dọc 50% gây cắt chữ).
 * @param {Array<Record<string, any>>} rawEvents
 * @param {string} mode
 */
function buildFullCalendarEvents(rawEvents = SAMPLE_EXAM_EVENTS, mode = currentSlotMode) {
  // Gom nhóm các môn cùng ngày và cùng ca để chia hàng ngang tuần tự trong ô ca
  const groupCounts = {};
  const groupIndices = {};
  rawEvents.forEach((item) => {
    const key = `${item.ngay_thi}_ca_${item.stt_ca}`;
    groupCounts[key] = (groupCounts[key] || 0) + 1;
  });

  return rawEvents.map((item) => {
    const palette = SHIFT_COLOR_PALETTE[item.stt_ca] || SHIFT_COLOR_PALETTE[1];
    const compactSlot = SHIFT_COMPACT_TIME_RANGES[item.stt_ca] || SHIFT_COMPACT_TIME_RANGES[1];
    const roomText = Array.isArray(item.rooms) ? item.rooms.join(", ") : String(item.rooms || "");

    const key = `${item.ngay_thi}_ca_${item.stt_ca}`;
    const totalInSlot = groupCounts[key] || 1;
    const indexInSlot = groupIndices[key] || 0;
    groupIndices[key] = indexInSlot + 1;

    let eventStart = item.start;
    let eventEnd = item.end;

    if (mode === "shift") {
      const slotMinutes = 60;
      const sliceMinutes = slotMinutes / totalInSlot;
      const startTime = addMinutesToTimeString(compactSlot.startSlot, indexInSlot * sliceMinutes);
      const endTime = addMinutesToTimeString(
        compactSlot.startSlot,
        (indexInSlot + 1) * sliceMinutes
      );
      eventStart = `${item.ngay_thi}T${startTime}`;
      eventEnd = `${item.ngay_thi}T${endTime}`;
    } else if (totalInSlot > 1) {
      const baseStartTime = String(item.start).split("T")[1] || "07:30:00";
      const slotMinutes = 90;
      const sliceMinutes = slotMinutes / totalInSlot;
      const startTime = addMinutesToTimeString(baseStartTime, indexInSlot * sliceMinutes);
      const endTime = addMinutesToTimeString(baseStartTime, (indexInSlot + 1) * sliceMinutes);
      eventStart = `${item.ngay_thi}T${startTime}`;
      eventEnd = `${item.ngay_thi}T${endTime}`;
    }

    return {
      id: item.id,
      title: `${item.ma_mon} - ${item.ten_mon} (${roomText})`,
      start: eventStart,
      end: eventEnd,
      backgroundColor: palette.backgroundColor,
      borderColor: palette.borderColor,
      textColor: palette.textColor,
      extendedProps: {
        ma_mon: item.ma_mon,
        ten_mon: item.ten_mon,
        stt_ca: item.stt_ca,
        khung_gio_ca: compactSlot.realTime,
        ngay_thi: item.ngay_thi,
        rooms: item.rooms,
        so_luong_sv: item.so_luong_sv,
        deg: item.deg,
      },
    };
  });
}

/**
 * Tạo nội dung hiển thị bên trong mỗi thẻ sự kiện của FullCalendar bằng DOM API an toàn.
 * Bố cục theo hàng ngang gọn gàng: Mã môn - Tên môn + Phòng thi & Sĩ số.
 * @param {Record<string, any>} arg
 */
function renderCustomEventContent(arg) {
  if (typeof document === "undefined" || typeof document.createElement !== "function") {
    return null;
  }
  const props = (arg && arg.event && arg.event.extendedProps) || {};
  const roomText = Array.isArray(props.rooms) ? props.rooms.join(", ") : String(props.rooms || "");

  const wrapper = document.createElement("div");
  wrapper.className = "flex flex-col justify-center h-full px-1 py-0.5 leading-tight overflow-hidden";

  const titleEl = document.createElement("div");
  titleEl.className = "font-bold text-xs truncate";
  titleEl.textContent = props.ma_mon
    ? `${props.ma_mon} - ${props.ten_mon}`
    : (arg.event && arg.event.title) || "";

  const metaEl = document.createElement("div");
  metaEl.className = "text-[11px] opacity-90 truncate";
  metaEl.textContent = roomText
    ? `Phòng: ${roomText} (${props.so_luong_sv || 0} SV)`
    : props.khung_gio_ca
      ? `Ca ${props.stt_ca}: ${props.khung_gio_ca}`
      : "";

  wrapper.appendChild(titleEl);
  if (metaEl.textContent) {
    wrapper.appendChild(metaEl);
  }
  return { domNodes: [wrapper] };
}

/**
 * Trả về cấu hình khởi tạo FullCalendar với chế độ xem Tuần (timeGridWeek) & Tháng (dayGridMonth)
 * cùng tùy chọn gộp 4 hàng Ca thi (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00).
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
    slotMinTime: isShiftAxis ? "01:00:00" : "07:00:00",
    slotMaxTime: isShiftAxis ? "05:00:00" : "18:00:00",
    slotDuration: "01:00:00",
    slotLabelInterval: "01:00:00",
    slotLabelContent: (arg) => formatSlotLabelByMode(arg.date, slotMode),
    eventContent: (arg) => renderCustomEventContent(arg),
    expandRows: true,
    height: "auto",
    nowIndicator: false,
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
    events: buildFullCalendarEvents(SAMPLE_EXAM_EVENTS, slotMode),
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
 * Đồng bộ trạng thái ô chọn Tuần (timeGridWeek - Chia Ca / Theo Giờ) và nút Tháng (dayGridMonth).
 * @param {string} viewName
 */
function updateCalendarViewButtons(viewName) {
  const weekBtn = document.getElementById("btn-view-week");
  const monthBtn = document.getElementById("btn-view-month");
  const viewBadge = document.getElementById("calendar-view-badge");
  const rangeHeading = document.getElementById("calendar-current-range");
  const fcContainer = document.getElementById("admin-fullcalendar");

  const isMonth = viewName === "dayGridMonth";
  const isShiftOnly = viewName === "shiftGridWeek";
  const isWeek = !isMonth && !isShiftOnly;

  const activeWeekClass =
    "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition cursor-pointer";
  const inactiveWeekClass =
    "px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 focus:outline-none focus:ring-2 focus:ring-blue-600 transition cursor-pointer";
  const activeBtnClass =
    "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white transition cursor-pointer";
  const inactiveBtnClass =
    "px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:text-slate-900 transition cursor-pointer";

  if (weekBtn) {
    weekBtn.className = isWeek ? activeWeekClass : inactiveWeekClass;
    weekBtn.setAttribute("aria-pressed", isWeek ? "true" : "false");
    if (typeof weekBtn.value === "string" && weekBtn.value !== currentSlotMode) {
      weekBtn.value = currentSlotMode;
    }
  }
  if (monthBtn) {
    monthBtn.className = isMonth ? activeBtnClass : inactiveBtnClass;
    monthBtn.setAttribute("aria-pressed", isMonth ? "true" : "false");
  }

  if (fcContainer && fcContainer.classList) {
    fcContainer.classList.toggle("hidden", isShiftOnly);
    fcContainer.classList.toggle("is-shift-axis", currentSlotMode === "shift");
  }

  if (viewBadge) {
    viewBadge.textContent = isMonth ? "Chế độ xem: Tháng" : "Chế độ xem: Tuần";
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
 * Chuyển đổi tùy chọn trong ô dropdown Tuần:
 * - "shift": Tuần: Chia Ca (Ca 1-4) (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00)
 * - "hour": Tuần: Theo Giờ (07:00 - 18:00)
 * Đồng thời tự động chuyển lịch sang chế độ xem Tuần (timeGridWeek) nếu đang ở chế độ Tháng.
 * @param {string} mode
 */
function switchCalendarSlotMode(mode) {
  currentSlotMode = mode === "hour" ? "hour" : "shift";
  const weekSelect = document.getElementById("btn-view-week");
  if (weekSelect && typeof weekSelect.value === "string" && weekSelect.value !== currentSlotMode) {
    weekSelect.value = currentSlotMode;
  }

  if (currentCalendarView !== "timeGridWeek") {
    currentCalendarView = "timeGridWeek";
    if (adminCalendarInstance && typeof adminCalendarInstance.changeView === "function") {
      adminCalendarInstance.changeView("timeGridWeek");
    }
  }

  if (adminCalendarInstance && typeof adminCalendarInstance.setOption === "function") {
    const isShiftAxis = currentSlotMode === "shift";
    adminCalendarInstance.setOption("slotMinTime", isShiftAxis ? "01:00:00" : "07:00:00");
    adminCalendarInstance.setOption("slotMaxTime", isShiftAxis ? "05:00:00" : "18:00:00");
    adminCalendarInstance.setOption("slotDuration", "01:00:00");
    adminCalendarInstance.setOption("slotLabelInterval", "01:00:00");
    adminCalendarInstance.setOption("slotLabelContent", (arg) =>
      formatSlotLabelByMode(arg.date, currentSlotMode)
    );
  }

  filterCalendarEvents();
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
 * Xử lý khi người dùng chọn Năm học, Học kỳ hoặc Tuần từ 3 ô dropdown điều hướng.
 * @param {string} changedField ('year' | 'semester' | 'week')
 */
function handleAcademicPeriodChange(changedField = "week") {
  const yearSelect = document.getElementById("calendar-select-year");
  const semesterSelect = document.getElementById("calendar-select-semester");
  const weekSelect = document.getElementById("calendar-select-week");
  const rangeHeading = document.getElementById("calendar-current-range");

  const yearVal = yearSelect ? yearSelect.value : "2026-2027";
  const semesterVal = semesterSelect ? semesterSelect.value : "HK1";

  if (changedField === "semester" && weekSelect) {
    if (semesterVal === "HK2") {
      weekSelect.value = "2027-01-18";
    } else if (semesterVal === "HK1") {
      weekSelect.value = "2026-12-15";
    }
  }

  const targetDate = weekSelect && weekSelect.value ? weekSelect.value : "2026-12-15";
  if (adminCalendarInstance && typeof adminCalendarInstance.gotoDate === "function") {
    adminCalendarInstance.gotoDate(targetDate);
  }

  updateCalendarViewButtons(currentCalendarView);

  if (rangeHeading && weekSelect && weekSelect.options && weekSelect.selectedIndex >= 0) {
    const selectedOption = weekSelect.options[weekSelect.selectedIndex];
    const weekLabel = selectedOption ? selectedOption.text : targetDate;
    const semesterLabel =
      semesterVal === "HK2" ? "Học Kỳ 2" : semesterVal === "HK3" ? "Học Kỳ Hè" : "Học Kỳ 1";
    rangeHeading.textContent = `${semesterLabel} (${yearVal}) • Tuần: ${weekLabel}`;
  }

  return {
    year: yearVal,
    semester: semesterVal,
    weekDate: targetDate,
  };
}

/**
 * Điều hướng thời gian trên FullCalendar ('prev' | 'next' | 'today' hoặc ngày ISO).
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
  } else if (action && typeof adminCalendarInstance.gotoDate === "function") {
    adminCalendarInstance.gotoDate(action);
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
    const fcEvents = buildFullCalendarEvents(filtered, currentSlotMode);
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
