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
  ky_thi: "Quản lý Dữ liệu Đầu vào • Kỳ thi (UC02)",
  mon_hoc: "Quản lý Dữ liệu Đầu vào • Môn học (UC04)",
  sinh_vien: "Quản lý Dữ liệu Đầu vào • Quản lý Sinh viên (UC03)",
  phong_thi: "Quản lý Dữ liệu Đầu vào • Phòng thi (UC06)",
  dang_ky_thi: "Quản lý Dữ liệu Đầu vào • Đăng ký thi (UC05)",
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

document.addEventListener("DOMContentLoaded", () => {
  const entity = new URLSearchParams(window.location.search).get("entity");
  if (entity && CRUD_HEADINGS[entity]) {
    switchCrudEntity(entity);
  } else {
    renderStudentTable();
  }
});
