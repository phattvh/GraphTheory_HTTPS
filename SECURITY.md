# Chính sách bảo mật (Security Policy)

## Các lớp bảo vệ chính trong GraphTheory_HTTPS

Dự án áp dụng kiến trúc phòng thủ nhiều lớp (chi tiết xem tại [docs/06. Security and authorization.md](docs/06.%20Security%20and%20authorization.md)):

- **Truyền tải (Caddy 2):** Auto HTTPS (`local_certs`), HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` cho `/api/v1/*`, ẩn header `Server`.
- **Xác thực (FastAPI + bcrypt + PyJWT):** Băm mật khẩu `bcrypt` cost 12 có salt ngẫu nhiên, chống timing attack bằng dummy hash, kiểm chứng `JWT_SECRET >= 32 bytes` ngay lúc khởi động và chặn secret mặc định khi `APP_ENV=production`.
- **Phân quyền (RBAC, Route Guard & Chống IDOR):** Dependency `get_current_user` (`401`) và `require_admin` (`403`) đọc vai trò trực tiếp từ PostgreSQL; sinh viên chỉ xem kỳ thi đã `cong_bo` và lịch thi theo `mssv` trích từ JWT; `enforceRouteGuard` phía Client chỉ lấy `vai_tro` từ JWT hợp lệ (không tin cậy query string `?role=`).
- **Dữ liệu, Giao diện & Toàn vẹn CDN:** Truy vấn tham số hóa qua SQLAlchemy ORM, validate nghiêm ngặt bằng Pydantic v2, dùng `textContent` chống XSS, gắn mã băm **SRI (`sha384`)** cho các thư viện CDN ghim phiên bản, và vô hiệu hóa Formula Injection (`=`, `+`, `-`, `@`) khi import/export CSV/Excel.

## Báo cáo lỗ hổng bảo mật

Không đăng chi tiết lỗ hổng bảo mật lên issue công khai. Vui lòng liên hệ trực tiếp **Trần Vũ Hòa Phát** hoặc tạo báo cáo bảo mật riêng tư (Private Vulnerability Reporting) trên GitHub repository kèm:

- Mô tả lỗ hổng và mức độ ảnh hưởng.
- Các bước tái hiện tối thiểu.
- Đề xuất hướng khắc phục (nếu có).

## Lưu ý triển khai

- Tuyệt đối không commit file `.env` chứa `JWT_SECRET` hoặc mật khẩu CSDL lên Git.
- Thay đổi `JWT_SECRET` (tối thiểu 256-bit ngẫu nhiên) và mật khẩu tài khoản `admin` mặc định trước khi chạy ngoài môi trường phát triển cục bộ.
