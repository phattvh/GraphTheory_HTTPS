"""Kiểm thử tự động tiện ích HTTP Client dùng chung web/js/core/api.js."""

from pathlib import Path
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"
BASE_URL = "https://localhost"
SSL_CTX = ssl._create_unverified_context()


def test_api_js_exists_and_xss_clean():
    api_js_path = WEB_DIR / "js" / "core" / "api.js"
    assert api_js_path.is_file(), f"Thiếu file bắt buộc: {api_js_path}"
    content = api_js_path.read_text(encoding="utf-8")
    for token in [
        "class ApiRequestError",
        "function resolveApiUrl",
        "async function apiFetch",
        "function apiGet",
        "function apiPost",
        "function apiPut",
        "function apiDelete",
    ]:
        assert token in content, f"web/js/core/api.js thiếu thành phần: {token}"
    assert "innerHTML" not in content, "web/js/core/api.js không được chứa innerHTML"


def test_api_js_runtime_behavior():
    if not shutil.which("node"):
        return

    script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

class MockFormData {
  constructor() { this.items = []; }
  append(k, v) { this.items.push([k, v]); }
}

const store = new Map();
let lastFetchCall = null;
let mockResponder = async () => ({
  ok: true,
  status: 200,
  headers: { get: () => "application/json" },
  json: async () => ({ ok: true }),
});

const sandbox = {
  localStorage: {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  },
  window: { location: { pathname: "/index.html", search: "", href: "/index.html" } },
  document: { addEventListener: () => {} },
  URLSearchParams,
  FormData: MockFormData,
  AbortController,
  setTimeout,
  clearTimeout,
  atob: (b64) => Buffer.from(b64, "base64").toString("binary"),
  TextDecoder,
  Uint8Array,
  fetch: async (url, init) => {
    lastFetchCall = { url, init };
    return mockResponder(url, init);
  },
};

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("web/js/core/auth.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("web/js/core/api.js", "utf8"), sandbox);

const makeJwt = (payload) => {
  const b64u = (obj) => Buffer.from(JSON.stringify(obj), "utf8").toString("base64url");
  return `${b64u({ alg: "HS256", typ: "JWT" })}.${b64u(payload)}.sig`;
};

(async () => {
  const now = Math.floor(Date.now() / 1000);
  const adminJwt = makeJwt({ sub: "admin", vai_tro: "admin", exp: now + 3600 });
  sandbox.saveAuthSession({ access_token: adminJwt });

  // 1. JSON POST auto-prefixes /api/v1, attaches Bearer JWT & serializes JSON body
  const created = await sandbox.apiPost("/mon-hoc", { ma_mon: "IT001", ten_mon: "Đồ thị" });
  assert.strictEqual(created.ok, true);
  assert.strictEqual(lastFetchCall.url, "/api/v1/mon-hoc");
  assert.strictEqual(lastFetchCall.init.method, "POST");
  assert.strictEqual(lastFetchCall.init.headers.Authorization, `Bearer ${adminJwt}`);
  assert.strictEqual(lastFetchCall.init.headers["Content-Type"], "application/json");
  assert.strictEqual(lastFetchCall.init.body, JSON.stringify({ ma_mon: "IT001", ten_mon: "Đồ thị" }));

  // 2. FormData upload strips Content-Type so browser sets multipart boundary automatically
  const fd = new MockFormData();
  fd.append("file", "dummy.csv");
  await sandbox.apiPost("/api/v1/import/sinh_vien", fd, { headers: { "Content-Type": "multipart/form-data" } });
  assert.strictEqual(lastFetchCall.url, "/api/v1/import/sinh_vien");
  assert.strictEqual(lastFetchCall.init.headers["Content-Type"], undefined);
  assert.strictEqual(lastFetchCall.init.body, fd);

  // 3. 204 No Content returns null cleanly
  mockResponder = async () => ({
    ok: true,
    status: 204,
    headers: { get: () => "" },
  });
  const delRes = await sandbox.apiDelete("/mon-hoc/5");
  assert.strictEqual(delRes, null);

  // 4. 401 Unauthorized clears session and redirects to /login.html
  mockResponder = async () => ({
    ok: false,
    status: 401,
    headers: { get: () => "application/json" },
    json: async () => ({ detail: "Phiên đăng nhập đã hết hạn." }),
  });
  let caught401 = null;
  try {
    await sandbox.apiGet("/auth/me");
  } catch (err) {
    caught401 = err;
  }
  assert.ok(caught401 && caught401.status === 401);
  assert.strictEqual(store.has("access_token"), false);
  assert.strictEqual(sandbox.window.location.href, "/login.html");

  // 5. Timeout triggers AbortController and throws ApiRequestError with isTimeout=true
  mockResponder = (_url, init) =>
    new Promise((_resolve, reject) => {
      init.signal.addEventListener("abort", () => {
        const abortErr = new Error("Aborted");
        abortErr.name = "AbortError";
        reject(abortErr);
      });
    });
  let caughtTimeout = null;
  try {
    await sandbox.apiGet("/ky-thi", { timeoutMs: 25 });
  } catch (err) {
    caughtTimeout = err;
  }
  assert.ok(caughtTimeout && caughtTimeout.isTimeout === true);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
"""
    res = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Node runtime api.js test failed:\n{res.stderr or res.stdout}"


def test_caddy_serves_api_js_if_running():
    try:
        with urllib.request.urlopen(BASE_URL + "/js/core/api.js", context=SSL_CTX, timeout=3) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "async function apiFetch" in body
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError:
        pass


if __name__ == "__main__":
    test_api_js_exists_and_xss_clean()
    test_api_js_runtime_behavior()
    test_caddy_serves_api_js_if_running()
    print("ALL API CLIENT TESTS PASSED!")
