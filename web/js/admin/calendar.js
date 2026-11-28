/**
 * Khởi tạo & Điều khiển Lịch thi Toàn trường trên FullCalendar (UC10 UI — TV4 Ngày 4 & Ngày 5)
 * File: web/js/admin/calendar.js
 * Hỗ trợ:
 * - Chuyển đổi chế độ xem: Tuần (timeGridWeek) & Tháng (dayGridMonth)
 * - Hiển thị 15 sự kiện mẫu (môn thi, thời gian ca thi, phòng thi, số lượng SV) với 4 bảng màu phân biệt
 *   theo ca thi / màu đồ thị (Ca 1..Ca 4).
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
    ten_mon: "Lý thuyết Đồ thị",
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
    ten_mon: "Trí tuệ Nhân tạo",
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
    ten_mon: "Lập trình Web",
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
    ten_mon: "Hệ Quản trị Cơ sở Dữ liệu PostgreSQL",
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

let adminCalendarInstance = null;
let currentCalendarView = "timeGridWeek";
let activeFilteredEvents = [...SAMPLE_EXAM_EVENTS];
let layoutSyncTimerId = null;

/**
 * Tự động thu nhỏ các cột ngày không có môn thi (76px) để nhường không gian cho các cột ngày có môn thi.
 * Hoạt động đồng nhất trên cả bảng Tuần (timeGridWeek) và bảng Tháng (dayGridMonth).
 * @param {Array<Record<string, any>>} eventsList
 */
function adjustCalendarColumnWidths(eventsList = activeFilteredEvents) {
  const calendarEl = document.getElementById("admin-fullcalendar");
  if (!calendarEl || typeof calendarEl.querySelectorAll !== "function") return null;

  const headerCells = Array.from(calendarEl.querySelectorAll(".fc-col-header-cell"));
  if (headerCells.length === 0) return null;

  const numCols = headerCells.length;
  const datesWithExams = new Set(
    (eventsList || []).map((ev) => String(ev.ngay_thi || String(ev.start || "").slice(0, 10)))
  );

  const isMonthView = currentCalendarView === "dayGridMonth";
  const colHasExam = new Array(numCols).fill(false);

  if (isMonthView) {
    // Ở bảng Tháng, quét toàn bộ các hàng tuần trong .fc-daygrid-body theo chỉ số cột (0..numCols-1)
    const weekRows = Array.from(calendarEl.querySelectorAll(".fc-daygrid-body tbody tr"));
    weekRows.forEach((row) => {
      const cells = Array.from(row.querySelectorAll("td[data-date]"));
      let rowHasExam = false;
      cells.forEach((cell, idx) => {
        if (idx >= numCols) return;
        const dateStr = cell.getAttribute("data-date");
        if (dateStr && datesWithExams.has(dateStr)) {
          colHasExam[idx] = true;
          rowHasExam = true;
        }
      });
      if (row.classList) {
        row.classList.toggle("is-empty-week-row", !rowHasExam);
      }
    });
  } else {
    headerCells.forEach((cell, idx) => {
      const dateStr = cell.getAttribute("data-date");
      if (dateStr && datesWithExams.has(dateStr)) {
        colHasExam[idx] = true;
      }
    });
  }

  const activeCount = colHasExam.filter(Boolean).length;
  const emptyCount = numCols - activeCount;
  const shouldAdjust = activeCount > 0 && emptyCount > 0;
  const emptyWidthCss = "76px";
  const activeWidthCss = shouldAdjust
    ? `calc((100% - ${emptyCount * 76}px) / ${activeCount})`
    : "";

  const widthForCol = (idx) => (shouldAdjust ? (colHasExam[idx] ? activeWidthCss : emptyWidthCss) : "");

  // 1. Áp dụng độ rộng cho hàng tiêu đề Thứ (.fc-col-header-cell)
  headerCells.forEach((cell, idx) => {
    if (cell.style) cell.style.width = widthForCol(idx);
    if (cell.classList) {
      cell.classList.toggle("is-empty-day-col", shouldAdjust && !colHasExam[idx]);
      cell.classList.toggle("is-active-day-col", shouldAdjust && colHasExam[idx]);
    }
  });

  // 2. Áp dụng độ rộng cho các bảng thân lịch (cả Tuần lẫn Tháng) và đồng bộ <colgroup>
  const bodyTables = Array.from(
    calendarEl.querySelectorAll(
      ".fc-col-header, .fc-timegrid-cols table, .fc-daygrid-body table"
    )
  );
  bodyTables.forEach((tbl) => {
    if (!tbl || typeof tbl.querySelectorAll !== "function") return;
    const cols = Array.from(tbl.querySelectorAll("colgroup col"));
    if (cols.length >= numCols) {
      const offset = cols.length - numCols;
      for (let idx = 0; idx < numCols; idx += 1) {
        const colEl = cols[offset + idx];
        if (colEl && colEl.style) colEl.style.width = widthForCol(idx);
      }
    }

    const rows = Array.from(tbl.querySelectorAll("tbody tr"));
    rows.forEach((row) => {
      const cells = Array.from(row.querySelectorAll("td[data-date]"));
      if (cells.length === numCols) {
        cells.forEach((cell, idx) => {
          if (cell.style) cell.style.width = widthForCol(idx);
          if (cell.classList) {
            cell.classList.toggle("is-empty-day-col", shouldAdjust && !colHasExam[idx]);
            cell.classList.toggle("is-active-day-col", shouldAdjust && colHasExam[idx]);
          }
        });
      }
    });
  });

  return {
    numCols,
    activeCount,
    emptyCount,
    collapsed: shouldAdjust,
  };
}

/**
 * Gọi đồng bộ độ rộng cột ngay lập tức và sau nhịp render tiếp theo của trình duyệt.
 * Hủy lịch đồng bộ cũ trước khi đặt lịch mới để tránh race condition khi gõ tìm kiếm nhanh.
 */
function scheduleCalendarLayoutSync(eventsList = activeFilteredEvents) {
  adjustCalendarColumnWidths(eventsList);
  if (typeof setTimeout === "function") {
    if (layoutSyncTimerId !== null && typeof clearTimeout === "function") {
      clearTimeout(layoutSyncTimerId);
    }
    layoutSyncTimerId = setTimeout(() => {
      layoutSyncTimerId = null;
      adjustCalendarColumnWidths(activeFilteredEvents);
    }, 0);
  }
}

/**
 * Định dạng nhãn trục giờ của FullCalendar theo 4 hàng Ca thi cố định (Ca 1..Ca 4).
 * Dùng duck-typing getTime() thay vì instanceof Date để hoạt động an toàn cross-realm.
 * @param {Date} dateObj
 * @param {string} mode
 */
function formatSlotLabelByMode(dateObj, mode = "shift") {
  if (!dateObj || typeof dateObj.getTime !== "function" || Number.isNaN(dateObj.getTime())) {
    return "";
  }
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
 * Tính số lượng môn thi tối đa trong cùng một ô (Ngày × Ca) để đồng bộ kích thước mọi thẻ môn thi bằng nhau
 * và tự động giãn chiều cao hàng Ca mà không bị nhồi nhét.
 * @param {Array<Record<string, any>>} rawEvents
 */
function getMaxCoursesPerShiftSlot(rawEvents = SAMPLE_EXAM_EVENTS) {
  const counts = {};
  let maxInOneSlot = 1;
  (rawEvents || []).forEach((item) => {
    const key = `${item.ngay_thi}_ca_${item.stt_ca}`;
    counts[key] = (counts[key] || 0) + 1;
    if (counts[key] > maxInOneSlot) {
      maxInOneSlot = counts[key];
    }
  });
  return Math.max(2, maxInOneSlot);
}

/**
 * Cập nhật chiều cao hàng Ca (--https-shift-row-height) tỉ lệ thuận với số môn tối đa trong 1 ca
 * để mỗi thẻ môn thi luôn giữ kích thước cố định nhỏ gọn (~4.5rem / thẻ) bằng nhau.
 * @param {Array<Record<string, any>>} rawEvents
 */
function syncUniformShiftRowHeight(rawEvents = activeFilteredEvents) {
  const calendarEl = document.getElementById("admin-fullcalendar");
  const uniformCapacity = getMaxCoursesPerShiftSlot(rawEvents);
  const rowHeightRem = (uniformCapacity * 5.25).toFixed(2);
  if (calendarEl && calendarEl.style && typeof calendarEl.style.setProperty === "function") {
    calendarEl.style.setProperty("--https-shift-row-height", `${rowHeightRem}rem`);
  }
  return uniformCapacity;
}

/**
 * Chuyển đổi danh sách ca thi thành định dạng Event Object chuẩn của FullCalendar.
 * Ở chế độ "shift", mọi môn thi (dù ngày đó có 1 môn hay nhiều môn) đều chiếm đúng 1 đơn vị chiều cao
 * chuẩn bằng nhau (60 / uniformCapacity phút), giúp tất cả các ô môn thi to bằng nhau 100% và không bị nhồi nhét.
 * @param {Array<Record<string, any>>} rawEvents
 * @param {string} mode
 */
function buildFullCalendarEvents(rawEvents = SAMPLE_EXAM_EVENTS, mode = "shift") {
  const groupIndices = {};
  const uniformCapacity = syncUniformShiftRowHeight(rawEvents);

  return rawEvents.map((item) => {
    const palette = SHIFT_COLOR_PALETTE[item.stt_ca] || SHIFT_COLOR_PALETTE[1];
    const compactSlot = SHIFT_COMPACT_TIME_RANGES[item.stt_ca] || SHIFT_COMPACT_TIME_RANGES[1];
    const roomText = Array.isArray(item.rooms) ? item.rooms.join(", ") : String(item.rooms || "");

    const key = `${item.ngay_thi}_ca_${item.stt_ca}`;
    const indexInSlot = groupIndices[key] || 0;
    groupIndices[key] = indexInSlot + 1;

    let eventStart = item.start;
    let eventEnd = item.end;

    if (mode === "shift") {
      const slotMinutes = 60;
      const uniformSliceMinutes = slotMinutes / uniformCapacity;
      const startTime = addMinutesToTimeString(
        compactSlot.startSlot,
        indexInSlot * uniformSliceMinutes
      );
      const endTime = addMinutesToTimeString(
        compactSlot.startSlot,
        (indexInSlot + 1) * uniformSliceMinutes
      );
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
  wrapper.className =
    "flex flex-col justify-center h-full px-1 py-0.5 leading-snug whitespace-normal break-words";

  const tdCourseName = document.createElement("div");
  tdCourseName.className = "font-bold text-xs whitespace-normal break-words";
  tdCourseName.textContent = props.ma_mon
    ? `${props.ma_mon} - ${props.ten_mon}`
    : (arg.event && arg.event.title) || "";

  const shiftText = props.khung_gio_ca
    ? `Ca ${props.stt_ca}: ${props.khung_gio_ca}`
    : props.stt_ca
      ? `Ca ${props.stt_ca}`
      : "";

  wrapper.appendChild(tdCourseName);

  if (shiftText) {
    const shiftEl = document.createElement("div");
    shiftEl.className = "text-[11px] opacity-90 whitespace-normal break-words mt-0.5";
    shiftEl.textContent = shiftText;
    wrapper.appendChild(shiftEl);
  }

  if (roomText) {
    const roomEl = document.createElement("div");
    roomEl.className = "text-[11px] opacity-90 whitespace-normal break-words mt-0.5";
    roomEl.textContent = `Phòng: ${roomText} (${props.so_luong_sv || 0} SV)`;
    wrapper.appendChild(roomEl);
  }

  return { domNodes: [wrapper] };
}

/**
 * Trả về cấu hình khởi tạo FullCalendar với chế độ xem Tuần (timeGridWeek) & Tháng (dayGridMonth)
 * cùng 4 hàng Ca thi cố định (Ca 1: 7h30-9h00, Ca 2: 9h30-11h00, Ca 3: 13h30-15h00, Ca 4: 15h30-17h00).
 * @param {string} initialView
 */
function getCalendarViewConfig(initialView = "timeGridWeek") {
  const safeView = initialView === "dayGridMonth" ? "dayGridMonth" : "timeGridWeek";

  return {
    initialView: safeView,
    initialDate: "2026-12-15",
    locale: "vi",
    firstDay: 1,
    hiddenDays: [0],
    allDaySlot: false,
    slotMinTime: "01:00:00",
    slotMaxTime: "05:00:00",
    slotDuration: "01:00:00",
    slotLabelInterval: "01:00:00",
    slotEventOverlap: false,
    slotLabelContent: (arg) => formatSlotLabelByMode(arg.date, "shift"),
    eventDisplay: "block",
    eventContent: (arg) => renderCustomEventContent(arg),
    datesSet: () => {
      scheduleCalendarLayoutSync(activeFilteredEvents);
    },
    expandRows: false,
    height: "auto",
    nowIndicator: false,
    dayMaxEvents: false,
    headerToolbar: false,
    views: {
      timeGridWeek: {
        type: "timeGrid",
        duration: { weeks: 1 },
        buttonText: "Tuần",
      },
      dayGridMonth: {
        type: "dayGrid",
        duration: { months: 1 },
        buttonText: "Tháng",
      },
    },
    events: buildFullCalendarEvents(SAMPLE_EXAM_EVENTS, "shift"),
  };
}

/**
 * Đồng bộ trạng thái nút Tuần (timeGridWeek) / Tháng (dayGridMonth) và khung chọn Tuần/Tháng.
 * @param {string} viewName
 */
function updateCalendarViewButtons(viewName) {
  const weekBtn = document.getElementById("btn-view-week");
  const monthBtn = document.getElementById("btn-view-month");
  const weekSelectGroup = document.getElementById("calendar-week-select-group");
  const monthSelectGroup = document.getElementById("calendar-month-select-group");
  const viewBadge = document.getElementById("calendar-view-badge");
  const rangeHeading = document.getElementById("calendar-current-range");
  const fcContainer = document.getElementById("admin-fullcalendar");

  const isMonth = viewName === "dayGridMonth";
  const isWeek = !isMonth;

  if (weekSelectGroup && weekSelectGroup.classList) {
    weekSelectGroup.classList.toggle("hidden", isMonth);
  }
  if (monthSelectGroup && monthSelectGroup.classList) {
    monthSelectGroup.classList.toggle("hidden", !isMonth);
  }

  const activeBtnClass =
    "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white transition cursor-pointer";
  const inactiveBtnClass =
    "px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:text-slate-900 transition cursor-pointer";

  if (weekBtn) {
    weekBtn.className = isWeek ? activeBtnClass : inactiveBtnClass;
    weekBtn.setAttribute("aria-pressed", isWeek ? "true" : "false");
  }
  if (monthBtn) {
    monthBtn.className = isMonth ? activeBtnClass : inactiveBtnClass;
    monthBtn.setAttribute("aria-pressed", isMonth ? "true" : "false");
  }

  if (fcContainer && fcContainer.classList) {
    fcContainer.classList.add("is-shift-axis");
  }

  if (viewBadge) {
    viewBadge.textContent = isMonth ? "Chế độ xem: Tháng" : "Chế độ xem: Tuần";
  }

  if (rangeHeading) {
    if (adminCalendarInstance && adminCalendarInstance.view && adminCalendarInstance.view.title) {
      rangeHeading.textContent = adminCalendarInstance.view.title;
    } else {
      rangeHeading.textContent = isMonth
        ? "Tháng 12 / 2026 (Toàn bộ đợt thi Học kỳ 1)"
        : "Tuần thi: Thứ Hai 15/12/2026 - Thứ Bảy 20/12/2026";
    }
  }
}

/**
 * Chuyển đổi chế độ hiển thị của FullCalendar giữa Tuần (timeGridWeek) và Tháng (dayGridMonth).
 * @param {string} viewName
 */
function switchCalendarView(viewName) {
  const targetView = viewName === "dayGridMonth" ? "dayGridMonth" : "timeGridWeek";
  currentCalendarView = targetView;

  if (adminCalendarInstance && typeof adminCalendarInstance.changeView === "function") {
    adminCalendarInstance.changeView(targetView);
  }
  updateCalendarViewButtons(targetView);
  scheduleCalendarLayoutSync(activeFilteredEvents);
  return targetView;
}

/**
 * Xử lý khi người dùng chọn Năm học, Học kỳ, Tuần hoặc Tháng từ các ô dropdown điều hướng.
 * @param {string} changedField ('year' | 'semester' | 'week' | 'month')
 */
function handleAcademicPeriodChange(changedField = "week") {
  const yearSelect = document.getElementById("calendar-select-year");
  const semesterSelect = document.getElementById("calendar-select-semester");
  const weekSelect = document.getElementById("calendar-select-week");
  const monthSelect = document.getElementById("calendar-select-month");
  const rangeHeading = document.getElementById("calendar-current-range");

  const yearVal = yearSelect ? yearSelect.value : "2026-2027";
  const semesterVal = semesterSelect ? semesterSelect.value : "HK1";
  const isMonthView = currentCalendarView === "dayGridMonth";

  if (changedField === "semester") {
    if (semesterVal === "HK2") {
      if (weekSelect) weekSelect.value = "2027-01-18";
      if (monthSelect) monthSelect.value = "2027-01-01";
    } else if (semesterVal === "HK3") {
      if (monthSelect) monthSelect.value = "2027-05-01";
    } else {
      if (weekSelect) weekSelect.value = "2026-12-15";
      if (monthSelect) monthSelect.value = "2026-12-15";
    }
  }

  let targetDate = "2026-12-15";
  if (changedField === "month" || isMonthView) {
    targetDate = monthSelect && monthSelect.value ? monthSelect.value : "2026-12-15";
  } else {
    targetDate = weekSelect && weekSelect.value ? weekSelect.value : "2026-12-15";
  }

  if (adminCalendarInstance && typeof adminCalendarInstance.gotoDate === "function") {
    adminCalendarInstance.gotoDate(targetDate);
  }

  updateCalendarViewButtons(currentCalendarView);

  const semesterLabel =
    semesterVal === "HK2" ? "Học kỳ 2" : semesterVal === "HK3" ? "Học kỳ hè" : "Học kỳ 1";

  if (
    rangeHeading &&
    isMonthView &&
    monthSelect &&
    monthSelect.options &&
    monthSelect.selectedIndex >= 0
  ) {
    const selectedMonthOpt = monthSelect.options[monthSelect.selectedIndex];
    const monthLabel = selectedMonthOpt ? selectedMonthOpt.text : targetDate;
    rangeHeading.textContent = `${semesterLabel} (${yearVal}) • ${monthLabel}`;
  } else if (
    rangeHeading &&
    weekSelect &&
    weekSelect.options &&
    weekSelect.selectedIndex >= 0
  ) {
    const selectedOption = weekSelect.options[weekSelect.selectedIndex];
    const weekLabel = selectedOption ? selectedOption.text : targetDate;
    rangeHeading.textContent = `${semesterLabel} (${yearVal}) • Tuần: ${weekLabel}`;
  }

  return {
    year: yearVal,
    semester: semesterVal,
    weekDate: targetDate,
  };
}

/**
 * Điền nhanh từ khóa gợi ý vào ô tìm kiếm và lọc sự kiện trên FullCalendar.
 * @param {string} keyword
 */
function applyCalendarSearchKeyword(keyword) {
  const searchInput = document.getElementById("calendar-search-input");
  if (searchInput) {
    searchInput.value = String(keyword || "").trim();
  }
  return filterCalendarEvents();
}

/**
 * Tìm kiếm và lọc danh sách sự kiện trên FullCalendar
 * theo từ khóa (mã môn, tên môn, phòng thi, ca thi).
 */
function filterCalendarEvents() {
  const searchInput = document.getElementById("calendar-search-input");
  const queryRaw = searchInput ? String(searchInput.value || "").trim() : "";
  const query = queryRaw.toLowerCase();

  const filtered = SAMPLE_EXAM_EVENTS.filter((item) => {
    if (!query) return true;
    const palette = SHIFT_COLOR_PALETTE[item.stt_ca] || SHIFT_COLOR_PALETTE[1];
    const roomStr = Array.isArray(item.rooms) ? item.rooms.join(" ") : String(item.rooms || "");
    const shiftStr = `ca ${item.stt_ca} ${palette.label}`;
    const searchableText =
      `${item.ma_mon} ${item.ten_mon} ${roomStr} ${shiftStr}`.toLowerCase();

    return searchableText.includes(query);
  });

  activeFilteredEvents = filtered;

  if (adminCalendarInstance && typeof adminCalendarInstance.removeAllEvents === "function") {
    adminCalendarInstance.removeAllEvents();
    const fcEvents = buildFullCalendarEvents(filtered, "shift");
    fcEvents.forEach((ev) => adminCalendarInstance.addEvent(ev));
  }

  scheduleCalendarLayoutSync(filtered);
  return filtered;
}

/**
 * Đặt lại ô tìm kiếm về trạng thái mặc định.
 */
function resetCalendarFilters() {
  const searchInput = document.getElementById("calendar-search-input");
  if (searchInput) searchInput.value = "";
  return filterCalendarEvents();
}

/**
 * Khởi tạo FullCalendar trên phần tử #admin-fullcalendar.
 */
function initExamFullCalendar() {
  const calendarEl = document.getElementById("admin-fullcalendar");
  if (!calendarEl) return null;

  updateCalendarViewButtons(currentCalendarView);

  if (!window.FullCalendar || typeof window.FullCalendar.Calendar !== "function") {
    return null;
  }

  const config = getCalendarViewConfig(currentCalendarView);
  adminCalendarInstance = new window.FullCalendar.Calendar(calendarEl, config);
  adminCalendarInstance.render();
  updateCalendarViewButtons(currentCalendarView);
  scheduleCalendarLayoutSync(activeFilteredEvents);
  return adminCalendarInstance;
}

document.addEventListener("DOMContentLoaded", () => {
  initExamFullCalendar();
});
