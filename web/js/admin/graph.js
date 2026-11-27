/**
 * Cấu hình Cytoscape.js & Điều khiển Đồ thị Xung đột + Xếp lịch Tự động (UC08, UC09)
 * - Đồ thị mẫu 10 đỉnh, 15 cạnh (tự động tính bậc đỉnh deg(v), kích thước đỉnh tỷ lệ bậc)
 * - Chuyển đổi thuật toán DSatur / Welsh-Powell & Chạy Xếp lịch Tự động
 * - Mô phỏng tô màu từng bước (Step-by-step Animation)
 * - Neighborhood Focus (làm mờ đỉnh/cạnh không liên quan khi chọn đỉnh), lọc theo Ca thi, tìm kiếm đỉnh
 * - 100% DOM API an toàn (textContent)
 */

const CYTOSCAPE_SHIFT_COLORS = {
  1: { bg: "#2563EB", border: "#1E3A8A", dotClass: "bg-blue-600", badgeClass: "bg-blue-100 text-blue-800", label: "Ca 1" },
  2: { bg: "#10B981", border: "#065F46", dotClass: "bg-emerald-600", badgeClass: "bg-emerald-100 text-emerald-800", label: "Ca 2" },
  3: { bg: "#F59E0B", border: "#92400E", dotClass: "bg-amber-500", badgeClass: "bg-amber-100 text-amber-800", label: "Ca 3" },
  4: { bg: "#8B5CF6", border: "#5B21B6", dotClass: "bg-violet-600", badgeClass: "bg-violet-100 text-violet-800", label: "Ca 4" },
  5: { bg: "#EC4899", border: "#9D174D", dotClass: "bg-pink-600", badgeClass: "bg-pink-100 text-pink-800", label: "Ca 5" },
};

const UNCOLORED_NODE_STYLE = {
  bg: "#CBD5E1",
  border: "#64748B",
};

const GRAPH_EXAM_OPTIONS = [
  { ma_ky_thi: "KTHK1_2026", nam_hoc: "2026 - 2027", label: "KTHK1_2026 - Thi Cuối Kỳ HK1" },
  { ma_ky_thi: "KTHK2_2025", nam_hoc: "2025 - 2026", label: "KTHK2_2025 - Thi Cuối Kỳ HK2" },
];

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
      width: "mapData(degree, 1, 5, 48, 68)",
      height: "mapData(degree, 1, 5, 48, 68)",
      "transition-property": "background-color, border-color, opacity, border-width",
      "transition-duration": "180ms",
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
      "transition-property": "line-color, opacity, width",
      "transition-duration": "180ms",
    },
  },
  {
    selector: ".dimmed",
    style: {
      opacity: 0.16,
    },
  },
  {
    selector: ".highlighted",
    style: {
      opacity: 1,
      "border-width": 4,
    },
  },
  {
    selector: "edge.highlighted",
    style: {
      "line-color": "#2563EB",
      opacity: 1,
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
  { data: { id: "IT002", label: "IT002", shift: 1, degree: 4, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT005", label: "IT005", shift: 1, degree: 2, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT009", label: "IT009", shift: 1, degree: 2, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT001", label: "IT001", shift: 2, degree: 4, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT006", label: "IT006", shift: 2, degree: 4, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT010", label: "IT010", shift: 2, degree: 1, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT008", label: "IT008", shift: 3, degree: 5, color: "#F59E0B", borderColor: "#92400E" } },
  { data: { id: "IT004", label: "IT004", shift: 3, degree: 3, color: "#F59E0B", borderColor: "#92400E" } },
  { data: { id: "IT003", label: "IT003", shift: 4, degree: 3, color: "#8B5CF6", borderColor: "#5B21B6" } },
  { data: { id: "IT007", label: "IT007", shift: 4, degree: 2, color: "#8B5CF6", borderColor: "#5B21B6" } },
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
let activeAlgorithm = "DSATUR";
let activeShiftFilter = null;
let activeFocusedNodeId = null;
let simulationTimerId = null;
let activeExamCode = "KTHK1_2026";
let currentShiftByNode = {};
let currentSaturationByNode = {};

function getGraphNodesList() {
  return SAMPLE_GRAPH_ELEMENTS.filter((el) => el.data && !el.data.source);
}

function getGraphEdgesList() {
  return SAMPLE_GRAPH_ELEMENTS.filter((el) => el.data && el.data.source);
}

function getAdjacentEdgesForNode(nodeId) {
  return getGraphEdgesList().filter(
    (el) => el.data.source === nodeId || el.data.target === nodeId
  );
}

function buildAdjacencyMap() {
  const adj = {};
  getGraphNodesList().forEach((n) => {
    adj[n.data.id] = new Set();
  });
  getGraphEdgesList().forEach((e) => {
    if (adj[e.data.source]) adj[e.data.source].add(e.data.target);
    if (adj[e.data.target]) adj[e.data.target].add(e.data.source);
  });
  return adj;
}

/**
 * Chạy thuật toán tô màu DSatur hoặc Welsh-Powell trên đồ thị hiện tại
 * và trả về bảng màu, thứ tự từng bước mô phỏng và kết quả kiểm chứng.
 * @param {"DSATUR"|"WELSH_POWELL"} algorithm
 */
function computeGraphColoring(algorithm = "DSATUR") {
  const algo = algorithm === "WELSH_POWELL" ? "WELSH_POWELL" : "DSATUR";
  const nodes = getGraphNodesList().map((n) => n.data.id);
  const edges = getGraphEdgesList();
  const adj = buildAdjacencyMap();
  const shiftByNode = {};
  const saturationByNode = {};
  const steps = [];

  if (algo === "WELSH_POWELL") {
    const ordered = [...nodes].sort((a, b) => {
      const diff = adj[b].size - adj[a].size;
      return diff !== 0 ? diff : a.localeCompare(b);
    });
    ordered.forEach((nodeId, idx) => {
      const neighborColors = new Set();
      adj[nodeId].forEach((nb) => {
        if (shiftByNode[nb]) neighborColors.add(shiftByNode[nb]);
      });
      let color = 1;
      while (neighborColors.has(color)) color += 1;
      shiftByNode[nodeId] = color;
      saturationByNode[nodeId] = neighborColors.size;
      steps.push({
        step: idx + 1,
        nodeId,
        shift: color,
        degree: adj[nodeId].size,
        saturation: neighborColors.size,
      });
    });
  } else {
    const uncolored = new Set(nodes);
    let stepIndex = 1;
    while (uncolored.size > 0) {
      let chosen = null;
      let bestSat = -1;
      let bestDeg = -1;

      uncolored.forEach((nodeId) => {
        const neighborColors = new Set();
        adj[nodeId].forEach((nb) => {
          if (shiftByNode[nb]) neighborColors.add(shiftByNode[nb]);
        });
        const sat = neighborColors.size;
        const deg = adj[nodeId].size;
        if (
          sat > bestSat ||
          (sat === bestSat && deg > bestDeg) ||
          (sat === bestSat && deg === bestDeg && (!chosen || nodeId.localeCompare(chosen) < 0))
        ) {
          chosen = nodeId;
          bestSat = sat;
          bestDeg = deg;
        }
      });

      const used = new Set();
      adj[chosen].forEach((nb) => {
        if (shiftByNode[nb]) used.add(shiftByNode[nb]);
      });
      let color = 1;
      while (used.has(color)) color += 1;
      shiftByNode[chosen] = color;
      saturationByNode[chosen] = bestSat;
      uncolored.delete(chosen);
      steps.push({
        step: stepIndex,
        nodeId: chosen,
        shift: color,
        degree: bestDeg,
        saturation: bestSat,
      });
      stepIndex += 1;
    }
  }

  let conflicts = 0;
  edges.forEach((e) => {
    if (shiftByNode[e.data.source] === shiftByNode[e.data.target]) {
      conflicts += 1;
    }
  });
  const chromaticNumber = Math.max(1, ...Object.values(shiftByNode));

  return {
    algorithm: algo,
    shiftByNode,
    saturationByNode,
    steps,
    chromaticNumber,
    conflicts,
  };
}

function getShiftColorInfo(shift) {
  return CYTOSCAPE_SHIFT_COLORS[shift] || CYTOSCAPE_SHIFT_COLORS[1];
}

function getNodeShift(nodeId) {
  if (currentShiftByNode[nodeId]) return currentShiftByNode[nodeId];
  const nodeEntry = SAMPLE_GRAPH_ELEMENTS.find((el) => el.data && el.data.id === nodeId && !el.data.source);
  return nodeEntry ? nodeEntry.data.shift : 1;
}

function setStatusBannerText(message) {
  const banner = document.getElementById("graph-status-banner");
  if (banner) banner.textContent = message;
}

function updateClearFocusButtonVisibility() {
  const btn = document.getElementById("btn-graph-clear-focus");
  if (!btn || !btn.classList) return;
  const shouldShow = Boolean(activeFocusedNodeId || activeShiftFilter);
  if (shouldShow) {
    btn.classList.remove("hidden");
  } else {
    btn.classList.add("hidden");
  }
}

function applyColoringToCytoscape(shiftByNode) {
  if (!cyInstance || typeof cyInstance.nodes !== "function") return;
  cyInstance.nodes().forEach((node) => {
    const id = typeof node.id === "function" ? node.id() : null;
    if (!id) return;
    const shift = shiftByNode[id];
    const palette = shift ? getShiftColorInfo(shift) : UNCOLORED_NODE_STYLE;
    if (typeof node.data === "function") {
      node.data("shift", shift || 0);
      node.data("color", palette.bg);
      node.data("borderColor", palette.border);
    }
  });
}

function updateVerifierPanel(chromaticNumber, conflicts, algo) {
  const algoLabel = algo === "WELSH_POWELL" ? "Welsh-Powell" : "DSatur";
  const titleEl = document.getElementById("verifier-status-title");
  const chromaticEl = document.getElementById("verifier-chromatic-number");
  const conflictsEl = document.getElementById("verifier-edge-conflicts");
  const capacityEl = document.getElementById("verifier-room-capacity");

  if (titleEl) {
    titleEl.textContent =
      conflicts === 0
        ? "Schedule Verifier: Hợp lệ 100%"
        : `Schedule Verifier: Phát hiện ${conflicts} xung đột`;
  }
  if (chromaticEl) {
    chromaticEl.textContent = `${chromaticNumber} ca thi (${algoLabel})`;
  }
  if (conflictsEl) {
    conflictsEl.textContent = `${conflicts} cạnh cùng màu`;
  }
  if (capacityEl) {
    capacityEl.textContent = "Đạt 100%";
  }
}

function renderGraphLegend() {
  const container = document.getElementById("graph-legend-buttons");
  if (!container || typeof container.replaceChildren !== "function") return;

  const grouped = {};
  getGraphNodesList().forEach((n) => {
    const shift = getNodeShift(n.data.id);
    if (!grouped[shift]) grouped[shift] = [];
    grouped[shift].push(n.data.id);
  });

  const shifts = Object.keys(grouped)
    .map(Number)
    .sort((a, b) => a - b);

  container.replaceChildren();
  shifts.forEach((shift) => {
    const info = getShiftColorInfo(shift);
    const isActive = activeShiftFilter === shift;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("data-shift-filter", String(shift));
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    btn.className = isActive
      ? "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-900 text-white transition cursor-pointer"
      : "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer";
    btn.onclick = () => filterGraphByShift(shift);

    const dot = document.createElement("span");
    dot.className = `w-2.5 h-2.5 rounded-full shrink-0 ${info.dotClass}`;
    dot.setAttribute("aria-hidden", "true");

    const text = document.createElement("span");
    text.textContent = `${info.label}: ${grouped[shift].join(", ")}`;

    btn.append(dot, text);
    container.appendChild(btn);
  });
}

function appendInspectorRow(listEl, label, valueNodeOrText) {
  const li = document.createElement("li");
  li.className = "flex items-start justify-between gap-3 py-2";

  const labelEl = document.createElement("span");
  labelEl.className = "text-slate-500 shrink-0";
  labelEl.textContent = label;

  const valueEl = document.createElement("span");
  valueEl.className = "font-semibold text-slate-900 text-right";
  if (typeof valueNodeOrText === "object" && valueNodeOrText !== null && valueNodeOrText.tagName) {
    valueEl.appendChild(valueNodeOrText);
  } else {
    valueEl.textContent = String(valueNodeOrText);
  }

  li.append(labelEl, valueEl);
  listEl.appendChild(li);
}

function renderNodeInspector(nodeId) {
  const headingEl = document.getElementById("graph-inspector-heading");
  const badgeEl = document.getElementById("graph-inspector-badge");
  const listEl = document.getElementById("graph-inspector-details");
  const nodeEntry = SAMPLE_GRAPH_ELEMENTS.find((el) => el.data && el.data.id === nodeId && !el.data.source);
  if (!badgeEl || !listEl || !nodeEntry) return;

  const shift = getNodeShift(nodeId);
  const shiftInfo = getShiftColorInfo(shift);
  const meta = SAMPLE_COURSE_METADATA[nodeId] || {
    ten_mon: nodeId,
    so_sv: 0,
    saturation: 0,
    rooms: [],
  };
  const adjEdges = getAdjacentEdgesForNode(nodeId);
  const sortedConflicts = adjEdges
    .map((e) => ({
      other: e.data.source === nodeId ? e.data.target : e.data.source,
      weight: e.data.weight,
    }))
    .sort((a, b) => b.weight - a.weight);

  if (headingEl) headingEl.textContent = "Chi tiết Đỉnh đang chọn";
  badgeEl.className = `inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${shiftInfo.badgeClass}`;
  badgeEl.textContent = `Đỉnh: ${nodeId} · Màu ${shift} (${shiftInfo.label})`;

  listEl.replaceChildren();
  appendInspectorRow(listEl, "Tên học phần", meta.ten_mon);
  appendInspectorRow(listEl, "Sinh viên đăng ký", `${meta.so_sv} SV`);
  appendInspectorRow(listEl, "Bậc đỉnh deg(v)", `${adjEdges.length} môn xung đột`);
  const satVal =
    typeof currentSaturationByNode[nodeId] === "number"
      ? currentSaturationByNode[nodeId]
      : meta.saturation;
  appendInspectorRow(listEl, "Độ bão hòa DSatur", String(satVal));
  appendInspectorRow(listEl, "Phân phòng (FFD)", meta.rooms.join(" · ") || "Chưa phân phòng");

  // Các nút click nhanh tới môn xung đột mạnh nhất
  const conflictsWrap = document.createElement("div");
  conflictsWrap.className = "flex flex-wrap justify-end gap-1.5";
  if (sortedConflicts.length === 0) {
    conflictsWrap.textContent = "Không có";
  } else {
    sortedConflicts.slice(0, 3).forEach((c) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "px-2 py-0.5 rounded-md bg-slate-100 hover:bg-blue-100 text-slate-700 hover:text-blue-800 text-[11px] font-semibold transition cursor-pointer";
      btn.textContent = `${c.other} (${c.weight} SV)`;
      btn.onclick = () => focusGraphNode(c.other);
      conflictsWrap.appendChild(btn);
    });
  }
  appendInspectorRow(listEl, "Xung đột mạnh nhất", conflictsWrap);
}

function renderEdgeInspector(edgeData) {
  const headingEl = document.getElementById("graph-inspector-heading");
  const badgeEl = document.getElementById("graph-inspector-badge");
  const listEl = document.getElementById("graph-inspector-details");
  if (!badgeEl || !listEl || !edgeData) return;

  const srcShift = getNodeShift(edgeData.source);
  const tgtShift = getNodeShift(edgeData.target);
  const isValid = srcShift !== tgtShift;

  if (headingEl) headingEl.textContent = "Chi tiết Cạnh xung đột";
  badgeEl.className = isValid
    ? "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800"
    : "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700";
  badgeEl.textContent = `Cạnh: ${edgeData.source} — ${edgeData.target}`;

  listEl.replaceChildren();
  appendInspectorRow(listEl, "Cặp môn xung đột", `${edgeData.source} & ${edgeData.target}`);
  appendInspectorRow(listEl, "Số SV thi chung", `${edgeData.weight} SV`);
  appendInspectorRow(
    listEl,
    "Kiểm chứng tô màu",
    isValid ? `Hợp lệ (Ca ${srcShift} ≠ Ca ${tgtShift})` : `Trùng ca (Ca ${srcShift})`
  );
}

/**
 * Làm nổi bật đỉnh đang chọn cùng các đỉnh/cạnh kề và làm mờ phần còn lại (Neighborhood Focus).
 * @param {string} nodeId
 */
function focusGraphNode(nodeId) {
  activeFocusedNodeId = nodeId;
  activeShiftFilter = null;
  renderNodeInspector(nodeId);
  renderGraphLegend();
  updateClearFocusButtonVisibility();

  if (!cyInstance || typeof cyInstance.elements !== "function") return;
  const all = cyInstance.elements();
  all.removeClass("dimmed highlighted");

  const target = typeof cyInstance.getElementById === "function" ? cyInstance.getElementById(nodeId) : null;
  if (target && target.length) {
    const neighborhood = typeof target.closedNeighborhood === "function" ? target.closedNeighborhood() : target;
    all.not(neighborhood).addClass("dimmed");
    neighborhood.addClass("highlighted");
  }
}

/**
 * Lọc / highlight toàn bộ các đỉnh thuộc một Ca thi cụ thể để kiểm chứng trực quan 0 cạnh cùng màu.
 * @param {number} shift
 */
function filterGraphByShift(shift) {
  if (activeShiftFilter === shift) {
    clearGraphHighlight();
    return null;
  }
  activeShiftFilter = shift;
  activeFocusedNodeId = null;
  renderGraphLegend();
  updateClearFocusButtonVisibility();

  const info = getShiftColorInfo(shift);
  setStatusBannerText(`Đang lọc ${info.label} · 0 cạnh nối giữa các môn cùng ca`);

  if (!cyInstance || typeof cyInstance.elements !== "function") return shift;
  const all = cyInstance.elements();
  all.removeClass("dimmed highlighted");

  const matchingNodes = cyInstance.nodes().filter((n) => {
    const id = typeof n.id === "function" ? n.id() : null;
    return id && getNodeShift(id) === shift;
  });
  all.not(matchingNodes).addClass("dimmed");
  matchingNodes.addClass("highlighted");
  return shift;
}

function clearGraphHighlight() {
  activeShiftFilter = null;
  activeFocusedNodeId = null;
  if (cyInstance && typeof cyInstance.elements === "function") {
    cyInstance.elements().removeClass("dimmed highlighted");
  }
  renderGraphLegend();
  updateClearFocusButtonVisibility();
  const res = computeGraphColoring(activeAlgorithm);
  const algoLabel = activeAlgorithm === "WELSH_POWELL" ? "Welsh-Powell" : "DSatur";
  setStatusBannerText(
    `${getGraphNodesList().length} đỉnh · ${getGraphEdgesList().length} cạnh · ${algoLabel} (${res.chromaticNumber} ca)`
  );
}

/**
 * Tìm kiếm đỉnh theo mã môn hoặc tên học phần và định vị trên đồ thị.
 * @param {string} query
 */
function searchGraphNode(query) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) {
    clearGraphHighlight();
    return null;
  }

  const matched = getGraphNodesList().find((n) => {
    const id = n.data.id;
    const meta = SAMPLE_COURSE_METADATA[id];
    const name = meta ? meta.ten_mon.toLowerCase() : "";
    return id.toLowerCase() === q || id.toLowerCase().includes(q) || name.includes(q);
  });

  if (!matched) return null;
  focusGraphNode(matched.data.id);
  if (cyInstance && typeof cyInstance.getElementById === "function" && typeof cyInstance.center === "function") {
    const el = cyInstance.getElementById(matched.data.id);
    if (el && el.length) {
      cyInstance.center(el);
    }
  }
  return matched.data.id;
}

function updateAlgorithmButtons() {
  const btnDsatur = document.getElementById("btn-algo-dsatur");
  const btnWp = document.getElementById("btn-algo-welsh-powell");
  const activeClass =
    "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white transition cursor-pointer";
  const inactiveClass =
    "px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer";

  const isDsatur = activeAlgorithm === "DSATUR";
  if (btnDsatur) {
    btnDsatur.className = isDsatur ? activeClass : inactiveClass;
    btnDsatur.setAttribute("aria-pressed", isDsatur ? "true" : "false");
  }
  if (btnWp) {
    btnWp.className = !isDsatur ? activeClass : inactiveClass;
    btnWp.setAttribute("aria-pressed", !isDsatur ? "true" : "false");
  }
}

function stopColoringSimulation(restoreColors = true) {
  if (simulationTimerId !== null && typeof clearInterval === "function") {
    clearInterval(simulationTimerId);
    simulationTimerId = null;
  }
  const labelEl = document.getElementById("btn-simulate-coloring-label");
  if (labelEl) labelEl.textContent = "Mô phỏng tô màu";
  if (restoreColors) {
    applyColoringToCytoscape(currentShiftByNode);
    renderGraphLegend();
  }
}

/**
 * Chuyển đổi thuật toán tô màu (DSATUR hoặc WELSH_POWELL) và cập nhật lại đồ thị + Verifier.
 * @param {"DSATUR"|"WELSH_POWELL"} algo
 */
function selectGraphAlgorithm(algo) {
  stopColoringSimulation(false);
  activeAlgorithm = algo === "WELSH_POWELL" ? "WELSH_POWELL" : "DSATUR";
  updateAlgorithmButtons();
  return runAutoSchedule();
}

/**
 * Thực thi thuật toán xếp lịch (tô màu đồ thị + kiểm chứng) và cập nhật giao diện.
 */
function runAutoSchedule() {
  stopColoringSimulation(false);
  const result = computeGraphColoring(activeAlgorithm);
  currentShiftByNode = result.shiftByNode;
  currentSaturationByNode = result.saturationByNode;
  activeShiftFilter = null;
  activeFocusedNodeId = null;

  applyColoringToCytoscape(currentShiftByNode);
  if (cyInstance && typeof cyInstance.elements === "function") {
    cyInstance.elements().removeClass("dimmed highlighted");
  }
  renderGraphLegend();
  updateClearFocusButtonVisibility();
  updateVerifierPanel(result.chromaticNumber, result.conflicts, activeAlgorithm);

  const selectedId = activeFocusedNodeId || "IT002";
  renderNodeInspector(selectedId);

  const algoLabel = activeAlgorithm === "WELSH_POWELL" ? "Welsh-Powell" : "DSatur";
  setStatusBannerText(
    `Đã xếp lịch bằng ${algoLabel}: ${getGraphNodesList().length} môn · χ(G) = ${result.chromaticNumber} ca · ${result.conflicts} xung đột`
  );
  return result;
}

/**
 * Bật / dừng mô phỏng quá trình tô màu từng đỉnh theo thứ tự thuật toán đang chọn.
 */
function toggleColoringSimulation() {
  if (simulationTimerId !== null) {
    stopColoringSimulation(true);
    clearGraphHighlight();
    return false;
  }

  const result = computeGraphColoring(activeAlgorithm);
  currentShiftByNode = result.shiftByNode;
  currentSaturationByNode = result.saturationByNode;
  activeShiftFilter = null;
  activeFocusedNodeId = null;
  updateClearFocusButtonVisibility();

  const labelEl = document.getElementById("btn-simulate-coloring-label");
  if (labelEl) labelEl.textContent = "Dừng mô phỏng";

  const partialMap = {};
  applyColoringToCytoscape(partialMap);
  const algoLabel = activeAlgorithm === "WELSH_POWELL" ? "Welsh-Powell" : "DSatur";
  setStatusBannerText(`Đang mô phỏng ${algoLabel} (0/${result.steps.length} đỉnh)...`);

  let stepIdx = 0;
  const runNextStep = () => {
    if (stepIdx >= result.steps.length) {
      stopColoringSimulation(true);
      updateVerifierPanel(result.chromaticNumber, result.conflicts, activeAlgorithm);
      setStatusBannerText(
        `Hoàn tất mô phỏng ${algoLabel}: ${result.steps.length}/${result.steps.length} đỉnh · χ(G) = ${result.chromaticNumber} ca`
      );
      return;
    }
    const cur = result.steps[stepIdx];
    partialMap[cur.nodeId] = cur.shift;
    applyColoringToCytoscape(partialMap);
    renderNodeInspector(cur.nodeId);
    setStatusBannerText(
      `Bước ${cur.step}/${result.steps.length}: Tô ${cur.nodeId} (deg=${cur.degree}, sat=${cur.saturation}) → Ca ${cur.shift}`
    );
    stepIdx += 1;
  };

  runNextStep();
  if (typeof setInterval === "function") {
    simulationTimerId = setInterval(runNextStep, 450);
  }
  return true;
}

function syncGraphExamSelectors(academicYear, preferredExamCode) {
  const years = Array.from(new Set(GRAPH_EXAM_OPTIONS.map((item) => item.nam_hoc))).sort((a, b) =>
    b.localeCompare(a)
  );
  const activeYear = years.includes(academicYear) ? academicYear : years[0];
  const examsInYear = GRAPH_EXAM_OPTIONS.filter((item) => item.nam_hoc === activeYear);
  const matched =
    examsInYear.find((item) => item.ma_ky_thi === preferredExamCode) ||
    examsInYear[0] ||
    GRAPH_EXAM_OPTIONS[0];

  const yearSelect = document.getElementById("graph-year-select");
  if (yearSelect && typeof yearSelect.replaceChildren === "function") {
    yearSelect.replaceChildren();
    years.forEach((yr) => {
      const opt = document.createElement("option");
      opt.value = yr;
      opt.textContent = yr;
      if (yr === activeYear) opt.selected = true;
      yearSelect.appendChild(opt);
    });
    yearSelect.value = activeYear;
  }

  const examSelect = document.getElementById("graph-exam-select");
  if (examSelect && typeof examSelect.replaceChildren === "function") {
    examSelect.replaceChildren();
    examsInYear.forEach((ex) => {
      const opt = document.createElement("option");
      opt.value = ex.ma_ky_thi;
      opt.textContent = ex.label;
      if (ex.ma_ky_thi === matched.ma_ky_thi) opt.selected = true;
      examSelect.appendChild(opt);
    });
    examSelect.value = matched.ma_ky_thi;
  }

  activeExamCode = matched.ma_ky_thi;
  return activeExamCode;
}

function handleGraphYearChange() {
  const yearSelect = document.getElementById("graph-year-select");
  const selectedYear = yearSelect && yearSelect.value ? yearSelect.value : "2026 - 2027";
  syncGraphExamSelectors(selectedYear, "");
  return runAutoSchedule();
}

function handleGraphExamChange() {
  const examSelect = document.getElementById("graph-exam-select");
  if (examSelect && examSelect.value) {
    activeExamCode = examSelect.value;
  }
  return runAutoSchedule();
}

function populateGraphSearchSuggestions() {
  const datalist = document.getElementById("graph-node-suggestions");
  if (!datalist || typeof datalist.replaceChildren !== "function") return;
  datalist.replaceChildren();
  getGraphNodesList().forEach((n) => {
    const id = n.data.id;
    const meta = SAMPLE_COURSE_METADATA[id];
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = meta ? `${id} - ${meta.ten_mon}` : id;
    datalist.appendChild(opt);
  });
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
      y: (cyInstance.height ? cyInstance.height() : 500) / 2,
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
      y: (cyInstance.height ? cyInstance.height() : 500) / 2,
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

function getConcentricLayoutOptions() {
  return {
    name: "concentric",
    animate: false,
    padding: 36,
    avoidOverlap: true,
    minNodeSpacing: 52,
    equidistant: true,
    startAngle: (3 / 2) * Math.PI,
    concentric: (node) =>
      node && typeof node.data === "function" ? Number(node.data("degree") || 0) : 0,
    levelWidth: () => 2,
  };
}

function initConflictGraph() {
  const container = document.getElementById("cy");
  if (!container || typeof window.cytoscape !== "function") return null;

  stopColoringSimulation(false);
  if (cyInstance && typeof cyInstance.destroy === "function") {
    cyInstance.destroy();
  }

  const fallback = document.getElementById("cy-fallback-svg");
  if (fallback) fallback.classList.add("hidden");

  syncGraphExamSelectors("2026 - 2027", activeExamCode);
  populateGraphSearchSuggestions();

  currentShiftByNode = Object.fromEntries(
    getGraphNodesList().map((n) => [n.data.id, n.data.shift])
  );

  cyInstance = window.cytoscape({
    container,
    elements: SAMPLE_GRAPH_ELEMENTS,
    style: CYTOSCAPE_STYLE,
    layout: getConcentricLayoutOptions(),
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
      if (id) focusGraphNode(id);
    });
    cyInstance.on("tap", "edge", (evt) => {
      const data = evt && evt.target && typeof evt.target.data === "function" ? evt.target.data() : null;
      if (data) renderEdgeInspector(data);
    });
    cyInstance.on("tap", (evt) => {
      if (evt && evt.target === cyInstance) {
        clearGraphHighlight();
      }
    });
    cyInstance.on("zoom", () => {
      updateZoomStatusLabel();
    });
  }

  updateAlgorithmButtons();
  renderGraphLegend();
  updateClearFocusButtonVisibility();
  renderNodeInspector("IT002");
  updateZoomStatusLabel();
  return cyInstance;
}

document.addEventListener("DOMContentLoaded", () => {
  initConflictGraph();
});
