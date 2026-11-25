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

/**
 * Kiểm tra hợp lệ từng trường form đăng nhập phía client.
 * Không kiểm tra hay gợi ý độ dài tối thiểu của mật khẩu để tránh lộ chính sách mật khẩu trước tấn công brute-force.
 * @param {string} name
 * @param {string} value
 * @param {boolean} required
 * @param {number} minLength
 * @param {string} [requiredMsg]
 * @returns {string}
 */
function validateLoginField(name, value, required, minLength, requiredMsg) {
  const raw = String(value == null ? "" : value);
  const effective = name === "mat_khau" ? raw : raw.trim();
  if (required && !effective) {
    return requiredMsg || "Trường này không được để trống.";
  }
  if (name !== "mat_khau" && minLength > 0 && effective.length < minLength) {
    return `Tên đăng nhập cần tối thiểu ${minLength} ký tự.`;
  }
  return "";
}

/**
 * Tính toán trạng thái Caps Lock chính xác đa nền tảng (Windows, macOS, Linux X11/Wayland).
 * Khắc phục lỗi X11/Chromium giữ nguyên getModifierState("CapsLock") === true ở cả keydown và keyup khi tắt Caps Lock.
 * @param {{ capsOn: boolean, capsPending: { wasOn: boolean, downState: boolean } | null }} state
 * @param {{ type: string, key?: string, code?: string, repeat?: boolean, modifierState: boolean }} evt
 * @returns {{ capsOn: boolean, capsPending: { wasOn: boolean, downState: boolean } | null }}
 */
function resolveCapsLockState(state, evt) {
  const prevOn = Boolean(state && state.capsOn);
  const prevPending = (state && state.capsPending) || null;
  const modState = Boolean(evt && evt.modifierState);
  const isCapsKey = Boolean(evt && (evt.key === "CapsLock" || evt.code === "CapsLock"));

  if (!isCapsKey) {
    return { capsOn: modState, capsPending: prevPending };
  }

  if (evt.type === "keydown") {
    if (evt.repeat) {
      return { capsOn: prevOn, capsPending: prevPending };
    }
    const nextPending = { wasOn: prevOn, downState: modState };
    const nextOn = modState !== prevOn ? modState : prevOn;
    return { capsOn: nextOn, capsPending: nextPending };
  }

  if (evt.type === "keyup") {
    if (prevPending && prevPending.wasOn && prevPending.downState && modState) {
      return { capsOn: false, capsPending: null };
    }
    return { capsOn: modState, capsPending: null };
  }

  return { capsOn: modState, capsPending: null };
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

  const messageFor = (el) =>
    validateLoginField(
      el.name,
      el.value,
      el.required,
      el.minLength,
      el.dataset.msg
    );

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

  // Cảnh báo bật Caps Lock (đồng bộ đa nền tảng, khắc phục lỗi kẹt trạng thái trên Linux X11/Chromium)
  let capsState = { capsOn: false, capsPending: null };
  let lastAnnouncedCaps = false;

  const syncCapsUi = (forceHide = false) => {
    if (!caps) return;
    const visible = !forceHide && Boolean(capsState.capsOn && document.activeElement === pw);
    caps.hidden = !visible;
    if (visible !== lastAnnouncedCaps) {
      lastAnnouncedCaps = visible;
      if (live) live.textContent = visible ? "Đang bật Caps Lock." : "";
    }
  };

  const handleCapsEvent = (e) => {
    if (typeof e.getModifierState !== "function") return;
    capsState = resolveCapsLockState(capsState, {
      type: e.type,
      key: e.key,
      code: e.code,
      repeat: Boolean(e.repeat),
      modifierState: e.getModifierState("CapsLock"),
    });
    syncCapsUi();
  };

  document.addEventListener("keydown", handleCapsEvent);
  document.addEventListener("keyup", handleCapsEvent);
  document.addEventListener("mousedown", handleCapsEvent);
  if (typeof window.addEventListener === "function") {
    window.addEventListener("blur", () => {
      capsState = { capsOn: capsState.capsOn, capsPending: null };
      syncCapsUi(true);
    });
  }

  // Hiệu ứng che mắt nhân vật SVG khi đang nhập mật khẩu ở chế độ ẩn
  const updateShyState = () => {
    const isShy = document.activeElement === pw && pw.type === "password";
    root.classList.toggle("is-shy", isShy);
    if (isShy) resetPupils();
  };
  pw.addEventListener("focus", () => {
    updateShyState();
    syncCapsUi();
  });
  pw.addEventListener("blur", () => {
    root.classList.remove("is-shy");
    syncCapsUi(true);
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
