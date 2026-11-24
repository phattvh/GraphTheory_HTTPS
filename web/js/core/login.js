/**
 * Xử lý tương tác màn hình Đăng nhập (UC01 UI) — web/js/core/login.js
 * Tái chế cơ chế validation, ẩn/hiện mật khẩu, cảnh báo Caps Lock và hiệu ứng che mắt từ login-page-08.
 */
(() => {
  "use strict";

  const root = document.querySelector(".https-login-card");
  if (!root) return;

  const form = root.querySelector("[data-login-form]");
  const live = root.querySelector("[data-live]");
  const caps = root.querySelector("[data-caps]");
  const alertBox = root.querySelector("[data-login-alert]");
  const submitBtn = root.querySelector("[data-login-submit]");
  const pw = form && form.elements.mat_khau;
  const toggle = root.querySelector("[data-pw-toggle]");
  if (!form || !pw) return;

  const showAlert = (message, isInfo = false) => {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.classList.toggle("is-info", isInfo);
    alertBox.hidden = !message;
  };

  const messageFor = (el) => {
    const val = el.value.trim();
    if (el.required && !val) {
      return el.dataset.msg || "Trường này không được để trống.";
    }
    if (el.minLength > 0 && el.value.length < el.minLength) {
      return el.name === "ten_dang_nhap"
        ? `Tên đăng nhập cần tối thiểu ${el.minLength} ký tự.`
        : `Mật khẩu cần tối thiểu ${el.minLength} ký tự.`;
    }
    return "";
  };

  const checkField = (field) => {
    const el = field.querySelector("input");
    const msg = messageFor(el);
    const errEl = field.querySelector("[data-error]");
    if (errEl) errEl.textContent = msg;
    field.classList.toggle("is-error", Boolean(msg));
    if (msg) {
      el.setAttribute("aria-invalid", "true");
    } else {
      el.removeAttribute("aria-invalid");
    }
    return !msg;
  };

  const fields = Array.from(form.querySelectorAll("[data-field]"));
  fields.forEach((field) => {
    field.addEventListener("focusout", (e) => {
      if (
        field.contains(e.relatedTarget) ||
        (e.relatedTarget && e.relatedTarget.matches("button")) ||
        !field.querySelector("input").value
      ) {
        return;
      }
      field.dataset.touched = "1";
      checkField(field);
    });
    field.addEventListener("input", () => {
      if (field.dataset.touched) checkField(field);
      if (alertBox && !alertBox.hidden) showAlert("");
    });
  });

  // Hiệu ứng che mắt nhân vật SVG khi đang nhập mật khẩu ở chế độ ẩn
  const updateShyState = () => {
    root.classList.toggle("is-shy", document.activeElement === pw && pw.type === "password");
  };
  pw.addEventListener("focus", updateShyState);
  pw.addEventListener("blur", () => {
    root.classList.remove("is-shy");
    if (caps) caps.hidden = true;
  });

  if (toggle) {
    toggle.addEventListener("click", () => {
      const show = pw.type === "password";
      pw.type = show ? "text" : "password";
      toggle.setAttribute("aria-pressed", String(show));
      toggle.setAttribute("aria-label", show ? "Ẩn mật khẩu" : "Hiện mật khẩu");
      updateShyState();
    });
  }

  // Cảnh báo bật Caps Lock
  let capsOn = false;
  const checkCaps = (e) => {
    if (!caps || typeof e.getModifierState !== "function") return;
    const on = e.getModifierState("CapsLock");
    caps.hidden = !on;
    if (on !== capsOn) {
      capsOn = on;
      if (live) live.textContent = on ? "Đang bật Caps Lock." : "";
    }
  };
  pw.addEventListener("keydown", checkCaps);
  pw.addEventListener("keyup", checkCaps);

  // Submit form tới POST /api/v1/auth/login (sẵn sàng cho TV3/TV4 nối JWT)
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showAlert("");
    fields.forEach((f) => {
      f.dataset.touched = "1";
    });
    const bad = fields.filter((f) => !checkField(f));
    if (bad.length) {
      const summary = bad.map((f) => f.querySelector("[data-error]").textContent).join(" ");
      if (live) live.textContent = summary;
      bad[0].querySelector("input").focus();
      return;
    }

    const payload = {
      ten_dang_nhap: form.elements.ten_dang_nhap.value.trim(),
      mat_khau: form.elements.mat_khau.value,
    };

    if (submitBtn) submitBtn.disabled = true;
    try {
      const resp = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
        }
        const role = data.vai_tro || (data.user && data.user.vai_tro) || "admin";
        if (typeof navigateByRole === "function") {
          window.location.href = role === "sinh_vien" ? "/student.html" : "/index.html";
        }
        return;
      }

      if (resp.status === 404 || resp.status === 405) {
        showAlert(
          "Giao diện Đăng nhập đã sẵn sàng. API POST /api/v1/auth/login đang chờ TV3 hoàn thiện ở Ngày 3.",
          true
        );
      } else {
        showAlert("Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng thử lại.");
      }
    } catch (_) {
      showAlert("Không thể kết nối tới máy chủ xác thực HTTPS. Vui lòng kiểm tra lại kết nối.");
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
})();
