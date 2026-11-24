/**
 * Điều khiển Layout Shell chuẩn Figma cho Admin Dashboard (web/js/admin/layout.js)
 */

const TAB_TITLES = {
  "tab-crud": "02. Quản lý Dữ liệu & Import Excel (UC02-07)",
  "tab-graph": "03. Đồ thị Xung đột & Xếp lịch DSatur (UC08-09)",
  "tab-calendar": "04. Lịch thi Toàn trường FullCalendar (UC10)",
  "tab-stats": "05. Thống kê & Phân tích Đồ thị (UC13-14)",
};

function switchAdminTab(tabId) {
  const sections = document.querySelectorAll(".admin-tab-section");
  if (!sections.length) return;

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
        "admin-nav-btn w-full flex items-center px-3.5 py-2.5 rounded-lg text-sm font-semibold bg-slate-100 text-slate-900 transition text-left";
    } else {
      btn.className =
        "admin-nav-btn w-full flex items-center px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition text-left";
    }
  });

  const titleEl = document.getElementById("admin-page-title");
  if (titleEl && TAB_TITLES[tabId]) {
    titleEl.textContent = TAB_TITLES[tabId];
  }
}

function applyHashTab() {
  const hash = window.location.hash.replace("#", "");
  if (hash && TAB_TITLES[hash]) {
    switchAdminTab(hash);
  }
}

window.addEventListener("hashchange", applyHashTab);
document.addEventListener("DOMContentLoaded", applyHashTab);
