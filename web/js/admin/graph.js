/**
 * Cấu hình nhúng CDN Cytoscape.js & Khởi tạo đồ thị xung đột mẫu 10 đỉnh, 15 cạnh (UC09)
 * — web/js/admin/graph.js
 */

const CYTOSCAPE_SHIFT_COLORS = {
  1: { bg: "#2563EB", border: "#1E3A8A", label: "Ca 1" },
  2: { bg: "#10B981", border: "#065F46", label: "Ca 2" },
  3: { bg: "#F59E0B", border: "#92400E", label: "Ca 3" },
  4: { bg: "#8B5CF6", border: "#5B21B6", label: "Ca 4" },
};

const SAMPLE_COURSE_METADATA = {
  IT001: { ten_mon: "Lý thuyết Đồ thị", so_sv: 145, saturation: 3, rooms: ["A101 (100 SV)", "B201 (45 SV)"] },
  IT002: { ten_mon: "Cấu trúc Dữ liệu & Giải thuật", so_sv: 180, saturation: 3, rooms: ["A101 (100 SV)", "A102 (80 SV)"] },
  IT003: { ten_mon: "Hệ Quản trị Cơ sở Dữ liệu PostgreSQL", so_sv: 120, saturation: 2, rooms: ["A101 (60 SV)", "A102 (60 SV)"] },
  IT004: { ten_mon: "Lập trình Web", so_sv: 110, saturation: 2, rooms: ["A102 (60 SV)", "B201 (50 SV)"] },
  IT005: { ten_mon: "An toàn & Bảo mật Thông tin", so_sv: 95, saturation: 2, rooms: ["B201 (50 SV)", "C301 (45 SV)"] },
  IT006: { ten_mon: "Trí tuệ Nhân tạo", so_sv: 130, saturation: 3, rooms: ["A101 (70 SV)", "A102 (60 SV)"] },
  IT007: { ten_mon: "Mạng Máy tính & Truyền thông", so_sv: 105, saturation: 2, rooms: ["A102 (60 SV)", "B201 (45 SV)"] },
  IT008: { ten_mon: "Toán Rời rạc & Tổ hợp", so_sv: 160, saturation: 3, rooms: ["A101 (100 SV)", "B201 (60 SV)"] },
  IT009: { ten_mon: "Phân tích & Thiết kế Hệ thống", so_sv: 90, saturation: 2, rooms: ["B201 (45 SV)", "C301 (45 SV)"] },
  IT010: { ten_mon: "Học máy Ứng dụng", so_sv: 85, saturation: 2, rooms: ["C301 (45 SV)", "C302 (40 SV)"] },
};

const CYTOSCAPE_STYLE = [
  {
    selector: "node",
    style: {
      "background-color": "data(color)",
      "border-color": "data(borderColor)",
      "border-width": 3,
      label: "data(label)",
      color: "#FFFFFF",
      "font-size": "12px",
      "font-weight": "700",
      "text-valign": "center",
      "text-halign": "center",
      width: 56,
      height: 56,
    },
  },
  {
    selector: "edge",
    style: {
      width: "mapData(weight, 5, 45, 1.5, 4.5)",
      "line-color": "#94A3B8",
      "curve-style": "bezier",
      label: "data(weightLabel)",
      "font-size": "10px",
      color: "#475569",
      "text-background-color": "#F8FAFC",
      "text-background-opacity": 0.9,
      "text-background-padding": "2px",
    },
  },
  {
    selector: "node:selected",
    style: {
      "border-width": 5,
      "overlay-color": "#2563EB",
      "overlay-opacity": 0.18,
    },
  },
  {
    selector: "edge:selected",
    style: {
      "line-color": "#2563EB",
      width: 5,
    },
  },
];

// Đồ thị mẫu 10 đỉnh (IT001..IT010), 15 cạnh xung đột, tô 4 màu (0 cạnh nối 2 đỉnh cùng màu)
const SAMPLE_GRAPH_ELEMENTS = [
  { data: { id: "IT002", label: "IT002", shift: 1, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT005", label: "IT005", shift: 1, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT009", label: "IT009", shift: 1, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT001", label: "IT001", shift: 2, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT006", label: "IT006", shift: 2, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT010", label: "IT010", shift: 2, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT008", label: "IT008", shift: 3, color: "#F59E0B", borderColor: "#92400E" } },
  { data: { id: "IT004", label: "IT004", shift: 3, color: "#F59E0B", borderColor: "#92400E" } },
  { data: { id: "IT003", label: "IT003", shift: 4, color: "#8B5CF6", borderColor: "#5B21B6" } },
  { data: { id: "IT007", label: "IT007", shift: 4, color: "#8B5CF6", borderColor: "#5B21B6" } },
  { data: { id: "e1", source: "IT002", target: "IT001", weight: 42, weightLabel: "42 SV" } },
  { data: { id: "e2", source: "IT002", target: "IT008", weight: 38, weightLabel: "38 SV" } },
  { data: { id: "e3", source: "IT002", target: "IT003", weight: 24, weightLabel: "24 SV" } },
  { data: { id: "e4", source: "IT002", target: "IT006", weight: 31, weightLabel: "31 SV" } },
  { data: { id: "e5", source: "IT001", target: "IT008", weight: 19, weightLabel: "19 SV" } },
  { data: { id: "e6", source: "IT001", target: "IT003", weight: 15, weightLabel: "15 SV" } },
  { data: { id: "e7", source: "IT008", target: "IT006", weight: 22, weightLabel: "22 SV" } },
  { data: { id: "e8", source: "IT003", target: "IT004", weight: 12, weightLabel: "12 SV" } },
  { data: { id: "e9", source: "IT006", target: "IT004", weight: 18, weightLabel: "18 SV" } },
  { data: { id: "e10", source: "IT001", target: "IT005", weight: 14, weightLabel: "14 SV" } },
  { data: { id: "e11", source: "IT008", target: "IT007", weight: 16, weightLabel: "16 SV" } },
  { data: { id: "e12", source: "IT005", target: "IT004", weight: 11, weightLabel: "11 SV" } },
  { data: { id: "e13", source: "IT009", target: "IT006", weight: 20, weightLabel: "20 SV" } },
  { data: { id: "e14", source: "IT009", target: "IT007", weight: 13, weightLabel: "13 SV" } },
  { data: { id: "e15", source: "IT010", target: "IT008", weight: 17, weightLabel: "17 SV" } },
];

let cyInstance = null;

function appendInspectorLine(listEl, label, value) {
  const li = document.createElement("li");
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  li.append("• ", strong, String(value));
  listEl.appendChild(li);
}

function getAdjacentEdgesForNode(nodeId) {
  return SAMPLE_GRAPH_ELEMENTS.filter(
    (el) => el.data && el.data.source && (el.data.source === nodeId || el.data.target === nodeId)
  );
}

function renderNodeInspector(nodeId) {
  const badgeEl = document.getElementById("graph-inspector-badge");
  const listEl = document.getElementById("graph-inspector-details");
  const nodeEntry = SAMPLE_GRAPH_ELEMENTS.find((el) => el.data && el.data.id === nodeId && !el.data.source);
  if (!badgeEl || !listEl || !nodeEntry) return;

  const { shift } = nodeEntry.data;
  const meta = SAMPLE_COURSE_METADATA[nodeId] || {
    ten_mon: nodeId,
    so_sv: 0,
    saturation: 0,
    rooms: [],
  };
  const adjEdges = getAdjacentEdgesForNode(nodeId);
  const topConflicts = adjEdges
    .map((e) => ({
      other: e.data.source === nodeId ? e.data.target : e.data.source,
      weight: e.data.weight,
    }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 3)
    .map((c) => `${c.other} (${c.weight} SV chung)`)
    .join(", ");

  badgeEl.textContent = `Đỉnh: ${nodeId} • Màu ${shift} (Ca thi số ${shift})`;
  listEl.replaceChildren();
  appendInspectorLine(listEl, "Tên môn", meta.ten_mon);
  appendInspectorLine(listEl, "Số sinh viên đăng ký", `${meta.so_sv} SV`);
  appendInspectorLine(listEl, "Độ bão hòa DSatur (Saturation)", meta.saturation);
  appendInspectorLine(listEl, "Bậc của đỉnh deg(v)", `${adjEdges.length} môn xung đột`);
  appendInspectorLine(listEl, "Xung đột mạnh nhất", topConflicts || "Không có");
  appendInspectorLine(listEl, "Phân phòng (First-Fit Decreasing)", meta.rooms.join(" • ") || "Chưa phân phòng");
}

function renderEdgeInspector(edgeData) {
  const badgeEl = document.getElementById("graph-inspector-badge");
  const listEl = document.getElementById("graph-inspector-details");
  if (!badgeEl || !listEl || !edgeData) return;

  const srcNode = SAMPLE_GRAPH_ELEMENTS.find((el) => el.data && el.data.id === edgeData.source);
  const tgtNode = SAMPLE_GRAPH_ELEMENTS.find((el) => el.data && el.data.id === edgeData.target);
  const srcShift = srcNode ? srcNode.data.shift : "?";
  const tgtShift = tgtNode ? tgtNode.data.shift : "?";

  badgeEl.textContent = `Cạnh: ${edgeData.source} — ${edgeData.target}`;
  listEl.replaceChildren();
  appendInspectorLine(listEl, "Cặp môn xung đột", `${edgeData.source} & ${edgeData.target}`);
  appendInspectorLine(listEl, "Số sinh viên thi chung", `${edgeData.weight} SV`);
  appendInspectorLine(
    listEl,
    "Kiểm chứng tô màu",
    srcShift !== tgtShift
      ? `Hợp lệ (Ca ${srcShift} ≠ Ca ${tgtShift})`
      : `Trùng ca (Ca ${srcShift})`
  );
}

function updateZoomStatusLabel() {
  const zoomLabel = document.getElementById("graph-zoom-label");
  if (!zoomLabel || !cyInstance || typeof cyInstance.zoom !== "function") return;
  const pct = Math.round(cyInstance.zoom() * 100);
  zoomLabel.textContent = `${pct}%`;
}

function zoomInGraph() {
  if (!cyInstance || typeof cyInstance.zoom !== "function") return;
  const next = Math.min(2.5, cyInstance.zoom() * 1.2);
  cyInstance.zoom({
    level: next,
    renderedPosition: {
      x: (cyInstance.width ? cyInstance.width() : 600) / 2,
      y: (cyInstance.height ? cyInstance.height() : 440) / 2,
    },
  });
  updateZoomStatusLabel();
}

function zoomOutGraph() {
  if (!cyInstance || typeof cyInstance.zoom !== "function") return;
  const next = Math.max(0.4, cyInstance.zoom() / 1.2);
  cyInstance.zoom({
    level: next,
    renderedPosition: {
      x: (cyInstance.width ? cyInstance.width() : 600) / 2,
      y: (cyInstance.height ? cyInstance.height() : 440) / 2,
    },
  });
  updateZoomStatusLabel();
}

function resetGraphView() {
  if (!cyInstance) return;
  if (typeof cyInstance.fit === "function") {
    cyInstance.fit(undefined, 28);
  }
  updateZoomStatusLabel();
}

function changeGraphLayout(layoutName) {
  const allowed = ["cose", "circle", "grid"];
  const chosen = allowed.includes(layoutName) ? layoutName : "cose";
  if (!cyInstance || typeof cyInstance.layout !== "function") return chosen;
  const layout = cyInstance.layout({
    name: chosen,
    animate: false,
    padding: 28,
  });
  if (layout && typeof layout.run === "function") {
    layout.run();
  }
  resetGraphView();
  return chosen;
}

function initConflictGraph() {
  const container = document.getElementById("cy");
  if (!container || typeof window.cytoscape !== "function") return null;

  const fallback = document.getElementById("cy-fallback-svg");
  if (fallback) fallback.classList.add("hidden");

  cyInstance = window.cytoscape({
    container,
    elements: SAMPLE_GRAPH_ELEMENTS,
    style: CYTOSCAPE_STYLE,
    layout: {
      name: "cose",
      animate: false,
      padding: 28,
    },
    minZoom: 0.4,
    maxZoom: 2.5,
    wheelSensitivity: 0.25,
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
  });

  if (cyInstance && typeof cyInstance.on === "function") {
    cyInstance.on("tap", "node", (evt) => {
      const id = evt && evt.target && typeof evt.target.id === "function" ? evt.target.id() : null;
      if (id) renderNodeInspector(id);
    });
    cyInstance.on("tap", "edge", (evt) => {
      const data = evt && evt.target && typeof evt.target.data === "function" ? evt.target.data() : null;
      if (data) renderEdgeInspector(data);
    });
    cyInstance.on("zoom", () => {
      updateZoomStatusLabel();
    });
  }

  renderNodeInspector("IT002");
  updateZoomStatusLabel();
  return cyInstance;
}

document.addEventListener("DOMContentLoaded", () => {
  initConflictGraph();
});
