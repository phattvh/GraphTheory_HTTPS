<p align="center">
  <img src="web/assets/logo.svg" alt="HTTPS — GraphTheory Exam Scheduler" width="220">
</p>

<h1 align="center">GraphTheory_HTTPS</h1>

<p align="center">
  Hệ thống xếp lịch thi tập trung cho sinh viên bằng thuật toán tô màu đồ thị (<strong>DSatur</strong> &amp; <strong>Welsh–Powell</strong>) kết hợp phân phòng <strong>First-Fit Decreasing (FFD)</strong>, đóng gói 100% Docker-First với Auto HTTPS.
</p>

Tài liệu thiết kế chi tiết nằm trong thư mục [docs](docs/README.md). Nhật ký thay đổi theo từng giai đoạn được ghi trong [CHANGELOG.md](CHANGELOG.md).

## Thành phần hệ thống

| Thành phần               | Công nghệ / Image                                                                | Vai trò chính                                                                                                                                |
| ------------------------ | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reverse Proxy & Web**  | `caddy:2-alpine`                                                                 | Auto HTTPS (`local_certs`), Security Headers (HSTS, `X-Frame-Options`, `nosniff`), phục vụ giao diện tĩnh `web/` và proxy `/api/*`, `/docs*` |
| **Backend & Thuật toán** | `python:3.12-slim` (FastAPI, NetworkX, SQLAlchemy, PyJWT, bcrypt)                | Xác thực Native JWT + RBAC, CRUD dữ liệu danh mục, dựng đồ thị xung đột $G=(V,E,W)$, tô màu DSatur/Welsh–Powell & phân phòng FFD             |
| **Cơ sở dữ liệu**        | `postgres:16-alpine`                                                             | Lưu trữ chuẩn 3NF gồm 8 bảng, ràng buộc toàn vẹn `CHECK`/`UNIQUE`/`FK`, chỉ mục B-tree và giao dịch ACID                                     |
| **Giao diện người dùng** | HTML5, Tailwind CSS CDN, Vanilla JS (`Cytoscape.js`, `FullCalendar`, `Chart.js`) | Cổng Quản trị (CRUD modal nổi, đồ thị tương tác, lịch toàn trường, thống kê) và Cổng Sinh viên tra cứu lịch cá nhân                          |

## Khởi chạy nhanh (100% Docker Images)

Chỉ cần cài **Docker (có Docker Compose)**, **Git** và **make** (không cần cài PostgreSQL hay Python venv trực tiếp trên máy):

```bash
git clone https://github.com/phattvh/GraphTheory_HTTPS.git
cd GraphTheory_HTTPS
cp .env.example .env
make up
```

Sau khi khởi chạy thành công:

- **Trang Quản trị (HTTPS):** `https://localhost` _(hoặc HTTP: `http://localhost:8080`)_
- **Đăng nhập:** `https://localhost/login.html` _(tài khoản mặc định dev: `admin` / `admin123`)_
- **Cổng Sinh viên:** `https://localhost/student.html`
- **Swagger UI (FastAPI):** `https://localhost/docs`

## Lệnh vận hành & Kiểm thử (`Makefile`)

Dự án chuẩn hóa toàn bộ thao tác Docker và **17 bộ kiểm thử tự động** thông qua [Makefile](Makefile). Chạy `make help` (hoặc `make`) để xem nhanh danh sách lệnh:

| Lệnh                | Mô tả                                                                                                                                                             |
| :------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `make help`         | Hiển thị danh sách toàn bộ lệnh hỗ trợ                                                                                                                            |
| `make up`           | Khởi chạy 3 container Docker (`postgres`, `fastapi`, `caddy`)                                                                                                     |
| `make down`         | Dừng toàn bộ container Docker                                                                                                                                     |
| `make logs`         | Xem log realtime (100 dòng gần nhất) của các container                                                                                                            |
| `make test`         | Chạy toàn bộ **17 bộ kiểm thử** (`test-host` + `test-backend`)                                                                                                    |
| `make test-host`    | Chạy 8 bộ test HTTP HTTPS, giao diện/runtime JS (`layout`, `login`, `student_room_ui`, `calendar_ui`) và `docs_test.py`                                           |
| `make test-backend` | Chạy 9 bộ test CSDL, ORM/Schemas, thuật toán (`graph_builder`, `dsatur`, `welsh_powell`, `room_allocator`), RBAC & bảo mật (`-W error`) trong container `fastapi` |
| `make clean`        | Dọn thư mục cache (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `htmlcov`)                                                                                      |

## Tham gia phát triển

- Quy trình nhánh Git, Conventional Commits & kiểm thử: xem [CONTRIBUTING.md](CONTRIBUTING.md).
- Kiến trúc bảo mật & báo cáo lỗ hổng: xem [SECURITY.md](SECURITY.md).
- Mục lục toàn bộ tài liệu thiết kế: xem [docs/README.md](docs/README.md).

## Giấy phép

Dự án được phát hành theo giấy phép [Apache-2.0](LICENSE).
