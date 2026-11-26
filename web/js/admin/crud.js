/**
 * Quản lý dữ liệu đầu vào Admin: chuyển sub-tab & Quản lý Sinh viên (UC03)
 * (web/js/admin/crud.js)
 */

let studentRecords = [
  { mssv: "22110001", ho_ten: "Nguyễn Văn An", email: "an.nv@univ.edu.vn", lop_sinh_hoat: "22CNTT1" },
  { mssv: "22110002", ho_ten: "Trần Thị Bình", email: "binh.tt@univ.edu.vn", lop_sinh_hoat: "22CNTT1" },
  { mssv: "22110003", ho_ten: "Lê Hoàng Cường", email: "cuong.lh@univ.edu.vn", lop_sinh_hoat: "22CNTT2" },
  { mssv: "22110004", ho_ten: "Phạm Minh Dung", email: "dung.pm@univ.edu.vn", lop_sinh_hoat: "22CNTT2" },
  { mssv: "22110399", ho_ten: "Bùi Thiên Phúc", email: "phuc.bt@univ.edu.vn", lop_sinh_hoat: "22CNTT1" },
];

let editingMssv = null;
let activeCrudEntity = "mon_hoc";
let pendingDeleteAction = null;

const CRUD_MODAL_IDS = [
  "course-crud-modal",
  "student-crud-modal",
  "exam-crud-modal",
  "room-crud-modal",
  "registration-crud-modal",
  "import-data-modal",
  "delete-confirm-modal",
];

const CRUD_HEADINGS = {
  ky_thi: "Quản lý Dữ liệu Đầu vào • Kỳ thi",
  mon_hoc: "Quản lý Dữ liệu Đầu vào • Môn học",
  sinh_vien: "Quản lý Dữ liệu Đầu vào • Quản lý Sinh viên",
  phong_thi: "Quản lý Dữ liệu Đầu vào • Phòng thi",
  dang_ky_thi: "Quản lý Dữ liệu Đầu vào • Đăng ký thi",
};

function setInputLockedState(inputEl, locked) {
  if (!inputEl) return;
  inputEl.readOnly = Boolean(locked);
  inputEl.classList.toggle("bg-slate-100", Boolean(locked));
  inputEl.classList.toggle("text-slate-500", Boolean(locked));
  inputEl.classList.toggle("cursor-not-allowed", Boolean(locked));
  inputEl.classList.toggle("bg-white", !locked);
}

function openCrudModal(modalId, focusInputId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.remove("hidden");
  document.body.classList.add("overflow-hidden");
  if (focusInputId) {
    const focusEl = document.getElementById(focusInputId);
    if (focusEl && typeof focusEl.focus === "function") {
      focusEl.focus();
    }
  }
}

function closeCrudModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.add("hidden");
  const anyOpen = CRUD_MODAL_IDS.some((id) => {
    const el = document.getElementById(id);
    return el && !el.classList.contains("hidden");
  });
  if (!anyOpen) {
    document.body.classList.remove("overflow-hidden");
  }
}

function closeAllCrudModals() {
  pendingDeleteAction = null;
  editingCourseCode = null;
  editingMssv = null;
  editingExamCode = null;
  editingRoomCode = null;
  editingRegistrationId = null;
  CRUD_MODAL_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
  });
  document.body.classList.remove("overflow-hidden");
}

function openDeleteAlert(title, message, onConfirm) {
  const titleEl = document.getElementById("delete-alert-title");
  const msgEl = document.getElementById("delete-alert-message");
  if (titleEl) titleEl.textContent = title;
  if (msgEl) msgEl.textContent = message;
  pendingDeleteAction = typeof onConfirm === "function" ? onConfirm : null;
  openCrudModal("delete-confirm-modal", "btn-cancel-delete");
}

function closeDeleteAlert() {
  pendingDeleteAction = null;
  closeCrudModal("delete-confirm-modal");
}

function confirmPendingDelete() {
  const action = pendingDeleteAction;
  closeDeleteAlert();
  if (typeof action === "function") {
    action();
  }
}

function handleCrudModalBackdropClick(event, modalId) {
  if (event && event.target === event.currentTarget) {
    if (modalId === "course-crud-modal") closeCourseModal();
    else if (modalId === "student-crud-modal") closeStudentModal();
    else if (modalId === "exam-crud-modal") closeExamModal();
    else if (modalId === "room-crud-modal") closeRoomModal();
    else if (modalId === "registration-crud-modal") closeRegistrationModal();
    else if (modalId === "import-data-modal") closeImportModal();
    else if (modalId === "delete-confirm-modal") closeDeleteAlert();
    else closeCrudModal(modalId);
  }
}

function switchCrudEntity(entity) {
  const validEntity = CRUD_HEADINGS[entity] ? entity : "mon_hoc";
  activeCrudEntity = validEntity;
  Object.keys(CRUD_HEADINGS).forEach((key) => {
    const el = document.getElementById(`crud-panel-${key}`);
    if (el) el.classList.toggle("hidden", key !== validEntity);
  });

  const headingEl = document.getElementById("crud-active-heading");
  if (headingEl) headingEl.textContent = CRUD_HEADINGS[validEntity];

  document.querySelectorAll("[data-crud-nav]").forEach((btn) => {
    const isActive = btn.getAttribute("data-crud-nav") === validEntity;
    btn.className = isActive
      ? "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-bold text-blue-700 border-b-2 border-blue-700 bg-white transition whitespace-nowrap"
      : "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-blue-700 hover:border-slate-300 border-b-2 border-transparent bg-white transition whitespace-nowrap";
    btn.setAttribute("aria-current", isActive ? "page" : "false");
  });

  if (validEntity === "sinh_vien") {
    renderStudentTable();
  } else if (validEntity === "ky_thi") {
    renderExamTable();
  } else if (validEntity === "mon_hoc") {
    renderCourseTable();
  } else if (validEntity === "phong_thi") {
    renderRoomTable();
  } else if (validEntity === "dang_ky_thi") {
    renderRegistrationTable();
  }
}

function createTableActionCell(onEdit, onDelete) {
  const tdAct = document.createElement("td");
  tdAct.className = "py-2.5 px-3 text-center whitespace-nowrap";

  const btnGroup = document.createElement("div");
  btnGroup.className = "inline-flex items-center justify-center gap-1.5";

  const btnEdit = document.createElement("button");
  btnEdit.type = "button";
  btnEdit.className =
    "px-2.5 py-1 rounded-md border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs transition";
  btnEdit.textContent = "Sửa";
  btnEdit.onclick = onEdit;

  const btnDel = document.createElement("button");
  btnDel.type = "button";
  btnDel.className =
    "px-2.5 py-1 rounded-md border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs transition";
  btnDel.textContent = "Xóa";
  btnDel.onclick = onDelete;

  btnGroup.append(btnEdit, btnDel);
  tdAct.appendChild(btnGroup);
  return tdAct;
}

function renderStudentTable() {
  const tbody = document.getElementById("student-table-body");
  const countEl = document.getElementById("student-count-label");
  const searchEl = document.getElementById("student-search-input");
  if (!tbody) return;

  const q = (searchEl ? searchEl.value : "").trim().toLowerCase();
  const filtered = q
    ? studentRecords.filter(
        (sv) =>
          sv.mssv.toLowerCase().includes(q) ||
          sv.ho_ten.toLowerCase().includes(q) ||
          sv.email.toLowerCase().includes(q) ||
          sv.lop_sinh_hoat.toLowerCase().includes(q)
      )
    : studentRecords;

  if (countEl) {
    countEl.textContent = `Danh sách Sinh viên (${filtered.length} sinh viên)`;
  }

  tbody.replaceChildren();
  filtered.forEach((sv) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdMssv = document.createElement("td");
    tdMssv.className = "py-2.5 px-3 text-center font-semibold text-slate-900 font-mono";
    tdMssv.textContent = sv.mssv;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = sv.ho_ten;

    const tdEmail = document.createElement("td");
    tdEmail.className = "py-2.5 px-3 text-slate-600";
    tdEmail.textContent = sv.email;

    const tdClass = document.createElement("td");
    tdClass.className = "py-2.5 px-3 text-center font-mono text-blue-700 font-semibold";
    tdClass.textContent = sv.lop_sinh_hoat;

    const tdAct = createTableActionCell(
      () => startEditStudent(sv.mssv),
      () => deleteStudent(sv.mssv)
    );
    tr.append(tdMssv, tdName, tdEmail, tdClass, tdAct);
    tbody.appendChild(tr);
  });
}

function resetStudentForm() {
  editingMssv = null;
  const form = document.getElementById("student-crud-form");
  const mssvInput = document.getElementById("sv-form-mssv");
  const errEl = document.getElementById("student-form-error");
  if (form) form.reset();
  setInputLockedState(mssvInput, false);
  if (errEl) errEl.textContent = "";
}

function openStudentModal() {
  resetStudentForm();
  const titleEl = document.getElementById("student-modal-title");
  const submitEl = document.getElementById("student-modal-submit");
  if (titleEl) titleEl.textContent = "Thêm Sinh viên mới";
  if (submitEl) submitEl.textContent = "+ Thêm Sinh viên";
  openCrudModal("student-crud-modal", "sv-form-mssv");
}

function closeStudentModal() {
  resetStudentForm();
  closeCrudModal("student-crud-modal");
}

function saveStudentForm(event) {
  event.preventDefault();
  const mssvInput = document.getElementById("sv-form-mssv");
  const nameInput = document.getElementById("sv-form-hoten");
  const emailInput = document.getElementById("sv-form-email");
  const classInput = document.getElementById("sv-form-lop");
  const errEl = document.getElementById("student-form-error");

  const mssv = mssvInput.value.trim().toUpperCase();
  const ho_ten = nameInput.value.trim();
  const email = emailInput.value.trim();
  const lop_sinh_hoat = classInput.value.trim().toUpperCase();
  if (!mssv || !ho_ten) {
    if (errEl) errEl.textContent = "Vui lòng nhập đầy đủ MSSV và họ tên sinh viên.";
    return;
  }

  const existingIdx = studentRecords.findIndex((s) => s.mssv === (editingMssv || mssv));
  const record = { mssv, ho_ten, email, lop_sinh_hoat };
  if (existingIdx >= 0) {
    studentRecords[existingIdx] = record;
  } else {
    studentRecords.unshift(record);
  }

  closeStudentModal();
  renderStudentTable();
  renderRegistrationTable();
}

function startEditStudent(mssv) {
  const sv = studentRecords.find((s) => s.mssv === mssv);
  if (!sv) return;
  editingMssv = mssv;
  const mssvInput = document.getElementById("sv-form-mssv");
  mssvInput.value = sv.mssv;
  setInputLockedState(mssvInput, true);
  document.getElementById("sv-form-hoten").value = sv.ho_ten;
  document.getElementById("sv-form-email").value = sv.email;
  document.getElementById("sv-form-lop").value = sv.lop_sinh_hoat;
  const errEl = document.getElementById("student-form-error");
  if (errEl) errEl.textContent = "";
  const titleEl = document.getElementById("student-modal-title");
  const submitEl = document.getElementById("student-modal-submit");
  if (titleEl) titleEl.textContent = "Chỉnh sửa Sinh viên";
  if (submitEl) submitEl.textContent = "Lưu thay đổi";
  openCrudModal("student-crud-modal", "sv-form-hoten");
}

function deleteStudent(mssv) {
  const sv = studentRecords.find((s) => s.mssv === mssv);
  const label = sv ? `${sv.mssv} - ${sv.ho_ten}` : mssv;
  openDeleteAlert(
    "Xác nhận xóa Sinh viên",
    `Bạn có chắc chắn muốn xóa sinh viên "${label}"? Hành động này không thể hoàn tác.`,
    () => {
      studentRecords = studentRecords.filter((s) => s.mssv !== mssv);
      if (editingMssv === mssv) closeStudentModal();
      renderStudentTable();
      renderRegistrationTable();
    }
  );
}

let examRecords = [
  {
    ma_ky_thi: "KTHK1_2026",
    ten_ky_thi: "Thi Cuối Kỳ HK1 (2026 - 2027)",
    ngay_bat_dau: "2026-12-15",
    ngay_ket_thuc: "2026-12-22",
    so_ca_moi_ngay: 4,
    trang_thai: "cong_bo",
  },
  {
    ma_ky_thi: "KTHK2_2025",
    ten_ky_thi: "Thi Cuối Kỳ HK2 (2025 - 2026)",
    ngay_bat_dau: "2026-06-10",
    ngay_ket_thuc: "2026-06-18",
    so_ca_moi_ngay: 4,
    trang_thai: "da_xep_lich",
  },
];

let editingExamCode = null;

const EXAM_STATUS_META = {
  khoi_tao: { label: "Khởi tạo", cls: "bg-slate-100 text-slate-700" },
  da_xep_lich: { label: "Đã xếp lịch", cls: "bg-amber-100 text-amber-800" },
  cong_bo: { label: "Công bố", cls: "bg-emerald-100 text-emerald-700" },
};

function formatDateVi(isoDate) {
  if (!isoDate || !isoDate.includes("-")) return isoDate || "";
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

function renderExamTable() {
  const tbody = document.getElementById("exam-table-body");
  const countEl = document.getElementById("exam-count-label");
  const searchEl = document.getElementById("exam-search-input");
  if (!tbody) return;

  const q = (searchEl ? searchEl.value : "").trim().toLowerCase();
  const filtered = q
    ? examRecords.filter(
        (kt) =>
          kt.ma_ky_thi.toLowerCase().includes(q) ||
          kt.ten_ky_thi.toLowerCase().includes(q) ||
          kt.trang_thai.toLowerCase().includes(q)
      )
    : examRecords;

  if (countEl) {
    countEl.textContent = `Danh sách Kỳ thi (${filtered.length} kỳ thi)`;
  }

  tbody.replaceChildren();
  filtered.forEach((kt) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdCode = document.createElement("td");
    tdCode.className = "py-2.5 px-3 text-center font-semibold text-slate-900 font-mono";
    tdCode.textContent = kt.ma_ky_thi;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = kt.ten_ky_thi;

    const tdRange = document.createElement("td");
    tdRange.className = "py-2.5 px-3 text-center text-slate-600";
    tdRange.textContent = `${formatDateVi(kt.ngay_bat_dau)} - ${formatDateVi(kt.ngay_ket_thuc)}`;

    const tdShifts = document.createElement("td");
    tdShifts.className = "py-2.5 px-3 text-center font-mono font-semibold text-blue-700";
    tdShifts.textContent = `${kt.so_ca_moi_ngay} ca/ngày`;

    const tdStatus = document.createElement("td");
    tdStatus.className = "py-2.5 px-3 text-center";
    const badge = document.createElement("span");
    const statusInfo = EXAM_STATUS_META[kt.trang_thai] || EXAM_STATUS_META.khoi_tao;
    badge.className = `px-2 py-0.5 rounded-full font-semibold ${statusInfo.cls}`;
    badge.textContent = statusInfo.label;
    tdStatus.appendChild(badge);

    const tdAct = createTableActionCell(
      () => startEditExam(kt.ma_ky_thi),
      () => deleteExam(kt.ma_ky_thi)
    );
    tr.append(tdCode, tdName, tdRange, tdShifts, tdStatus, tdAct);
    tbody.appendChild(tr);
  });
}

function resetExamForm() {
  editingExamCode = null;
  const form = document.getElementById("exam-crud-form");
  const codeInput = document.getElementById("exam-form-ma");
  const errEl = document.getElementById("exam-form-error");
  if (form) form.reset();
  setInputLockedState(codeInput, false);
  if (errEl) errEl.textContent = "";
}

function openExamModal() {
  resetExamForm();
  const titleEl = document.getElementById("exam-modal-title");
  const submitEl = document.getElementById("exam-modal-submit");
  if (titleEl) titleEl.textContent = "Thêm Kỳ thi mới";
  if (submitEl) submitEl.textContent = "+ Thêm Kỳ thi";
  openCrudModal("exam-crud-modal", "exam-form-ma");
}

function closeExamModal() {
  resetExamForm();
  closeCrudModal("exam-crud-modal");
}

function saveExamForm(event) {
  event.preventDefault();
  const codeInput = document.getElementById("exam-form-ma");
  const nameInput = document.getElementById("exam-form-ten");
  const startInput = document.getElementById("exam-form-start");
  const endInput = document.getElementById("exam-form-end");
  const shiftsInput = document.getElementById("exam-form-shifts");
  const statusInput = document.getElementById("exam-form-status");
  const errEl = document.getElementById("exam-form-error");

  const ma_ky_thi = codeInput.value.trim().toUpperCase();
  const ten_ky_thi = nameInput.value.trim();
  const ngay_bat_dau = startInput.value;
  const ngay_ket_thuc = endInput.value;
  const so_ca_moi_ngay = Number.parseInt(shiftsInput.value, 10);
  const trang_thai = statusInput.value;

  if (!ma_ky_thi || !ten_ky_thi || !ngay_bat_dau || !ngay_ket_thuc) {
    if (errEl) errEl.textContent = "Vui lòng điền đầy đủ thông tin kỳ thi.";
    return;
  }
  if (ngay_ket_thuc < ngay_bat_dau) {
    if (errEl) errEl.textContent = "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.";
    return;
  }
  if (!Number.isInteger(so_ca_moi_ngay) || so_ca_moi_ngay <= 0) {
    if (errEl) errEl.textContent = "Số ca mỗi ngày phải là số nguyên dương.";
    return;
  }

  const record = {
    ma_ky_thi,
    ten_ky_thi,
    ngay_bat_dau,
    ngay_ket_thuc,
    so_ca_moi_ngay,
    trang_thai,
  };

  const existingIdx = examRecords.findIndex((e) => e.ma_ky_thi === (editingExamCode || ma_ky_thi));
  if (existingIdx >= 0) {
    examRecords[existingIdx] = record;
  } else {
    examRecords.unshift(record);
  }

  closeExamModal();
  renderExamTable();
  renderRegistrationTable();
}

function startEditExam(maKyThi) {
  const kt = examRecords.find((e) => e.ma_ky_thi === maKyThi);
  if (!kt) return;
  editingExamCode = maKyThi;
  const codeInput = document.getElementById("exam-form-ma");
  codeInput.value = kt.ma_ky_thi;
  setInputLockedState(codeInput, true);
  document.getElementById("exam-form-ten").value = kt.ten_ky_thi;
  document.getElementById("exam-form-start").value = kt.ngay_bat_dau;
  document.getElementById("exam-form-end").value = kt.ngay_ket_thuc;
  document.getElementById("exam-form-shifts").value = String(kt.so_ca_moi_ngay);
  document.getElementById("exam-form-status").value = kt.trang_thai;
  const errEl = document.getElementById("exam-form-error");
  if (errEl) errEl.textContent = "";
  const titleEl = document.getElementById("exam-modal-title");
  const submitEl = document.getElementById("exam-modal-submit");
  if (titleEl) titleEl.textContent = "Chỉnh sửa Kỳ thi";
  if (submitEl) submitEl.textContent = "Lưu thay đổi";
  openCrudModal("exam-crud-modal", "exam-form-ten");
}

function deleteExam(maKyThi) {
  const kt = examRecords.find((e) => e.ma_ky_thi === maKyThi);
  const label = kt ? `${kt.ma_ky_thi} - ${kt.ten_ky_thi}` : maKyThi;
  openDeleteAlert(
    "Xác nhận xóa Kỳ thi",
    `Bạn có chắc chắn muốn xóa kỳ thi "${label}"? Hành động này không thể hoàn tác.`,
    () => {
      examRecords = examRecords.filter((e) => e.ma_ky_thi !== maKyThi);
      if (editingExamCode === maKyThi) closeExamModal();
      renderExamTable();
      renderRegistrationTable();
    }
  );
}

let courseRecords = [
  { ma_mon: "IT001", ten_mon: "Lý thuyết Đồ thị", thoi_luong_phut: 90, so_tin_chi: 3 },
  { ma_mon: "IT002", ten_mon: "Cấu trúc Dữ liệu & Giải thuật", thoi_luong_phut: 90, so_tin_chi: 4 },
  { ma_mon: "IT003", ten_mon: "Hệ Quản trị Cơ sở Dữ liệu PostgreSQL", thoi_luong_phut: 90, so_tin_chi: 3 },
  { ma_mon: "IT004", ten_mon: "Lập trình Web", thoi_luong_phut: 120, so_tin_chi: 4 },
  { ma_mon: "IT005", ten_mon: "An toàn & Bảo mật Thông tin", thoi_luong_phut: 90, so_tin_chi: 3 },
  { ma_mon: "IT006", ten_mon: "Trí tuệ Nhân tạo", thoi_luong_phut: 90, so_tin_chi: 3 },
  { ma_mon: "IT007", ten_mon: "Mạng Máy tính & Truyền thông", thoi_luong_phut: 90, so_tin_chi: 3 },
  { ma_mon: "IT008", ten_mon: "Toán Rời rạc & Tổ hợp", thoi_luong_phut: 90, so_tin_chi: 3 },
];

let editingCourseCode = null;

function renderCourseTable() {
  const tbody = document.getElementById("course-table-body");
  const countEl = document.getElementById("course-count-label");
  const searchEl = document.getElementById("course-search-input");
  if (!tbody) return;

  const q = (searchEl ? searchEl.value : "").trim().toLowerCase();
  const filtered = q
    ? courseRecords.filter(
        (mh) =>
          mh.ma_mon.toLowerCase().includes(q) ||
          mh.ten_mon.toLowerCase().includes(q)
      )
    : courseRecords;

  if (countEl) {
    countEl.textContent = `Danh mục Học phần / Môn thi (${filtered.length} môn học)`;
  }

  tbody.replaceChildren();
  filtered.forEach((mh) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdCode = document.createElement("td");
    tdCode.className = "py-2.5 px-3 text-center font-semibold text-slate-900 font-mono";
    tdCode.textContent = mh.ma_mon;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = mh.ten_mon;

    const tdDuration = document.createElement("td");
    tdDuration.className = "py-2.5 px-3 text-center text-slate-600";
    tdDuration.textContent = `${mh.thoi_luong_phut} phút`;

    const tdCredits = document.createElement("td");
    tdCredits.className = "py-2.5 px-3 text-center font-mono font-semibold text-blue-700";
    tdCredits.textContent = `${mh.so_tin_chi} TC`;

    const tdAct = createTableActionCell(
      () => startEditCourse(mh.ma_mon),
      () => deleteCourse(mh.ma_mon)
    );
    tr.append(tdCode, tdName, tdDuration, tdCredits, tdAct);
    tbody.appendChild(tr);
  });
}

function resetCourseForm() {
  editingCourseCode = null;
  const form = document.getElementById("course-crud-form");
  const codeInput = document.getElementById("course-form-ma");
  const errEl = document.getElementById("course-form-error");
  if (form) form.reset();
  setInputLockedState(codeInput, false);
  if (errEl) errEl.textContent = "";
}

function openCourseModal() {
  resetCourseForm();
  const titleEl = document.getElementById("course-modal-title");
  const submitEl = document.getElementById("course-modal-submit");
  if (titleEl) titleEl.textContent = "Thêm Môn học mới";
  if (submitEl) submitEl.textContent = "+ Thêm Môn học";
  openCrudModal("course-crud-modal", "course-form-ma");
}

function closeCourseModal() {
  resetCourseForm();
  closeCrudModal("course-crud-modal");
}

function saveCourseForm(event) {
  event.preventDefault();
  const codeInput = document.getElementById("course-form-ma");
  const nameInput = document.getElementById("course-form-ten");
  const durationInput = document.getElementById("course-form-duration");
  const creditsInput = document.getElementById("course-form-credits");
  const errEl = document.getElementById("course-form-error");

  const ma_mon = codeInput.value.trim().toUpperCase();
  const ten_mon = nameInput.value.trim();
  const thoi_luong_phut = Number.parseInt(durationInput.value, 10);
  const so_tin_chi = Number.parseInt(creditsInput.value, 10);

  if (!ma_mon || !ten_mon) {
    if (errEl) errEl.textContent = "Vui lòng nhập đầy đủ mã môn và tên học phần.";
    return;
  }
  if (!Number.isInteger(thoi_luong_phut) || thoi_luong_phut <= 0) {
    if (errEl) errEl.textContent = "Thời lượng thi phải là số nguyên dương.";
    return;
  }
  if (!Number.isInteger(so_tin_chi) || so_tin_chi <= 0) {
    if (errEl) errEl.textContent = "Số tín chỉ phải là số nguyên dương.";
    return;
  }

  const record = { ma_mon, ten_mon, thoi_luong_phut, so_tin_chi };
  const existingIdx = courseRecords.findIndex((c) => c.ma_mon === (editingCourseCode || ma_mon));
  if (existingIdx >= 0) {
    courseRecords[existingIdx] = record;
  } else {
    courseRecords.unshift(record);
  }

  closeCourseModal();
  renderCourseTable();
  renderRegistrationTable();
}

function startEditCourse(maMon) {
  const mh = courseRecords.find((c) => c.ma_mon === maMon);
  if (!mh) return;
  editingCourseCode = maMon;
  const codeInput = document.getElementById("course-form-ma");
  codeInput.value = mh.ma_mon;
  setInputLockedState(codeInput, true);
  document.getElementById("course-form-ten").value = mh.ten_mon;
  document.getElementById("course-form-duration").value = String(mh.thoi_luong_phut);
  document.getElementById("course-form-credits").value = String(mh.so_tin_chi);
  const errEl = document.getElementById("course-form-error");
  if (errEl) errEl.textContent = "";
  const titleEl = document.getElementById("course-modal-title");
  const submitEl = document.getElementById("course-modal-submit");
  if (titleEl) titleEl.textContent = "Chỉnh sửa Môn học";
  if (submitEl) submitEl.textContent = "Lưu thay đổi";
  openCrudModal("course-crud-modal", "course-form-ten");
}

function deleteCourse(maMon) {
  const mh = courseRecords.find((c) => c.ma_mon === maMon);
  const label = mh ? `${mh.ma_mon} - ${mh.ten_mon}` : maMon;
  openDeleteAlert(
    "Xác nhận xóa Môn học",
    `Bạn có chắc chắn muốn xóa môn học "${label}"? Hành động này không thể hoàn tác.`,
    () => {
      courseRecords = courseRecords.filter((c) => c.ma_mon !== maMon);
      if (editingCourseCode === maMon) closeCourseModal();
      renderCourseTable();
      renderRegistrationTable();
    }
  );
}

let roomRecords = [
  { ma_phong: "A101", ten_phong: "Phòng thi A101", suc_chua: 60, toa_nha: "Nhà A", dang_su_dung: true },
  { ma_phong: "A102", ten_phong: "Phòng thi A102", suc_chua: 60, toa_nha: "Nhà A", dang_su_dung: true },
  { ma_phong: "B201", ten_phong: "Phòng thi B201", suc_chua: 45, toa_nha: "Nhà B", dang_su_dung: true },
  { ma_phong: "C302", ten_phong: "Phòng máy C302", suc_chua: 40, toa_nha: "Nhà C", dang_su_dung: false },
];

let editingRoomCode = null;

function renderRoomTable() {
  const tbody = document.getElementById("room-table-body");
  const countEl = document.getElementById("room-count-label");
  const searchEl = document.getElementById("room-search-input");
  if (!tbody) return;

  const q = (searchEl ? searchEl.value : "").trim().toLowerCase();
  const filtered = q
    ? roomRecords.filter(
        (p) =>
          p.ma_phong.toLowerCase().includes(q) ||
          p.ten_phong.toLowerCase().includes(q) ||
          (p.toa_nha || "").toLowerCase().includes(q)
      )
    : roomRecords;

  if (countEl) {
    countEl.textContent = `Danh mục Phòng thi & Sức chứa (${filtered.length} phòng)`;
  }

  tbody.replaceChildren();
  filtered.forEach((p) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdCode = document.createElement("td");
    tdCode.className = "py-2.5 px-3 text-center font-semibold text-slate-900 font-mono";
    tdCode.textContent = p.ma_phong;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = p.ten_phong;

    const tdCap = document.createElement("td");
    tdCap.className = "py-2.5 px-3 text-center font-mono font-semibold text-blue-700";
    tdCap.textContent = `${p.suc_chua} chỗ`;

    const tdBuilding = document.createElement("td");
    tdBuilding.className = "py-2.5 px-3 text-center text-slate-600";
    tdBuilding.textContent = p.toa_nha || "—";

    const tdStatus = document.createElement("td");
    tdStatus.className = "py-2.5 px-3 text-center";
    const badge = document.createElement("span");
    badge.className = p.dang_su_dung
      ? "px-2 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-700"
      : "px-2 py-0.5 rounded-full font-semibold bg-amber-100 text-amber-800";
    badge.textContent = p.dang_su_dung ? "Đang sử dụng" : "Tạm bảo trì";
    tdStatus.appendChild(badge);

    const tdAct = createTableActionCell(
      () => startEditRoom(p.ma_phong),
      () => deleteRoom(p.ma_phong)
    );
    tr.append(tdCode, tdName, tdCap, tdBuilding, tdStatus, tdAct);
    tbody.appendChild(tr);
  });
}

function resetRoomForm() {
  editingRoomCode = null;
  const form = document.getElementById("room-crud-form");
  const codeInput = document.getElementById("room-form-ma");
  const errEl = document.getElementById("room-form-error");
  if (form) form.reset();
  setInputLockedState(codeInput, false);
  if (errEl) errEl.textContent = "";
}

function openRoomModal() {
  resetRoomForm();
  const titleEl = document.getElementById("room-modal-title");
  const submitEl = document.getElementById("room-modal-submit");
  if (titleEl) titleEl.textContent = "Thêm Phòng thi mới";
  if (submitEl) submitEl.textContent = "+ Thêm Phòng thi";
  openCrudModal("room-crud-modal", "room-form-ma");
}

function closeRoomModal() {
  resetRoomForm();
  closeCrudModal("room-crud-modal");
}

function saveRoomForm(event) {
  event.preventDefault();
  const codeInput = document.getElementById("room-form-ma");
  const nameInput = document.getElementById("room-form-ten");
  const capInput = document.getElementById("room-form-capacity");
  const buildingInput = document.getElementById("room-form-building");
  const activeInput = document.getElementById("room-form-active");
  const errEl = document.getElementById("room-form-error");

  const ma_phong = codeInput.value.trim().toUpperCase();
  const ten_phong = nameInput.value.trim();
  const suc_chua = Number.parseInt(capInput.value, 10);
  const toa_nha = buildingInput ? buildingInput.value.trim() : "";
  const dang_su_dung = activeInput ? activeInput.value !== "false" : true;

  if (!ma_phong || !ten_phong) {
    if (errEl) errEl.textContent = "Vui lòng nhập đầy đủ mã phòng và tên phòng thi.";
    return;
  }
  if (!Number.isInteger(suc_chua) || suc_chua <= 0 || suc_chua > 10000) {
    if (errEl) errEl.textContent = "Sức chứa phòng thi phải là số nguyên từ 1 đến 10000.";
    return;
  }

  const record = { ma_phong, ten_phong, suc_chua, toa_nha, dang_su_dung };
  const existingIdx = roomRecords.findIndex((p) => p.ma_phong === (editingRoomCode || ma_phong));
  if (existingIdx >= 0) {
    roomRecords[existingIdx] = record;
  } else {
    roomRecords.unshift(record);
  }

  closeRoomModal();
  renderRoomTable();
}

function startEditRoom(maPhong) {
  const p = roomRecords.find((r) => r.ma_phong === maPhong);
  if (!p) return;
  editingRoomCode = maPhong;
  const codeInput = document.getElementById("room-form-ma");
  codeInput.value = p.ma_phong;
  setInputLockedState(codeInput, true);
  document.getElementById("room-form-ten").value = p.ten_phong;
  document.getElementById("room-form-capacity").value = String(p.suc_chua);
  const buildingInput = document.getElementById("room-form-building");
  if (buildingInput) buildingInput.value = p.toa_nha || "";
  const activeInput = document.getElementById("room-form-active");
  if (activeInput) activeInput.value = p.dang_su_dung ? "true" : "false";
  const errEl = document.getElementById("room-form-error");
  if (errEl) errEl.textContent = "";
  const titleEl = document.getElementById("room-modal-title");
  const submitEl = document.getElementById("room-modal-submit");
  if (titleEl) titleEl.textContent = "Chỉnh sửa Phòng thi";
  if (submitEl) submitEl.textContent = "Lưu thay đổi";
  openCrudModal("room-crud-modal", "room-form-ten");
}

function deleteRoom(maPhong) {
  const p = roomRecords.find((r) => r.ma_phong === maPhong);
  const label = p ? `${p.ma_phong} - ${p.ten_phong}` : maPhong;
  openDeleteAlert(
    "Xác nhận xóa Phòng thi",
    `Bạn có chắc chắn muốn xóa phòng thi "${label}"? Hành động này không thể hoàn tác.`,
    () => {
      roomRecords = roomRecords.filter((r) => r.ma_phong !== maPhong);
      if (editingRoomCode === maPhong) closeRoomModal();
      renderRoomTable();
    }
  );
}

let registrationRecords = [
  { id: 1, ma_ky_thi: "KTHK1_2026", ma_mon: "IT001", mssv: "22110399" },
  { id: 2, ma_ky_thi: "KTHK1_2026", ma_mon: "IT001", mssv: "22110001" },
  { id: 3, ma_ky_thi: "KTHK1_2026", ma_mon: "IT001", mssv: "22110002" },
  { id: 4, ma_ky_thi: "KTHK1_2026", ma_mon: "IT002", mssv: "22110399" },
  { id: 5, ma_ky_thi: "KTHK1_2026", ma_mon: "IT002", mssv: "22110003" },
  { id: 6, ma_ky_thi: "KTHK1_2026", ma_mon: "IT003", mssv: "22110001" },
  { id: 7, ma_ky_thi: "KTHK1_2026", ma_mon: "IT003", mssv: "22110004" },
  { id: 8, ma_ky_thi: "KTHK1_2026", ma_mon: "IT004", mssv: "22110002" },
  { id: 9, ma_ky_thi: "KTHK1_2026", ma_mon: "IT005", mssv: "22110399" },
];

let nextRegistrationId = 10;
let editingRegistrationId = null;

function enrichRegistrationRecord(reg) {
  const course = courseRecords.find((c) => c.ma_mon === reg.ma_mon);
  const student = studentRecords.find((s) => s.mssv === reg.mssv);
  return {
    ...reg,
    ten_mon: course ? course.ten_mon : "Học phần chưa cập nhật",
    ho_ten: student ? student.ho_ten : "Sinh viên chưa cập nhật",
    lop_sinh_hoat: student ? student.lop_sinh_hoat : "—",
  };
}

function populateRegistrationFilterOptions() {
  const filterEl = document.getElementById("registration-course-filter");
  if (!filterEl) return;

  const currentVal = filterEl.value || "ALL";
  filterEl.replaceChildren();

  const optAll = document.createElement("option");
  optAll.value = "ALL";
  optAll.textContent = "Tất cả môn học";
  filterEl.appendChild(optAll);

  courseRecords.forEach((course) => {
    const opt = document.createElement("option");
    opt.value = course.ma_mon;
    opt.textContent = `${course.ma_mon} - ${course.ten_mon}`;
    filterEl.appendChild(opt);
  });

  const exists = currentVal === "ALL" || courseRecords.some((c) => c.ma_mon === currentVal);
  filterEl.value = exists ? currentVal : "ALL";
}

function renderRegistrationTable() {
  const tbody = document.getElementById("registration-table-body");
  const countEl = document.getElementById("registration-count-label");
  const searchEl = document.getElementById("registration-search-input");
  const filterEl = document.getElementById("registration-course-filter");
  if (!tbody) return;

  populateRegistrationFilterOptions();
  const selectedCourse = filterEl ? filterEl.value : "ALL";

  const q = (searchEl ? searchEl.value : "").trim().toLowerCase();
  const enriched = registrationRecords.map(enrichRegistrationRecord);

  const filtered = enriched.filter((item) => {
    if (selectedCourse && selectedCourse !== "ALL" && item.ma_mon !== selectedCourse) {
      return false;
    }
    if (!q) return true;
    return (
      item.ma_ky_thi.toLowerCase().includes(q) ||
      item.ma_mon.toLowerCase().includes(q) ||
      item.ten_mon.toLowerCase().includes(q) ||
      item.mssv.toLowerCase().includes(q) ||
      item.ho_ten.toLowerCase().includes(q) ||
      item.lop_sinh_hoat.toLowerCase().includes(q)
    );
  });

  if (countEl) {
    if (selectedCourse && selectedCourse !== "ALL") {
      countEl.textContent = `Danh sách Sinh viên đăng ký môn (${filtered.length} sinh viên)`;
    } else {
      countEl.textContent = `Danh sách Đăng ký dự thi theo Môn học (${filtered.length} lượt đăng ký)`;
    }
  }

  tbody.replaceChildren();
  if (filtered.length === 0) {
    const emptyTr = document.createElement("tr");
    const emptyTd = document.createElement("td");
    emptyTd.colSpan = 7;
    emptyTd.className = "py-6 px-3 text-center text-xs text-slate-500";
    emptyTd.textContent = "Không có lượt đăng ký dự thi nào phù hợp.";
    emptyTr.appendChild(emptyTd);
    tbody.appendChild(emptyTr);
    return;
  }

  filtered.forEach((item) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdExam = document.createElement("td");
    tdExam.className = "py-2.5 px-3 text-center font-mono text-slate-600 font-semibold";
    tdExam.textContent = item.ma_ky_thi;

    const tdCourseCode = document.createElement("td");
    tdCourseCode.className = "py-2.5 px-3 text-center font-mono font-semibold text-blue-700";
    tdCourseCode.textContent = item.ma_mon;

    const tdCourseName = document.createElement("td");
    tdCourseName.className = "py-2.5 px-3 font-medium text-slate-800";
    tdCourseName.textContent = item.ten_mon;

    const tdMssv = document.createElement("td");
    tdMssv.className = "py-2.5 px-3 text-center font-semibold text-slate-900 font-mono";
    tdMssv.textContent = item.mssv;

    const tdStudentName = document.createElement("td");
    tdStudentName.className = "py-2.5 px-3";
    tdStudentName.textContent = item.ho_ten;

    const tdClass = document.createElement("td");
    tdClass.className = "py-2.5 px-3 text-center font-mono text-blue-700 font-semibold";
    tdClass.textContent = item.lop_sinh_hoat;

    const tdAct = createTableActionCell(
      () => startEditRegistration(item.id),
      () => deleteRegistration(item.id)
    );
    tr.append(tdExam, tdCourseCode, tdCourseName, tdMssv, tdStudentName, tdClass, tdAct);
    tbody.appendChild(tr);
  });
}

function ensureSelectOption(selectEl, value, fallbackLabel) {
  if (!selectEl || !value) return;
  const options = Array.from(selectEl.options || selectEl.children || []);
  const exists = options.some((opt) => opt.value === value);
  if (!exists) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = fallbackLabel || `${value} (Đã xóa khỏi danh mục)`;
    selectEl.appendChild(opt);
  }
}

function populateRegistrationFormSelects() {
  const examSelect = document.getElementById("reg-form-ky-thi");
  const courseSelect = document.getElementById("reg-form-ma-mon");
  const studentSelect = document.getElementById("reg-form-mssv");

  if (examSelect) {
    examSelect.replaceChildren();
    examRecords.forEach((kt) => {
      const opt = document.createElement("option");
      opt.value = kt.ma_ky_thi;
      opt.textContent = `${kt.ma_ky_thi} - ${kt.ten_ky_thi}`;
      examSelect.appendChild(opt);
    });
  }

  if (courseSelect) {
    courseSelect.replaceChildren();
    courseRecords.forEach((mh) => {
      const opt = document.createElement("option");
      opt.value = mh.ma_mon;
      opt.textContent = `${mh.ma_mon} - ${mh.ten_mon}`;
      courseSelect.appendChild(opt);
    });
  }

  if (studentSelect) {
    studentSelect.replaceChildren();
    studentRecords.forEach((sv) => {
      const opt = document.createElement("option");
      opt.value = sv.mssv;
      opt.textContent = `${sv.mssv} - ${sv.ho_ten} (${sv.lop_sinh_hoat})`;
      studentSelect.appendChild(opt);
    });
  }
}

function resetRegistrationForm() {
  editingRegistrationId = null;
  populateRegistrationFormSelects();
  const form = document.getElementById("registration-crud-form");
  const errEl = document.getElementById("registration-form-error");
  if (form) form.reset();
  if (errEl) errEl.textContent = "";
}

function openRegistrationModal() {
  resetRegistrationForm();
  const filterEl = document.getElementById("registration-course-filter");
  const courseSelect = document.getElementById("reg-form-ma-mon");
  if (filterEl && filterEl.value && filterEl.value !== "ALL" && courseSelect) {
    courseSelect.value = filterEl.value;
  }
  const titleEl = document.getElementById("registration-modal-title");
  const submitEl = document.getElementById("registration-modal-submit");
  if (titleEl) titleEl.textContent = "Thêm Đăng ký thi mới";
  if (submitEl) submitEl.textContent = "+ Thêm Đăng ký thi";
  openCrudModal("registration-crud-modal", "reg-form-ma-mon");
}

function closeRegistrationModal() {
  resetRegistrationForm();
  closeCrudModal("registration-crud-modal");
}

function saveRegistrationForm(event) {
  event.preventDefault();
  const examSelect = document.getElementById("reg-form-ky-thi");
  const courseSelect = document.getElementById("reg-form-ma-mon");
  const studentSelect = document.getElementById("reg-form-mssv");
  const errEl = document.getElementById("registration-form-error");

  const ma_ky_thi = (examSelect ? examSelect.value : "").trim().toUpperCase();
  const ma_mon = (courseSelect ? courseSelect.value : "").trim().toUpperCase();
  const mssv = (studentSelect ? studentSelect.value : "").trim().toUpperCase();

  if (!ma_ky_thi || !ma_mon || !mssv) {
    if (errEl) errEl.textContent = "Vui lòng chọn đầy đủ kỳ thi, môn học và sinh viên đăng ký.";
    return;
  }

  const duplicate = registrationRecords.find(
    (r) =>
      r.ma_ky_thi === ma_ky_thi &&
      r.ma_mon === ma_mon &&
      r.mssv === mssv &&
      r.id !== editingRegistrationId
  );
  if (duplicate) {
    if (errEl) {
      errEl.textContent = `Sinh viên ${mssv} đã đăng ký môn ${ma_mon} trong kỳ thi ${ma_ky_thi}.`;
    }
    return;
  }

  if (editingRegistrationId !== null) {
    const idx = registrationRecords.findIndex((r) => r.id === editingRegistrationId);
    if (idx >= 0) {
      registrationRecords[idx] = { id: editingRegistrationId, ma_ky_thi, ma_mon, mssv };
    }
  } else {
    registrationRecords.unshift({
      id: nextRegistrationId++,
      ma_ky_thi,
      ma_mon,
      mssv,
    });
  }

  closeRegistrationModal();
  renderRegistrationTable();
}

function startEditRegistration(regId) {
  const reg = registrationRecords.find((r) => r.id === regId);
  if (!reg) return;
  populateRegistrationFormSelects();
  editingRegistrationId = regId;
  const examSelect = document.getElementById("reg-form-ky-thi");
  const courseSelect = document.getElementById("reg-form-ma-mon");
  const studentSelect = document.getElementById("reg-form-mssv");
  ensureSelectOption(examSelect, reg.ma_ky_thi, `${reg.ma_ky_thi} (Kỳ thi đã xóa)`);
  ensureSelectOption(courseSelect, reg.ma_mon, `${reg.ma_mon} (Môn học đã xóa)`);
  ensureSelectOption(studentSelect, reg.mssv, `${reg.mssv} (Sinh viên đã xóa)`);
  if (examSelect) examSelect.value = reg.ma_ky_thi;
  if (courseSelect) courseSelect.value = reg.ma_mon;
  if (studentSelect) studentSelect.value = reg.mssv;

  const errEl = document.getElementById("registration-form-error");
  if (errEl) errEl.textContent = "";
  const titleEl = document.getElementById("registration-modal-title");
  const submitEl = document.getElementById("registration-modal-submit");
  if (titleEl) titleEl.textContent = "Chỉnh sửa Đăng ký thi";
  if (submitEl) submitEl.textContent = "Lưu thay đổi";
  openCrudModal("registration-crud-modal", "reg-form-ma-mon");
}

function deleteRegistration(regId) {
  const reg = registrationRecords.find((r) => r.id === regId);
  const item = reg ? enrichRegistrationRecord(reg) : null;
  const label = item
    ? `${item.mssv} (${item.ho_ten}) - Môn ${item.ma_mon}`
    : String(regId);
  openDeleteAlert(
    "Xác nhận xóa Đăng ký thi",
    `Bạn có chắc chắn muốn xóa đăng ký dự thi của sinh viên "${label}"? Hành động này không thể hoàn tác.`,
    () => {
      registrationRecords = registrationRecords.filter((r) => r.id !== regId);
      if (editingRegistrationId === regId) closeRegistrationModal();
      renderRegistrationTable();
    }
  );
}

const IMPORT_MAX_BYTES = 5 * 1024 * 1024;
let selectedImportFile = null;

function resetImportModalState() {
  selectedImportFile = null;
  const form = document.getElementById("import-data-form");
  const fileInput = document.getElementById("import-file-input");
  const selectedEl = document.getElementById("import-selected-file");
  const errEl = document.getElementById("import-form-error");
  const statusEl = document.getElementById("import-form-status");
  if (form) form.reset();
  if (fileInput) fileInput.value = "";
  if (selectedEl) {
    selectedEl.textContent = "";
    selectedEl.classList.add("hidden");
  }
  if (errEl) errEl.textContent = "";
  if (statusEl) {
    statusEl.textContent = "";
    statusEl.classList.add("hidden");
  }
}

function openImportModal(entity) {
  resetImportModalState();
  const selectEl = document.getElementById("import-entity-select");
  const target = entity && CRUD_HEADINGS[entity] ? entity : activeCrudEntity;
  if (selectEl && CRUD_HEADINGS[target]) {
    selectEl.value = target;
  }
  openCrudModal("import-data-modal", "import-entity-select");
}

function closeImportModal() {
  resetImportModalState();
  closeCrudModal("import-data-modal");
}

function triggerImportFilePicker() {
  const fileInput = document.getElementById("import-file-input");
  if (fileInput) fileInput.click();
}

function selectImportFile(file) {
  const selectedEl = document.getElementById("import-selected-file");
  const errEl = document.getElementById("import-form-error");
  const statusEl = document.getElementById("import-form-status");
  if (errEl) errEl.textContent = "";
  if (statusEl) {
    statusEl.textContent = "";
    statusEl.classList.add("hidden");
  }
  if (!file) {
    selectedImportFile = null;
    if (selectedEl) {
      selectedEl.textContent = "";
      selectedEl.classList.add("hidden");
    }
    return;
  }

  const lowerName = String(file.name || "").toLowerCase();
  if (!lowerName.endsWith(".xlsx") && !lowerName.endsWith(".csv")) {
    selectedImportFile = null;
    if (selectedEl) selectedEl.classList.add("hidden");
    if (errEl) errEl.textContent = "Chỉ hỗ trợ định dạng tệp .xlsx hoặc .csv.";
    return;
  }
  if (file.size > IMPORT_MAX_BYTES) {
    selectedImportFile = null;
    if (selectedEl) selectedEl.classList.add("hidden");
    if (errEl) errEl.textContent = "Dung lượng tệp vượt quá giới hạn tối đa 5MB.";
    return;
  }

  selectedImportFile = file;
  if (selectedEl) {
    const sizeKb = Math.max(1, Math.round(file.size / 1024));
    selectedEl.textContent = `Đã chọn: ${file.name} (${sizeKb} KB)`;
    selectedEl.classList.remove("hidden");
  }
}

function handleImportFileInputChange(event) {
  const file = event && event.target && event.target.files ? event.target.files[0] : null;
  selectImportFile(file);
}

function submitImportForm(event) {
  event.preventDefault();
  const errEl = document.getElementById("import-form-error");
  const statusEl = document.getElementById("import-form-status");
  const selectEl = document.getElementById("import-entity-select");
  if (errEl) errEl.textContent = "";

  if (!selectedImportFile) {
    if (errEl) errEl.textContent = "Vui lòng chọn tệp .xlsx hoặc .csv trước khi nạp dữ liệu.";
    return;
  }

  const entityLabel =
    selectEl && selectEl.selectedOptions && selectEl.selectedOptions[0]
      ? selectEl.selectedOptions[0].textContent
      : "Dữ liệu";
  if (statusEl) {
    statusEl.textContent = `Đã tiếp nhận tệp "${selectedImportFile.name}" cho danh mục ${entityLabel}. Sẵn sàng đồng bộ qua API Import Transaction ACID.`;
    statusEl.classList.remove("hidden");
  }
}

function sanitizeCsvCell(value) {
  const str = String(value == null ? "" : value);
  const safe = /^[=+\-@\t\r]/.test(str) ? `'${str}` : str;
  return `"${safe.replace(/"/g, '""')}"`;
}

function exportSelectedEntityData() {
  const selectEl = document.getElementById("import-entity-select");
  const statusEl = document.getElementById("import-form-status");
  const errEl = document.getElementById("import-form-error");
  if (errEl) errEl.textContent = "";

  const entity = (selectEl && selectEl.value) || activeCrudEntity || "mon_hoc";
  let headers = [];
  let rows = [];

  if (entity === "mon_hoc") {
    headers = ["ma_mon", "ten_mon", "thoi_luong_phut", "so_tin_chi"];
    rows = courseRecords.map((r) => [r.ma_mon, r.ten_mon, r.thoi_luong_phut, r.so_tin_chi]);
  } else if (entity === "sinh_vien") {
    headers = ["mssv", "ho_ten", "email", "lop_sinh_hoat"];
    rows = studentRecords.map((r) => [r.mssv, r.ho_ten, r.email, r.lop_sinh_hoat]);
  } else if (entity === "ky_thi") {
    headers = ["ma_ky_thi", "ten_ky_thi", "ngay_bat_dau", "ngay_ket_thuc", "so_ca_moi_ngay", "trang_thai"];
    rows = examRecords.map((r) => [
      r.ma_ky_thi,
      r.ten_ky_thi,
      r.ngay_bat_dau,
      r.ngay_ket_thuc,
      r.so_ca_moi_ngay,
      r.trang_thai,
    ]);
  } else if (entity === "phong_thi") {
    headers = ["ma_phong", "ten_phong", "suc_chua", "toa_nha", "dang_su_dung"];
    rows = roomRecords.map((r) => [
      r.ma_phong,
      r.ten_phong,
      r.suc_chua,
      r.toa_nha || "",
      r.dang_su_dung ? "true" : "false",
    ]);
  } else if (entity === "dang_ky_thi") {
    headers = ["ma_ky_thi", "ma_mon", "ten_mon", "mssv", "ho_ten", "lop_sinh_hoat"];
    rows = registrationRecords.map((r) => {
      const item = enrichRegistrationRecord(r);
      return [item.ma_ky_thi, item.ma_mon, item.ten_mon, item.mssv, item.ho_ten, item.lop_sinh_hoat];
    });
  } else {
    if (statusEl) {
      statusEl.textContent = "Đã sẵn sàng xuất file Excel khi đồng bộ dữ liệu từ máy chủ.";
      statusEl.classList.remove("hidden");
    }
    return;
  }

  const csvLines = [headers, ...rows].map((row) => row.map(sanitizeCsvCell).join(",")).join("\r\n");
  const blob = new Blob(["\uFEFF" + csvLines], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${entity}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);

  if (statusEl) {
    statusEl.textContent = `Đã xuất tệp ${entity}.csv (${rows.length} bản ghi).`;
    statusEl.classList.remove("hidden");
  }
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAllCrudModals();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const entity = new URLSearchParams(window.location.search).get("entity");
  if (entity && CRUD_HEADINGS[entity]) {
    switchCrudEntity(entity);
  } else {
    renderCourseTable();
    renderStudentTable();
    renderExamTable();
    renderRoomTable();
    renderRegistrationTable();
  }

  const dropzone = document.getElementById("import-dropzone");
  if (dropzone) {
    dropzone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        triggerImportFilePicker();
      }
    });
    dropzone.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropzone.classList.add("border-blue-500", "bg-blue-100/60");
    });
    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("border-blue-500", "bg-blue-100/60");
    });
    dropzone.addEventListener("drop", (event) => {
      event.preventDefault();
      dropzone.classList.remove("border-blue-500", "bg-blue-100/60");
      const file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
      selectImportFile(file);
    });
  }
});
