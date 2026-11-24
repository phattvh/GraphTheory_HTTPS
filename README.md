# GraphTheory_HTTPS

Hệ thống xếp lịch thi tập trung cho sinh viên bằng thuật toán tô màu đồ thị (**DSatur** & **Welsh–Powell**) kết hợp phân phòng **First-Fit Decreasing (FFD)**.

## Khởi chạy nhanh (100% Docker Images)

```bash
cp .env.example .env
docker compose up -d --build
```

- **Web HTTPS (Caddy):** `https://localhost` *(hoặc HTTP: `http://localhost:8080`)*
- **Cổng Sinh viên:** `https://localhost/student.html`
- **Swagger UI (FastAPI):** `https://localhost/docs`

## Chạy kiểm thử

```bash
python3 tests/docker_setup_test.py
python3 tests/layout_test.py
docker compose exec fastapi python tests/graph_builder_test.py
```

## Tài liệu thiết kế (`docs/`)
- [01. Product features.md](./docs/01.%20Product%20features.md) · [02. Use case diagram.md](./docs/02.%20Use%20case%20diagram.md) · [03. Architecture and algorithms.md](./docs/03.%20Architecture%20and%20algorithms.md)
- [04. Database design.md](./docs/04.%20Database%20design.md) · [05. Flow diagrams.md](./docs/05.%20Flow%20diagrams.md) · [06. Security and authorization.md](./docs/06.%20Security%20and%20authorization.md)
- [07. Technology stack.md](./docs/07.%20Technology%20stack.md) · [08. Implementation plan.md](./docs/08.%20Implementation%20plan.md) · [09. Project structure.md](./docs/09.%20Project%20structure.md)