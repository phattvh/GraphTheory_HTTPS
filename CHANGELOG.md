# Nhật ký thay đổi (Changelog)

Tài liệu ghi nhận chi tiết mọi thay đổi đáng chú ý của dự án **GraphTheory_HTTPS** theo từng cột mốc phát triển, tham chiếu theo quy ước [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Chưa phát hành] — Tuần 1 / Ngày 4 (2026-11-26)

### Đã thêm (Added)
- **Hoàn thiện Reverse Proxy Caddy (TV3 — Ngày 5):**
  - Bật nén `encode zstd gzip`, bổ sung header `Permissions-Policy`, tách định tuyến rõ `handle /api/v1/*` (kèm `Cache-Control: no-store`), `handle /docs*`, `handle /redoc*`, `handle /openapi.json` và `handle /` (`Cache-Control: no-cache`) trong `Caddyfile`.
  - Thêm bộ kiểm thử `tests/caddy_config_test.py` (`caddy validate`, giải nén `gzip`, kiểm tra định tuyến & OWASP headers) và đăng ký vào `Makefile`.
- **Chuẩn hóa kho mã nguồn mở & tự động hóa kiểm thử (TV3):**
  - Thêm `Makefile` chuẩn hóa toàn bộ lệnh vận hành (`make up`, `make down`, `make logs`, `make test`, `make test-host`, `make test-backend`, `make clean`).
  - Nâng cấp `README.md` (logo vector, bảng kiến trúc thành phần, hướng dẫn Quick Start 1 lệnh) và bổ sung `docs/README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`.
  - Đồng bộ cây thư mục dự án trong `docs/09. Project structure.md`.
  - Thêm bộ kiểm thử `tests/docs_test.py` (tự động kiểm tra tệp bắt buộc, độ phủ chỉ mục `docs/README.md`, 0 liên kết Markdown gãy và đồng bộ 100% `tests/*_test.py` với `Makefile`).
- **Bảo mật & Phân quyền RBAC (TV3 — Ngày 4):**
  - Bổ sung dependency `get_current_user` (trả `401 Unauthorized` kèm header `WWW-Authenticate: Bearer`) và `require_admin` (trả `403 Forbidden`) trong `backend/core/security.py`.
  - Tái cấu trúc `GET /api/v1/auth/me` trong `backend/routers/auth.py` để dùng chung `get_current_user`.
  - Bảo vệ toàn bộ 10 endpoint CRUD `/api/v1/ky-thi` và `/api/v1/mon-hoc` trong `backend/routers/master_data.py`: tài khoản `sinh_vien` chỉ xem được kỳ thi trạng thái `cong_bo`, bị chặn `403` với kỳ thi nháp và mọi thao tác quản trị.
  - Thêm bộ kiểm thử tích hợp `tests/rbac_test.py` và cập nhật `tests/master_data_api_test.py` sử dụng Bearer JWT quản trị.
- **Phân bổ phòng thi First-Fit Decreasing — FFD (TV1 — Ngày 4):**
  - Triển khai 3 hàm phân phòng `allocate_shift_rooms_ffd`, `allocate_exam_rooms_ffd`, `allocate_graph_schedule_rooms_ffd` (`UC08.3`) trong `backend/algorithms/room_allocator.py`, hỗ trợ tái sử dụng phòng qua nhiều ca, phân loại nguyên nhân `unallocated_courses` (hết phòng vs vượt sức chứa) và tích hợp trực tiếp với DSatur / Welsh–Powell.
  - Gia cố biên dữ liệu: chuẩn hóa cờ `dang_su_dung` (`0`/`"false"`), bắt `OverflowError` cho `float("inf")`, khử trùng `ma_mon` trong cùng ca, fallback tra cứu khi có khoảng trắng thừa và sắp xếp an toàn khóa `shift_id`.
  - Thêm bộ kiểm thử `tests/room_allocator_test.py` (11 test case) và đăng ký vào `Makefile`.
- **Giao diện Lịch thi Toàn trường FullCalendar (TV4 — Ngày 4):**
  - Nhúng `FullCalendar v6.1.15` (kèm gói ngôn ngữ tiếng Việt `vi.global.min.js`) trên `web/calendar.html` và triển khai `web/js/admin/calendar.js` (`UC10` UI): chế độ xem Tuần (`timeGridWeek`) / Tháng (`dayGridMonth`), gộp gọn 4 hàng Ca thi cố định không có giờ nghỉ, ẩn cột Chủ nhật, tự động thu nhỏ cột ngày trống & đồng bộ chiều cao thẻ môn thi, thanh tìm kiếm hợp nhất và bộ chọn Năm học / Học kỳ (`HK1`/`HK2`/`HK3`) / Tuần / Tháng.
  - Gia cố & dọn mã: chống race condition đồng bộ layout (`clearTimeout`), hỗ trợ `Date` cross-realm trong `formatSlotLabelByMode`, gỡ bỏ ~245 dòng mã thừa không còn DOM, bảo đảm 100% DOM bằng `textContent` (không `innerHTML`).
  - Thêm bộ kiểm thử `tests/calendar_ui_test.py` (kèm runtime Node.js & kiểm tra Caddy HTTPS) và đăng ký vào `Makefile`.
- **Giao diện Quản lý Đăng ký dự thi (`UC05`, TV5 — Ngày 4):**
  - Bổ sung bảng & modal CRUD Đăng ký thi (`#crud-panel-dang_ky_thi`, `#registration-crud-modal`) trong `web/index.html` và `web/js/admin/crud.js`, hỗ trợ lọc theo Môn học, tìm kiếm theo mã/tên môn/MSSV/lớp, chặn trùng bộ `(ma_ky_thi, ma_mon, mssv)` và xuất CSV an toàn.
  - Gia cố biên UI: giữ option dự phòng khi sửa bản ghi có danh mục cha đã xóa, đồng bộ bảng đăng ký khi sửa/xóa Kỳ thi, reset trạng thái sửa khi bấm `Escape` (`closeAllCrudModals`) và hiển thị trạng thái rỗng khi lọc ra 0 kết quả.
  - Mở rộng bộ kiểm thử `tests/student_room_ui_test.py` (kiểm tra cấu trúc DOM & runtime Node.js cho Sinh viên, Phòng thi và Đăng ký thi).
- **API CRUD Danh mục Kỳ thi & Môn học (TV2 — Ngày 4):**
  - Triển khai 10 endpoint CRUD đầy đủ cho `/api/v1/ky-thi` (`UC02`) và `/api/v1/mon-hoc` (`UC04`) trong `backend/routers/master_data.py`, hỗ trợ tìm kiếm escape SQL `LIKE`, phân trang `skip`/`limit`, và kiểm tra chéo ngày bắt đầu/kết thúc.
  - Thêm bộ kiểm thử tích hợp `tests/master_data_api_test.py`.

### Đã thay đổi (Changed)
- **Tinh gọn giao diện quản trị (`web/index.html`, `web/js/admin/layout.js`, `web/js/admin/crud.js`):**
  - Gỡ bỏ khối tĩnh `Cấu hình Kỳ thi hiện tại` để toàn bộ 5 bảng CRUD hiển thị hết chiều rộng (`full-width`).
  - Gỡ bỏ khối mockup tĩnh `Trạng thái Engine` khỏi thanh điều hướng bên (`#admin-sidebar`).
  - Căn giữa tiêu đề cột `<thead>` và các cột mã, chỉ số, thao tác trên tất cả bảng CRUD.

### Đã sửa & Gia cố (Fixed & Hardened)
- Bổ sung helper `_commit_or_409` trong `backend/routers/master_data.py` để đảm bảo rollback phiên PostgreSQL an toàn khi `DELETE` vi phạm ràng buộc khóa ngoại.
- Giới hạn cận trên `skip <= 100_000` cho tham số phân trang và thay hằng số cũ `HTTP_422_UNPROCESSABLE_ENTITY` bằng mã trạng thái `422`.

---

## [Milestone Ngày 3] — 2026-11-25 (Hoàn thành 5/5 thành viên)

### Đã thêm (Added)
- **Thuật toán đối chứng Welsh–Powell & Benchmark (TV1):**
  - Cài đặt thuật toán tô màu **Welsh–Powell** và bộ đối chứng benchmark (so sánh sắc số và thời gian thực thi với DSatur) trong `backend/algorithms/coloring.py`.
  - Thêm bộ kiểm thử `tests/welsh_powell_test.py` (8 kịch bản gồm $K_5$, $C_5$, $K_{3,3}$, đồ thị 10 môn thực tế và đối chứng benchmark).
- **ORM Models & Pydantic v2 Schemas danh mục (TV2):**
  - Bổ sung ORM Models `MonHoc`, `SinhVien`, `PhongThi` trong `backend/models/models.py` và các Pydantic v2 schemas tương ứng trong `backend/schemas/master_data.py`.
  - Thêm bộ kiểm thử `tests/models_schemas_test.py`.
- **API Xác thực JWT (TV3):**
  - Triển khai `POST /api/v1/auth/login` và `GET /api/v1/auth/me` trong `backend/routers/auth.py` cùng schemas `LoginRequest`, `TokenResponse`, `UserOut` trong `backend/schemas/auth.py`.
  - Thêm bộ kiểm thử `tests/auth_test.py`.
- **Quản lý phiên JWT & Điều hướng theo vai trò (TV4):**
  - Kết nối form đăng nhập với API `/api/v1/auth/login`, lưu JWT vào `localStorage`, điều hướng tự động theo `vai_tro` (`admin` / `sinh_vien`) trong `web/js/core/auth.js` và `web/js/core/login.js`.
  - Mở rộng `tests/login_test.py` với kiểm thử runtime Node.js cho `auth.js` và `login.js`.
- **Giao diện CRUD Sinh viên & Phòng thi (TV5):**
  - Hoàn thiện bảng dữ liệu và modal Thêm/Sửa cho Sinh viên (`UC03`) và Phòng thi (`UC06`, bám sát schema `PhongThiBase`) trong `web/index.html` và `web/js/admin/crud.js`.
  - Thêm bộ kiểm thử `tests/student_room_ui_test.py`.
- **Tái cấu trúc giao diện dùng chung (`refactor/shared-ui`):**
  - Bổ sung logo vector nền trong suốt `web/assets/logo.svg`, wordmark gradient `HTTPS`, nút mở sidebar dạng ô vuông kiểu GitHub (`w-10 h-10`) và thanh danh mục CRUD nền trắng liền mạch có gạch dưới xanh đậm.
  - Chuyển toàn bộ form Thêm/Sửa (`Kỳ thi`, `Môn học`, `Sinh viên`, `Phòng thi`) và Nạp/Xuất CSV–Excel thành cửa sổ nổi (modal).
  - Tách thao tác dòng thành 2 nút riêng biệt `Sửa` và `Xóa`, bổ sung hộp thoại cảnh báo xác nhận xóa (`role="alertdialog"`, `#delete-confirm-modal`).

### Đã sửa & Bảo mật (Security & Fixed)
- Chống lộ tên tài khoản qua thời gian phản hồi (*timing enumeration*) khi đăng nhập và kiểm tra chặt kiểu dữ liệu claim `sub` trong `backend/routers/auth.py`.
- Áp dụng nguyên tắc *fail-closed* trong `web/js/core/auth.js` (từ chối JWT thiếu/sai định dạng và không mặc định điều hướng vào trang quản trị khi gặp `vai_tro` lạ).
- Gỡ bỏ gợi ý độ dài tối thiểu mật khẩu trên form đăng nhập (`web/js/core/login.js`) để tránh thu hẹp không gian dò brute-force.
- Khắc phục lỗi kẹt cảnh báo Caps Lock trên Linux X11 / Chromium bằng `resolveCapsLockState` trong `web/js/core/login.js`.
- Chống **CSV Formula Injection** (prefix an toàn với ký tự `=`, `+`, `-`, `@`) khi xuất tệp CSV từ bảng CRUD.
- Thêm header `Cache-Control: no-cache` cho tài nguyên tĩnh trong `Caddyfile` nhằm tránh trình duyệt giữ bản cache cũ.

---

## [Milestone Ngày 2] — 2026-11-24 (Hoàn thành 5/5 thành viên)

### Đã thêm (Added)
- **Thuật toán tô màu DSatur (TV1):** Cài đặt thuật toán **DSatur** (`UC08.2`) kèm hàm thống kê ca thi trong `backend/algorithms/coloring.py` và bộ kiểm thử `tests/dsatur_test.py`.
- **Kết nối SQLAlchemy & ORM nền tảng (TV2):** Khởi tạo engine/session PostgreSQL trong `backend/core/database.py`, định nghĩa ORM Models `NguoiDung`, `KyThi` và bộ kiểm thử `tests/backend_db_test.py`.
- **Lõi bảo mật mật khẩu & JWT (TV3):** Triển khai băm `bcrypt` và cấp/giải mã JWT `HS256` trong `backend/core/security.py` (ép độ dài `JWT_SECRET >= 32 bytes` theo RFC 7518), kèm bộ kiểm thử `tests/security_test.py`.
- **Xử lý đăng nhập Frontend (TV4):** Xây dựng hàm validate và gửi yêu cầu JSON đăng nhập trong `web/js/core/login.js`.
- **Giao diện quản lý Kỳ thi & Môn học (TV5):** Xây dựng bảng CRUD `Kỳ thi` (`UC02`) và `Môn học` (`UC04`) có cơ chế chống XSS trong `web/index.html` và `web/js/admin/crud.js`.

---

## [Milestone Ngày 1] — Nền tảng Docker-First & Khởi tạo (Hoàn thành 5/5 thành viên)

### Đã thêm (Added)
- **Bộ dựng đồ thị xung đột (TV1):** Xây dựng mô-đun dựng đồ thị vô hướng có trọng số $G=(V,E,W)$ bằng NetworkX (`UC08.1`) trong `backend/algorithms/graph_builder.py` và bộ kiểm thử `tests/graph_builder_test.py`.
- **Thiết kế CSDL PostgreSQL 16 (TV2):** Tạo script `db/init/init.sql` với 8 bảng đạt chuẩn 3NF, 5 chỉ mục và các ràng buộc `CHECK`, kèm bộ kiểm thử `tests/db_schema_test.py`.
- **Hạ tầng Docker Compose & Reverse Proxy HTTPS (TV3):** Thiết lập kiến trúc 3 container (`postgres:16-alpine`, `python:3.12-slim`, `caddy:2-alpine`) trong `docker-compose.yml` và `Caddyfile` (Auto HTTPS + OWASP security headers), kèm bộ kiểm thử `tests/docker_setup_test.py`.
- **Khung giao diện Quản trị & Cổng Sinh viên (TV4):** Khởi tạo 4 trang Admin (`web/index.html`, `web/graph.html`, `web/calendar.html`, `web/stats.html`), Cổng Sinh viên (`web/student.html`), hàm render khung dùng chung `initAdminShell` (`web/js/admin/layout.js`) và bộ kiểm thử `tests/layout_test.py`.
- **Trang Đăng nhập & Đồ thị Cytoscape.js (TV5):** Thiết kế `web/login.html` + `web/css/login.css` với đồ thị SVG tương tác theo con trỏ chuột, tích hợp CDN `Cytoscape.js` trên `web/graph.html` và bộ kiểm thử `tests/login_test.py`.
- **Tài liệu thiết kế hệ thống:** Hoàn thiện bộ 9 tài liệu `docs/01`–`09` và giấy phép mã nguồn mở `Apache-2.0` (`LICENSE`).
