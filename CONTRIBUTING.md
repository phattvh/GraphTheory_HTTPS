# Hướng dẫn đóng góp (Contributing)

Cảm ơn bạn đã đóng góp cho **GraphTheory_HTTPS**. Mọi thay đổi mã nguồn trong nhóm 5 thành viên (TV1–TV5) tuân thủ các quy ước dưới đây để giữ repo sạch, dễ kiểm thử và hạn chế tối đa xung đột Git.

## 1. Chuẩn bị môi trường (Docker-First)

Toàn bộ dịch vụ chạy bằng 3 Docker image (`postgres:16-alpine`, `python:3.12-slim`, `caddy:2-alpine`). Chỉ cần cài **Docker**, **Git** và **make**:

```bash
git clone https://github.com/phattvh/GraphTheory_HTTPS.git
cd GraphTheory_HTTPS
cp .env.example .env
make up
```

## 2. Quy tắc quản lý nhánh (Branching)

- **`main`:** Chỉ nhận code đã kiểm thử ổn định thông qua merge từ `test` (không push trực tiếp).
- **`test`:** Nhánh tích hợp và kiểm thử chung của cả nhóm trước khi chốt lên `main`.
- **Nhánh chức năng / sửa lỗi riêng biệt** (luôn tách từ bản mới nhất của `test`):
  - `feat/<ten-chuc-nang>` *(VD: `feat/rbac-dependencies`)*
  - `fix/<ten-loi>` *(VD: `fix/capslock-x11`)*
  - `refactor/<pham-vi>` *(VD: `refactor/shared-ui`)*
  - `docs/<noi-dung>` *(VD: `docs/oss-standard-polish`)*
  - `test/<ten-chuc-nang>` *(VD: `test/rbac-guard`)*
- Luôn `git pull` bản mới nhất từ `test` trước khi tách nhánh và trước khi merge ngược lại; **xóa nhánh tính năng** sau khi đã merge xong.

## 3. Quy ước Commit & Kiểm thử

- **Commit nhỏ, tách bạch (Atomic Commits):** Hoàn thành từng phần việc nhỏ thì commit ngay, không gộp nhiều tính năng hoặc sửa lỗi không liên quan vào một commit.
- **Conventional Commits:** Dùng tiền tố thống nhất:
  - `feat:` thêm chức năng mới
  - `fix:` sửa lỗi
  - `test:` thêm hoặc cập nhật kiểm thử tự động
  - `refactor:` tái cấu trúc code không đổi hành vi
  - `style:` chỉnh sửa giao diện / định dạng
  - `docs:` cập nhật tài liệu
  - `chore:` cập nhật cấu hình, `Makefile`, file phụ
- **Chạy pass toàn bộ test trước khi commit / merge:**
  ```bash
  make test
  ```
- **Dọn sạch file tạm trước khi commit:** chạy `make clean`, tuyệt đối không commit `.env`, log thử nghiệm hoặc `__pycache__/`.

## 4. Đồng bộ tài liệu

- Khi thêm file mã nguồn, router hoặc file test mới (`tests/<ten>_test.py`), nhớ cập nhật:
  - [docs/08. Implementation plan.md](docs/08.%20Implementation%20plan.md) (trạng thái tiến độ)
  - [docs/09. Project structure.md](docs/09.%20Project%20structure.md) (cây thư mục chuẩn)
  - [Makefile](Makefile) (đăng ký file test mới vào `test-host` hoặc `test-backend`)
  - [CHANGELOG.md](CHANGELOG.md) (các thay đổi đáng chú ý)
- Chạy `python3 tests/docs_test.py` để xác nhận không có link tài liệu bị gãy và toàn bộ test đã có trong `Makefile`.

## 5. Giấy phép

Mọi đóng góp cho dự án được phát hành theo giấy phép [Apache-2.0](LICENSE).
