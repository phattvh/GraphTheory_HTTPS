/**
 * Cấu hình nhúng CDN Cytoscape.js & Khởi tạo đồ thị xung đột (UC09) — web/js/admin/graph.js
 */

const CYTOSCAPE_SHIFT_COLORS = {
  1: { bg: "#2563EB", border: "#1E3A8A" },
  2: { bg: "#10B981", border: "#065F46" },
  3: { bg: "#F59E0B", border: "#92400E" },
  4: { bg: "#8B5CF6", border: "#5B21B6" },
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
      width: 58,
      height: 58,
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
      "overlay-opacity": 0.15,
    },
  },
];

const SAMPLE_GRAPH_ELEMENTS = [
  { data: { id: "IT002", label: "IT002", shift: 1, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT005", label: "IT005", shift: 1, color: "#2563EB", borderColor: "#1E3A8A" } },
  { data: { id: "IT001", label: "IT001", shift: 2, color: "#10B981", borderColor: "#065F46" } },
  { data: { id: "IT006", label: "IT006", shift: 2, color: "#10B981", borderColor: "#065F46" } },
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
];

function initConflictGraph() {
  const container = document.getElementById("cy");
  if (!container || typeof window.cytoscape !== "function") return null;

  const fallback = document.getElementById("cy-fallback-svg");
  if (fallback) fallback.classList.add("hidden");

  return window.cytoscape({
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
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initConflictGraph();
});
