/**
 * Dùng chung Header 2 tầng & Right Collapsible Drawer cho 4 trang Admin
 * (index.html, graph.html, calendar.html, stats.html)
 */

const ADMIN_PAGES = {
  crud: {
    href: "/index.html",
    icon: "🗂️",
    navLabel: "1. Quản lý dữ liệu",
    title: "02. Quản lý Dữ liệu & Import Excel",
  },
  graph: {
    href: "/graph.html",
    icon: "🕸️",
    navLabel: "2. Đồ thị & Xếp lịch",
    title: "03. Đồ thị Xung đột & Xếp lịch DSatur",
  },
  calendar: {
    href: "/calendar.html",
    icon: "📅",
    navLabel: "3. Lịch thi toàn trường",
    title: "04. Lịch thi Toàn trường FullCalendar",
  },
  stats: {
    href: "/stats.html",
    icon: "📊",
    navLabel: "4. Thống kê & Phân tích",
    title: "05. Thống kê & Phân tích Đồ thị",
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
  { key: "ky_thi", icon: "🗓️", label: "Kỳ thi" },
  { key: "mon_hoc", icon: "📚", label: "Môn học" },
  { key: "sinh_vien", icon: "👨‍🎓", label: "Quản lý Sinh viên" },
  { key: "phong_thi", icon: "🏫", label: "Phòng thi" },
  { key: "dang_ky_thi", icon: "📝", label: "Đăng ký thi" },
];

function initAdminShell(activePage) {
  const mount = document.getElementById("admin-shell-mount");
  if (!mount) return;

  const activeEntity = new URLSearchParams(window.location.search).get("entity") || "mon_hoc";

  const crudSubNav =
    activePage === "crud"
      ? `
      <div id="crud-entity-menubar" class="w-full px-6 bg-slate-50/90 border-t border-slate-200 flex items-center justify-between overflow-x-auto">
        <nav aria-label="Data Management Entity Menu" class="flex items-center gap-1">
          ${CRUD_ENTITIES.map((ent) => {
            const isActive = ent.key === activeEntity;
            const cls = isActive
              ? "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold text-blue-700 border-b-2 border-blue-600 bg-white transition whitespace-nowrap"
              : "admin-nav-btn flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-white/60 border-b-2 border-transparent transition whitespace-nowrap";
            return `<button type="button" data-crud-nav="${ent.key}" onclick="switchCrudEntity('${ent.key}')" class="${cls}"><span>${ent.icon}</span><span>${ent.label}</span></button>`;
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
      return `<a href="${cfg.href}" class="${cls}"><span>${cfg.icon}</span><span>${cfg.navLabel}</span></a>`;
    })
    .join("\n");

  mount.innerHTML = `
    <header id="admin-header" class="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm no-print">
      <div class="w-full px-6 h-16 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <button id="btn-open-right-drawer" type="button" onclick="toggleRightDrawer()"
            aria-expanded="false" aria-controls="admin-sidebar"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition shrink-0"
            title="Mở Menu điều hướng">
            <span>☰</span>
            <span class="hidden sm:inline">Menu</span>
          </button>

          <a href="/index.html" class="flex items-center gap-2.5 shrink-0">
            <div class="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">H</div>
            <h1 class="text-base font-bold text-slate-900 leading-tight">HTTPS</h1>
          </a>

          <div class="hidden sm:flex items-center bg-slate-100 border border-slate-200 focus-within:border-blue-500 focus-within:bg-white rounded-lg px-3 py-1.5 w-56 lg:w-64 text-xs transition ml-1">
            <span class="mr-2 text-slate-400">🔍</span>
            <input id="global-search-input" type="text" placeholder="Tìm nhanh môn, phòng, SV (/)..."
              class="bg-transparent border-none outline-none text-slate-800 placeholder-slate-400 w-full text-xs" />
          </div>
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
            <div class="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm">H</div>
            <div>
              <div class="text-sm font-bold text-slate-900">HTTPS</div>
              <div class="text-xs text-slate-500">Admin: Phòng Đào Tạo</div>
            </div>
          </div>
          <button id="btn-close-right-drawer" type="button" onclick="closeRightDrawer()"
            class="w-8 h-8 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border-2 border-blue-600 flex items-center justify-center text-sm font-bold transition"
            title="Đóng menu (Esc)">✕</button>
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

      <div class="p-4 border-t border-slate-200 bg-slate-50 space-y-3">
        <div class="p-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-600 space-y-1">
          <div class="font-bold text-slate-800">Trạng thái Engine</div>
          <div>• Thuật toán: <span class="font-semibold text-blue-700">DSatur + FFD</span></div>
          <div>• Sắc số đạt được: <span class="font-semibold text-emerald-700">χ(G) = 4 ca thi</span></div>
          <div>• Xung đột lịch SV: <span class="font-bold text-emerald-700">0.0%</span></div>
        </div>
        <button type="button" onclick="handleLogout()"
          class="w-full py-2 px-3 rounded-lg border border-slate-300 bg-white hover:bg-red-50 hover:text-red-600 hover:border-red-200 text-xs font-semibold text-slate-700 transition">
          🚪 Đăng xuất khỏi hệ thống
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
