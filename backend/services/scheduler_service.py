"""Tầng dịch vụ điều phối xếp lịch thi (Scheduler Service - UC08).

Ngày 8 (UC08.1):
- Trích xuất tập đỉnh V (môn học + sĩ số) và tập cạnh E + trọng số W (cặp môn xung đột)
  trực tiếp từ PostgreSQL bằng truy vấn SQL Self-Join tối ưu theo `ky_thi_id`.
- Tận dụng 2 composite indexes trên bảng `dang_ky_thi`:
  + `idx_dang_ky_thi_ky_thi_mon (ky_thi_id, mon_hoc_id)`
  + `idx_dang_ky_thi_ky_thi_sv (ky_thi_id, sinh_vien_id)`
- Dựng đối tượng `nx.Graph` tương thích 100% với tầng thuật toán thuần túy
  (`coloring.py`, `room_allocator.py`, `verifier.py`), đồng thời giữ sẵn `mon_hoc_id`
  trên từng đỉnh để phục vụ bước ghi bảng `lich_thi` (Ngày 9–10).
"""

from typing import Any, Dict, List
import networkx as nx
from sqlalchemy import text
from sqlalchemy.orm import Session


# Truy vấn 1: Trích xuất tập đỉnh V và sĩ số đăng ký theo kỳ thi
SQL_FETCH_GRAPH_NODES = text(
    """
    SELECT
        m.id AS mon_hoc_id,
        m.ma_mon,
        m.ten_mon,
        COUNT(DISTINCT dk.sinh_vien_id) AS so_luong_sv
    FROM mon_hoc m
    JOIN dang_ky_thi dk ON m.id = dk.mon_hoc_id
    WHERE dk.ky_thi_id = :ky_thi_id
    GROUP BY m.id, m.ma_mon, m.ten_mon
    ORDER BY so_luong_sv DESC, m.ma_mon ASC
    """
)

# Truy vấn 2: Self-Join tối ưu trích xuất tập cạnh E và trọng số xung đột W
# Điều kiện dk1.mon_hoc_id < dk2.mon_hoc_id loại bỏ cạnh tự khuyên (u = v)
# và loại trừ cạnh lặp đối xứng (u, v) <-> (v, u) của đồ thị vô hướng.
SQL_FETCH_GRAPH_EDGES = text(
    """
    SELECT
        m1.id AS mon_u_id,
        m1.ma_mon AS mon_u,
        m2.id AS mon_v_id,
        m2.ma_mon AS mon_v,
        COUNT(DISTINCT dk1.sinh_vien_id) AS trong_so_xung_dot
    FROM dang_ky_thi dk1
    JOIN dang_ky_thi dk2
      ON dk1.sinh_vien_id = dk2.sinh_vien_id
     AND dk1.ky_thi_id    = dk2.ky_thi_id
     AND dk1.mon_hoc_id   < dk2.mon_hoc_id
    JOIN mon_hoc m1 ON m1.id = dk1.mon_hoc_id
    JOIN mon_hoc m2 ON m2.id = dk2.mon_hoc_id
    WHERE dk1.ky_thi_id = :ky_thi_id
    GROUP BY m1.id, m1.ma_mon, m2.id, m2.ma_mon
    ORDER BY trong_so_xung_dot DESC, m1.ma_mon ASC, m2.ma_mon ASC
    """
)

SQL_CHECK_EXAM_EXISTS = text(
    """
    SELECT id FROM ky_thi WHERE id = :ky_thi_id LIMIT 1
    """
)


def _validate_ky_thi_id(ky_thi_id: Any) -> int:
    """Kiểm tra tính hợp lệ của tham số ky_thi_id."""
    if isinstance(ky_thi_id, bool) or not isinstance(ky_thi_id, int):
        raise ValueError(f"ky_thi_id không hợp lệ (cần số nguyên dương): {ky_thi_id!r}")
    if ky_thi_id <= 0:
        raise ValueError(f"ky_thi_id phải lớn hơn 0, nhận được: {ky_thi_id}")
    return ky_thi_id


def fetch_conflict_graph_nodes(db: Session, ky_thi_id: int) -> List[Dict[str, Any]]:
    """Trích xuất tập đỉnh V (các môn thi có sinh viên đăng ký) từ PostgreSQL.

    Args:
        db: SQLAlchemy Session kết nối tới PostgreSQL.
        ky_thi_id: Khóa chính ID của kỳ thi cần xếp lịch.

    Returns:
        Danh sách dict [{'mon_hoc_id', 'ma_mon', 'ten_mon', 'size'}],
        sắp xếp giảm dần theo số lượng sinh viên dự thi.
    """
    exam_id = _validate_ky_thi_id(ky_thi_id)
    rows = db.execute(SQL_FETCH_GRAPH_NODES, {"ky_thi_id": exam_id}).mappings().all()

    return [
        {
            "mon_hoc_id": int(row["mon_hoc_id"]),
            "ma_mon": str(row["ma_mon"]).strip(),
            "ten_mon": str(row["ten_mon"] or "").strip(),
            "size": int(row["so_luong_sv"]),
        }
        for row in rows
    ]


def fetch_conflict_graph_edges(db: Session, ky_thi_id: int) -> List[Dict[str, Any]]:
    """Trích xuất tập cạnh E và trọng số xung đột W bằng truy vấn SQL Self-Join.

    Args:
        db: SQLAlchemy Session kết nối tới PostgreSQL.
        ky_thi_id: Khóa chính ID của kỳ thi cần xếp lịch.

    Returns:
        Danh sách dict [{'mon_u_id', 'mon_u', 'mon_v_id', 'mon_v', 'weight'}],
        sắp xếp giảm dần theo số lượng sinh viên thi chung.
    """
    exam_id = _validate_ky_thi_id(ky_thi_id)
    rows = db.execute(SQL_FETCH_GRAPH_EDGES, {"ky_thi_id": exam_id}).mappings().all()

    return [
        {
            "mon_u_id": int(row["mon_u_id"]),
            "mon_u": str(row["mon_u"]).strip(),
            "mon_v_id": int(row["mon_v_id"]),
            "mon_v": str(row["mon_v"]).strip(),
            "weight": int(row["trong_so_xung_dot"]),
        }
        for row in rows
    ]


def build_conflict_graph_from_db(db: Session, ky_thi_id: int) -> nx.Graph:
    """Dựng đồ thị xung đột G = (V, E, W) trực tiếp từ PostgreSQL theo `ky_thi_id`.

    Mỗi đỉnh dùng `ma_mon` làm định danh (`node_id`) và lưu đầy đủ thuộc tính:
    `mon_hoc_id` (BIGINT PK), `ma_mon`, `ten_mon`, `size` (số thí sinh).
    Mỗi cạnh vô hướng `(mon_u, mon_v)` mang trọng số `weight` (số SV thi chung).

    Args:
        db: SQLAlchemy Session kết nối tới PostgreSQL.
        ky_thi_id: ID kỳ thi cần dựng đồ thị.

    Returns:
        nx.Graph: Đồ thị xung đột hoàn chỉnh sẵn sàng cho DSatur / Welsh-Powell / FFD / Verifier.

    Raises:
        ValueError: Nếu `ky_thi_id` không hợp lệ hoặc không tồn tại trong bảng `ky_thi`.
    """
    exam_id = _validate_ky_thi_id(ky_thi_id)

    exam_exists = db.execute(SQL_CHECK_EXAM_EXISTS, {"ky_thi_id": exam_id}).first()
    if exam_exists is None:
        raise ValueError(f"Không tìm thấy kỳ thi có id={exam_id} trong cơ sở dữ liệu.")

    nodes = fetch_conflict_graph_nodes(db, exam_id)
    edges = fetch_conflict_graph_edges(db, exam_id)

    G = nx.Graph()

    for node in nodes:
        G.add_node(
            node["ma_mon"],
            mon_hoc_id=node["mon_hoc_id"],
            ma_mon=node["ma_mon"],
            ten_mon=node["ten_mon"],
            size=node["size"],
        )

    for edge in edges:
        G.add_edge(
            edge["mon_u"],
            edge["mon_v"],
            weight=edge["weight"],
        )

    return G
