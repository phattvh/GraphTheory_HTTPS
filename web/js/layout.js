/**
 * Điều khiển Layout Shell cho Admin Dashboard & Student Portal (TV4 - Ngày 1)
 */

const TAB_TITLES = {
  "tab-crud": "02. Quản lý Dữ liệu & Import Excel (UC02 - UC07)",
  "tab-graph": "03. Đồ thị Xung đột & Xếp lịch DSatur (UC08 - UC09)",
  "tab-calendar": "04. Lịch thi Toàn trường FullCalendar (UC10)",
  "tab-stats": "05. Thống kê & Phân tích Đồ thị (UC13 - UC14)",
};

function switchAdminTab(tabId) {
  const sections = document.querySelectorAll(".admin-tab-section");
  sections.forEach((sec) => {
    if (sec.id === tabId) {
      sec.classList.remove("hidden");
    } else {
      sec.classList.add("hidden");
    }
  });

  const navButtons = document.querySelectorAll(".admin-nav-btn");
  navButtons.forEach((btn) => {
    if (btn.getAttribute("data-tab") === tabId) {
      btn.className =
        "admin-nav-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-semibold bg-blue-50 text-blue-700 transition text-left";
    } else {
      btn.className =
        "admin-nav-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition text-left";
    }
  });

  const titleEl = document.getElementById("admin-page-title");
  if (titleEl && TAB_TITLES[tabId]) {
    titleEl.textContent = TAB_TITLES[tabId];
  }
}

function switchRoleLayout(role) {
  const adminShell = document.getElementById("admin-layout-shell");
  const studentShell = document.getElementById("student-layout-shell");
  const btnAdmin = document.getElementById("btn-switch-admin");
  const btnStudent = document.getElementById("btn-switch-student");

  if (!adminShell || !studentShell) return;

  if (role === "sinh_vien") {
    adminShell.classList.add("hidden");
    studentShell.classList.remove("hidden");
    if (btnStudent && btnAdmin) {
      btnStudent.className = "px-2.5 py-1 rounded bg-blue-600 text-white font-semibold transition";
      btnAdmin.className = "px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium transition";
    }
  } else {
    studentShell.classList.add("hidden");
    adminShell.classList.remove("hidden");
    if (btnStudent && btnAdmin) {
      btnAdmin.className = "px-2.5 py-1 rounded bg-blue-600 text-white font-semibold transition";
      btnStudent.className = "px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium transition";
    }
  }
}

// Tự động kiểm tra query param ?role=sinh_vien nếu có
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("role") === "sinh_vien") {
    switchRoleLayout("sinh_vien");
  }
});
