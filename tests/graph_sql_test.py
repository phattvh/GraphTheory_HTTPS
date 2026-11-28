"""Integration tests for SQL Self-Join graph extraction from PostgreSQL (UC08.1 - Ngày 8).

Chạy trong container:
    docker compose exec fastapi python tests/graph_sql_test.py
"""

from datetime import date
from pathlib import Path
import sys
import time
import networkx as nx

# Thêm thư mục gốc vào PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.algorithms import (
    allocate_graph_schedule_with_overflow,
    build_conflict_graph,
    dsatur_coloring,
    verify_schedule,
)
from backend.core.database import SessionLocal
from backend.models.models import DangKyThi, KyThi, MonHoc, PhongThi, SinhVien
from backend.services import (
    build_conflict_graph_from_db,
    fetch_conflict_graph_edges,
    fetch_conflict_graph_nodes,
)
from scripts.seed import SEED_EXAM_CODE, SEED_ROOMS, seed_database


def test_sql_graph_matches_python_builder_100_percent() -> None:
    """Test 1 & 2 & 3: Đối chiếu đẳng cấu 100% (đỉnh, size, cạnh, trọng số) giữa SQL Self-Join và Python in-memory."""
    seed_database()
    db = SessionLocal()
    try:
        exam = db.query(KyThi).filter(KyThi.ma_ky_thi == SEED_EXAM_CODE).first()
        assert exam is not None, f"Không tìm thấy kỳ thi mẫu {SEED_EXAM_CODE}"

        # 1. Dựng đồ thị bằng truy vấn SQL Self-Join
        t0 = time.perf_counter()
        G_sql = build_conflict_graph_from_db(db, exam.id)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # 2. Dựng đồ thị đối chứng bằng Python từ dữ liệu thô dang_ky_thi
        regs_rows = (
            db.query(SinhVien.mssv, MonHoc.ma_mon)
            .join(DangKyThi, DangKyThi.sinh_vien_id == SinhVien.id)
            .join(MonHoc, DangKyThi.mon_hoc_id == MonHoc.id)
            .filter(DangKyThi.ky_thi_id == exam.id)
            .all()
        )
        G_py = build_conflict_graph([(r[0], r[1]) for r in regs_rows])

        # Kiểm tra tập đỉnh khớp 100%
        assert set(G_sql.nodes()) == set(G_py.nodes()), "Tập đỉnh SQL và Python không khớp!"
        assert G_sql.number_of_nodes() == 15

        # Kiểm tra từng thuộc tính đỉnh (mon_hoc_id, ma_mon, ten_mon, size)
        for ma_mon in G_sql.nodes():
            sql_attr = G_sql.nodes[ma_mon]
            py_attr = G_py.nodes[ma_mon]
            assert isinstance(sql_attr["mon_hoc_id"], int) and sql_attr["mon_hoc_id"] > 0
            assert sql_attr["ma_mon"] == ma_mon
            assert isinstance(sql_attr["ten_mon"], str) and len(sql_attr["ten_mon"]) > 0
            assert sql_attr["size"] == py_attr["size"], (
                f"Lệch sĩ số môn {ma_mon}: SQL={sql_attr['size']} vs Python={py_attr['size']}"
            )

        # Kiểm tra không có cạnh tự khuyên (self-loop) và không có cạnh lặp đối xứng
        assert nx.number_of_selfloops(G_sql) == 0, "Phát hiện cạnh tự khuyên (self-loop)!"
        raw_edges = fetch_conflict_graph_edges(db, exam.id)
        edge_pairs = [tuple(sorted((e["mon_u"], e["mon_v"]))) for e in raw_edges]
        assert len(edge_pairs) == len(set(edge_pairs)), "Phát hiện cạnh lặp đối xứng từ Self-Join!"

        # Kiểm tra tập cạnh và trọng số khớp tuyệt đối 100%
        sql_edges = {
            tuple(sorted((u, v))): d["weight"] for u, v, d in G_sql.edges(data=True)
        }
        py_edges = {
            tuple(sorted((u, v))): d["weight"] for u, v, d in G_py.edges(data=True)
        }
        assert sql_edges == py_edges, "Tập cạnh hoặc trọng số SQL Self-Join lệch so với Python!"
        assert elapsed_ms < 500.0, f"Truy vấn SQL Self-Join quá chậm: {elapsed_ms:.2f} ms"

        print(
            f"[PASS] Test 1-3: SQL Self-Join khớp 100% với Python "
            f"({G_sql.number_of_nodes()} đỉnh, {G_sql.number_of_edges()} cạnh, "
            f"thời gian: {elapsed_ms:.2f} ms)."
        )
    finally:
        db.close()


def test_exam_isolation_by_ky_thi_id() -> None:
    """Test 4: Kiểm chứng cô lập dữ liệu theo ky_thi_id (không rò rỉ đăng ký từ kỳ thi khác)."""
    db = SessionLocal()
    temp_exam_id = None
    try:
        # Dọn bản ghi tồn dư nếu lần chạy trước bị gián đoạn giữa chừng
        db.query(KyThi).filter(KyThi.ma_ky_thi == "KT_TEMP_SQL_ISO_TEST").delete()
        db.flush()

        # Tạo 1 kỳ thi tạm chỉ có đúng 1 sinh viên đăng ký 2 môn
        temp_exam = KyThi(
            ma_ky_thi="KT_TEMP_SQL_ISO_TEST",
            ten_ky_thi="Kỳ thi tạm kiểm tra cô lập SQL Self-Join",
            ngay_bat_dau=date(2026, 9, 1),
            ngay_ket_thuc=date(2026, 9, 10),
            so_ca_moi_ngay=4,
            trang_thai="khoi_tao",
        )
        db.add(temp_exam)
        db.flush()
        temp_exam_id = temp_exam.id

        sv = db.query(SinhVien).first()
        courses = db.query(MonHoc).limit(2).all()
        assert sv is not None and len(courses) == 2

        db.add(DangKyThi(ky_thi_id=temp_exam_id, sinh_vien_id=sv.id, mon_hoc_id=courses[0].id))
        db.add(DangKyThi(ky_thi_id=temp_exam_id, sinh_vien_id=sv.id, mon_hoc_id=courses[1].id))
        db.commit()

        G_iso = build_conflict_graph_from_db(db, temp_exam_id)
        assert G_iso.number_of_nodes() == 2, f"Kỳ vọng 2 đỉnh, nhận {G_iso.number_of_nodes()}"
        assert G_iso.number_of_edges() == 1, f"Kỳ vọng 1 cạnh, nhận {G_iso.number_of_edges()}"
        assert G_iso[courses[0].ma_mon][courses[1].ma_mon]["weight"] == 1
        assert G_iso.nodes[courses[0].ma_mon]["size"] == 1
        assert G_iso.nodes[courses[1].ma_mon]["size"] == 1

        print("[PASS] Test 4: Cô lập tuyệt đối theo ky_thi_id (2 đỉnh, 1 cạnh, 0 rò rỉ dữ liệu).")
    finally:
        db.rollback()
        if temp_exam_id is not None:
            db.query(KyThi).filter(KyThi.id == temp_exam_id).delete()
            db.commit()
        db.close()


def test_empty_exam_and_invalid_exam_id() -> None:
    """Test 5 & 6: Kỳ thi 0 đăng ký trả đồ thị rỗng; ky_thi_id không tồn tại / không hợp lệ ném ValueError."""
    db = SessionLocal()
    empty_exam_id = None
    try:
        db.query(KyThi).filter(KyThi.ma_ky_thi == "KT_TEMP_EMPTY_GRAPH_TEST").delete()
        db.flush()

        empty_exam = KyThi(
            ma_ky_thi="KT_TEMP_EMPTY_GRAPH_TEST",
            ten_ky_thi="Kỳ thi rỗng 0 đăng ký",
            ngay_bat_dau=date(2026, 10, 1),
            ngay_ket_thuc=date(2026, 10, 5),
            so_ca_moi_ngay=4,
            trang_thai="khoi_tao",
        )
        db.add(empty_exam)
        db.commit()
        empty_exam_id = empty_exam.id

        G_empty = build_conflict_graph_from_db(db, empty_exam_id)
        assert G_empty.number_of_nodes() == 0
        assert G_empty.number_of_edges() == 0
        assert fetch_conflict_graph_nodes(db, empty_exam_id) == []
        assert fetch_conflict_graph_edges(db, empty_exam_id) == []

        # Kiểm tra ky_thi_id không tồn tại, tràn PostgreSQL BIGINT hoặc kiểu bẩn
        for bad_id in [99999999, 10**25, 0, -5, True, "1"]:
            raised = False
            try:
                build_conflict_graph_from_db(db, bad_id)  # type: ignore[arg-type]
            except ValueError:
                raised = True
            assert raised, f"Kỳ vọng ValueError cho ky_thi_id={bad_id!r}"

        print("[PASS] Test 5-6: Kỳ thi rỗng trả đồ thị 0 đỉnh; ky_thi_id không tồn tại/bẩn ném ValueError.")
    finally:
        db.rollback()
        if empty_exam_id is not None:
            db.query(KyThi).filter(KyThi.id == empty_exam_id).delete()
            db.commit()
        db.close()


def test_end_to_end_sql_to_verifier_pipeline() -> None:
    """Test 7: Luồng khép kín PostgreSQL -> SQL Self-Join -> DSatur -> FFD/Overflow -> Verifier."""
    db = SessionLocal()
    try:
        exam = db.query(KyThi).filter(KyThi.ma_ky_thi == SEED_EXAM_CODE).first()
        assert exam is not None

        rooms = [
            {
                "ma_phong": r.ma_phong,
                "ten_phong": r.ten_phong,
                "suc_chua": r.suc_chua,
                "dang_su_dung": r.dang_su_dung,
            }
            for r in db.query(PhongThi)
            .filter(PhongThi.ma_phong.in_([x["ma_phong"] for x in SEED_ROOMS]))
            .all()
        ]

        G = build_conflict_graph_from_db(db, exam.id)
        coloring = dsatur_coloring(G)
        alloc = allocate_graph_schedule_with_overflow(G, coloring["color_map"], rooms)
        report = verify_schedule(G, alloc, rooms=rooms)

        assert report["is_valid"] is True, f"Pipeline DB->Verifier thất bại: {report['errors']}"
        assert report["summary"]["total_violations"] == 0
        assert report["summary"]["total_courses_scheduled"] == 15
        assert report["summary"]["total_students_scheduled"] == 300

        print(
            f"[PASS] Test 7: End-to-End DB -> SQL Self-Join -> DSatur -> FFD -> Verifier "
            f"(is_valid=True, {alloc['total_shifts']} ca, 15/15 môn, 300/300 SV, 0% xung đột)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    test_sql_graph_matches_python_builder_100_percent()
    test_exam_isolation_by_ky_thi_id()
    test_empty_exam_and_invalid_exam_id()
    test_end_to_end_sql_to_verifier_pipeline()
    print("\nALL SQL SELF-JOIN GRAPH EXTRACTION TESTS PASSED 100%!")
