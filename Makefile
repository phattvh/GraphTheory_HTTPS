.PHONY: help up down logs test test-host test-backend clean

PYTHON ?= python3
COMPOSE ?= docker compose

help:
	@echo "Các lệnh dùng chung cho GraphTheory_HTTPS:"
	@echo "  make up            Khởi chạy 3 container Docker (postgres, fastapi, caddy)"
	@echo "  make down          Dừng các container Docker"
	@echo "  make logs          Xem log realtime của các container"
	@echo "  make test          Chạy toàn bộ bộ kiểm thử (host + container fastapi)"
	@echo "  make test-host     Chạy các bộ kiểm thử HTTP / Frontend / Docs từ máy host"
	@echo "  make test-backend  Chạy các bộ kiểm thử CSDL / Thuật toán / RBAC trong container"
	@echo "  make clean         Dọn thư mục cache (__pycache__, .pytest_cache, .ruff_cache)"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

test: test-host test-backend

test-host:
	$(PYTHON) tests/docker_setup_test.py
	$(PYTHON) tests/auth_test.py
	$(PYTHON) tests/master_data_api_test.py
	$(PYTHON) tests/layout_test.py
	$(PYTHON) tests/login_test.py
	$(PYTHON) tests/student_room_ui_test.py
	$(PYTHON) tests/docs_test.py

test-backend:
	$(COMPOSE) exec -T fastapi python tests/db_schema_test.py
	$(COMPOSE) exec -T fastapi python tests/backend_db_test.py
	$(COMPOSE) exec -T fastapi python tests/models_schemas_test.py
	$(COMPOSE) exec -T fastapi python tests/graph_builder_test.py
	$(COMPOSE) exec -T fastapi python tests/dsatur_test.py
	$(COMPOSE) exec -T fastapi python tests/welsh_powell_test.py
	$(COMPOSE) exec -T fastapi python tests/room_allocator_test.py
	$(COMPOSE) exec -T fastapi python tests/rbac_test.py
	$(COMPOSE) exec -T fastapi python -W error tests/security_test.py

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
