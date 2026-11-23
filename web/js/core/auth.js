/**
 * Tiện ích xác thực & điều hướng theo vai trò dùng chung cho mọi trang (web/js/core/auth.js)
 */

function navigateByRole(role) {
  if (role === "sinh_vien" && !window.location.pathname.endsWith("/student.html")) {
    window.location.href = "/student.html";
  } else if (role === "admin" && window.location.pathname.endsWith("/student.html")) {
    window.location.href = "/index.html";
  }
}

async function handleLogout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("exam_jwt");
  try {
    const resp = await fetch("/login.html", { method: "HEAD" });
    if (resp.ok) {
      window.location.href = "/login.html";
      return;
    }
  } catch (_) {}
  alert("Đã đăng xuất khỏi phiên hiện tại (trang /login.html sẽ được TV5 bổ sung).");
}

// Tự động điều hướng nếu truy cập với ?role=sinh_vien hoặc ?role=admin
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const role = params.get("role");
  if (role === "sinh_vien" || role === "admin") {
    navigateByRole(role);
  }
});
