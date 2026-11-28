/**
 * Dùng chung Header 2 tầng & Right Collapsible Drawer cho 4 trang Admin
 * (index.html, graph.html, calendar.html, stats.html)
 * Toàn bộ biểu tượng sử dụng bộ Lucide Icons (https://lucide.dev/) dạng inline SVG.
 */

const LUCIDE_ICON_PATHS = {
  database:
    '<ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5V19A9 3 0 0 0 21 19V5"></path><path d="M3 12A9 3 0 0 0 21 12"></path>',
  "share-2":
    '<circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"></line><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"></line>',
  "calendar-days":
    '<path d="M8 2v4"></path><path d="M16 2v4"></path><rect width="18" height="18" x="3" y="4" rx="2"></rect><path d="M3 10h18"></path><path d="M8 14h.01"></path><path d="M12 14h.01"></path><path d="M16 14h.01"></path><path d="M8 18h.01"></path><path d="M12 18h.01"></path><path d="M16 18h.01"></path>',
  "bar-chart-3":
    '<path d="M3 3v16a2 2 0 0 0 2 2h16"></path><path d="M18 17V9"></path><path d="M13 17V5"></path><path d="M8 17v-3"></path>',
  calendar:
    '<path d="M8 2v4"></path><path d="M16 2v4"></path><rect width="18" height="18" x="3" y="4" rx="2"></rect><path d="M3 10h18"></path>',
  "book-open":
    '<path d="M12 7v14"></path><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"></path>',
  "graduation-cap":
    '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"></path><path d="M22 10v6"></path><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"></path>',
  "building-2":
    '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"></path><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"></path><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"></path><path d="M10 6h4"></path><path d="M10 10h4"></path><path d="M10 14h4"></path><path d="M10 18h4"></path>',
  "clipboard-list":
    '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="M12 11h4"></path><path d="M12 16h4"></path><path d="M8 11h.01"></path><path d="M8 16h.01"></path>',
  "log-out":
    '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" x2="9" y1="12" y2="12"></line>',
  x: '<path d="M18 6 6 18"></path><path d="m6 6 12 12"></path>',
};

function renderLucideIcon(name, sizeClass = "w-4 h-4") {
  const inner = LUCIDE_ICON_PATHS[name] || "";
  return `<svg class="${sizeClass} shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
}

const ADMIN_PAGES = {
  crud: {
    href: "/index.html",
    icon: "database",
    navLabel: "1. Quản lý dữ liệu",
    title: "02. Quản lý dữ liệu & nạp Excel",
  },
  graph: {
    href: "/graph.html",
    icon: "share-2",
    navLabel: "2. Đồ thị & xếp lịch",
    title: "03. Đồ thị xung đột & xếp lịch DSatur",
  },
  calendar: {
    href: "/calendar.html",
    icon: "calendar-days",
    navLabel: "3. Lịch thi toàn trường",
    title: "04. Lịch thi toàn trường",
  },
  stats: {
    href: "/stats.html",
    icon: "bar-chart-3",
    navLabel: "4. Thống kê & phân tích",
    title: "05. Thống kê & phân tích kỳ thi",
  },
};

function switchAdminTab(tabId) {
  const map = {
    "tab-crud": "/index.html",
    "tab-graph": "/graph.html",
    "tab-calendar": "/calendar.html",
    "tab-stats": "/stats.html",
  };
  if (map[tabId]) {
    window.location.href = map[tabId];
  }
}

function openRightDrawer() {
  const sidebar = document.getElementById("admin-sidebar");
  const backdrop = document.getElementById("right-drawer-backdrop");
  const trigger = document.getElementById("btn-open-right-drawer");
  if (!sidebar || !backdrop) return;
  sidebar.classList.remove("-translate-x-full");
  backdrop.classList.remove("hidden");
  if (trigger) trigger.setAttribute("aria-expanded", "true");
}

function closeRightDrawer() {
  const sidebar = document.getElementById("admin-sidebar");
  const backdrop = document.getElementById("right-drawer-backdrop");
  const trigger = document.getElementById("btn-open-right-drawer");
  if (!sidebar || !backdrop) return;
  sidebar.classList.add("-translate-x-full");
  backdrop.classList.add("hidden");
  if (trigger) trigger.setAttribute("aria-expanded", "false");
}

function toggleRightDrawer() {
  const sidebar = document.getElementById("admin-sidebar");
  if (!sidebar) return;
  if (sidebar.classList.contains("-translate-x-full")) {
    openRightDrawer();
  } else {
    closeRightDrawer();
  }
}

const CRUD_ENTITIES = [
  { key: "ky_thi", icon: "calendar", label: "Kỳ thi" },
  { key: "mon_hoc", icon: "book-open", label: "Môn học" },
  { key: "sinh_vien", icon: "graduation-cap", label: "Sinh viên" },
  { key: "phong_thi", icon: "building-2", label: "Phòng thi" },
  { key: "dang_ky_thi", icon: "clipboard-list", label: "Đăng ký thi" },
];

function initAdminShell(activePage) {
  const mount = document.getElementById("admin-shell-mount");
  if (!mount) return;

  const activeEntity = new URLSearchParams(window.location.search).get("entity") || "mon_hoc";

  const crudSubNav =
    activePage === "crud"
      ? `
      <div id="crud-entity-menubar" class="w-full px-6 bg-white flex items-center justify-between overflow-x-auto">
        <nav aria-label="Data Management Entity Menu" class="flex items-center gap-1">
          ${CRUD_ENTITIES.map((ent) => {
            const isActive = ent.key === activeEntity;
            const cls = isActive
              ? "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-bold text-blue-700 border-b-2 border-blue-700 bg-white transition whitespace-nowrap"
              : "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-blue-700 hover:border-slate-300 border-b-2 border-transparent bg-white transition whitespace-nowrap";
            return `<button type="button" data-crud-nav="${ent.key}" aria-current="${isActive ? "page" : "false"}" onclick="switchCrudEntity('${ent.key}')" class="${cls}">${renderLucideIcon(ent.icon, "w-4 h-4")}<span>${ent.label}</span></button>`;
          }).join("\n")}
        </nav>
      </div>`
      : "";

  const drawerLinks = Object.entries(ADMIN_PAGES)
    .map(([key, cfg]) => {
      const isActive = key === activePage;
      const cls = isActive
        ? "drawer-nav-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-semibold bg-blue-50 text-blue-700 transition text-left"
        : "drawer-nav-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition text-left";
      return `<a href="${cfg.href}" class="${cls}">${renderLucideIcon(cfg.icon, "w-4 h-4")}<span>${cfg.navLabel}</span></a>`;
    })
    .join("\n");

  mount.innerHTML = `
    <header id="admin-header" class="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm no-print">
      <div class="w-full px-6 h-16 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <button id="btn-open-right-drawer" type="button" onclick="toggleRightDrawer()"
            aria-expanded="false" aria-controls="admin-sidebar" aria-label="Mở menu điều hướng"
            class="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition shrink-0"
            title="Mở menu điều hướng">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <line x1="4" x2="20" y1="6" y2="6"></line>
              <line x1="4" x2="20" y1="12" y2="12"></line>
              <line x1="4" x2="20" y1="18" y2="18"></line>
            </svg>
          </button>

          <a href="/index.html" class="flex items-center gap-2.5 shrink-0">
            <img src="/assets/logo.svg" alt="HTTPS Logo" width="59" height="28" class="h-7 w-[59px] shrink-0 object-contain" />
            <span class="h-5 w-[1.5px] rounded-full bg-slate-300 shrink-0" aria-hidden="true"></span>
            <h1 class="https-brand-wordmark text-lg">HTTPS</h1>
          </a>
        </div>

        <div class="flex items-center gap-2.5 shrink-0">
          <div class="hidden md:block text-xs font-semibold text-slate-800 pl-1" id="header-user-display">
            Admin: Phòng Đào Tạo
          </div>

          <button type="button" id="btn-admin-logout" onclick="handleLogout()"
            class="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition">
            Đăng xuất
          </button>
        </div>
      </div>
      ${crudSubNav}
    </header>

    <div id="right-drawer-backdrop" onclick="closeRightDrawer()"
      class="fixed inset-0 bg-slate-900/40 backdrop-blur-[1px] z-40 hidden transition-opacity no-print"></div>

    <aside id="admin-sidebar" aria-label="Collapsible Sidebar Menu"
      class="fixed top-0 left-0 h-full w-80 bg-white border-r border-slate-200 z-50 transform -translate-x-full transition-transform duration-200 ease-in-out flex flex-col justify-between shadow-2xl no-print">
      <div class="p-5 overflow-y-auto space-y-5">
        <div class="flex items-center justify-between pb-4 border-b border-slate-200">
          <div class="flex items-center gap-2.5">
            <img src="/assets/logo.svg" alt="HTTPS Logo" width="50" height="24" class="h-6 w-[50px] shrink-0 object-contain" />
            <span class="h-5 w-[1.5px] rounded-full bg-slate-300 shrink-0" aria-hidden="true"></span>
            <div>
              <div class="https-brand-wordmark text-sm">HTTPS</div>
              <div class="text-xs text-slate-500 mt-0.5">Admin: Phòng Đào Tạo</div>
            </div>
          </div>
          <button id="btn-close-right-drawer" type="button" onclick="closeRightDrawer()"
            aria-label="Đóng menu"
            class="w-8 h-8 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border-2 border-blue-600 flex items-center justify-center transition"
            title="Đóng menu (Esc)">${renderLucideIcon("x", "w-4 h-4")}</button>
        </div>

        <div class="space-y-1.5">
          <div class="px-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Các phân hệ chức năng</div>
          ${drawerLinks}
        </div>

        <div class="pt-4 border-t border-slate-200 space-y-2">
          <div class="px-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">Danh sách Kỳ thi gần đây</div>
          <div class="space-y-1 text-xs">
            <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 text-slate-900 font-semibold">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Thi Cuối Kỳ HK1 (2026 - 2027)</span>
            </div>
            <div class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-50">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              <span>Thi Cuối Kỳ HK2 (2025 - 2026)</span>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 border-t border-slate-200 bg-slate-50">
        <button type="button" onclick="handleLogout()"
          class="w-full py-2 px-3 rounded-lg border border-slate-300 bg-white hover:bg-red-50 hover:text-red-600 hover:border-red-200 text-xs font-semibold text-slate-700 transition inline-flex items-center justify-center gap-2">
          ${renderLucideIcon("log-out", "w-4 h-4")}
          <span>Đăng xuất khỏi hệ thống</span>
        </button>
      </div>
    </aside>
  `;
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeRightDrawer();
});

document.addEventListener("DOMContentLoaded", () => {
  const activePage = document.body.getAttribute("data-admin-page");
  if (activePage) {
    initAdminShell(activePage);
  }
});
