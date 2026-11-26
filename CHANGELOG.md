# Nhật ký thay đổi (Changelog)

Tài liệu ghi nhận các thay đổi đáng chú ý của dự án **GraphTheory_HTTPS** theo từng mốc triển khai.

## [Chưa phát hành] — Tuần 1 (Đang triển khai Ngày 4)

### Đã thêm
- **Bảo mật & RBAC (TV3 — Ngày 4):** Dependency `get_current_user` (`401` + `WWW-Authenticate: Bearer`) và `require_admin` (`403`), bảo vệ toàn bộ 10 endpoint CRUD `/api/v1/ky-thi` & `/api/v1/mon-hoc` (sinh viên chỉ xem kỳ thi `cong_bo`), kèm bộ kiểm thử `tests/rbac_test.py`.
- **API CRUD Danh mục (TV2 — Ngày 4):** 10 endpoint CRUD `/api/v1/ky-thi` (`UC02`) và `/api/v1/mon-hoc` (`UC04`) có tìm kiếm escape SQL `LIKE`, phân trang, kiểm tra chéo ngày thi và rollback an toàn, kèm `tests/master_data_api_test.py`.
- **Giao diện Quản trị & Đăng nhập (Tái cấu trúc UI chung + TV5 Ngày 3):**
  - Logo vector nền trong suốt `web/assets/logo.svg`, wordmark gradient `HTTPS`, nút mở sidebar kiểu GitHub, thanh danh mục CRUD nền trắng liền mạch có gạch dưới xanh đậm.
  - Chuyển toàn bộ form Thêm/Sửa (`Kỳ thi`, `Môn học`, `Sinh viên`, `Phòng thi`) và Nạp/Xuất CSV–Excel thành cửa sổ nổi (modal), tách 2 nút `Sửa` / `Xóa` kèm hộp thoại cảnh báo xác nhận xóa (`role="alertdialog"`).
  - Hoàn thiện bảng & modal CRUD Phòng thi (`UC06`) cùng bộ kiểm thử `tests/student_room_ui_test.py`.
  - Đồ thị SVG tương tác có mắt dõi theo con trỏ chuột trên `web/login.html`.
- **Chuẩn hóa repo nguồn mở:** Thêm `Makefile`, `docs/README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` và `tests/docs_test.py`.

### Đã sửa
- Bỏ gợi ý độ dài tối thiểu mật khẩu trên form đăng nhập để tránh thu hẹp không gian dò brute-force.
- Khắc phục lỗi kẹt thông báo Caps Lock trên Linux X11 / Chromium khi tắt Caps Lock.
- Thêm `Cache-Control: no-cache` cho tài nguyên tĩnh trong `Caddyfile` để trình duyệt luôn kiểm tra bản mới nhất.
- Gỡ bỏ các khối mockup tĩnh thừa (`Cấu hình Kỳ thi hiện tại`, `Trạng thái Engine`) và căn giữa tiêu đề / cột mã trên các bảng CRUD.

## [Milestone Ngày 1–3] — Nền tảng Docker-First, Thuật toán & Xác thực

### Đã thêm
- **Ngày 1:** Môi trường 100% Docker Compose (`postgres:16-alpine`, `python:3.12-slim`, `caddy:2-alpine`), schema 8 bảng 3NF (`db/init/init.sql`), dựng đồ thị xung đột NetworkX (`UC08.1`), khung giao diện 4 trang Admin + Cổng Sinh viên, trang Đăng nhập & cấu hình `Cytoscape.js`.
- **Ngày 2:** Thuật toán tô màu **DSatur** (`UC08.2`), kết nối SQLAlchemy + ORM `NguoiDung`/`KyThi`, module băm `bcrypt` & JWT `HS256`, submit form đăng nhập JSON và giao diện CRUD Kỳ thi / Môn học.
- **Ngày 3:** Thuật toán đối chứng **Welsh–Powell** + benchmark, ORM & Pydantic v2 schemas cho `MonHoc`/`SinhVien`/`PhongThi`, API `POST /api/v1/auth/login` & `GET /api/v1/auth/me`, lưu JWT `localStorage` + điều hướng theo `vai_tro`, và giao diện CRUD Sinh viên & Phòng thi.
