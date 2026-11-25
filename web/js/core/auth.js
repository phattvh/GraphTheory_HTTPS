/**
 * Tiện ích xác thực JWT, lưu trữ localStorage & điều hướng phân quyền theo vai_tro (UC01 UI)
 * File: web/js/core/auth.js (TV4 Ngày 1 & Ngày 3)
 */

const AUTH_TOKEN_KEY = "access_token";
const AUTH_USER_KEY = "current_user";

/**
 * Giải mã payload Base64URL của JWT token (hỗ trợ chuỗi UTF-8 tiếng Việt như ho_ten).
 * @param {string} token
 * @returns {Record<string, any> | null}
 */
function parseJwtPayload(token) {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0));
    const jsonText = new TextDecoder("utf-8").decode(bytes);
    return JSON.parse(jsonText);
  } catch (_) {
    return null;
  }
}

/**
 * Kiểm tra JWT token đã hết hạn hay chưa dựa trên claim exp (Unix timestamp giây).
 * @param {string | Record<string, any> | null} tokenOrPayload
 * @returns {boolean}
 */
function isTokenExpired(tokenOrPayload) {
  const payload =
    typeof tokenOrPayload === "string" ? parseJwtPayload(tokenOrPayload) : tokenOrPayload;
  if (!payload || typeof payload !== "object") return true;
  if (typeof payload.exp !== "number") return false;
  return Date.now() >= payload.exp * 1000;
}

/**
 * Chuẩn hóa vai trò hợp lệ ('admin' hoặc 'sinh_vien'), trả về null nếu không hợp lệ (fail-closed).
 * @param {any} role
 * @returns {"admin" | "sinh_vien" | null}
 */
function normalizeRole(role) {
  if (role === "admin" || role === "sinh_vien") {
    return role;
  }
  return null;
}

/**
 * Lưu JWT access_token và thông tin người dùng vào localStorage sau khi đăng nhập thành công.
 * @param {Record<string, any> | string} authData
 * @returns {{ token: string, vai_tro: "admin" | "sinh_vien", sub: string, mssv: string | null, ho_ten: string | null } | null}
 */
function saveAuthSession(authData) {
  const data =
    typeof authData === "string" ? { access_token: authData } : authData || {};
  const token = String(data.access_token || data.token || "").trim();
  const jwtClaims = parseJwtPayload(token);
  if (!token || !jwtClaims || isTokenExpired(jwtClaims)) {
    clearAuthSession();
    return null;
  }

  const userObj = (data.user && typeof data.user === "object" ? data.user : {}) || {};

  const vai_tro = normalizeRole(data.vai_tro || userObj.vai_tro || jwtClaims.vai_tro);
  if (!vai_tro) {
    clearAuthSession();
    return null;
  }
  const sub =
    data.ten_dang_nhap ||
    userObj.ten_dang_nhap ||
    jwtClaims.sub ||
    "";
  const mssv =
    data.mssv || userObj.mssv || jwtClaims.mssv || (vai_tro === "sinh_vien" ? sub : null);
  const ho_ten = data.ho_ten || userObj.ho_ten || jwtClaims.ho_ten || null;

  const sessionUser = {
    ten_dang_nhap: sub,
    vai_tro,
    mssv,
    ho_ten,
  };

  try {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(sessionUser));
  } catch (_) {}

  return {
    token,
    vai_tro,
    sub,
    mssv,
    ho_ten,
  };
}

/**
 * Đọc JWT access_token từ localStorage (xóa phiên và trả về null nếu không hợp lệ hoặc đã hết hạn).
 * @returns {string | null}
 */
function getAccessToken() {
  try {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return null;
    if (token.split(".").length !== 3 || isTokenExpired(token)) {
      clearAuthSession();
      return null;
    }
    return token;
  } catch (_) {
    return null;
  }
}

/**
 * Lấy thông tin người dùng hiện tại từ localStorage hoặc giải mã trực tiếp từ JWT.
 * @returns {{ ten_dang_nhap: string, vai_tro: string, mssv: string | null, ho_ten: string | null } | null}
 */
function getCurrentUser() {
  try {
    const token = getAccessToken();
    if (!token) return null;

    const rawUser = localStorage.getItem(AUTH_USER_KEY);
    if (rawUser) {
      const parsed = JSON.parse(rawUser);
      const validRole = normalizeRole(parsed && parsed.vai_tro);
      if (parsed && validRole) {
        return { ...parsed, vai_tro: validRole };
      }
    }

    const claims = parseJwtPayload(token);
    const claimRole = normalizeRole(claims && claims.vai_tro);
    if (!claims || !claimRole) return null;
    return {
      ten_dang_nhap: claims.sub || "",
      vai_tro: claimRole,
      mssv: claims.mssv || null,
      ho_ten: claims.ho_ten || null,
    };
  } catch (_) {
    return null;
  }
}

/**
 * Tạo đối tượng HTTP Headers có đính kèm Authorization: Bearer <JWT>.
 * @param {Record<string, string>} extraHeaders
 * @returns {Record<string, string>}
 */
function getAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Xóa toàn bộ token và thông tin phiên đăng nhập khỏi localStorage.
 */
function clearAuthSession() {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem("exam_jwt");
    localStorage.removeItem(AUTH_USER_KEY);
  } catch (_) {}
}

/**
 * Điều hướng trình duyệt tới trang phù hợp dựa trên vai_tro ('admin' hoặc 'sinh_vien').
 * @param {string} role
 */
function navigateByRole(role) {
  const normalizedRole = normalizeRole(role);
  if (!normalizedRole) return;
  const path = window.location.pathname || "";
  const isStudentPage = path.endsWith("/student.html");
  const isLoginPage = path.endsWith("/login.html");

  if (normalizedRole === "sinh_vien") {
    if (!isStudentPage) {
      window.location.href = "/student.html";
    }
  } else if (normalizedRole === "admin") {
    if (isStudentPage || isLoginPage) {
      window.location.href = "/index.html";
    }
  }
}

/**
 * Đăng xuất người dùng: xóa JWT khỏi localStorage và quay về màn hình đăng nhập.
 */
async function handleLogout() {
  clearAuthSession();
  try {
    const resp = await fetch("/login.html", { method: "HEAD" });
    if (resp.ok) {
      window.location.href = "/login.html";
      return;
    }
  } catch (_) {}
  window.location.href = "/login.html";
}

// Tự động kiểm tra tham số ?role=... hoặc đồng bộ quyền từ JWT khi tải trang
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const queryRole = params.get("role");
  if (queryRole === "sinh_vien" || queryRole === "admin") {
    navigateByRole(queryRole);
    return;
  }

  const token = getAccessToken();
  const user = token ? getCurrentUser() : null;
  if (user && (user.vai_tro === "sinh_vien" || user.vai_tro === "admin")) {
    const path = window.location.pathname || "";
    if (!path.endsWith("/login.html")) {
      navigateByRole(user.vai_tro);
    }
  }
});
