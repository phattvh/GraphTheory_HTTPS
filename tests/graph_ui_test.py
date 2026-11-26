"""
Kiểm tra tab Đồ thị xung đột (web/graph.html) và script Cytoscape.js (web/js/admin/graph.js)
hiển thị đồ thị mẫu 10 nodes, 15 edges có zoom/pan, đổi layout và tương tác Node/Edge Inspector (UC09).
"""

from pathlib import Path
import shutil
import subprocess

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
GRAPH_HTML = WEB_DIR / "graph.html"
GRAPH_JS = WEB_DIR / "js" / "admin" / "graph.js"


def test_graph_html_elements():
    """Kiểm tra đầy đủ phần tử HTML cho tab Đồ thị xung đột (UC09)."""
    html = GRAPH_HTML.read_text(encoding="utf-8")

    for marker in [
        'data-admin-page="graph"',
        'id="tab-graph"',
        'id="cy"',
        'id="cy-fallback-svg"',
        "cytoscape.min.js",
        'id="graph-layout-select"',
        'onchange="changeGraphLayout(this.value)"',
        'id="btn-graph-zoom-in"',
        'onclick="zoomInGraph()"',
        'id="btn-graph-zoom-out"',
        'onclick="zoomOutGraph()"',
        'id="btn-graph-fit"',
        'onclick="resetGraphView()"',
        'id="graph-zoom-label"',
        'id="graph-legend"',
        'id="graph-inspector-badge"',
        'id="graph-inspector-details"',
        'src="/js/admin/graph.js"',
    ]:
        assert marker in html, f"Thiếu phần tử UI đồ thị trong graph.html: {marker}"


def test_graph_js_structure_and_xss():
    """Kiểm tra cấu trúc graph.js và không dùng innerHTML."""
    js = GRAPH_JS.read_text(encoding="utf-8")
    assert "innerHTML" not in js, "web/js/admin/graph.js không được dùng innerHTML"

    for symbol in [
        "SAMPLE_GRAPH_ELEMENTS",
        "CYTOSCAPE_STYLE",
        "function initConflictGraph",
        "function zoomInGraph",
        "function zoomOutGraph",
        "function resetGraphView",
        "function changeGraphLayout",
        "function renderNodeInspector",
        "function renderEdgeInspector",
        "userZoomingEnabled: true",
        "userPanningEnabled: true",
    ]:
        assert symbol in js, f"Thiếu thành phần bắt buộc trong graph.js: {symbol}"


def test_graph_js_runtime_10_nodes_15_edges_and_zoom_pan():
    """Kiểm thử runtime Node.js: đúng 10 nodes, 15 edges, 0 xung đột màu, zoom/pan/layout/inspector."""
    if shutil.which("node") is None:
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const makeClassList = (initial = []) => {
  const set = new Set(initial);
  return {
    add: (...cls) => cls.forEach((c) => set.add(c)),
    remove: (...cls) => cls.forEach((c) => set.delete(c)),
    contains: (c) => set.has(c),
  };
};

const makeEl = (tag = "div") => {
  const el = {
    tagName: tag.toUpperCase(),
    textContent: "",
    children: [],
    classList: makeClassList(),
    append: (...nodes) => el.children.push(...nodes),
    appendChild: (node) => el.children.push(node),
    replaceChildren: (...nodes) => { el.children = [...nodes]; },
  };
  return el;
};

const elements = {
  cy: makeEl("div"),
  "cy-fallback-svg": makeEl("svg"),
  "graph-inspector-badge": makeEl("span"),
  "graph-inspector-details": makeEl("ul"),
  "graph-zoom-label": makeEl("span"),
};

let capturedConfig = null;
let currentZoom = 1.0;
let fitCalls = 0;
let lastLayoutName = null;
const eventHandlers = {};

const mockCy = {
  zoom: (arg) => {
    if (arg && typeof arg === "object" && typeof arg.level === "number") {
      currentZoom = arg.level;
      return mockCy;
    }
    return currentZoom;
  },
  width: () => 800,
  height: () => 440,
  fit: () => { fitCalls += 1; currentZoom = 1.0; },
  layout: (opts) => {
    lastLayoutName = opts.name;
    return { run: () => {} };
  },
  on: (evt, selector, fn) => {
    const key = typeof selector === "string" ? `${evt}:${selector}` : evt;
    const handler = typeof selector === "function" ? selector : fn;
    eventHandlers[key] = handler;
  },
};

const sandbox = {
  document: {
    getElementById: (id) => elements[id] || null,
    createElement: (tag) => makeEl(tag),
    addEventListener: () => {},
  },
  window: {
    cytoscape: (config) => {
      capturedConfig = config;
      return mockCy;
    },
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/admin/graph.js", "utf8"), sandbox);

const cy = sandbox.initConflictGraph();
assert.ok(cy, "initConflictGraph() phải trả về instance Cytoscape");
assert.ok(elements["cy-fallback-svg"].classList.contains("hidden"), "Phải ẩn fallback SVG khi Cytoscape khởi tạo");
assert.strictEqual(capturedConfig.userZoomingEnabled, true);
assert.strictEqual(capturedConfig.userPanningEnabled, true);

// Kiểm tra đúng 10 nodes và 15 edges, 0 cạnh nối 2 đỉnh cùng màu
const nodes = capturedConfig.elements.filter((el) => el.data && !el.data.source);
const edges = capturedConfig.elements.filter((el) => el.data && el.data.source);
assert.strictEqual(nodes.length, 10, `Kỳ vọng 10 nodes, thực tế ${nodes.length}`);
assert.strictEqual(edges.length, 15, `Kỳ vọng 15 edges, thực tế ${edges.length}`);

const shiftByNode = Object.fromEntries(nodes.map((n) => [n.data.id, n.data.shift]));
edges.forEach((e) => {
  assert.notStrictEqual(
    shiftByNode[e.data.source],
    shiftByNode[e.data.target],
    `Xung đột màu tại cạnh ${e.data.source}-${e.data.target}`
  );
});

// Kiểm tra zoom in / zoom out / fit
sandbox.zoomInGraph();
assert.ok(currentZoom > 1.0, "zoomInGraph phải tăng mức zoom");
assert.notStrictEqual(elements["graph-zoom-label"].textContent, "100%");

sandbox.zoomOutGraph();
assert.ok(Math.abs(currentZoom - 1.0) < 0.05, "zoomOutGraph phải đưa zoom về gần 100%");

sandbox.resetGraphView();
assert.strictEqual(fitCalls, 1);
assert.strictEqual(elements["graph-zoom-label"].textContent, "100%");

// Kiểm tra đổi layout
const chosenLayout = sandbox.changeGraphLayout("circle");
assert.strictEqual(chosenLayout, "circle");
assert.strictEqual(lastLayoutName, "circle");

// Kiểm tra click node & click edge cập nhật Inspector
eventHandlers["tap:node"]({ target: { id: () => "IT010" } });
assert.ok(elements["graph-inspector-badge"].textContent.includes("IT010"));

eventHandlers["tap:edge"]({ target: { data: () => ({ source: "IT002", target: "IT001", weight: 42 }) } });
assert.ok(elements["graph-inspector-badge"].textContent.includes("IT002 — IT001"));
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime graph UI test failed:\n{res.stderr or res.stdout}"


if __name__ == "__main__":
    test_graph_html_elements()
    test_graph_js_structure_and_xss()
    test_graph_js_runtime_10_nodes_15_edges_and_zoom_pan()
    print("ALL GRAPH UI TESTS PASSED!")
