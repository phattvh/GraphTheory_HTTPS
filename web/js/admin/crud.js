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

const CRUD_HEADINGS = {
  ky_thi: "Quản lý Dữ liệu Đầu vào • Kỳ thi",
  mon_hoc: "Quản lý Dữ liệu Đầu vào • Môn học",
  sinh_vien: "Quản lý Dữ liệu Đầu vào • Quản lý Sinh viên",
  phong_thi: "Quản lý Dữ liệu Đầu vào • Phòng thi",
  dang_ky_thi: "Quản lý Dữ liệu Đầu vào • Đăng ký thi",
};

function switchCrudEntity(entity) {
  const validEntity = CRUD_HEADINGS[entity] ? entity : "mon_hoc";
  Object.keys(CRUD_HEADINGS).forEach((key) => {
    const el = document.getElementById(`crud-panel-${key}`);
    if (el) el.classList.toggle("hidden", key !== validEntity);
  });

  const headingEl = document.getElementById("crud-active-heading");
  if (headingEl) headingEl.textContent = CRUD_HEADINGS[validEntity];

  document.querySelectorAll("[data-crud-nav]").forEach((btn) => {
    const isActive = btn.getAttribute("data-crud-nav") === validEntity;
    btn.className = isActive
      ? "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold text-blue-700 border-b-2 border-blue-600 bg-white transition whitespace-nowrap"
      : "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-white/60 border-b-2 border-transparent transition whitespace-nowrap";
  });

  if (validEntity === "sinh_vien") {
    renderStudentTable();
  } else if (validEntity === "ky_thi") {
    renderExamTable();
  }
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

  tbody.innerHTML = "";
  filtered.forEach((sv) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const tdMssv = document.createElement("td");
    tdMssv.className = "py-2.5 px-3 font-semibold text-slate-900";
    tdMssv.textContent = sv.mssv;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = sv.ho_ten;

    const tdEmail = document.createElement("td");
    tdEmail.className = "py-2.5 px-3 text-slate-600";
    tdEmail.textContent = sv.email;

    const tdClass = document.createElement("td");
    tdClass.className = "py-2.5 px-3 font-mono text-blue-700 font-semibold";
    tdClass.textContent = sv.lop_sinh_hoat;

    const tdAct = document.createElement("td");
    tdAct.className = "py-2.5 px-3 text-right space-x-2";

    const btnEdit = document.createElement("button");
    btnEdit.type = "button";
    btnEdit.className = "font-medium text-blue-600 hover:underline";
    btnEdit.textContent = "Sửa";
    btnEdit.onclick = () => startEditStudent(sv.mssv);

    const btnDel = document.createElement("button");
    btnDel.type = "button";
    btnDel.className = "font-medium text-red-600 hover:underline";
    btnDel.textContent = "Xóa";
    btnDel.onclick = () => deleteStudent(sv.mssv);

    tdAct.append(btnEdit, document.createTextNode(" • "), btnDel);
    tr.append(tdMssv, tdName, tdEmail, tdClass, tdAct);
    tbody.appendChild(tr);
  });
}

function saveStudentForm(event) {
  event.preventDefault();
  const mssvInput = document.getElementById("sv-form-mssv");
  const nameInput = document.getElementById("sv-form-hoten");
  const emailInput = document.getElementById("sv-form-email");
  const classInput = document.getElementById("sv-form-lop");

  const mssv = mssvInput.value.trim().toUpperCase();
  const ho_ten = nameInput.value.trim();
  const email = emailInput.value.trim();
  const lop_sinh_hoat = classInput.value.trim().toUpperCase();
  if (!mssv || !ho_ten) return;

  const existingIdx = studentRecords.findIndex((s) => s.mssv === (editingMssv || mssv));
  const record = { mssv, ho_ten, email, lop_sinh_hoat };
  if (existingIdx >= 0) {
    studentRecords[existingIdx] = record;
  } else {
    studentRecords.unshift(record);
  }

  editingMssv = null;
  mssvInput.readOnly = false;
  event.target.reset();
  renderStudentTable();
}

function startEditStudent(mssv) {
  const sv = studentRecords.find((s) => s.mssv === mssv);
  if (!sv) return;
  editingMssv = mssv;
  const mssvInput = document.getElementById("sv-form-mssv");
  mssvInput.value = sv.mssv;
  mssvInput.readOnly = true;
  document.getElementById("sv-form-hoten").value = sv.ho_ten;
  document.getElementById("sv-form-email").value = sv.email;
  document.getElementById("sv-form-lop").value = sv.lop_sinh_hoat;
}

function deleteStudent(mssv) {
  studentRecords = studentRecords.filter((s) => s.mssv !== mssv);
  renderStudentTable();
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
    tdCode.className = "py-2.5 px-3 font-semibold text-slate-900 font-mono";
    tdCode.textContent = kt.ma_ky_thi;

    const tdName = document.createElement("td");
    tdName.className = "py-2.5 px-3";
    tdName.textContent = kt.ten_ky_thi;

    const tdRange = document.createElement("td");
    tdRange.className = "py-2.5 px-3 text-slate-600";
    tdRange.textContent = `${formatDateVi(kt.ngay_bat_dau)} - ${formatDateVi(kt.ngay_ket_thuc)}`;

    const tdShifts = document.createElement("td");
    tdShifts.className = "py-2.5 px-3 font-mono font-semibold text-blue-700";
    tdShifts.textContent = `${kt.so_ca_moi_ngay} ca/ngày`;

    const tdStatus = document.createElement("td");
    tdStatus.className = "py-2.5 px-3";
    const badge = document.createElement("span");
    const statusInfo = EXAM_STATUS_META[kt.trang_thai] || EXAM_STATUS_META.khoi_tao;
    badge.className = `px-2 py-0.5 rounded-full font-semibold ${statusInfo.cls}`;
    badge.textContent = statusInfo.label;
    tdStatus.appendChild(badge);

    const tdAct = document.createElement("td");
    tdAct.className = "py-2.5 px-3 text-right space-x-2";

    const btnEdit = document.createElement("button");
    btnEdit.type = "button";
    btnEdit.className = "font-medium text-blue-600 hover:underline";
    btnEdit.textContent = "Sửa";
    btnEdit.onclick = () => startEditExam(kt.ma_ky_thi);

    const btnDel = document.createElement("button");
    btnDel.type = "button";
    btnDel.className = "font-medium text-red-600 hover:underline";
    btnDel.textContent = "Xóa";
    btnDel.onclick = () => deleteExam(kt.ma_ky_thi);

    tdAct.append(btnEdit, document.createTextNode(" • "), btnDel);
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
  if (codeInput) codeInput.readOnly = false;
  if (errEl) errEl.textContent = "";
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

  resetExamForm();
  renderExamTable();
}

function startEditExam(maKyThi) {
  const kt = examRecords.find((e) => e.ma_ky_thi === maKyThi);
  if (!kt) return;
  editingExamCode = maKyThi;
  const codeInput = document.getElementById("exam-form-ma");
  codeInput.value = kt.ma_ky_thi;
  codeInput.readOnly = true;
  document.getElementById("exam-form-ten").value = kt.ten_ky_thi;
  document.getElementById("exam-form-start").value = kt.ngay_bat_dau;
  document.getElementById("exam-form-end").value = kt.ngay_ket_thuc;
  document.getElementById("exam-form-shifts").value = String(kt.so_ca_moi_ngay);
  document.getElementById("exam-form-status").value = kt.trang_thai;
  const errEl = document.getElementById("exam-form-error");
  if (errEl) errEl.textContent = "";
}

function deleteExam(maKyThi) {
  examRecords = examRecords.filter((e) => e.ma_ky_thi !== maKyThi);
  if (editingExamCode === maKyThi) resetExamForm();
  renderExamTable();
}

document.addEventListener("DOMContentLoaded", () => {
  const entity = new URLSearchParams(window.location.search).get("entity");
  if (entity && CRUD_HEADINGS[entity]) {
    switchCrudEntity(entity);
  } else {
    renderStudentTable();
    renderExamTable();
  }
});
