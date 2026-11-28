"""Tầng điều phối dịch vụ nghiệp vụ (Service Orchestration Layer).

Mục đích kiến trúc (Tuần 2+):
- Đóng vai trò cầu nối mỏng nhưng tường minh giữa `backend/routers/` (HTTP/REST)
  với `backend/algorithms/` (Pure Functional Core) và `backend/models/` (SQLAlchemy ORM).
- Mọi luồng nghiệp vụ nhiều bước có ghi CSDL — đặc biệt là:
  1. `scheduler_service.py` (`UC08`): Đọc `dang_ky_thi` -> Dựng đồ thị -> Tô màu
     DSatur/Welsh-Powell -> Phân phòng FFD/Overflow -> Kiểm chứng `verify_schedule`
     -> Xóa `ca_thi` cũ (`CASCADE` `lich_thi`) -> Ghi `ca_thi` + `lich_thi` mới
     -> Cập nhật `ky_thi.trang_thai = 'da_xep_lich'`.
  2. `import_service.py` (`UC07`): Đọc CSV/Excel (`csv` / `openpyxl`), chống Formula
     Injection, validate từng dòng và ghi hàng loạt (all-or-nothing rollback).
  đều phải bọc trong một giao dịch ACID nguyên tử thông qua `transactional_scope(db)`.
"""

from contextlib import contextmanager
from typing import Iterator
from sqlalchemy.orm import Session


@contextmanager
def transactional_scope(db: Session) -> Iterator[Session]:
    """Thực thi khối nghiệp vụ trong một giao dịch ACID nguyên tử (commit hoặc rollback toàn bộ)."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


from .scheduler_service import (
    build_conflict_graph_from_db,
    fetch_conflict_graph_edges,
    fetch_conflict_graph_nodes,
)

__all__ = [
    "transactional_scope",
    "fetch_conflict_graph_nodes",
    "fetch_conflict_graph_edges",
    "build_conflict_graph_from_db",
]
