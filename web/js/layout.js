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

function navigateByRole(role) {
  if (role === "sinh_vien" && !window.location.pathname.endsWith("/student.html")) {
    window.location.href = "/student.html";
  } else if (role === "admin" && window.location.pathname.endsWith("/student.html")) {
    window.location.href = "/index.html";
  }
}

// Tự động điều hướng sang student.html nếu truy cập với ?role=sinh_vien
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const role = params.get("role");
  if (role === "sinh_vien" || role === "admin") {
    navigateByRole(role);
  }
});
