/**
 * Tiện ích gọi REST API dùng chung cho Admin & Sinh viên Portal
 * File: web/js/core/api.js (Tham chiếu: docs/09. Project structure.md)
 *
 * Tự động:
 * - Chuẩn hóa tiền tố /api/v1
 * - Đính kèm Authorization: Bearer <JWT> từ web/js/core/auth.js
 * - Tự động JSON.stringify object & giữ nguyên boundary khi gửi FormData (CSV/Excel)
 * - Áp dụng timeout qua AbortController
 * - Xóa phiên & chuyển về /login.html khi gặp 401 Unauthorized
 */

const API_BASE_PREFIX = "/api/v1";
const DEFAULT_API_TIMEOUT_MS = 15000;

class ApiRequestError extends Error {
  /**
   * @param {string} message
   * @param {{ status?: number, detail?: any, payload?: any, isTimeout?: boolean }} meta
   */
  constructor(message, meta = {}) {
    super(message);
    this.name = "ApiRequestError";
    this.status = typeof meta.status === "number" ? meta.status : 0;
    this.detail = meta.detail !== undefined ? meta.detail : message;
    this.payload = meta.payload !== undefined ? meta.payload : null;
    this.isTimeout = Boolean(meta.isTimeout);
  }
}

/**
 * Chuẩn hóa đường dẫn endpoint về /api/v1/...
 * @param {string} endpoint
 * @returns {string}
 */
function resolveApiUrl(endpoint) {
  const raw = String(endpoint || "").trim();
  if (!raw) {
    throw new ApiRequestError("Đường dẫn API không được để trống.");
  }
  if (/^https?:\/\//i.test(raw) || raw.startsWith("/api/")) {
    return raw;
  }
  return raw.startsWith("/") ? `${API_BASE_PREFIX}${raw}` : `${API_BASE_PREFIX}/${raw}`;
}

/**
 * Rút trích thông báo lỗi thân thiện từ payload lỗi của FastAPI.
 * @param {any} payload
 * @param {number} status
 * @returns {string}
 */
function extractApiErrorMessage(payload, status) {
  if (payload && typeof payload === "object") {
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail.trim();
    }
    if (Array.isArray(payload.detail) && payload.detail.length > 0) {
      const first = payload.detail[0];
      if (first && typeof first.msg === "string") {
        return first.msg;
      }
    }
  }
  if (status === 401) return "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.";
  if (status === 403) return "Bạn không có quyền thực hiện thao tác này.";
  if (status === 404) return "Không tìm thấy dữ liệu yêu cầu.";
  if (status === 409) return "Dữ liệu bị trùng lặp hoặc xung đột ràng buộc.";
  return `Yêu cầu thất bại (HTTP ${status}).`;
}

/**
 * Kiểm tra đối tượng FormData an toàn trên cả trình duyệt và môi trường test.
 * @param {any} value
 * @returns {boolean}
 */
function isFormDataBody(value) {
  return typeof FormData !== "undefined" && value instanceof FormData;
}

/**
 * Gửi HTTP request chuẩn hóa tới FastAPI Backend.
 * @param {string} endpoint
 * @param {RequestInit & { timeoutMs?: number, redirectOn401?: boolean, parseJson?: boolean }} options
 * @returns {Promise<any>}
 */
async function apiFetch(endpoint, options = {}) {
  const {
    method = "GET",
    headers: customHeaders = {},
    body: rawBody,
    timeoutMs = DEFAULT_API_TIMEOUT_MS,
    redirectOn401 = true,
    parseJson = true,
    ...restOptions
  } = options || {};

  const url = resolveApiUrl(endpoint);
  const headers =
    typeof getAuthHeaders === "function"
      ? getAuthHeaders({ ...customHeaders })
      : { ...customHeaders };

  if (!headers.Accept && !headers.accept) {
    headers.Accept = "application/json";
  }

  let requestBody = rawBody;
  if (isFormDataBody(rawBody)) {
    // Để trình duyệt tự sinh multipart/form-data kèm boundary chính xác
    delete headers["Content-Type"];
    delete headers["content-type"];
  } else if (
    rawBody !== undefined &&
    rawBody !== null &&
    typeof rawBody === "object" &&
    !(typeof URLSearchParams !== "undefined" && rawBody instanceof URLSearchParams) &&
    !(typeof Blob !== "undefined" && rawBody instanceof Blob) &&
    !(typeof ArrayBuffer !== "undefined" && rawBody instanceof ArrayBuffer)
  ) {
    if (!headers["Content-Type"] && !headers["content-type"]) {
      headers["Content-Type"] = "application/json";
    }
    requestBody = JSON.stringify(rawBody);
  }

  const canAbort = typeof AbortController !== "undefined" && timeoutMs > 0;
  const controller = canAbort ? new AbortController() : null;
  let didTimeout = false;
  const timerId = controller
    ? setTimeout(() => {
        didTimeout = true;
        controller.abort();
      }, timeoutMs)
    : null;

  try {
    const fetchInit = {
      method: String(method).toUpperCase(),
      headers,
      ...restOptions,
    };
    if (requestBody !== undefined) {
      fetchInit.body = requestBody;
    }
    if (controller && !fetchInit.signal) {
      fetchInit.signal = controller.signal;
    }

    const resp = await fetch(url, fetchInit);

    if (resp.status === 401 && redirectOn401) {
      if (typeof clearAuthSession === "function") {
        clearAuthSession();
      }
      if (
        typeof window !== "undefined" &&
        window.location &&
        !(window.location.pathname || "").endsWith("/login.html")
      ) {
        window.location.href = "/login.html";
      }
    }

    if (parseJson === false && resp.ok) {
      return resp;
    }

    if (resp.status === 204) {
      return null;
    }

    const contentType = (
      (resp.headers && typeof resp.headers.get === "function" && resp.headers.get("content-type")) ||
      ""
    ).toLowerCase();

    let payload = null;
    if (contentType.includes("application/json")) {
      try {
        payload = await resp.json();
      } catch (_) {
        payload = null;
      }
    } else if (typeof resp.text === "function") {
      const text = await resp.text();
      payload = text || null;
    }

    if (!resp.ok) {
      const msg = extractApiErrorMessage(payload, resp.status);
      throw new ApiRequestError(msg, {
        status: resp.status,
        detail: payload && payload.detail !== undefined ? payload.detail : msg,
        payload,
      });
    }

    return payload;
  } catch (err) {
    if (err instanceof ApiRequestError) {
      throw err;
    }
    if (didTimeout || (err && err.name === "AbortError")) {
      throw new ApiRequestError("Yêu cầu quá thời gian phản hồi. Vui lòng thử lại.", {
        status: 0,
        isTimeout: true,
      });
    }
    throw new ApiRequestError("Không thể kết nối tới máy chủ. Vui lòng kiểm tra mạng.", {
      status: 0,
      detail: err && err.message ? err.message : "Network error",
    });
  } finally {
    if (timerId !== null) {
      clearTimeout(timerId);
    }
  }
}

function apiGet(endpoint, options = {}) {
  return apiFetch(endpoint, { ...options, method: "GET" });
}

function apiPost(endpoint, body, options = {}) {
  return apiFetch(endpoint, { ...options, method: "POST", body });
}

function apiPut(endpoint, body, options = {}) {
  return apiFetch(endpoint, { ...options, method: "PUT", body });
}

function apiDelete(endpoint, options = {}) {
  return apiFetch(endpoint, { ...options, method: "DELETE" });
}
