/**
 * Xử lý tương tác màn hình Đăng nhập, nối API login, lưu JWT & điều hướng theo vai_tro (UC01 UI)
 * File: web/js/core/login.js (TV5 Ngày 1, TV4 Ngày 2 & Ngày 3)
 */

/**
 * Trích xuất và chuẩn hóa payload JSON từ form đăng nhập.
 * @param {HTMLFormElement} formEl
 * @returns {{ ten_dang_nhap: string, mat_khau: string }}
 */
function buildLoginPayload(formEl) {
  const usernameEl = formEl && formEl.elements && formEl.elements.ten_dang_nhap;
  const passwordEl = formEl && formEl.elements && formEl.elements.mat_khau;
  return {
    ten_dang_nhap: usernameEl ? String(usernameEl.value || "").trim() : "",
    mat_khau: passwordEl ? String(passwordEl.value || "") : "",
  };
}

/**
 * Gửi HTTP POST với payload JSON tới endpoint xác thực /api/v1/auth/login.
 * @param {{ ten_dang_nhap: string, mat_khau: string }} payload
 * @returns {Promise<Response>}
 */
async function sendLoginJsonPayload(payload) {
  return fetch("/api/v1/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });
}

/**
 * Xử lý dữ liệu phản hồi đăng nhập thành công: lưu JWT vào localStorage và điều hướng theo vai_tro.
 * @param {Record<string, any>} data
 * @returns {{ token: string, vai_tro: string }}
 */
function handleLoginSuccessResponse(data) {
  if (typeof saveAuthSession === "function") {
    const session = saveAuthSession(data);
    if (!session || !session.token || !session.vai_tro) {
      return null;
    }
    if (typeof navigateByRole === "function") {
      navigateByRole(session.vai_tro);
    } else {
      window.location.href = session.vai_tro === "sinh_vien" ? "/student.html" : "/index.html";
    }
    return session;
  }

  const token = String((data && data.access_token) || "").trim();
  const roleRaw = (data && data.vai_tro) || (data && data.user && data.user.vai_tro);
  const role = roleRaw === "admin" || roleRaw === "sinh_vien" ? roleRaw : null;
  if (!token || token.split(".").length !== 3 || !role) {
    return null;
  }
  localStorage.setItem("access_token", token);
  if (typeof navigateByRole === "function") {
    navigateByRole(role);
  } else {
    window.location.href = role === "sinh_vien" ? "/student.html" : "/index.html";
  }
  return { token, vai_tro: role };
}

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

  // Hiệu ứng tròng mắt nhân vật SVG hướng theo con trỏ chuột
  const sceneSvg = root.querySelector(".https-login__scene");
  const pupils = Array.from(root.querySelectorAll(".https-login__pupil"));
  const reducedMotionQuery =
    typeof window.matchMedia === "function"
      ? window.matchMedia("(prefers-reduced-motion: reduce)")
      : null;

  const resetPupils = () => {
    pupils.forEach((pupil) => {
      pupil.setAttribute("transform", "translate(0, 0)");
    });
  };

  if (sceneSvg && pupils.length) {
    let rafId = null;
    let pointerX = 0;
    let pointerY = 0;

    const updatePupils = () => {
      rafId = null;
      if (
        root.classList.contains("is-shy") ||
        (reducedMotionQuery && reducedMotionQuery.matches)
      ) {
        return;
      }
      const rect = sceneSvg.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const viewBox = sceneSvg.viewBox && sceneSvg.viewBox.baseVal;
      const vbW = viewBox && viewBox.width ? viewBox.width : 360;
      const vbH = viewBox && viewBox.height ? viewBox.height : 360;

      pupils.forEach((pupil) => {
        const cx = Number.parseFloat(pupil.dataset.eyeCx || "180");
        const cy = Number.parseFloat(pupil.dataset.eyeCy || "180");
        const maxOffset = Number.parseFloat(pupil.dataset.eyeMax || "5");
        const eyeScreenX = rect.left + (cx / vbW) * rect.width;
        const eyeScreenY = rect.top + (cy / vbH) * rect.height;

        const dx = pointerX - eyeScreenX;
        const dy = pointerY - eyeScreenY;
        const dist = Math.hypot(dx, dy);
        if (dist < 1) {
          pupil.setAttribute("transform", "translate(0, 0)");
          return;
        }
        const angle = Math.atan2(dy, dx);
        const mag = Math.min(maxOffset, dist / 26);
        const tx = Math.cos(angle) * mag;
        const ty = Math.sin(angle) * mag;
        pupil.setAttribute("transform", `translate(${tx.toFixed(2)}, ${ty.toFixed(2)})`);
      });
    };

    document.addEventListener(
      "pointermove",
      (e) => {
        pointerX = e.clientX;
        pointerY = e.clientY;
        if (!rafId) {
          rafId = window.requestAnimationFrame(updatePupils);
        }
      },
      { passive: true }
    );

    if (document.documentElement) {
      document.documentElement.addEventListener("mouseleave", resetPupils);
    }
  }

  // Hiệu ứng che mắt nhân vật SVG khi đang nhập mật khẩu ở chế độ ẩn
  const updateShyState = () => {
    const isShy = document.activeElement === pw && pw.type === "password";
    root.classList.toggle("is-shy", isShy);
    if (isShy) resetPupils();
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

  // Bắt sự kiện submit form, gọi API POST /api/v1/auth/login, lưu JWT và điều hướng theo vai_tro (TV4 Ngày 2 & Ngày 3)
  const handleLoginFormSubmit = async (e) => {
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

    const payload = buildLoginPayload(form);

    // Phát sự kiện CustomEvent mang thông tin payload JSON đã chuẩn bị gửi đi
    form.dispatchEvent(
      new CustomEvent("https:login-submit", {
        bubbles: true,
        detail: {
          endpoint: "/api/v1/auth/login",
          method: "POST",
          payload: { ten_dang_nhap: payload.ten_dang_nhap },
        },
      })
    );

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.setAttribute("aria-busy", "true");
    }
    try {
      const resp = await sendLoginJsonPayload(payload);

      if (resp.ok) {
        const data = await resp.json();
        const session = handleLoginSuccessResponse(data);
        if (!session) {
          showAlert("Phản hồi đăng nhập từ máy chủ không hợp lệ (thiếu JWT hoặc vai trò).");
        }
        return;
      }

      let errorDetail = "";
      try {
        const errBody = await resp.json();
        if (errBody && typeof errBody.detail === "string") {
          errorDetail = errBody.detail;
        }
      } catch (_) {}

      if (resp.status === 401) {
        showAlert(errorDetail || "Sai tên đăng nhập hoặc mật khẩu. Vui lòng thử lại.");
      } else if (resp.status === 404 || resp.status === 405) {
        showAlert(
          "Giao diện Đăng nhập đã sẵn sàng. API POST /api/v1/auth/login đang chờ TV3 hoàn thiện ở Ngày 3.",
          true
        );
      } else {
        showAlert(errorDetail || "Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng thử lại.");
      }
    } catch (_) {
      showAlert("Không thể kết nối tới máy chủ xác thực HTTPS. Vui lòng kiểm tra lại kết nối.");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.removeAttribute("aria-busy");
      }
    }
  };

  form.addEventListener("submit", handleLoginFormSubmit);
})();
