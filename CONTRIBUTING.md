# Đóng góp cho GraphTheory_HTTPS

Cảm ơn bạn đã quan tâm và đóng góp cho **GraphTheory_HTTPS**. Mọi đóng góp từ tính năng mới, sửa lỗi, tối ưu thuật toán đến hoàn thiện tài liệu đều được tiếp nhận qua **Issue** và **Pull Request** trên GitHub.

---

## 1. Báo lỗi và đề xuất tính năng

- **Báo lỗi / Đề xuất tính năng:** Mở một [GitHub Issue](https://github.com/phattvh/GraphTheory_HTTPS/issues) mô tả rõ bước tái hiện, kết quả mong đợi, kết quả thực tế và môi trường chạy (OS, phiên bản Docker).
- **Lỗ hổng bảo mật:** **Không** công khai lỗ hổng qua Issue. Vui lòng tuân theo quy trình báo cáo riêng tại [SECURITY.md](SECURITY.md).

---

## 2. Chuẩn bị môi trường (Docker-First)

Dự án chạy hoàn toàn bằng 3 Docker image chính thức (`postgres:16-alpine`, `python:3.12-slim`, `caddy:2-alpine`). Bạn không cần cài PostgreSQL hay các thư viện Python của backend trực tiếp lên máy chủ.

**Yêu cầu tối thiểu:**

- `Docker` & `Docker Compose` v2
- `Git`, `make`, `python3` (chạy kiểm thử từ host)
- `node` (khuyến nghị — chạy kiểm thử runtime cho `web/js/`)

**Khởi chạy cục bộ:**

```bash
git clone https://github.com/phattvh/GraphTheory_HTTPS.git
cd GraphTheory_HTTPS
cp .env.example .env
make up
```

Kiểm tra hệ thống đã sẵn sàng:

- Giao diện web: `https://localhost` (chấp nhận chứng chỉ tự ký cục bộ của Caddy)
- API Health: `curl -k https://localhost/api/v1/health`
- Xem log realtime: `make logs`

---

## 3. Quy trình nhánh Git & Pull Request

Dự án áp dụng mô hình nhánh 3 tầng để bảo vệ bản phát hành ổn định:

| Nhánh            | Vai trò               | Quy tắc                                                             |
| :--------------- | :-------------------- | :------------------------------------------------------------------ |
| `main`           | Bản phát hành ổn định | Không push trực tiếp; chỉ nhận code đã kiểm thử qua merge từ `test` |
| `test`           | Nhánh tích hợp chung  | Nơi gộp và kiểm thử tích hợp toàn hệ thống trước khi đưa lên `main` |
| `feat/<ten>`     | Tính năng mới         | Tách từ bản mới nhất của `test` (VD: `feat/rbac-dependencies`)      |
| `fix/<ten>`      | Sửa lỗi               | Tách từ bản mới nhất của `test` (VD: `fix/capslock-x11`)            |
| `refactor/<ten>` | Tái cấu trúc mã       | Không làm thay đổi hành vi chức năng (VD: `refactor/shared-ui`)     |
| `docs/<ten>`     | Cập nhật tài liệu     | Chỉ thay đổi tài liệu / hướng dẫn (VD: `docs/oss-standard-polish`)  |
| `test/<ten>`     | Bổ sung kiểm thử      | Thêm hoặc mở rộng bộ test tự động                                   |

**Quy trình chuẩn cho mỗi thay đổi:**

```bash
# 1. Đồng bộ nhánh test mới nhất trước khi tách nhánh
git checkout test
git pull origin test

# 2. Tạo nhánh làm việc riêng
git checkout -b feat/<ten-chuc-nang>

# 3. Code + viết test + chạy make test PASS 100% + commit nhỏ gọn
# 4. Đẩy nhánh lên GitHub và mở Pull Request nhắm vào nhánh test
git push -u origin feat/<ten-chuc-nang>
```

Sau khi Pull Request được review và merge vào `test`, hãy **xóa nhánh tính năng** (cả cục bộ và trên remote) để giữ kho mã sạch gọn.

---

## 4. Kiểm thử trước khi commit

Mọi thay đổi bắt buộc vượt qua **100%** bộ kiểm thử tự động trước khi commit và trước khi mở Pull Request:

```bash
make test
```

Lệnh `make test` lần lượt chạy hai nhóm kiểm thử:

- **`make test-host`:** Kiểm thử tích hợp qua `https://localhost` (Caddy HTTPS, OWASP headers, API xác thực, CRUD danh mục), kiểm thử giao diện & runtime JS (`layout`, `login`, `student_room_ui`) và kiểm thử tính toàn vẹn tài liệu (`tests/docs_test.py`).
- **`make test-backend`:** Chạy bên trong container `fastapi` để kiểm thử lược đồ 8 bảng PostgreSQL, ORM/Pydantic schemas, thuật toán đồ thị (`graph_builder`, `dsatur`, `welsh_powell`), phân quyền RBAC và bảo mật mật khẩu/JWT (với cờ `-W error` để không bỏ lọt cảnh báo deprecation).

**Quy tắc viết kiểm thử:**

- Mỗi chức năng mới phải có file kiểm thử tương ứng đặt tại `tests/<ten_chuc_nang>_test.py`.
- Đăng ký file test mới vào target phù hợp (`test-host` hoặc `test-backend`) trong [Makefile](Makefile).
- Kết hợp kiểm thử thủ công trên trình duyệt / API đối với các thay đổi giao diện và luồng người dùng.

---

## 5. Quy ước Commit & Tổ chức mã nguồn

### Commit nhỏ gọn & Conventional Commits

- **Atomic Commits:** Hoàn thành một phần việc độc lập thì commit ngay; không gộp nhiều tính năng hoặc bản sửa lỗi không liên quan vào chung một commit.
- **Tiền tố chuẩn [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):**

| Tiền tố     | Mục đích                               | Ví dụ                                                             |
| :---------- | :------------------------------------- | :---------------------------------------------------------------- |
| `feat:`     | Thêm tính năng mới                     | `feat(auth): add get_current_user and require_admin dependencies` |
| `fix:`      | Sửa lỗi hoặc gia cố bảo mật            | `fix(api): harden DELETE rollback and cap pagination offset`      |
| `test:`     | Thêm / cập nhật kiểm thử tự động       | `test(docs): add docs_test.py to validate markdown links`         |
| `refactor:` | Tái cấu trúc mã không đổi hành vi      | `refactor(ui): remove static exam config card`                    |
| `style:`    | Chỉnh sửa bố cục / định dạng           | `style(ui): center CRUD table headers and code columns`           |
| `docs:`     | Cập nhật tài liệu                      | `docs: add SaigonOS-style root docs and docs/README.md`           |
| `chore:`    | Cập nhật cấu hình, `Makefile`, tooling | `chore: add Makefile for Docker Compose and test automation`      |

### Tổ chức mã & Vệ sinh kho lưu trữ

- Giữ đúng cấu trúc phân lớp đã thống nhất trong [docs/09. Project structure.md](docs/09.%20Project%20structure.md) (mỗi nhóm API 1 router trong `backend/routers/`, mỗi trang Admin 1 file JS trong `web/js/admin/`) để hạn chế xung đột Git.
- Không sửa đổi comment/docstring không liên quan ngoài phạm vi thay đổi.
- Chạy `make clean` và kiểm tra `git status` trước khi commit; **tuyệt đối không** commit `.env`, `__pycache__/`, `.pytest_cache/`, log hoặc tệp tạm.

---

## 6. Đồng bộ tài liệu & Changelog

Khi thêm tính năng, endpoint, trang giao diện hoặc tệp kiểm thử mới, hãy cập nhật đồng bộ:

1. **[docs/README.md](docs/README.md):** Thêm liên kết nếu bổ sung tài liệu mới trong `docs/`.
2. **[docs/08. Implementation plan.md](docs/08.%20Implementation%20plan.md):** Cập nhật trạng thái hạng mục hoàn thành.
3. **[docs/09. Project structure.md](docs/09.%20Project%20structure.md):** Bổ sung file mới vào cây thư mục chuẩn.
4. **[Makefile](Makefile):** Đăng ký tệp `tests/*_test.py` mới.
5. **[CHANGELOG.md](CHANGELOG.md):** Ghi nhận các thay đổi đáng chú ý vào mục **Chưa phát hành**.

Chạy lệnh sau để xác nhận toàn bộ liên kết Markdown, chỉ mục tài liệu và `Makefile` đều khớp 100%:

```bash
python3 tests/docs_test.py
```

---

## 7. Giấy phép của phần đóng góp

Mọi đóng góp gửi vào **GraphTheory_HTTPS** được phát hành theo giấy phép **[Apache-2.0](LICENSE)**, thống nhất với phần còn lại của dự án.
